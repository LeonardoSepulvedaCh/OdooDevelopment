from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    hide_closing_summary = fields.Boolean(
        string='Ocultar resumen al cerrar caja',
        default=False,
        help='Oculta el resumen de pagos al cerrar la caja, mostrando únicamente el campo para ingresar el monto de cierre'
    )
