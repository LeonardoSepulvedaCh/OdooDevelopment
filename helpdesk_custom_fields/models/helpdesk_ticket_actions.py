from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Sobrescribir create para asignar card_code y consecutivo
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('partner_id') and not vals.get('card_code'):
                partner = self.env['res.partner'].browse(vals['partner_id'])
                if partner.card_code:
                    vals['card_code'] = partner.card_code
            
            # Generar consecutivo usando secuencias de Odoo si se especifica una serie
            if vals.get('serie'):
                vals['consecutive_number'] = self._get_next_consecutive_number(vals['serie'])
        
        return super().create(vals_list)
    
    # Sobrescribir write para regenerar consecutivo y crear actividades
    def write(self, vals):
        # Esto consumirá el numero de la secuencia anterior (ejem: si esta en la serie de cucuta con el 01 y cambio a bucara, el 01 de cucuta no se reutilizara)
        if 'serie' in vals:
            for ticket in self:
                if vals['serie'] != ticket.serie:
                    vals['consecutive_number'] = self._get_next_consecutive_number(vals['serie'])
        
        # Detectar cambio de etapa a "En Progreso" y crear actividades
        if 'stage_id' in vals:
            _logger.info('Detectado cambio de stage_id en write()')
            for ticket in self:
                new_stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
                old_stage_name = ticket.stage_id.name if ticket.stage_id else 'Sin etapa'
                new_stage_name = new_stage.name if new_stage else 'Sin etapa'
                
                _logger.info('Ticket #%s - Cambio de etapa: "%s" -> "%s"', ticket.id, old_stage_name, new_stage_name)
                
                if new_stage and ticket.stage_id != new_stage:
                    trigger_stage_name = self.env['ir.config_parameter'].sudo().get_param(
                        'helpdesk_custom_fields.stage_trigger_name', 
                        default='In Progress'
                    )
                    
                    _logger.info('Etapa configurada para disparar actividades: "%s"', trigger_stage_name)
                    
                    if new_stage.name == trigger_stage_name:
                        _logger.info('La nueva etapa coincide con la configurada - Iniciando creación de actividades')
                        ticket._create_activities_for_warehouse_users()
                    else:
                        _logger.info('La nueva etapa "%s" NO coincide con la etapa configurada "%s"', 
                                    new_stage.name, trigger_stage_name)
                    
                    # Detectar si el ticket pasa a una etapa de finalización
                    closed_stage_name = self.env['ir.config_parameter'].sudo().get_param(
                        'helpdesk_custom_fields.stage_closed_name', 
                        default='Done'
                    )
                    
                    _logger.info('Etapa configurada como finalización: "%s"', closed_stage_name)
                    
                    # Si el ticket pasa a la etapa de finalización y no tiene fecha de cierre
                    if new_stage.name == closed_stage_name and not ticket.date_closed:
                        # Registrar la fecha y hora de finalización
                        vals['date_closed'] = fields.Datetime.now()
                        _logger.info('Ticket #%s - Registrando fecha de finalización: %s', ticket.id, vals['date_closed'])
                    
                    # Si se reabre el ticket (pasa de etapa cerrada a una abierta), limpiar la fecha de cierre
                    if ticket.stage_id.name == closed_stage_name and new_stage.name != closed_stage_name and ticket.date_closed:
                        vals['date_closed'] = False
                        _logger.info('Ticket #%s - Ticket reabierto, limpiando fecha de finalización', ticket.id)
        
        return super().write(vals)
    
    # Obtener el siguiente número consecutivo usando ir.sequence
    def _get_next_consecutive_number(self, serie):
        if not serie:
            return 0
        
        sequence_code = self._SERIE_SEQUENCE_MAP.get(serie)
        if not sequence_code:
            return 0
        
        next_number = self.env['ir.sequence'].next_by_code(sequence_code)
        
        if next_number:
            return int(next_number)
        else:
            return 0
    
    # Enviar mensaje al canal de garantías cuando el ticket pasa a "En Progreso"
    def _create_activities_for_warehouse_users(self):
        self.ensure_one()
        
        _logger.info('=== INICIO: Notificación de ticket en progreso %s ===', self.id)
        _logger.info('Nombre del ticket: %s', self.name)
        _logger.info('Almacén del ticket (branch_id): %s (ID: %s)', 
                     self.branch_id.name if self.branch_id else 'NO ASIGNADO', 
                     self.branch_id.id if self.branch_id else None)
        
        if not self.branch_id:
            _logger.warning('No se puede enviar notificación: El ticket no tiene almacén (branch_id) asignado')
            return
        
        # Buscar o crear el canal de garantías para este almacén
        channel = self._get_or_create_warranty_channel()
        
        if not channel:
            _logger.error('No se pudo obtener o crear el canal de garantías para el almacén %s', self.branch_id.name)
            return
        
        # Obtener el partner del OdooBot o del usuario actual
        try:
            odoobot_user = self.env.ref('base.user_root')
            author_partner = odoobot_user.partner_id
        except Exception:
            author_partner = self.env.user.partner_id
        
        # Construir el mensaje
        serie_display = dict(self._fields['serie'].selection).get(self.serie, self.serie) if self.serie else 'Sin serie'
        
        message_body = """
        <div style="padding: 10px;">
            <h4>
                🎫Nuevo Ticket de Garantía
            </h4>
            <p style="margin: 2px 0;"><strong>Ticket:</strong> %s</p>
            <p style="margin: 2px 0;"><strong>Serie:</strong> %s # %s</p>
            <p style="margin: 2px 0;"><strong>Cliente:</strong> %s</p>
            <p style="margin: 2px 0;"><strong>Almacén:</strong> %s</p>
            <p style="margin: 2px 0;"><strong>Asignado a:</strong> %s</p>
            <p style="margin: 2px 0;"><strong>Descripción:</strong> %s</p>
            <p style="margin-top: 10px; margin-bottom: 0;">
                <a href="/web#id=%s&model=helpdesk.ticket&view_type=form" 
                   style="background-color: #2c3e50; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">
                    Ver Ticket
                </a>
            </p>
        </div>
        """ % (
            self.name or 'Sin nombre',
            serie_display,
            self.consecutive_number or '0',
            self.partner_id.name if self.partner_id else 'Sin cliente',
            self.branch_id.name,
            self.user_id.name if self.user_id else 'Sin asignar',
            self.description or 'Sin descripción',
            self.id
        )
        
        # Enviar el mensaje al canal
        try:
            message = channel.sudo().message_post(
                body=message_body,
                body_is_html=True,
                author_id=author_partner.id if author_partner else False,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            _logger.info('✓ Mensaje enviado al canal "%s" (ID: %s, Mensaje ID: %s)', 
                        channel.name, channel.id, message.id)
        except Exception as e:
            _logger.exception('✗ Error al enviar mensaje al canal: %s', e)
        
        _logger.info('=== FIN: Notificación enviada ===')
    
    # Busca o crea el canal de garantías para el almacén del ticket
    def _get_or_create_warranty_channel(self):
        self.ensure_one()
        
        if not self.branch_id:
            return None
        
        channel_name = f"Garantias {self.branch_id.name}"
        Channel = self.env['discuss.channel']
        
        # Buscar el canal existente
        channel = Channel.sudo().search([
            ('name', '=', channel_name),
            ('channel_type', '=', 'channel')
        ], limit=1)
        
        # Si no existe, crearlo
        if not channel:
            try:
                channel = Channel.sudo().create({
                    'name': channel_name,
                    'channel_type': 'channel',
                    'description': f'Canal de notificaciones de garantías para el almacén {self.branch_id.name}',
                })
                _logger.info('Canal de garantías creado: "%s" (ID: %s)', channel_name, channel.id)
            except Exception as e:
                _logger.exception('Error al crear el canal de garantías "%s": %s', channel_name, e)
                return None
        
        return channel
    
    # Método para imprimir el reporte de garantía con el panel de impresión del navegador
    def action_print_warranty_certificate(self):
        self.ensure_one()
        print_url = '/helpdesk/warranty/print/%s' % self.id
        
        return {
            'type': 'ir.actions.act_url',
            'url': print_url,
            'target': 'new',
        }

