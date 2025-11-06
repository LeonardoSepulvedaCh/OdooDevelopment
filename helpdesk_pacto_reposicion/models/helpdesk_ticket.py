from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import logging

_logger = logging.getLogger(__name__)


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

    is_pacto_stage_critical = fields.Boolean(
        string='Etapa Crítica para Pacto',
        compute='_compute_is_pacto_stage_critical',
        store=False,
        help='Indica si el ticket está en una etapa crítica (NO en "Nuevo", "Pendiente de Revisión", "Rechazado")'
    )

    # Determinar si el ticket está en una etapa crítica. (NO en "Nuevo", "Pendiente de Revisión", "Rechazado")
    @api.depends('stage_id')
    def _compute_is_pacto_stage_critical(self):
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        
        stage_new_name = IrConfigParam.get_param('helpdesk_custom_fields.stage_new_name', 'Nuevo')
        stage_pending_review_name = IrConfigParam.get_param('helpdesk_custom_fields.stage_pending_review_name', 'Pendiente de Revisión')
        stage_rejected_name = IrConfigParam.get_param('helpdesk_custom_fields.stage_rejected_name', 'Rechazado')
        
        non_critical_stages = [stage_new_name, stage_pending_review_name, stage_rejected_name]
        
        for ticket in self:
            ticket.is_pacto_stage_critical = ticket.stage_id.name not in non_critical_stages

    # Validar que el liquidador esté completo antes de permitir cambios de etapa en tickets de Pacto de Reposición.
    def write(self, vals): 
        if 'stage_id' in vals:
            IrConfigParam = self.env['ir.config_parameter'].sudo()
            
            stage_dispatch_name = IrConfigParam.get_param('helpdesk_custom_fields.stage_dispatch_name', 'Por Realizar (Despacho)')
            stage_waiting_payment_name = IrConfigParam.get_param('helpdesk_pacto_reposicion.stage_waiting_payment_name', 'En espera de pago')
            stage_closed_name = IrConfigParam.get_param('helpdesk_custom_fields.stage_closed_name', 'Resuelto')
            
            new_stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            
            for ticket in self:
                if new_stage.name == stage_waiting_payment_name and not ticket.is_pacto_reposicion:
                    raise ValidationError(_(
                        'La etapa "%s" es exclusiva para tickets de Pacto de Reposición.\n\n'
                        'Los tickets de garantía normales no pueden utilizar esta etapa porque implica '
                        'el envío automático del email de liquidación del pacto.\n\n'
                        'Si este ticket debe ser procesado como Pacto de Reposición, por favor active '
                        'la opción "¿Es Pacto de Reposición?" en el ticket.'
                    ) % new_stage.name)
                
                if ticket.is_pacto_reposicion:
                    if new_stage.name in [stage_dispatch_name, stage_waiting_payment_name, stage_closed_name]:
                        if not ticket._check_datos_completos_liquidador():
                            raise ValidationError(_(
                                'No se puede cambiar el ticket a la etapa "%s" porque el registro del liquidador no está completo.\n\n'
                                'El liquidador debe tener todos sus campos diligenciados antes de realizar este cambio de etapa.\n\n'
                                'Por favor, complete el liquidador accediendo al botón "Liquidador Pacto de Reposición".'
                            ) % new_stage.name)
        
        result = super(HelpdeskTicket, self).write(vals)
        
        if 'stage_id' in vals:
            IrConfigParam = self.env['ir.config_parameter'].sudo()
            stage_waiting_payment_name = IrConfigParam.get_param('helpdesk_pacto_reposicion.stage_waiting_payment_name', 'En espera de pago')
            
            for ticket in self:
                if ticket.is_pacto_reposicion and ticket.stage_id.name == stage_waiting_payment_name:
                    if ticket.pacto_beneficio_aplica and ticket._check_datos_completos_liquidador():
                        try:
                            ticket._send_pacto_email_auto()
                        except Exception as e:
                            _logger.warning(
                                f'No se pudo enviar automáticamente el email del pacto para el ticket {ticket.name}. '
                                f'Error: {str(e)}'
                            )
                            ticket.message_post(
                                body=f'Advertencia: No se pudo enviar automáticamente el email del pacto. Error: {str(e)}',
                                subject='Advertencia: Email no enviado',
                                message_type='notification',
                                subtype_xmlid='mail.mt_note',
                            )
        
        return result

    # Enviar automáticamente el email del pacto de reposición cuando se cambia a "En espera de pago".
    def _send_pacto_email_auto(self):
        self.ensure_one()
        
        from .helpdesk_pacto_email_template import get_email_template_html
        
        if not self.partner_id:
            raise UserError(_('El ticket no tiene un cliente asociado.'))
        
        if not self.partner_id.email:
            raise UserError(_('El cliente no tiene un correo electrónico configurado.'))
        
        pdf_content, pdf_format = self.env['ir.actions.report']._render_qweb_pdf(
            'helpdesk_pacto_reposicion.action_report_pacto_carta',
            res_ids=self.ids
        )
        
        pdf_base64 = base64.b64encode(pdf_content)
        
        nombre_archivo = f'Carta_Pacto_Reposicion_{self.name}.pdf'
        adjunto = self.env['ir.attachment'].create({
            'name': nombre_archivo,
            'type': 'binary',
            'datas': pdf_base64,
            'res_model': 'helpdesk.ticket',
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        
        valor_consignar = self._get_valor_a_consignar()
        valor_formateado = '{:,.0f}'.format(valor_consignar).replace(',', '.')
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        logo_url = f"{base_url}/helpdesk_pacto_reposicion/static/src/img/logo_milan.png"
        porcentaje_aprobacion = f'{self.pacto_porcentaje_aprobacion:.0f}'
        
        cuerpo_email = get_email_template_html(
            self,
            logo_url,
            valor_formateado,
            porcentaje_aprobacion
        )
        
        mail_values = {
            'subject': f'Solicitud de Pacto de Reposición - {self.partner_id.name}',
            'body_html': cuerpo_email,
            'email_to': self.partner_id.email,
            'email_from': self.env.user.email or self.env.company.email or 'servicioalcliente@bicicletasmilan.com',
            'attachment_ids': [(6, 0, [adjunto.id])],
        }
        
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        self.message_post(
            body=f'Se ha enviado automáticamente la carta de liquidación del pacto de reposición al correo {self.partner_id.email}',
            subject='Email Enviado Automáticamente - Carta de Liquidación',
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        
        _logger.info(f'Email del pacto enviado automáticamente para el ticket {self.name} a {self.partner_id.email}')

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
