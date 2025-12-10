from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountPaymentTermDiscount(models.Model):
    _name = 'account.payment.term.discount'
    _description = 'Payment Term Discount'
    _order = 'discount_days'

    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term', required=True, ondelete='cascade')
    discount_percentage = fields.Float(string='Discount %', required=True, help='Early Payment Discount granted for this payment term')
    discount_days = fields.Integer(string='Days', required=True, default=10)
    delay_type = fields.Selection([
            ('days_after', 'Days after invoice date'),
            ('days_after_end_of_month', 'Days after end of month'),
            ('days_after_end_of_next_month', 'Days after end of next month'),
        ], required=True, default='days_after')
    days_next_month = fields.Char(
        string='Days on the next month',
        readonly=False,
        default='10',
        size=2,
    )

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        for record in self:
            if not (0 <= record.discount_percentage <= 100):
                raise ValidationError(_("Discount percentage must be between 0 and 100."))

    @api.constrains('discount_days')
    def _check_discount_days(self):
        for record in self:
            if record.discount_days < 0:
                raise ValidationError(_("Discount days must be positive."))

    def _get_discount_date(self, date_ref):
        self.ensure_one()
        # Assuming date_utils and relativedelta are imported or available in the context
        # For Odoo, these typically come from odoo.tools.date_utils and dateutil.relativedelta
        from odoo.tools import date_utils
        from dateutil.relativedelta import relativedelta

        due_date = fields.Date.from_string(date_ref) or fields.Date.today()
        if self.delay_type == 'days_after_end_of_month':
            return date_utils.end_of(due_date, 'month') + relativedelta(days=self.discount_days)
        elif self.delay_type == 'days_after_end_of_next_month':
            return date_utils.end_of(due_date + relativedelta(months=1), 'month') + relativedelta(days=self.discount_days)
        return due_date + relativedelta(days=self.discount_days)
