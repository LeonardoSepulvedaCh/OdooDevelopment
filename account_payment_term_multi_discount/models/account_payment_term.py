from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang
from odoo.tools import format_date
from odoo.tools.float_utils import float_round


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    discount_ids = fields.One2many(
        "account.payment.term.discount",
        "payment_term_id",
        string="Early Payment Discounts",
        help="Configure multiple early payment discount options with different percentages and dates",
    )

    @api.depends(
        "discount_ids",
        "discount_ids.discount_percentage",
        "discount_ids.discount_days",
        "discount_ids.delay_type",
    )
    def _compute_example_preview(self):
        super()._compute_example_preview()
        for record in self:
            if record.discount_ids:
                currency = record.currency_id
                example_date = record.example_date or fields.Date.context_today(record)
                preview_lines = []
                for discount in record.discount_ids.sorted(lambda d: d.discount_days):
                    discount_date = discount._get_discount_date(example_date)
                    # Calculate amount after discount
                    # We reuse the logic from _get_amount_due_after_discount but adapted for specific discount
                    total_amount = record.example_amount

                    percentage = discount.discount_percentage / 100.0
                    if record.early_pay_discount_computation in ("excluded", "mixed"):
                        discount_amt = (total_amount - 0.0) * percentage
                    else:
                        discount_amt = total_amount * percentage

                    amount_due = currency.round(total_amount - discount_amt)

                    preview_lines.append(
                        _(
                            "Early Payment Discount: <b>%(amount)s</b> (%(percent)s%%) if paid before <b>%(date)s</b>",
                            amount=formatLang(
                                self.env, amount_due, currency_obj=currency
                            ),
                            percent=discount.discount_percentage,
                            date=format_date(self.env, discount_date),
                        )
                    )

                record.example_preview_discount = "<br/>".join(preview_lines)

    def _get_latest_due_date(self, ref_date):
        """
        Calculate the latest due date from payment term lines.

        :param ref_date: Reference date to calculate due dates
        :return: Latest due date or None if no valid due dates found
        """
        due_dates = [
            line._get_due_date(ref_date)
            for line in self.line_ids
            if line._get_due_date(ref_date)
        ]
        return max(due_dates) if due_dates else None

    def _validate_discount_dates(self, latest_due_date, ref_date):
        """
        Validate that discount dates do not exceed the latest payment due date.

        :param latest_due_date: Latest payment term due date
        :param ref_date: Reference date for discount calculation
        :raises ValidationError: If any discount date exceeds the latest due date
        """
        for discount in self.discount_ids:
            discount_date = discount._get_discount_date(ref_date)
            if discount_date and discount_date > latest_due_date:
                raise ValidationError(
                    _(
                        "The early payment discount date (%(discount_date)s) cannot exceed the last payment deadline (%(latest_due_date)s).",
                        discount_date=discount_date.strftime("%d/%m/%Y"),
                        latest_due_date=latest_due_date.strftime("%d/%m/%Y"),
                    )
                )

    @api.constrains("line_ids", "early_discount", "discount_ids")
    def _check_lines(self):
        """
        Validate payment term lines and discount configurations.
        """
        super()._check_lines()
        for terms in self:
            if not (terms.discount_ids and terms.line_ids):
                continue

            ref_date = fields.Date.today()
            latest_due_date = terms._get_latest_due_date(ref_date)

            if latest_due_date:
                terms._validate_discount_dates(latest_due_date, ref_date)
