from odoo import models, fields, api, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_credit_quota_approver = fields.Boolean(
        string='Aprobador de Cupos de Crédito',
        default=False,
        help='Indica si el usuario tiene permisos para aprobar solicitudes de cupo de crédito'
    )

