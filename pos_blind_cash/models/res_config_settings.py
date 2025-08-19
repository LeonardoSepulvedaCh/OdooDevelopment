from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_hide_closing_summary = fields.Boolean(
        related='pos_config_id.hide_closing_summary',
        readonly=False,
        string='Ocultar resumen al cerrar caja'
    )
