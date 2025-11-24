from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json


class PosOrderPending(models.Model):
    _name = 'pos.order.pending'
    _description = 'Orden pendiente'
    _order = 'date_order desc'

    name = fields.Char(string='Nombre de la Orden', required=True)
    pos_reference = fields.Char(string='Referencia POS')
    salesperson_id = fields.Many2one('res.users', string='Vendedor', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente')
    date_order = fields.Datetime(string='Fecha de la Orden', default=fields.Datetime.now, required=True)
    status = fields.Selection([
        ('pending', 'Pendiente'), 
        ('completed', 'Completado'), 
        ('cancelled', 'Cancelado')
    ], string='Estado', default='pending')
    
    amount_total = fields.Float(string='Total con Impuestos')
    amount_untaxed = fields.Float(string='Total sin Impuestos') 
    amount_tax = fields.Float(string='Impuestos')
    
    order_lines = fields.Text(string='Líneas de la Orden')
    
    pos_config_id = fields.Many2one('pos.config', string='Punto de Venta')
    note = fields.Text(string='Notas')
    
    @api.constrains('name', 'pos_config_id')
    def _check_unique_name_per_config(self):
        """
        Valida que el nombre del pedido sea único por punto de venta.
        """
        for record in self:
            if record.name and record.pos_config_id:
                # Buscar otros registros con el mismo nombre y config
                existing_orders = self.search([
                    ('name', '=', record.name),
                    ('pos_config_id', '=', record.pos_config_id.id),
                    ('id', '!=', record.id)
                ])
                if existing_orders:
                    raise ValidationError(
                        _('Ya existe un pedido con el nombre "%s" en este punto de venta.') % record.name
                    )
    
    def get_order_lines_data(self):
        if self.order_lines:
            try:
                return json.loads(self.order_lines)
            except (ValueError, TypeError):
                return []
        return []
    
    def set_order_lines_data(self, lines_data):
        self.order_lines = json.dumps(lines_data) if lines_data else False
    