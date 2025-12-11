from odoo import models, fields, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """
    Extends sale.order to add POS configurations association for POS store payments.
    """

    _inherit = "sale.order"

    pos_config_ids = fields.Many2many(
        "pos.config",
        "sale_order_pos_config_rel",
        "sale_order_id",
        "pos_config_id",
        string="Associated POS",
        help="POS configurations associated with this order"
    )

    def _check_cart_is_ready_to_be_paid(self):
        """
        Override to skip shipping method validation for POS store payments.
        
        POS store payments don't require a shipping method since the customer
        will pick up the order at the physical store.
        """
        # Check basic cart validity
        if not self._is_cart_ready():
            raise ValidationError(_(
                "Your cart is not ready to be paid, please verify previous steps."
            ))

        # Skip shipping validation if using POS store payment
        if self._is_using_pos_store_payment():
            return

        # Original validation: shipping method required for deliverable products
        if not self.only_services and not self.carrier_id:
            raise ValidationError(_("No shipping method is selected."))

    def _is_using_pos_store_payment(self):
        """
        Check if the current order is using POS store payment method.
        
        :return: True if using POS store payment
        :rtype: bool
        """
        self.ensure_one()
        
        # Check if partner is a POS customer with POS configs
        if not (self.partner_id.pos_customer and self.partner_id.pos_config_ids):
            return False
        
            
        return True
