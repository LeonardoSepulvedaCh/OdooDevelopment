from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PosConfig(models.Model):
    _inherit = 'pos.config'

    pos_default_customer_id = fields.Many2one(
        'res.partner', 
        string='Cliente Predeterminado en el POS', 
        help='Elegir un cliente que se mostrará por defecto en el POS al seleccionar un cliente',
        domain=[('pos_customer', '=', True)]
    )

    @api.constrains('pos_default_customer_id')
    def _check_default_customer(self):
        for record in self:
            if record.pos_default_customer_id:
                if not record.pos_default_customer_id.active:
                    raise ValidationError('El cliente predeterminado debe estar activo.')
