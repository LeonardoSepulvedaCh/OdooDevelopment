from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _inherit = ['helpdesk.ticket', 'helpdesk.pacto.mixin']
    _name = 'helpdesk.ticket'

    is_pacto_reposicion = fields.Boolean(
        string='¿Es Pacto de Reposición?',
        default=False,
        tracking=True,
        help='Indica si este ticket de garantía corresponde a un pacto de reposición'
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        tracking=True,
        help='Orden de venta relacionada con este ticket de pacto de reposición'
    )

    # Abrir el wizard del liquidador de pacto de reposición
    def action_open_liquidador_pacto(self):
        self.ensure_one()
        
        return {
            'name': _('Liquidador Pacto de Reposición Optimus'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.pacto.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'active_id': self.id,
            },
        }

    # Abrir el wizard de creación de venta
    def action_open_venta_wizard(self):
        self.ensure_one()
        
        if not self.pacto_beneficio_aplica:
            raise UserError(_(
                'El beneficio de pacto de reposición NO aplica para este ticket.\n\n'
                'Las siguientes condiciones deben estar en SI:\n'
                '- ¿Registra su equipo Optimus en la página web dentro de los 30 días posteriores a la compra?\n'
                '- ¿Presenta la factura legal de compra?\n'
                '- ¿Presenta documento de identidad?\n'
                '- ¿Firma el pacto vigente como señal de conocimiento?\n'
                '- ¿Presenta denuncio ante la entidad competente?'
            ))
        
        if self.sale_order_id:
            return {
                'name': _('Orden de Venta'),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': self.sale_order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        if not self.partner_id:
            raise UserError(_('El ticket debe tener un cliente asignado para crear una orden de venta.'))
        
        if not self.product_ids:
            raise UserError(_('El ticket debe tener productos relacionados para crear una orden de venta.'))
        
        sale_order_vals = {
            'partner_id': self.partner_id.id,
            'origin': _('Ticket Pacto de Reposición: %s') % self.name,
        }
        
        sale_order = self.env['sale.order'].create(sale_order_vals)
        
        SaleOrderLine = self.env['sale.order.line']
        for product in self.product_ids:
            line_vals = {
                'order_id': sale_order.id,
                'product_id': product.id,
                'product_uom_qty': 1,
            }
            SaleOrderLine.create(line_vals)
        
        self.write({
            'sale_order_id': sale_order.id
        })
        
        return {
            'name': _('Orden de Venta'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # Ver la orden de venta relacionada
    def action_view_sale_order(self):
        self.ensure_one()
        
        if not self.sale_order_id:
            raise UserError(_('No hay una orden de venta relacionada con este ticket.'))
        
        return {
            'name': _('Orden de Venta'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            if not self.pacto_nombre_cliente:
                self.pacto_nombre_cliente = self.partner_id.name
            if not self.pacto_almacen_venta:
                self.pacto_almacen_venta = self.partner_id.name

    @api.onchange('is_pacto_reposicion')
    def _onchange_is_pacto_reposicion(self):
        if not self.is_pacto_reposicion:
            self._limpiar_campos_pacto()
        else:
            if not self.pacto_fecha_envio_comercial and self.create_date:
                fecha_creacion = self.create_date.date() if hasattr(self.create_date, 'date') else self.create_date
                self.pacto_fecha_envio_comercial = fecha_creacion

    @api.onchange('invoice_id')
    def _onchange_invoice_id_pacto(self):
        if self.is_pacto_reposicion and self.invoice_id and self.invoice_id.invoice_date:
            if not self.pacto_fecha_compra:
                self.pacto_fecha_compra = self.invoice_id.invoice_date

    @api.onchange('product_ids')
    def _onchange_product_ids_pacto(self):
        if self.is_pacto_reposicion and self.product_ids:
            if not self.pacto_descripcion_bicicleta:
                productos_nombres = ', '.join(self.product_ids.mapped('name'))
                self.pacto_descripcion_bicicleta = productos_nombres
                if not self.pacto_descripcion_entrega:
                    self.pacto_descripcion_entrega = productos_nombres

    def _limpiar_campos_pacto(self):
        self.write({
            'pacto_registro_web_30dias': False,
            'pacto_factura_legal': False,
            'pacto_documento_identidad': False,
            'pacto_testigos_hurto': False,
            'pacto_carta_datos_personales': False,
            'pacto_firma_pacto_vigente': False,
            'pacto_presenta_denuncio': False,
            'pacto_tiempo_reporte': False,
            'pacto_hurto_con_violencia': False,
            'pacto_valor_factura_iva': 0.0,
            'pacto_pvp_actual_iva': 0.0,
        })
