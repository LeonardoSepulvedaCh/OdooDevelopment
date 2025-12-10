from odoo import models, fields, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _is_eligible_for_early_payment_discount(self, currency, reference_date):
        """Extend to support multiple early payment discounts"""
        self.ensure_one()

        # First check standard logic. If it passes, good.
        if super()._is_eligible_for_early_payment_discount(currency, reference_date):
            return True
        
        if not self.invoice_payment_term_id.discount_ids:
            # If no multi-discount configured, rely on super (or standard fallback logic if super failed only due to partials)
            # But super fails for partials. So we replicate logic but allowing partials.
            
            # Re-check logic for standard single EPD but allowing partials
            payment_terms = self.line_ids.filtered(lambda line: line.display_type == 'payment_term')
            if not payment_terms:
                return False
                
            if not (
                self.currency_id == currency 
                and self.move_type in self._early_payment_discount_move_types() 
                and self.invoice_payment_term_id.early_discount
            ):
                return False
                
            if not reference_date or not self.invoice_date:
                return True
                
            # Check date for single discount
            existing_discount_date = payment_terms[0].discount_date
            return existing_discount_date and reference_date <= existing_discount_date
        
        # Multiple Discounts Logic
        payment_terms = self.line_ids.filtered(lambda line: line.display_type == 'payment_term')
        if not payment_terms:
            return False
        
        if not (
            self.currency_id == currency 
            and self.move_type in self._early_payment_discount_move_types() 
            and self.invoice_payment_term_id.early_discount
        ):
            return False

        # Allow partial payments for EPD (removed check for matched debits/credits)
        # if payment_terms.sudo().matched_debit_ids + payment_terms.sudo().matched_credit_ids:
        #    return False
            
        if not reference_date or not self.invoice_date:
            return True
        
        invoice_date = self.invoice_date or fields.Date.context_today(self)
        for discount in self.invoice_payment_term_id.discount_ids:
            discount_date = discount._get_discount_date(invoice_date)
            if reference_date <= discount_date:
                return True
        
        return False

    def _get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line(self):
        """
        Override to support Dynamic Multi-Discount percentages.
        Standard Odoo uses the stored 'discount_percentage' and 'discount_amount_currency'.
        We need to scale the result to match the CURRENTLY APPLICABLE discount percentage.
        """
        res = super()._get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line()
        
        # Check if we should apply dynamic scaling
        if not self.invoice_payment_term_id.discount_ids:
            return res
            
        # Determine applicable discount
        payment_date = self.env.context.get('payment_date') or fields.Date.context_today(self)
        invoice_date = self.invoice_date or fields.Date.context_today(self)
        
        applicable_discount = False
        possible_discounts = []
        for discount in self.invoice_payment_term_id.discount_ids:
            discount_date = discount._get_discount_date(invoice_date)
            if payment_date <= discount_date:
                possible_discounts.append(discount)
        
        if possible_discounts:
            applicable_discount = max(possible_discounts, key=lambda d: d.discount_percentage)
            
        dynamic_percentage = applicable_discount.discount_percentage if applicable_discount else 0.0
        standard_percentage = self.invoice_payment_term_id.discount_percentage or 0.0
        
        if standard_percentage == dynamic_percentage:
            return res
            
        # Calculate Scaling Factor
        # If standard is 0, we can't scale. But standard usually matches one of the tiers.
        # If standard is 0, res is empty (checked in standard code).
        if not standard_percentage:
             return res # Cannot scale from 0
             
        scaling_factor = dynamic_percentage / standard_percentage
        
        # Apply scaling to all lines in res
        # Res structure: {'term_lines': {line: {group: val}}, 'tax_lines': ..., 'base_lines': ...}
        
        for key in ('term_lines', 'tax_lines', 'base_lines'):
            if key not in res: continue
            for line, groups in res[key].items():
                for group, vals in groups.items():
                    if 'amount_currency' in vals:
                        vals['amount_currency'] *= scaling_factor
                    if 'balance' in vals:
                        vals['balance'] *= scaling_factor
                        
        return res

    def _get_invoice_next_payment_values(self, custom_amount=None):
        """
        Override to suggest proportional amount when EPD is eligible (supporting Multi-Discount).
        Also updates informational fields (dates, messages) to reflect the currently applicable discount.
        """
        res = super()._get_invoice_next_payment_values(custom_amount)
        
        if res.get('installment_state') == 'epd':
            self.ensure_one()
            term_lines = self.line_ids.filtered(lambda l: l.display_type == 'payment_term')
            
            # Total Residual (Gross Debt)
            total_residual = sum(l.amount_residual_currency for l in term_lines)
            # Total Original Gross
            total_original_gross = sum(l.amount_currency for l in term_lines)
            
            # Calculate Dynamic Original Discount based on current date (Context Today)
            invoice_date = self.invoice_date or fields.Date.context_today(self)
            payment_date = fields.Date.context_today(self)
            
            # Find applicable discount percentage and date
            discount_percentage = 0.0
            best_discount_date = False
            
            # Check Multi-Discount
            if self.invoice_payment_term_id.discount_ids:
                possible_discounts = []
                for discount in self.invoice_payment_term_id.discount_ids:
                    discount_date = discount._get_discount_date(invoice_date)
                    if payment_date <= discount_date:
                        possible_discounts.append((discount, discount_date))
                if possible_discounts:
                    best_discount, best_discount_date = max(possible_discounts, key=lambda x: x[0].discount_percentage)
                    discount_percentage = best_discount.discount_percentage
            # Check Single Standard Discount
            elif self.invoice_payment_term_id.early_discount:
                discount_percentage = self.invoice_payment_term_id.discount_percentage
                best_discount_date = term_lines[0].discount_date if term_lines else False

            # Calculate Total Original Discount based on this percentage
            total_original_discount = 0.0
            currency = self.currency_id
            
            if discount_percentage:
                percentage = discount_percentage / 100.0
                
                if self.invoice_payment_term_id.early_pay_discount_computation in ('excluded', 'mixed'):
                    # Discount on Untaxed
                    untaxed = self.amount_untaxed
                    # Total Discount Amount = Untaxed * %
                    total_original_discount = currency.round(untaxed * percentage)
                else:
                    # Discount on Total
                    # Total Discount Amount = Total Gross * %
                    total_original_discount = currency.round(abs(total_original_gross) * percentage)
            
            if not self.currency_id.is_zero(abs(total_original_gross)):
                # Remaining Ratio = Current Residual / Original Gross
                remaining_ratio = abs(total_residual) / abs(total_original_gross)
                
                # Remaining Discount = Original Discount * Remaining Ratio
                remaining_discount = abs(total_original_discount) * remaining_ratio
                
                # Suggested Net = Residual - Remaining Discount
                suggested_net = abs(total_residual) - remaining_discount
                
                # Rounding
                suggested_net = self.currency_id.round(suggested_net)
                
                # Update res amounts
                res['next_amount_to_pay'] = suggested_net
                res['amount_due'] = suggested_net
                
                # Update Informational Fields for Portal Display
                res['epd_discount_amount_currency'] = remaining_discount
                
                if best_discount_date:
                    res['discount_date'] = fields.Date.to_string(best_discount_date)
                    res['next_due_date'] = best_discount_date
                    
                    days_left = max(0, (best_discount_date - payment_date).days)
                    res['epd_days_left'] = days_left
                    
                    if days_left > 0:
                        discount_msg = _(
                            "Discount of %(amount)s if paid within %(days)s days",
                            amount=self.currency_id.format(remaining_discount),
                            days=days_left,
                        )
                    else:
                        discount_msg = _(
                            "Discount of %(amount)s if paid today",
                            amount=self.currency_id.format(remaining_discount),
                        )
                    res['epd_discount_msg'] = discount_msg
                
        return res
