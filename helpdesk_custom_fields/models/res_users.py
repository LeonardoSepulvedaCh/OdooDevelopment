from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    can_close_tickets = fields.Boolean(
        string='Puede finalizar tickets',
        default=False,
        help='Si está activado, este usuario podrá mover tickets a la etapa de finalización'
    )

