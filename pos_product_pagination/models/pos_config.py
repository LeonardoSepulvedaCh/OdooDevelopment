from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    products_per_page = fields.Integer(
        string='Productos por Página',
        default=20,
        help='Número de productos a mostrar por página en el POS. '
             'Valores recomendados: entre 10 y 50 productos.'
    )

