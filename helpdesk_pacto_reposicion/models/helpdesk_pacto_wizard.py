from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HelpdeskPactoWizard(models.TransientModel):
    _name = 'helpdesk.pacto.wizard'
    _inherit = 'helpdesk.pacto.mixin'
    _description = 'Liquidador Pacto de Reposición'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        readonly=True
    )

    # Sobrescribir campos del mixin para hacerlos requeridos en el wizard
    pacto_fecha_envio_comercial = fields.Date(required=True)
    pacto_almacen_venta = fields.Char(required=True)
    pacto_descripcion_bicicleta = fields.Char(required=True)
    pacto_cod_base_liquidacion = fields.Char(required=True)
    pacto_fecha_compra = fields.Date(required=True)
    pacto_fecha_registro_web = fields.Date(required=True)
    pacto_descripcion_entrega = fields.Char(required=True)
    pacto_registro_web_30dias = fields.Selection(required=True)
    pacto_factura_legal = fields.Selection(required=True)
    pacto_documento_identidad = fields.Selection(required=True)
    pacto_testigos_hurto = fields.Selection(required=True)
    pacto_carta_datos_personales = fields.Selection(required=True)
    pacto_firma_pacto_vigente = fields.Selection(required=True)
    pacto_presenta_denuncio = fields.Selection(required=True)
    pacto_tiempo_reporte = fields.Selection(required=True)
    pacto_hurto_con_violencia = fields.Selection(required=True)
    pacto_valor_factura_iva = fields.Monetary(required=True)
    pacto_pvp_actual_iva = fields.Monetary(required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        ticket_id = self.env.context.get('active_id')
        force_default = self.env.context.get('force_default_values', False)
        
        if ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(ticket_id)
            res['ticket_id'] = ticket.id
            
            # Si force_default_values está en True, solo cargar datos básicos del partner
            if force_default:
                if ticket.partner_id:
                    partner_name = ticket.partner_id.name
                    if 'pacto_nombre_cliente' in fields_list:
                        res.setdefault('pacto_nombre_cliente', partner_name)
                    if 'pacto_almacen_venta' in fields_list:
                        res.setdefault('pacto_almacen_venta', partner_name)
                
                # Traer fecha de envío a comercial desde la fecha de creación del ticket
                if ticket.create_date:
                    if 'pacto_fecha_envio_comercial' in fields_list:
                        # Convertir datetime a fecha
                        fecha_creacion = ticket.create_date.date() if hasattr(ticket.create_date, 'date') else ticket.create_date
                        res.setdefault('pacto_fecha_envio_comercial', fecha_creacion)
                
                # Traer fecha de compra desde la factura
                if ticket.invoice_id and ticket.invoice_id.invoice_date:
                    if 'pacto_fecha_compra' in fields_list:
                        res.setdefault('pacto_fecha_compra', ticket.invoice_id.invoice_date)
                
                # Traer descripción desde los productos del ticket
                if ticket.product_ids:
                    if 'pacto_descripcion_bicicleta' in fields_list:
                        productos_nombres = ', '.join(ticket.product_ids.mapped('name'))
                        res.setdefault('pacto_descripcion_bicicleta', productos_nombres)
                        # La descripción de entrega es la misma que la hurtada
                        if 'pacto_descripcion_entrega' in fields_list:
                            res.setdefault('pacto_descripcion_entrega', productos_nombres)
            else:
                # Si el ticket ya tiene datos del pacto, cargarlos
                if ticket.pacto_fecha_envio_comercial:
                    res.update(self._get_datos_ticket_to_wizard(ticket))
                    # Asegurar que la descripción de entrega esté sincronizada con la hurtada
                    if ticket.pacto_descripcion_bicicleta and 'pacto_descripcion_entrega' in fields_list:
                        if not ticket.pacto_descripcion_entrega or ticket.pacto_descripcion_entrega != ticket.pacto_descripcion_bicicleta:
                            res['pacto_descripcion_entrega'] = ticket.pacto_descripcion_bicicleta
                else:
                    # Si no hay datos guardados, pre-llenar con datos básicos
                    if ticket.partner_id:
                        partner_name = ticket.partner_id.name
                        if 'pacto_nombre_cliente' in fields_list:
                            res.setdefault('pacto_nombre_cliente', partner_name)
                        if 'pacto_almacen_venta' in fields_list:
                            res.setdefault('pacto_almacen_venta', partner_name)
                    
                    # Traer fecha de envío a comercial desde la fecha de creación del ticket
                    if ticket.create_date:
                        if 'pacto_fecha_envio_comercial' in fields_list:
                            # Convertir datetime a fecha
                            fecha_creacion = ticket.create_date.date() if hasattr(ticket.create_date, 'date') else ticket.create_date
                            res.setdefault('pacto_fecha_envio_comercial', fecha_creacion)
                    
                    # Traer fecha de compra desde la factura
                    if ticket.invoice_id and ticket.invoice_id.invoice_date:
                        if 'pacto_fecha_compra' in fields_list:
                            res.setdefault('pacto_fecha_compra', ticket.invoice_id.invoice_date)
                    
                    # Traer descripción desde los productos del ticket
                    if ticket.product_ids:
                        if 'pacto_descripcion_bicicleta' in fields_list:
                            productos_nombres = ', '.join(ticket.product_ids.mapped('name'))
                            res.setdefault('pacto_descripcion_bicicleta', productos_nombres)
                            # La descripción de entrega es la misma que la hurtada
                            if 'pacto_descripcion_entrega' in fields_list:
                                res.setdefault('pacto_descripcion_entrega', productos_nombres)
        
        return res

    def _get_datos_ticket_to_wizard(self, ticket):
        return {
            'pacto_fecha_envio_comercial': ticket.pacto_fecha_envio_comercial,
            'pacto_nombre_cliente': ticket.pacto_nombre_cliente,
            'pacto_almacen_venta': ticket.pacto_almacen_venta,
            'pacto_descripcion_bicicleta': ticket.pacto_descripcion_bicicleta,
            'pacto_cod_base_liquidacion': ticket.pacto_cod_base_liquidacion,
            'pacto_fecha_compra': ticket.pacto_fecha_compra,
            'pacto_fecha_registro_web': ticket.pacto_fecha_registro_web,
            'pacto_descripcion_entrega': ticket.pacto_descripcion_entrega,
            'pacto_registro_web_30dias': ticket.pacto_registro_web_30dias,
            'pacto_factura_legal': ticket.pacto_factura_legal,
            'pacto_documento_identidad': ticket.pacto_documento_identidad,
            'pacto_testigos_hurto': ticket.pacto_testigos_hurto,
            'pacto_carta_datos_personales': ticket.pacto_carta_datos_personales,
            'pacto_firma_pacto_vigente': ticket.pacto_firma_pacto_vigente,
            'pacto_presenta_denuncio': ticket.pacto_presenta_denuncio,
            'pacto_tiempo_reporte': ticket.pacto_tiempo_reporte,
            'pacto_hurto_con_violencia': ticket.pacto_hurto_con_violencia,
            'pacto_valor_factura_iva': ticket.pacto_valor_factura_iva,
            'pacto_pvp_actual_iva': ticket.pacto_pvp_actual_iva,
        }

    def _get_datos_wizard_to_ticket(self):
        self.ensure_one()
        # Guardar los criterios de validación y valores monetarios.
        # Los campos computados (puntos, puntuación y porcentaje) se recalcularán automáticamente
        # gracias a las dependencias @api.depends
        return {
            'pacto_fecha_envio_comercial': self.pacto_fecha_envio_comercial,
            'pacto_nombre_cliente': self.pacto_nombre_cliente,
            'pacto_almacen_venta': self.pacto_almacen_venta,
            'pacto_descripcion_bicicleta': self.pacto_descripcion_bicicleta,
            'pacto_cod_base_liquidacion': self.pacto_cod_base_liquidacion,
            'pacto_fecha_compra': self.pacto_fecha_compra,
            'pacto_fecha_registro_web': self.pacto_fecha_registro_web,
            'pacto_descripcion_entrega': self.pacto_descripcion_entrega,
            'pacto_registro_web_30dias': self.pacto_registro_web_30dias,
            'pacto_factura_legal': self.pacto_factura_legal,
            'pacto_documento_identidad': self.pacto_documento_identidad,
            'pacto_testigos_hurto': self.pacto_testigos_hurto,
            'pacto_carta_datos_personales': self.pacto_carta_datos_personales,
            'pacto_firma_pacto_vigente': self.pacto_firma_pacto_vigente,
            'pacto_presenta_denuncio': self.pacto_presenta_denuncio,
            'pacto_tiempo_reporte': self.pacto_tiempo_reporte,
            'pacto_hurto_con_violencia': self.pacto_hurto_con_violencia,
            'pacto_valor_factura_iva': self.pacto_valor_factura_iva,
            'pacto_pvp_actual_iva': self.pacto_pvp_actual_iva,
        }

    def action_save_liquidador(self):
        self.ensure_one()
        
        if not self.ticket_id:
            raise ValidationError(_('No se encontró el ticket asociado.'))
        
        # Guardar todos los datos en el ticket
        valores = self._get_datos_wizard_to_ticket()
        self.ticket_id.write(valores)
        
        return {'type': 'ir.actions.act_window_close'}

    def action_restablecer_valores(self):
        """Reestablece todos los campos del wizard abriendo uno nuevo con valores por defecto."""
        self.ensure_one()
        
        return {
            'name': _('Liquidador Pacto de Reposición Optimus'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.pacto.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.ticket_id.id,
                'active_id': self.ticket_id.id,
                'force_default_values': True,
            },
        }