from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_cashier_user_ids = fields.Many2many(
        related='pos_config_id.cashier_user_ids',
        readonly=False,
        string='Cajeros del POS'
    )
    
    pos_salesperson_user_ids = fields.Many2many(
        related='pos_config_id.salesperson_user_ids',
        readonly=False,
        string='Vendedores del POS'
    )
