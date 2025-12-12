from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    hide_closing_summary = fields.Boolean(
        string='Ocultar resumen al cerrar caja',
        default=True,
        readonly=True,
        help='Oculta el resumen de pagos al cerrar la caja, mostrando únicamente el campo para ingresar el monto de cierre'
    )

    force_cash_denomination_usage = fields.Boolean(
        string='Forzar uso de denominaciones',
        default=True,
        readonly=True,
        help='Obliga al usuario a usar el botón de denominaciones al abrir o cerrar la caja, deshabilitando el campo de entrada manual'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['hide_closing_summary'] = True
            vals['force_cash_denomination_usage'] = True
        return super().create(vals_list)

    def write(self, vals):
        vals['hide_closing_summary'] = True
        vals['force_cash_denomination_usage'] = True
        return super().write(vals)
