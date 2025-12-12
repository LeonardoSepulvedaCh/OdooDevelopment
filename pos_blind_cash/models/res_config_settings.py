from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_hide_closing_summary = fields.Boolean(
        related='pos_config_id.hide_closing_summary',
        readonly=True,
        string='Ocultar resumen al cerrar caja'
    )

    pos_force_cash_denomination_usage = fields.Boolean(
        related='pos_config_id.force_cash_denomination_usage',
        readonly=True,
        string='Forzar uso de denominaciones'
    )
