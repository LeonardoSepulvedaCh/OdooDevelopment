# Author: Sebastián Rodríguez
from odoo.addons.website_sale.controllers import payment as website_payment_portal
from odoo import _
from odoo.exceptions import ValidationError
from odoo.http import request


class PaymentPortalCredit(website_payment_portal.PaymentPortal):
    """
    Extension of PaymentPortal to add credit validation for Rutavity provider.
    """

    def _create_transaction(
        self, provider_id, payment_method_id, token_id, amount, currency_id, partner_id, flow,
        tokenization_requested, landing_route, reference_prefix=None, is_validation=False,
        custom_create_values=None, **kwargs
    ):
        """
        Override of `payment` to add a credit validation step for Rutavity credit payments.

        :param int provider_id: The provider of the provider payment method or token, as a
                                `payment.provider` id.
        :param int|None payment_method_id: The payment method, if any, as a `payment.method` id.
        :param int|None token_id: The token, if any, as a `payment.token` id.
        :param float|None amount: The amount to pay, or `None` if in a validation operation.
        :param int|None currency_id: The currency of the amount, as a `res.currency` id, or `None`
                                     if in a validation operation.
        :param int partner_id: The partner making the payment, as a `res.partner` id.
        :param str flow: The online payment flow of the transaction: 'redirect', 'direct' or 'token'.
        :param bool tokenization_requested: Whether the user requested that a token is created.
        :param str landing_route: The route the user is redirected to after the transaction.
        :param str reference_prefix: The custom prefix to compute the full reference.
        :param bool is_validation: Whether the operation is a validation.
        :param dict custom_create_values: Additional create values overwriting the default ones.
        :param dict kwargs: Locally unused data passed to `_is_tokenization_required` and
                            `_compute_reference`.
        :return: The sudoed transaction that was created.
        :rtype: payment.transaction
        """
        provider_sudo = request.env['payment.provider'].sudo().browse(provider_id)
        payment_method_sudo = request.env['payment.method'].sudo().browse(payment_method_id)

        # If payment is with rutavity credit, check partner credit
        if provider_sudo.code == 'rutavity' and payment_method_sudo.code == 'credit':
            partner = request.env['res.partner'].sudo().browse(partner_id)
            amount_to_check = amount or 0.0
            if not partner._has_sufficient_credit(amount_to_check):
                raise ValidationError(_("You do not have sufficient credit to complete this transaction."))

        return super()._create_transaction(
            provider_id, payment_method_id, token_id, amount, currency_id, partner_id, flow,
            tokenization_requested, landing_route,
            reference_prefix=reference_prefix, is_validation=is_validation,
            custom_create_values=custom_create_values, **kwargs
        )
