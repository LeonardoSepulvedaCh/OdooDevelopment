from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    can_close_tickets = fields.Boolean(
        string='Puede finalizar tickets',
        default=False,
        help='Si está activado, este usuario podrá mover tickets a la etapa de finalización'
    )
    
    @api.model
    def _has_can_close_tickets_field(self):
        """Verifica si el campo can_close_tickets existe en el modelo"""
        return 'can_close_tickets' in self._fields

