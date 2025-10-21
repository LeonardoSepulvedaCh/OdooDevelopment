from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    is_warranty_team = fields.Boolean(
        string='Es equipo de garantías',
        default=False,
        help='Indica si este equipo maneja tickets de garantías. '
             'Si está activado, los campos personalizados de garantías estarán disponibles en los tickets.'
    )

