# -*- coding: utf-8 -*-
# Author: Sebastián Rodríguez
from odoo import models, _
from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_credit.controllers.main import CreditController

_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """
        Override of `payment` to return credit-specific rendering values for Rutavity provider.

        Note: `self.ensure_one()` from `_get_rendering_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        rendering_values = super()._get_specific_rendering_values(processing_values)
        
        if self.provider_code == 'rutavity' and self.payment_method_code == 'credit':
            rendering_values.update({
                'api_url': CreditController._process_url,
                'reference': self.reference,
                'payment_method_code': self.payment_method_code,
            })

        return rendering_values

    def _extract_amount_data(self, payment_data):
        """
        Override of `payment` to skip the amount validation for credit offline flow.

        :param dict payment_data: The payment data sent by the provider.
        :return: The amount data, in the {amount: float, currency_code: str, precision_digits: int}
                 format.
        :rtype: dict|None
        """
        if self.provider_code == 'rutavity' and self.payment_method_code == 'credit':
            return None
        return super()._extract_amount_data(payment_data)

    def _apply_updates(self, payment_data):
        """
        Override of `payment` to update the transaction based on the payment data for credit payments.

        Note: `self.ensure_one()` from :meth:`_process`

        :param dict payment_data: The payment data sent by the provider.
        :return: None
        """
        if self.provider_code != 'rutavity' or self.payment_method_code != 'credit':
            return super()._apply_updates(payment_data)

        # Confirm the related sale order
        self._action_confirm_order()

    def _action_confirm_order(self):
        """
        Confirm the related sale order if any.

        Note: `self.ensure_one()`
        :return: None
        """
        self.ensure_one()
        if self.sale_order_ids:
            self.sale_order_ids.filtered(
                lambda so: so.state == 'draft'
            ).with_context(send_email=True).action_confirm()

    def _get_sent_message(self):
        """
        Override of `payment` to return a different message for credit payments.

        Note: `self.ensure_one()`

        :return: The message to log.
        :rtype: str
        """
        message = super()._get_sent_message()
        if self.provider_code == 'rutavity' and self.payment_method_code == 'credit':
            message = _("Selected payment method: %s",
                        self.payment_method_id.name)
        return message
