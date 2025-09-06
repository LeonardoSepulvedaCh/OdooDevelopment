from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    # Campo para almacenar el vendedor seleccionado
    salesperson_id = fields.Many2one(
        'res.users',
        string='Vendedor',
        help='Vendedor responsable de la venta'
    )
    
    @api.model
    def _process_order(self, order, existing_order):
        # Si hay un vendedor (salesperson_id) en la orden, establecerlo como user_id
        if order.get('salesperson_id'):
            order['user_id'] = order['salesperson_id']
            _logger.info("Estableciendo user_id=%s basado en salesperson_id para orden %s", 
                        order['salesperson_id'], order.get('name', 'sin nombre'))
        
        # Llamar al método padre
        return super()._process_order(order, existing_order)
    
    def write(self, vals):
        # Si se está actualizando el salesperson_id, también actualizar user_id
        if 'salesperson_id' in vals and vals['salesperson_id']:
            vals['user_id'] = vals['salesperson_id']
            _logger.info("Sincronizando user_id con salesperson_id: %s", vals['salesperson_id'])
        
        return super().write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Si hay salesperson_id pero no user_id, o si queremos forzar el user_id
            if vals.get('salesperson_id'):
                vals['user_id'] = vals['salesperson_id']
                _logger.info("Creando orden con user_id=%s basado en salesperson_id", vals['salesperson_id'])
        
        return super().create(vals_list)
