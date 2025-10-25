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
    
    # Crear actividades para usuarios del mismo almacén cuando el ticket pasa a "En Progreso"
    def _create_activities_for_warehouse_users(self):
        self.ensure_one()
        
        _logger.info('=== INICIO: Creación de actividades para ticket %s ===', self.id)
        _logger.info('Nombre del ticket: %s', self.name)
        _logger.info('Almacén del ticket (branch_id): %s (ID: %s)', 
                     self.branch_id.name if self.branch_id else 'NO ASIGNADO', 
                     self.branch_id.id if self.branch_id else None)
        
        if not self.branch_id:
            _logger.warning('No se puede crear actividad: El ticket no tiene almacén (branch_id) asignado')
            return
        
        all_users = self.env['res.users'].sudo().search([])
        _logger.info('Total de usuarios en el sistema: %s', len(all_users))
        
        matching_users = all_users.filtered(
            lambda u: u.property_warehouse_id and u.property_warehouse_id.id == self.branch_id.id
        )
        
        _logger.info('Usuarios con el almacén %s:', self.branch_id.name)
        for user in matching_users:
            _logger.info('  - Usuario: %s (ID: %s) - Warehouse: %s', 
                        user.name, user.id, 
                        user.property_warehouse_id.name if user.property_warehouse_id else 'Ninguno')
        
        if not matching_users:
            _logger.warning('No se encontraron usuarios con el almacén %s (ID: %s)', 
                          self.branch_id.name, self.branch_id.id)
            return
        
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            activity_type = self.env['mail.activity.type'].search([], limit=1)
        
        _logger.info('Tipo de actividad a usar: %s', activity_type.name if activity_type else 'Ninguno')
        
        activities_created = 0
        for user in matching_users:
            try:
                activity = self.env['mail.activity'].create({
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model']._get('helpdesk.ticket').id,
                    'activity_type_id': activity_type.id if activity_type else False,
                    'summary': f'Ticket en progreso: {self.name}',
                    'note': f'El ticket #{self.id} de la sucursal {self.branch_id.name} ha pasado a estado "En Progreso".',
                    'user_id': user.id,
                })
                activities_created += 1
                _logger.info('✓ Actividad creada para usuario: %s (ID actividad: %s)', user.name, activity.id)
            except Exception as e:
                _logger.error('✗ Error al crear actividad para usuario %s: %s', user.name, str(e))
        
        _logger.info('=== FIN: Se crearon %s actividades ===', activities_created)
    
    # Método para imprimir el reporte de garantía con el panel de impresión del navegador
    def action_print_warranty_certificate(self):
        self.ensure_one()
        print_url = '/helpdesk/warranty/print/%s' % self.id
        
        return {
            'type': 'ir.actions.act_url',
            'url': print_url,
            'target': 'new',
        }

