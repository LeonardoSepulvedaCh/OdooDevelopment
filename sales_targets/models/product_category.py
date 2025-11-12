from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    active_for_targets = fields.Boolean(
        string='Activa para Metas',
        default=False,
        help='Si está marcada, esta categoría estará disponible para asignar metas de ventas.',
    )

