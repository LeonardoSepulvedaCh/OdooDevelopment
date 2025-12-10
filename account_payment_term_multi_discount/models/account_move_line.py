from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_installments_data(self, payment_currency=None, payment_date=None, next_payment_date=None):
        installments = super()._get_installments_data(payment_currency, payment_date, next_payment_date)
        
        move = self.move_id
        if not move.invoice_payment_term_id.discount_ids:
            return installments

        payment_date = payment_date or fields.Date.context_today(self)
        
        # Find applicable discount
        applicable_discount = False
        possible_discounts = []
        for discount in move.invoice_payment_term_id.discount_ids:
            discount_date = discount._get_discount_date(move.invoice_date or fields.Date.context_today(self))
            if payment_date <= discount_date:
                possible_discounts.append(discount)
        
        if possible_discounts:
            # Pick the one with highest percentage
            applicable_discount = max(possible_discounts, key=lambda d: d.discount_percentage)
        
        if not applicable_discount:
            # No discount applicable. 
            pass
        
        # We need to iterate over the result and fix it.
        for installment in installments:
            if installment['type'] == 'early_payment_discount':
                # Re-calculate amounts based on applicable_discount
                if applicable_discount:
                    line = installment['line']
                    
                    move = line.move_id
                    percentage = applicable_discount.discount_percentage / 100.0
                    
                    # We need to handle currency rounding
                    currency = line.currency_id
                    company_currency = line.company_currency_id
                    
                    # Re-implementing the calculation logic:
                    if move.invoice_payment_term_id.early_pay_discount_computation in ('excluded', 'mixed'):
                        # Discount on untaxed amount only
                        # Example: Invoice $1,150 = $1,000 untaxed + $150 tax
                        # 10% discount = $100 (10% of $1,000)
                        # Amount to pay = $1,150 - $100 = $1,050
                        
                        untaxed = move.amount_untaxed
                        total = move.amount_total
                        
                        # Calculate discount on untaxed amount
                        discount_on_untaxed = currency.round(untaxed * percentage)
                        discount_amount_currency = currency.round(total - discount_on_untaxed)
                        
                        # Same for company currency
                        discount_on_untaxed_company = company_currency.round(move.amount_untaxed_signed * percentage)
                        discount_balance = company_currency.round(move.amount_total_signed - discount_on_untaxed_company)
                        
                    else:
                        # Included: Discount on total amount
                        discount_amount_currency = currency.round(line.amount_currency * (1 - percentage))
                        discount_balance = company_currency.round(line.balance * (1 - percentage))


                    # Update installment
                    sign = move.direction_sign
                    installment.update({
                        'amount_residual_currency': discount_amount_currency,
                        'amount_residual': discount_balance,
                        'amount_residual_currency_unsigned': -sign * discount_amount_currency,
                        'amount_residual_unsigned': -sign * discount_balance,
                        'discount_amount_currency': line.amount_currency - discount_amount_currency,
                        'discount_amount': line.balance - discount_balance,
                    })
                else:
                    # No applicable discount found (e.g. expired)
                    # Revert to standard payment (no discount).
                    line = installment['line']
                    installment.update({
                        'amount_residual_currency': line.amount_residual_currency,
                        'amount_residual': line.amount_residual,
                        'amount_residual_currency_unsigned': -move.direction_sign * line.amount_residual_currency,
                        'amount_residual_unsigned': -move.direction_sign * line.amount_residual,
                        'type': 'other', 
                    })
                    
                    # Re-eval type
                    if next_payment_date and (line.date_maturity or line.date) <= next_payment_date:
                        installment['type'] = 'before_date'
                    elif (line.date_maturity or line.date) < payment_date:
                        installment['type'] = 'overdue'
                    else:
                        installment['type'] = 'next' 
                        
        return installments
