from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _is_eligible_for_early_payment_discount(self, currency, reference_date):
        """
        Override to allow Early Payment Discount (EPD) on invoices with partial payments.

        Standard Odoo behavior disables EPD eligibility once any partial payment is made.
        This override removes that restriction, enabling proportional discount application
        across multiple partial payments within the discount period.

        :param currency: Currency to validate against invoice currency
        :param reference_date: Date to check if within discount period
        :return: True if invoice is eligible for EPD, False otherwise
        """
        # First check standard logic. If it passes, good.
        if super()._is_eligible_for_early_payment_discount(currency, reference_date):
            return True

        self.ensure_one()
        payment_terms = self.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )

        # Re-check basic conditions from original method, but OMIT the partial payment check
        # Original check: and not (payment_terms.sudo().matched_debit_ids + payment_terms.sudo().matched_credit_ids)

        return (
            self.currency_id == currency
            and self.move_type in self._early_payment_discount_move_types()
            and self.invoice_payment_term_id.early_discount
            and (
                not reference_date
                or not self.invoice_date
                or (
                    (existing_discount_date := next(iter(payment_terms)).discount_date)
                    and reference_date <= existing_discount_date
                )
            )
        )

    def _get_invoice_next_payment_values(self, custom_amount=None):
        """
        Override to suggest proportional amount when EPD is eligible.
        
        When a custom amount is provided (partial payment context) or when determining 
        next installment, if EPD is applicable, we calculate the suggested amount 
        subtracting the proportional discount.
        
        Standard Odoo behavior applies full discount if eligible, which is wrong for partials.
        """
        self.ensure_one()
        res = super()._get_invoice_next_payment_values(custom_amount)
        
        if res.get('installment_state') == 'epd':            
            term_lines = self.line_ids.filtered(lambda l: l.display_type == 'payment_term')
            
            # Total Residual (Gross Debt)
            total_residual = sum(l.amount_residual_currency for l in term_lines)
            
            # Total Original Net (Discounted)
            total_original_net = sum(l.discount_amount_currency for l in term_lines)
            
            # Total Original Gross
            total_original_gross = sum(l.amount_currency for l in term_lines)
            
            # Total Original Discount
            # Use abs to handle signs correctly
            total_original_discount = abs(total_original_gross) - abs(total_original_net)
            
            if not self.currency_id.is_zero(abs(total_original_gross)):
                # Remaining Ratio = Current Residual / Original Gross
                remaining_ratio = abs(total_residual) / abs(total_original_gross)
                
                # Remaining Discount = Original Discount * Remaining Ratio
                remaining_discount = total_original_discount * remaining_ratio
                
                # Suggested Net = Residual - Remaining Discount
                suggested_net = abs(total_residual) - remaining_discount
                
                # Rounding
                suggested_net = self.currency_id.round(suggested_net)
                
                # Update res
                # next_amount_to_pay is what is shown in portal button
                res['next_amount_to_pay'] = suggested_net
                res['amount_due'] = suggested_net # Update amount due displayed
                
        return res
