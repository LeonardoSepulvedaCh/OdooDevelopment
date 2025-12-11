# -*- coding: utf-8 -*-
# Author: Sebastián Rodríguez
from odoo import api, models, _
from odoo.addons.payment import utils as payment_utils


class PaymentMethod(models.Model):
    """
    Extends payment.method to filter POS store payment based on partner configuration.
    """

    _inherit = "payment.method"

    @api.model
    def _get_compatible_payment_methods(
        self,
        provider_ids,
        partner_id,
        currency_id=None,
        force_tokenization=False,
        is_express_checkout=False,
        report=None,
        **kwargs
    ):
        """
        Override to filter payment methods based on partner POS customer status.

        Logic:
        - If partner is a POS customer (pos_customer=True) with POS configs assigned:
          * Only show pos_store payment method (hide all others)
        - If partner is NOT a POS customer or has no POS configs:
          * Hide pos_store payment method (show all others)

        :param list provider_ids: Provider IDs to check
        :param int partner_id: Partner making the payment
        :param int currency_id: Currency ID
        :param bool force_tokenization: Whether tokenization is required
        :param bool is_express_checkout: Whether it's express checkout
        :param dict report: Availability report
        :param dict kwargs: Additional context (sale_order_id, is_invoice_payment, etc.)
        :return: Compatible payment methods
        :rtype: payment.method
        """
        compatible_methods = super()._get_compatible_payment_methods(
            provider_ids,
            partner_id,
            currency_id=currency_id,
            force_tokenization=force_tokenization,
            is_express_checkout=is_express_checkout,
            report=report,
            **kwargs
        )

        # Get context information
        partner = self.env["res.partner"].browse(partner_id).exists()
        is_pos_customer = self._is_valid_pos_customer(partner, kwargs)
        pos_store_method = compatible_methods.filtered(lambda m: m.code == "pos_store")

        # Skip filtering for express checkout - show all compatible methods
        if is_express_checkout:
            return compatible_methods

        if is_pos_customer:
            compatible_methods = self._filter_for_pos_customer(
                compatible_methods, pos_store_method, report
            )
        else:
            compatible_methods = self._filter_for_regular_customer(
                compatible_methods, pos_store_method, partner, kwargs, report
            )

        return compatible_methods

    def _is_valid_pos_customer(self, partner, kwargs):
        """
        Check if partner is a valid POS customer with proper configuration.

        :param partner: res.partner record
        :param kwargs: Additional context
        :return: True if valid POS customer
        :rtype: bool
        """
        sale_order_id = kwargs.get("sale_order_id")
        is_invoice_payment = kwargs.get("is_invoice_payment", False)
        sale_order = (
            self.env["sale.order"].browse(sale_order_id).exists()
            if sale_order_id
            else False
        )

        return (
            partner
            and partner.pos_customer
            and partner.pos_config_ids
            and not is_invoice_payment
            and sale_order
        )

    def _filter_for_pos_customer(self, compatible_methods, pos_store_method, report):
        """
        Filter payment methods for POS customers (only show pos_store).

        :param compatible_methods: All compatible methods
        :param pos_store_method: POS store payment method
        :param report: Availability report
        :return: Filtered payment methods
        :rtype: payment.method
        """
        if not pos_store_method:
            return compatible_methods

        # Keep only pos_store method
        other_methods = compatible_methods - pos_store_method

        # Add reasons for why other methods are not available
        for method in other_methods:
            payment_utils.add_to_report(
                report,
                method,
                available=False,
                reason=_("Only POS store payment is available for POS customers"),
            )

        return pos_store_method

    def _filter_for_regular_customer(
        self, compatible_methods, pos_store_method, partner, kwargs, report
    ):
        """
        Filter payment methods for regular customers (hide pos_store).

        :param compatible_methods: All compatible methods
        :param pos_store_method: POS store payment method
        :param partner: res.partner record
        :param kwargs: Additional context
        :param report: Availability report
        :return: Filtered payment methods
        :rtype: payment.method
        """
        if not pos_store_method:
            return compatible_methods

        # Remove POS store method from compatible methods
        compatible_methods = compatible_methods - pos_store_method

        # Get reason for unavailability
        reason = self._get_pos_store_unavailable_reason(partner, kwargs)

        # Add to report why POS store is not available
        payment_utils.add_to_report(
            report,
            pos_store_method,
            available=False,
            reason=reason,
        )

        return compatible_methods

    def _get_pos_store_unavailable_reason(self, partner, kwargs):
        """
        Get the reason why POS store payment is not available.

        :param partner: res.partner record
        :param kwargs: Additional context
        :return: Reason message
        :rtype: str
        """
        sale_order_id = kwargs.get("sale_order_id")
        is_invoice_payment = kwargs.get("is_invoice_payment", False)
        sale_order = (
            self.env["sale.order"].browse(sale_order_id).exists()
            if sale_order_id
            else False
        )

        if is_invoice_payment or not sale_order:
            return _("POS store payment is only available for sale orders")
        if not partner or not partner.pos_customer:
            return _("POS store payment is only available for POS customers")
        return _("No POS configuration assigned to this customer")
