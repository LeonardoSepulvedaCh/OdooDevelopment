from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    can_close_tickets = fields.Boolean(
        string='Puede gestionar todas las etapas de tickets',
        default=False,
        help='Si está activado, este usuario podrá mover tickets a través de todas las etapas del flujo, '
             'incluyendo "Por Realizar (Despacho)", "Rechazado" y "Resuelto". '
             'Los usuarios sin este permiso solo pueden mover tickets de "Nuevo" a "Pendiente de Revisión".'
    )
    
    @api.model
    def _has_can_close_tickets_field(self):
        """Verifica si el campo can_close_tickets existe en el modelo"""
        return 'can_close_tickets' in self._fields

