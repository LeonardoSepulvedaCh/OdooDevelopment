from odoo import _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.addons.payment_credit.controllers import payment as payment_credit


class PaymentPortalPortfolioBlock(payment_credit.PaymentPortalCredit):

    def _create_transaction(
        self, provider_id, payment_method_id, token_id, amount, currency_id, partner_id, flow,
        tokenization_requested, landing_route, reference_prefix=None, is_validation=False,
        custom_create_values=None, **kwargs
    ):
        provider_sudo = request.env['payment.provider'].sudo().browse(provider_id)
        payment_method_sudo = request.env['payment.method'].sudo().browse(payment_method_id)

        # Si el pago es con credito Rutavity, verifica primero el bloqueo por cartera
        if provider_sudo.code == 'rutavity' and payment_method_sudo.code == 'credit':
            partner = request.env['res.partner'].sudo().browse(partner_id)
            
            # Verifica si el contacto está bloqueado por problemas de cartera
            if partner._is_portfolio_blocked():
                block_reason = partner._get_portfolio_block_reason()
                if block_reason:
                    raise ValidationError(
                        _("Su cuenta está bloqueada por problemas de cartera. Razón: %s", block_reason)
                    )
                else:
                    raise ValidationError(
                        _("Su cuenta está bloqueada por problemas de cartera. Por favor, contacte al servicio de atención al cliente.")
                    )

        # Llama al método padre que manejará la validación de crédito
        return super()._create_transaction(
            provider_id, payment_method_id, token_id, amount, currency_id, partner_id, flow,
            tokenization_requested, landing_route,
            reference_prefix=reference_prefix, is_validation=is_validation,
            custom_create_values=custom_create_values, **kwargs
        )

