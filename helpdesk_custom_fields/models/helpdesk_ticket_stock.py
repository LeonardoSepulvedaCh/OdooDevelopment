from odoo import fields, models, api


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

