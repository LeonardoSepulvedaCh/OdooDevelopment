from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_auto_invoice = fields.Boolean(related='pos_config_id.auto_invoice', readonly=False)