from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    pos_customer = fields.Boolean(string='Cliente POS', default=False,help='Habilitar para que el cliente sea visible en el POS', index=True)

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields.append('pos_customer')
        return fields