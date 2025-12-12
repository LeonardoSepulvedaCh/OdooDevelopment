from odoo import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Extiende el método para asegurar que se carguen los datos del vendedor (user_id) junto con la orden de venta.
    def load_sale_order_from_pos(self, config_id):
        result = super().load_sale_order_from_pos(config_id)
        
        # Cargar los datos del usuario (vendedor) si existe para que se carguen en el POS
        if self.user_id:
            user_fields = self.env['res.users']._load_pos_data_fields(config_id)
            user_read = self.user_id.read(user_fields, load=False)
            result['res.users'] = user_read
        
        return result

