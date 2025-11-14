"""
Extension of account.move model to add effective due date calculation.
"""

from odoo import models, fields, api
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """
    Extension of account.move to add effective due date calculation.

    Adds computed field for effective due date which includes grace period days
    configured in system parameters. This is used for commission calculations
    to determine if payments were made on time.
    """

    _inherit = "account.move"

    effective_due_date = fields.Date(
        compute="_compute_effective_due_date",
        string="Effective due date",
        help="Effective due date + grace days configured in the system. "
        "It is used to calculate if a payment was made on time for commissions.",
    )

    @api.depends("invoice_date_due", "line_ids.date_maturity")
    def _compute_effective_due_date(self):
        """
        Calculate effective due date by adding grace period days to the invoice due date.

        The grace period is configured in ir.config_parameter with key:
        'sale_commission_achievement_target.collection_grace_days'

        For invoices with payment terms (multiple installments), uses the earliest
        non-reconciled installment's maturity date.

        Returns:
            None: Updates the effective_due_date field for each record.
        """
        # Get grace days from system parameters
        grace_days_str = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale_commission_achievement_target.collection_grace_days", "7")
        )

        try:
            grace_days = int(grace_days_str)
            if grace_days < 0:
                _logger.warning(
                    "Grace days parameter is negative (%s), using default 7 days.",
                    grace_days,
                )
                grace_days = 7
        except (ValueError, TypeError) as e:
            _logger.warning(
                "Invalid grace days parameter '%s': %s. Using default 7 days instead.",
                grace_days_str,
                e,
            )
            grace_days = 7

        for move in self:
            # Only process customer invoices and credit notes
            if move.move_type not in ("out_invoice", "out_refund"):
                move.effective_due_date = False
                continue

            # Try to get the next payment values which considers installments
            try:
                payment_values = move._get_invoice_next_payment_values()

                if payment_values and payment_values.get("next_due_date"):
                    # Use the next due date from payment values
                    base_due_date = payment_values["next_due_date"]
                elif move.invoice_date_due:
                    # Fallback to invoice_date_due
                    base_due_date = move.invoice_date_due
                else:
                    # No due date available
                    move.effective_due_date = False
                    continue

                # Add grace period days
                move.effective_due_date = base_due_date + timedelta(days=grace_days)

            except Exception as e:
                _logger.error(
                    "Error calculating effective_due_date for invoice %s: %s",
                    move.name,
                    e,
                    exc_info=True,
                )
                # Fallback to invoice_date_due + grace days if available
                if move.invoice_date_due:
                    move.effective_due_date = move.invoice_date_due + timedelta(
                        days=grace_days
                    )
                else:
                    move.effective_due_date = False
