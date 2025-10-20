from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    can_block_portfolio = fields.Boolean(
        string='Puede Bloquear por Cartera',
        default=False,
        help='Indica si el usuario tiene permisos para bloquear contactos por problemas de cartera'
    )

