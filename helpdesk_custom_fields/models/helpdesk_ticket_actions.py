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
                    
                    # Detectar si el ticket pasa a una etapa de rechazo
                    rejected_stage_name = self.env['ir.config_parameter'].sudo().get_param(
                        'helpdesk_custom_fields.stage_rejected_name', 
                        default='Rechazado'
                    )
                    
                    _logger.info('Etapa configurada como rechazo: "%s"', rejected_stage_name)
                    
                    # Si el ticket pasa a la etapa de rechazo, notificar al canal
                    if new_stage.name == rejected_stage_name and ticket.is_warranty_team:
                        _logger.info('Ticket #%s - Pasando a etapa de rechazo, enviando notificación', ticket.id)
                        ticket._notify_rejection_to_channel()
        
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
    
    # Método para imprimir el reporte de garantía con el panel de impresión del navegador
    def action_print_warranty_certificate(self):
        self.ensure_one()
        print_url = '/helpdesk/warranty/print/%s' % self.id
        
        return {
            'type': 'ir.actions.act_url',
            'url': print_url,
            'target': 'new',
        }

