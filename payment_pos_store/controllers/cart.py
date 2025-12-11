from odoo.addons.website_sale.controllers.cart import Cart
from odoo.http import request


class CartPosStore(Cart):
    """
    Extend Cart controller to ensure POS store express checkout values are included.
    """

    def _get_express_shop_payment_values(self, order, **kwargs):
        """
        Override to ensure sale_order_id is included for POS store templates.

        :param sale.order order: The current cart order
        :param dict kwargs: Additional parameters
        :return: Payment values including sale_order_id
        :rtype: dict
        """
        values = super()._get_express_shop_payment_values(order, **kwargs)

        # Add sale_order_id for POS store templates
        values["sale_order_id"] = order.id

        return values
