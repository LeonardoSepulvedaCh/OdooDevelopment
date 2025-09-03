from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_use_custom_receipt = fields.Boolean(
        related='pos_config_id.use_custom_receipt',
        readonly=False,
        string='Usar recibo personalizado'
    )
    
    pos_custom_receipt_header = fields.Text(
        related='pos_config_id.custom_receipt_header',
        readonly=False,
        string='Encabezado personalizado'
    )
    
    pos_custom_receipt_footer = fields.Text(
        related='pos_config_id.custom_receipt_footer',
        readonly=False,
        string='Pie de página personalizado'
    )