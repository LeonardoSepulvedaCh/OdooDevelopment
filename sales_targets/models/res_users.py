from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_salesperson = fields.Boolean(
        string='Es Vendedor',
        default=False,
        help='Marque esta opción si el usuario es un vendedor activo para metas comerciales',
    )

