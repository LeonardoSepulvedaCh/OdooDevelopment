from odoo import models, fields, api, _
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
    
    # Campos para almacenar los totales
    amount_total = fields.Float(string='Total con Impuestos')
    amount_untaxed = fields.Float(string='Total sin Impuestos') 
    amount_tax = fields.Float(string='Impuestos')
    
    # Campo JSON para almacenar las líneas de la orden
    order_lines = fields.Text(string='Líneas de la Orden')
    
    # Campos adicionales
    pos_config_id = fields.Many2one('pos.config', string='Punto de Venta')
    note = fields.Text(string='Notas')
    
    def get_order_lines_data(self):
        """Devuelve las líneas de la orden como lista de diccionarios"""
        if self.order_lines:
            try:
                return json.loads(self.order_lines)
            except:
                return []
        return []
    
    def set_order_lines_data(self, lines_data):
        """Establece las líneas de la orden desde una lista de diccionarios"""
        self.order_lines = json.dumps(lines_data) if lines_data else False
    