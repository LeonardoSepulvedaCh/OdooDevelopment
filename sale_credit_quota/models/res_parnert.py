from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    normal_credit_quota = fields.Float(string='Cupo Normal', digits=(16, 2), default=0.0)
    golden_credit_quota = fields.Float(string='Cupo Dorado', digits=(16, 2), default=0.0)
