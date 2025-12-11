# -*- coding: utf-8 -*-
# Author: Sebastián Rodríguez
from odoo import models, api, _


class PaymentTransaction(models.Model):
    """
    Extends payment.transaction to handle POS store payment method.
    """

    _inherit = "payment.transaction"

    def _get_specific_rendering_values(self, processing_values):
        """
        Override to add POS store specific rendering values.

        :param dict processing_values: The generic and specific processing values
        :return: The dict of provider-specific rendering values
        :rtype: dict
        """
        rendering_values = super()._get_specific_rendering_values(processing_values)

        if self.payment_method_code == "pos_store":
            # Add sale_order_id for POS store templates
            if self.sale_order_ids:
                rendering_values.update(
                    {
                        "sale_order_id": self.sale_order_ids[0].id,
                    }
                )

            # Add API URL and reference for redirect form
            base_url = self.provider_id.get_base_url()
            rendering_values.update(
                {
                    "api_url": f"{base_url}/payment/pos_store/process",
                    "reference": processing_values.get("reference"),
                    "payment_method_code": self.payment_method_code,
                }
            )

        return rendering_values

    def _send_payment_request(self):
        """
        Override to handle POS store payment requests.

        For POS store payments, we don't send any request.
        The order confirmation is handled by the redirect controller.
        """
        if self.payment_method_code == "pos_store":
            return

        return super()._send_payment_request()

    @api.model
    def _send_refund_request(self, amount_to_refund=None):
        """
        Override to prevent refunds for POS store payments.

        POS store refunds must be handled manually at the physical store.
        """
        if self.payment_method_code == "pos_store":
            self._log_message_on_linked_documents(
                _("POS store refunds must be processed manually at the physical store.")
            )
            return

        return super()._send_refund_request(amount_to_refund=amount_to_refund)

    def _send_capture_request(self):
        """
        Override to prevent captures for POS store payments.

        POS store payments don't support manual capture.
        """
        if self.payment_method_code == "pos_store":
            self._log_message_on_linked_documents(
                _("POS store payments are captured automatically at the store.")
            )
            return

        return super()._send_capture_request()

    def _send_void_request(self):
        """
        Override to prevent voids for POS store payments.

        POS store payment cancellations must be handled manually.
        """
        if self.payment_method_code == "pos_store":
            self._log_message_on_linked_documents(
                _(
                    "POS store payment cancellations must be processed manually at the store."
                )
            )
            return

        return super()._send_void_request()

    def _extract_amount_data(self, payment_data):
        """
        Override to skip amount validation for POS store payments.

        POS store payments don't need amount validation since they're processed
        manually at the physical store.
        """
        if self.payment_method_code == "pos_store":
            return None

        return super()._extract_amount_data(payment_data)

    def _apply_updates(self, payment_data):
        """
        Override to handle POS store payment updates.

        For POS store payments, we confirm the sale order but keep the
        transaction in draft state (no payment has been collected yet).
        """
        if self.payment_method_code == "pos_store":
            # Confirm the sale order(s) linked to this transaction
            for sale_order in self.sale_order_ids:
                if sale_order.state in ("draft", "sent"):
                    sale_order._check_cart_is_ready_to_be_paid()
                    sale_order.action_confirm()

            return
        return super()._apply_updates(payment_data)
