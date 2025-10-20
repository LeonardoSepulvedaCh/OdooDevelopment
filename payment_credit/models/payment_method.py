# -*- coding: utf-8 -*-
# Author: Sebastián Rodríguez
from odoo import api, models, _
from odoo.addons.payment import utils as payment_utils


class PaymentMethod(models.Model):
    _inherit = 'payment.method'
    
    @api.model
    def _get_compatible_payment_methods(
        self, provider_ids, partner_id, currency_id=None, force_tokenization=False,
        is_express_checkout=False, report=None, **kwargs
    ):
        """
        Override to filter credit payment method based on payment context.
        
        Credit payment is only available when:
        - There is a sale order context (sale_order_id exists)
        - It's not an invoice payment (is_invoice_payment is False)
        
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
            provider_ids, partner_id, currency_id=currency_id,
            force_tokenization=force_tokenization, is_express_checkout=is_express_checkout,
            report=report, **kwargs
        )
        
        # Check if this is an invoice payment without sale order
        sale_order_id = kwargs.get('sale_order_id')
        is_invoice_payment = kwargs.get('is_invoice_payment', False)
        sale_order = self.env['sale.order'].browse(sale_order_id).exists() if sale_order_id else False
        
        # Filter out credit method if there's no sale order context
        should_filter_credit = is_invoice_payment or not sale_order
        
        if should_filter_credit:
            # Find credit payment method
            credit_method = compatible_methods.filtered(lambda m: m.code == 'credit')
            
            if credit_method:
                # Remove credit method from compatible methods
                compatible_methods = compatible_methods - credit_method
                
                # Add to report why credit is not available
                payment_utils.add_to_report(
                    report,
                    credit_method,
                    available=False,
                    reason=_("Credit payment is only available for sale orders"),
                )
        
        return compatible_methods

