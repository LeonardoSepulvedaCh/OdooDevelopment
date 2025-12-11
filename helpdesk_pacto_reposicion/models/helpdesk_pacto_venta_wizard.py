from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HelpdeskPactoVentaWizard(models.TransientModel):
    _name = 'helpdesk.pacto.venta.wizard'
    _description = 'Wizard para Crear Venta - Pacto de Reposición'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        readonly=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        help='Cliente para la nueva orden de venta'
    )

    product_ids = fields.Many2many(
        'product.product',
        string='Productos',
        required=True,
        help='Productos a incluir en la nueva orden de venta'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        ticket_id = self.env.context.get('default_ticket_id') or self.env.context.get('active_id')
        
        if ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(ticket_id)
            res['ticket_id'] = ticket.id
            
            # Pre-cargar datos del ticket para crear nueva venta
            if 'partner_id' in fields_list and ticket.partner_id:
                res['partner_id'] = ticket.partner_id.id
                
            if 'product_ids' in fields_list and ticket.product_id:
                res['product_ids'] = [(6, 0, [ticket.product_id.id])]
        
        return res

    # Crear nueva venta y relacionarla con el ticket
    def action_crear_venta(self):
        self.ensure_one()
        
        if not self.ticket_id:
            raise ValidationError(_('No se encontró el ticket asociado.'))
        
        return self._crear_nueva_venta()

    def _crear_nueva_venta(self):
        if not self.partner_id:
            raise ValidationError(_('Debe seleccionar un cliente para crear la venta.'))
        
        if not self.product_ids:
            raise ValidationError(_('Debe seleccionar al menos un producto para crear la venta.'))
        
        sale_order_vals = {
            'partner_id': self.partner_id.id,
            'origin': _('Ticket Pacto de Reposición: %s') % self.ticket_id.name,
        }
        
        sale_order = self.env['sale.order'].create(sale_order_vals)
        
        sale_order_line = self.env['sale.order.line']
        for product in self.product_ids:
            line_vals = {
                'order_id': sale_order.id,
                'product_id': product.id,
                'product_uom_qty': 1,
            }
            
            # Aplicar descuento del pacto si cumple con las validaciones mínimas
            if self.ticket_id.pacto_beneficio_aplica and self.ticket_id.pacto_porcentaje_aprobacion > 0:
                line_vals['discount'] = self.ticket_id.pacto_porcentaje_aprobacion
            
            sale_order_line.create(line_vals)
        
        self.ticket_id.write({
            'sale_order_ids': [(4, sale_order.id)]
        })
        
        return {
            'name': _('Orden de Venta'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

