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
    
    def write(self, vals):
        self._handle_serie_change(vals)
        self._handle_stage_change(vals)
        return super().write(vals)
    
    # Maneja el cambio de serie y regenera el consecutivo si es necesario. - Esto consumirá el numero de la secuencia anterior (ejem: si esta en la serie de cucuta con el 01 y cambio a bucara, el 01 de cucuta no se reutilizara)
    def _handle_serie_change(self, vals):
        if 'serie' not in vals:
            return
        
        for ticket in self:
            if vals['serie'] != ticket.serie:
                vals['consecutive_number'] = self._get_next_consecutive_number(vals['serie'])
    
    # Maneja el cambio de etapa y ejecuta las acciones correspondientes.
    def _handle_stage_change(self, vals):
        if 'stage_id' not in vals:
            return
        
        _logger.info('Detectado cambio de stage_id en write()')
        new_stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
        
        for ticket in self:
            ticket._process_stage_change(new_stage, vals)
    
    # Procesa el cambio de etapa para un ticket individual.
    def _process_stage_change(self, new_stage, vals):
        old_stage_name = self.stage_id.name if self.stage_id else 'Sin etapa'
        new_stage_name = new_stage.name if new_stage else 'Sin etapa'
        
        _logger.info('Ticket #%s - Cambio de etapa: "%s" -> "%s"', self.id, old_stage_name, new_stage_name)
        
        if not new_stage or self.stage_id == new_stage:
            return
        
        stage_names = self._get_stage_config_names()
        
        self._handle_trigger_stage(new_stage, stage_names['trigger'])
        self._handle_closed_stage(new_stage, stage_names['closed'], vals)
        self._handle_rejection_stage(new_stage, stage_names['rejected'])
    
    # Obtener los nombres de las etapas configuradas en los parámetros del sistema
    def _get_stage_config_names(self):
        ir_config = self.env['ir.config_parameter'].sudo()
        
        return {
            'trigger': ir_config.get_param('helpdesk_custom_fields.stage_trigger_name', default='In Progress'),
            'closed': ir_config.get_param('helpdesk_custom_fields.stage_closed_name', default='Done'),
            'rejected': ir_config.get_param('helpdesk_custom_fields.stage_rejected_name', default='Rechazado'),
        }
    
    # Maneja la lógica cuando el ticket pasa a la etapa que dispara actividades.
    def _handle_trigger_stage(self, new_stage, trigger_stage_name):
        _logger.info('Etapa configurada para disparar actividades: "%s"', trigger_stage_name)
        
        if new_stage.name == trigger_stage_name:
            _logger.info('La nueva etapa coincide con la configurada - Iniciando creación de actividades')
            self._create_activities_for_warehouse_users()
        else:
            _logger.info('La nueva etapa "%s" NO coincide con la etapa configurada "%s"', 
                        new_stage.name, trigger_stage_name)
    
    # Maneja la lógica de fecha de cierre cuando el ticket se cierra o se reabre.
    def _handle_closed_stage(self, new_stage, closed_stage_name, vals):
        _logger.info('Etapa configurada como finalización: "%s"', closed_stage_name)
        
        # Registrar fecha de cierre si el ticket pasa a etapa cerrada
        if new_stage.name == closed_stage_name and not self.date_closed:
            vals['date_closed'] = fields.Datetime.now()
            _logger.info('Ticket #%s - Registrando fecha de finalización: %s', self.id, vals['date_closed'])
        
        # Limpiar fecha de cierre si el ticket se reabre
        if self.stage_id.name == closed_stage_name and new_stage.name != closed_stage_name and self.date_closed:
            vals['date_closed'] = False
            _logger.info('Ticket #%s - Ticket reabierto, limpiando fecha de finalización', self.id)
    
    # Maneja la lógica cuando el ticket pasa a la etapa de rechazo.
    def _handle_rejection_stage(self, new_stage, rejected_stage_name):
        _logger.info('Etapa configurada como rechazo: "%s"', rejected_stage_name)
        
        if new_stage.name == rejected_stage_name and self.is_warranty_team:
            _logger.info('Ticket #%s - Pasando a etapa de rechazo, enviando notificación', self.id)
            self._notify_rejection_to_channel()
    
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

