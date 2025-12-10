from odoo import api, fields, models, Command
import logging

_logger = logging.getLogger(__name__)


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    is_warranty_team = fields.Boolean(
        string='Es equipo de garantías',
        default=False,
        help='Indica si este equipo maneja tickets de garantías. '
             'Si está activado, los campos personalizados de garantías estarán disponibles en los tickets.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        teams = super().create(vals_list)
        
        # Asignar etapas de garantías a los equipos que se crean con is_warranty_team=True
        for team in teams:
            if team.is_warranty_team:
                team._assign_warranty_stages()
        
        return teams

    def write(self, vals):
        result = super().write(vals)
        
        # Si se activa is_warranty_team, asignar las etapas de garantías
        if vals.get('is_warranty_team'):
            for team in self:
                team._assign_warranty_stages()
        
        return result

    # Asignar las etapas al equipo de tipo garantías
    def _assign_warranty_stages(self):
        self.ensure_one()
        
        # Obtener las etapas de garantías desde los XML IDs
        stage_xml_ids = [
            'helpdesk_custom_fields.warranty_stage_new',
            'helpdesk_custom_fields.warranty_stage_pending_review',
            'helpdesk_custom_fields.warranty_stage_waiting_payment',
            'helpdesk_custom_fields.warranty_stage_dispatch',
            'helpdesk_custom_fields.warranty_stage_resolved',
            'helpdesk_custom_fields.warranty_stage_cancelled',
            'helpdesk_custom_fields.warranty_stage_rejected',
        ]
        
        warranty_stages = self.env['helpdesk.stage']
        for xml_id in stage_xml_ids:
            stage = self.env.ref(xml_id, raise_if_not_found=False)
            if stage:
                warranty_stages += stage
            else:
                _logger.warning(f'No se encontró la etapa con XML ID: {xml_id}')
        
        if warranty_stages:
            # Asignar las etapas al equipo (reemplazando las existentes)
            self.stage_ids = [Command.set(warranty_stages.ids)]
            _logger.info(f'Etapas de garantías asignadas al equipo: {self.name}')
        else:
            _logger.warning(f'No se pudieron asignar etapas de garantías al equipo: {self.name}')

