from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    # Calcular el número de movimientos de inventario
    def _compute_picking_count_custom(self):
        for ticket in self:
            if hasattr(ticket, 'picking_ids'):
                ticket.picking_count = len(ticket.picking_ids)
            else:
                ticket.picking_count = 0
    
    # Obtener información de los movimientos de inventario
    def _get_inventory_movements_info(self):
        self.ensure_one()
        
        # Verificar si el campo picking_ids existe y tiene valores
        picking_ids = getattr(self, 'picking_ids', False)
        
        if not picking_ids:
            return {
                'has_movements': False,
                'incoming': [],
                'outgoing': [],
                'internal': [],
                'products': []
            }
        
        incoming = []
        outgoing = []
        internal = []
        products_set = set()
        
        for picking in picking_ids:
            picking_info = {
                'name': picking.name,
                'origin': picking.origin or '',
                'date': picking.date_done or picking.scheduled_date,
                'state': dict(picking._fields['state'].selection).get(picking.state, picking.state),
                'partner': picking.partner_id.name if picking.partner_id else '',
                'products': []
            }
            
            # Obtener productos del movimiento
            for move in picking.move_ids:
                product_name = move.product_id.display_name
                products_set.add(product_name)
                picking_info['products'].append({
                    'name': product_name,
                    'qty': move.product_uom_qty,
                    'uom': move.product_uom.name
                })
            
            # Clasificar por tipo de movimiento
            if picking.picking_type_id.code == 'incoming':
                incoming.append(picking_info)
            elif picking.picking_type_id.code == 'outgoing':
                outgoing.append(picking_info)
            elif picking.picking_type_id.code == 'internal':
                internal.append(picking_info)
        
        return {
            'has_movements': True,
            'incoming': incoming,
            'outgoing': outgoing,
            'internal': internal,
            'products': list(products_set)
        }
    
    # Sobrescribe el método para crear automáticamente el picking de reemplazo seleccionando la bodega con stock disponible y respetando su flujo de salida.
    def action_create_replacement(self):
        self.ensure_one()
        
        # Validar que haya un producto seleccionado
        if not self.product_id:
            raise UserError(_('Debe seleccionar un producto antes de crear un reemplazo.'))
        
        # Buscar bodega con stock disponible
        warehouse = self._find_warehouse_with_stock()
        
        if not warehouse:
            # Si no hay bodega con stock, abrir el formulario manual
            return super().action_create_replacement()
        
        # Crear el picking según el flujo de la bodega
        picking = self._create_replacement_picking(warehouse)
        
        # Abrir el picking creado
        return {
            'type': 'ir.actions.act_window',
            'name': _('Orden de Reemplazo'),
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # Busca una bodega que tenga stock disponible del producto del ticket. Retorna el primer warehouse encontrado con stock.
    def _find_warehouse_with_stock(self):
        if not self.product_id:
            return False
        
        # Buscar todas las bodegas activas de la compañía
        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
        ])
        
        _logger.info('Buscando stock de producto %s en %d bodegas', 
                    self.product_id.display_name, len(warehouses))
        
        # Buscar stock en cada bodega
        for warehouse in warehouses:
            stock_qty = self._get_available_qty_in_warehouse(warehouse)
            
            _logger.info('Bodega %s: Stock disponible = %.2f', 
                        warehouse.name, stock_qty)
            
            if stock_qty > 0:
                _logger.info('Bodega seleccionada: %s (Stock: %.2f)', 
                            warehouse.name, stock_qty)
                return warehouse
        
        _logger.warning('No se encontró stock disponible en ninguna bodega para el producto %s', 
                       self.product_id.display_name)
        return False
    
    # Obtiene la cantidad disponible del producto en una bodega específica.
    def _get_available_qty_in_warehouse(self, warehouse):
        if not self.product_id or not warehouse:
            return 0.0
        
        # Obtener la cantidad disponible en la ubicación de stock de la bodega
        stock_location = warehouse.lot_stock_id
        
        if not stock_location:
            return 0.0
        
        # Buscar el stock considerando las ubicaciones hijas
        qty = self.env['stock.quant']._get_available_quantity(
            self.product_id,
            stock_location,
            lot_id=self.lot_id if self.lot_id else None,
            strict=False
        )
        
        return qty
    
    # Crea el picking de reemplazo según el flujo de salida configurado en la bodega.
    def _create_replacement_picking(self, warehouse):
        self.ensure_one()
        
        # Determinar el tipo de operación según el flujo de la bodega
        picking_type = self._get_initial_picking_type(warehouse)
        
        if not picking_type:
            raise UserError(_('No se pudo determinar el tipo de operación para la bodega %s.') % warehouse.name)
        
        # Determinar las ubicaciones origen y destino
        location_src, location_dest = self._get_picking_locations(warehouse, picking_type)
        
        # Preparar valores del picking
        picking_vals = {
            'partner_id': self.partner_id.address_get(['delivery'])['delivery'],
            'picking_type_id': picking_type.id,
            'location_id': location_src.id,
            'location_dest_id': location_dest.id,
            'origin': _('Ticket: %s') % self.name,
            'company_id': self.company_id.id,
            'ticket_id': self.id,
            'is_replacement': True,
            'move_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': self.product_qty or 1.0,
                'product_uom': self.product_id.uom_id.id,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'company_id': self.company_id.id,
            })],
        }
        
        # Crear el picking con el contexto de replacement_create_trigger
        picking = self.env['stock.picking'].with_context(
            replacement_create_trigger=True
        ).create(picking_vals)
        
        # Confirmar el picking para que genere los siguientes pasos automáticamente
        if warehouse.delivery_steps in ('pick_ship', 'pick_pack_ship'):
            picking.action_confirm()
            _logger.info('Picking PICK confirmado - Se generarán automáticamente los siguientes pasos')
        
        _logger.info('Picking de reemplazo creado: %s (Tipo: %s, Bodega: %s)', 
                    picking.name, picking_type.name, warehouse.name)
        
        return picking
    
    # Retorna el tipo de operación inicial según el flujo de salida de la bodega.
    def _get_initial_picking_type(self, warehouse):
        if warehouse.delivery_steps == 'ship_only':
            # 1 paso: directamente OUT
            return warehouse.out_type_id
        elif warehouse.delivery_steps == 'pick_ship':
            # 2 pasos: iniciar con PICK
            return warehouse.pick_type_id
        elif warehouse.delivery_steps == 'pick_pack_ship':
            # 3 pasos: iniciar con PICK
            return warehouse.pick_type_id
        
        return False
    
    # Determina las ubicaciones origen y destino según el tipo de operación.
    def _get_picking_locations(self, warehouse, picking_type):
        # El origen siempre es el stock de la bodega
        location_src = warehouse.lot_stock_id
        
        # El destino depende del flujo de salida
        if warehouse.delivery_steps == 'pick_ship':
            # 2 pasos: de stock a output
            location_dest = warehouse.wh_output_stock_loc_id
        elif warehouse.delivery_steps == 'pick_pack_ship':
            # 3 pasos: de stock a packing
            location_dest = warehouse.wh_pack_stock_loc_id
        else:
            # 1 paso o por defecto: de stock a cliente
            location_dest = self.partner_id.property_stock_customer
        
        return location_src, location_dest

