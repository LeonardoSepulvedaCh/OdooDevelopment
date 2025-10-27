from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Enviar mensaje al canal de garantías cuando el ticket pasa a "En Progreso"
    def _create_activities_for_warehouse_users(self):
        self.ensure_one()
          
        if not self.branch_id:
            _logger.warning('No se puede enviar notificación: El ticket no tiene almacén (branch_id) asignado')
            return
        
        channel = self._get_or_create_warranty_channel()
        
        if not channel:
            _logger.error('No se pudo obtener o crear el canal de garantías para el almacén %s', self.branch_id.name)
            return
        
        try:
            odoobot_user = self.env.ref('base.user_root')
            author_partner = odoobot_user.partner_id
        except Exception:
            author_partner = self.env.user.partner_id
        
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
        
        try:
            message = channel.sudo().message_post(
                body=message_body,
                body_is_html=True,
                author_id=author_partner.id if author_partner else False,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            _logger.info('Mensaje enviado al canal "%s" (ID: %s, Mensaje ID: %s)', 
                        channel.name, channel.id, message.id)
        except Exception as e:
            _logger.exception('Error al enviar mensaje al canal: %s', e)

    
    # Busca o crea el canal de garantías para el almacén del ticket
    def _get_or_create_warranty_channel(self):
        self.ensure_one()
        
        if not self.branch_id:
            return None
        
        channel_name = f"Garantias {self.branch_id.name}"
        Channel = self.env['discuss.channel']
        
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
                
                # Agregar automáticamente a los usuarios que tienen este almacén como predeterminado
                self._add_warehouse_users_to_channel(channel, self.branch_id)
                
            except Exception as e:
                _logger.exception('Error al crear el canal de garantías "%s": %s', channel_name, e)
                return None
        
        return channel
    
    # Agregar usuarios al canal de garantías basado en su almacén predeterminado
    def _add_warehouse_users_to_channel(self, channel, warehouse):
        if not channel or not warehouse:
            return
        
        try:
            # Buscar usuarios con este almacén como predeterminado
            users = self.env['res.users'].sudo().search([
                ('property_warehouse_id', '=', warehouse.id),
                ('active', '=', True)
            ])
            
            if not users:
                _logger.info('No se encontraron usuarios con el almacén "%s" como predeterminado', warehouse.name)
                return
            
            partners = users.mapped('partner_id')
            
            channel.sudo().write({
                'channel_member_ids': [(0, 0, {
                    'partner_id': partner.id,
                }) for partner in partners]
            })
            
            _logger.info('✓ Agregados %d usuarios al canal "%s": %s', 
                        len(users), 
                        channel.name, 
                        ', '.join(users.mapped('name')))
            
        except Exception as e:
            _logger.exception('Error al agregar usuarios al canal "%s": %s', channel.name, e)
    
    # Enviar mensaje al canal de garantías cuando el ticket es rechazado
    def _notify_rejection_to_channel(self):
        self.ensure_one()
        
        if not self.branch_id:
            _logger.warning('No se puede enviar notificación: El ticket no tiene almacén (branch_id) asignado')
            return
        
        channel = self._get_or_create_warranty_channel()
        
        if not channel:
            _logger.error('No se pudo obtener o crear el canal de garantías para el almacén %s', self.branch_id.name)
            return
        
        try:
            odoobot_user = self.env.ref('base.user_root')
            author_partner = odoobot_user.partner_id
        except Exception:
            author_partner = self.env.user.partner_id
        
        serie_display = dict(self._fields['serie'].selection).get(self.serie, self.serie) if self.serie else 'Sin serie'
        
        message_body = """
        <div style="padding: 10px; border-left: 4px solid #dc3545;">
            <h4 style="color: #dc3545;">
                ❌ Garantía Rechazada
            </h4>
            <p style="margin: 2px 0;"><strong>Ticket:</strong> %s</p>
            <p style="margin: 2px 0;"><strong>Serie:</strong> %s # %s</p>
            <p style="margin: 2px 0;"><strong>Cliente:</strong> %s</p>
            <p style="margin: 2px 0;"><strong>Almacén:</strong> %s</p>
            <p style="margin: 2px 0;"><strong>Asignado a:</strong> %s</p>
            <p style="margin: 2px 0;"><strong>Descripción:</strong> %s</p>
            <p style="margin: 2px 0;"><strong>Motivo:</strong> %s</p>
            <p style="margin-top: 10px; margin-bottom: 0;">
                <a href="/web#id=%s&model=helpdesk.ticket&view_type=form" 
                   style="background-color: #dc3545; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">
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
            ', '.join(self.tag_ids.mapped('name')) if self.tag_ids else 'No especificado',
            self.id
        )
        
        try:
            message = channel.sudo().message_post(
                body=message_body,
                body_is_html=True,
                author_id=author_partner.id if author_partner else False,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            _logger.info('Mensaje de rechazo enviado al canal "%s" (ID: %s, Mensaje ID: %s)', 
                        channel.name, channel.id, message.id)
        except Exception as e:
            _logger.exception('Error al enviar mensaje de rechazo al canal: %s', e)
        

