from odoo import models, fields, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    auto_invoice = fields.Boolean(string='Facturación Automática', default=True, help='Activa la facturación automática por venta.')