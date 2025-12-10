from odoo import api, models
from odoo.exceptions import ValidationError, UserError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Validar que la serie sea obligatoria para equipos de garantías
    @api.constrains('serie', 'team_id')
    def _check_serie_required_for_warranty_team(self):
        for ticket in self:
            if ticket.is_warranty_team and not ticket.serie:
                raise ValidationError(
                    'El campo "Serie" es obligatorio para tickets del equipo de garantías.'
                )
    
    # Validar que la factura sea obligatoria para equipos de garantías
    @api.constrains('invoice_id', 'team_id')
    def _check_invoice_required_for_warranty_team(self):
        for ticket in self:
            if ticket.is_warranty_team and not ticket.invoice_id:
                raise ValidationError(
                    'El campo "Factura" es obligatorio para tickets del equipo de garantías.'
                )
    
    # Validar que solo usuarios autorizados puedan mover tickets entre etapas. Validación de permisos: Usuarios básicos solo pueden mover de "Nuevo" a "Pendiente de Revisión". Gestores pueden mover a cualquier etapa.
    @api.constrains('stage_id')
    def _check_user_can_move_ticket(self):
        for ticket in self:
            if not ticket.stage_id:
                continue
            
            if ticket._user_is_manager():
                continue
            
            ticket._validate_stage_transition()
    
    # Verificar si el usuario actual es gestor
    def _user_is_manager(self):
        return self.env.user.has_group('helpdesk_custom_fields.group_helpdesk_custom_manager')
    
    # Validar que la transición de etapa sea permitida para usuarios sin permisos de gestor
    def _validate_stage_transition(self):
        stage_config = self._get_stage_validation_config()
        current_stage_name = self.stage_id.name
        old_stage_name = self._get_previous_stage_name()
        
        if self._is_transition_allowed(old_stage_name, current_stage_name, stage_config):
            return
        
        self._raise_stage_transition_error(current_stage_name, stage_config)
    
    # Obtener la configuración de nombres de etapas del sistema
    def _get_stage_validation_config(self):
        config_params = self.env['ir.config_parameter'].sudo()
        
        return {
            'new': config_params.get_param('helpdesk_custom_fields.stage_new_name', default='Nuevo'),
            'pending_review': config_params.get_param('helpdesk_custom_fields.stage_pending_review_name', default='Pendiente de Revisión'),
            'dispatch': config_params.get_param('helpdesk_custom_fields.stage_dispatch_name', default='Por Realizar (Despacho)'),
            'rejected': config_params.get_param('helpdesk_custom_fields.stage_rejected_name', default='Rechazado'),
            'closed': config_params.get_param('helpdesk_custom_fields.stage_closed_name', default='Resuelto'),
        }
    
    # Obtener el nombre de la etapa anterior del ticket (antes del cambio actual)
    def _get_previous_stage_name(self):
        if not self.id:
            return None
        
        if not self._origin.stage_id:
            return None
        
        return self._origin.stage_id.name
    
    # Verificar si la transición de etapa es permitida para usuarios sin permisos especiales
    def _is_transition_allowed(self, old_stage_name, current_stage_name, stage_config):
        # Transición permitida: de "Nuevo" a "Pendiente de Revisión"
        allowed_transition = (
            old_stage_name == stage_config['new'] and 
            current_stage_name == stage_config['pending_review']
        )
        
        # Etapas permitidas sin restricciones
        allowed_stages = [stage_config['new'], stage_config['pending_review']]
        is_in_allowed_stage = current_stage_name in allowed_stages
        
        # Etapas restringidas
        restricted_stages = [stage_config['dispatch'], stage_config['rejected'], stage_config['closed']]
        is_restricted_stage = current_stage_name in restricted_stages
        
        # La transición es válida si:
        # 1. Es una transición permitida, O
        # 2. El ticket está en una etapa permitida Y NO es una etapa restringida
        return allowed_transition or (is_in_allowed_stage and not is_restricted_stage)
    
    # Lanzar error cuando la transición de etapa no es permitida
    def _raise_stage_transition_error(self, current_stage_name, stage_config):
        raise UserError(
            f'No tienes permisos para mover tickets a la etapa "{current_stage_name}". '
            'Los usuarios sin permisos especiales solo pueden mover tickets de '
            f'"{stage_config["new"]}" a "{stage_config["pending_review"]}". '
            'Contacta al administrador del sistema para obtener los permisos necesarios.'
        )
    
    # Validar que exista un acta de garantía antes de finalizar el ticket
    @api.constrains('stage_id')
    def _check_warranty_certificate_attachment(self):
        for ticket in self:
            if ticket.stage_id and ticket.is_warranty_team:
                closed_stage_name = self.env['ir.config_parameter'].sudo().get_param(
                    'helpdesk_custom_fields.stage_closed_name', 
                    default='Done'
                )
                
                if ticket.stage_id.name == closed_stage_name:
                    has_warranty_certificate = any(
                        attachment.is_warranty_certificate 
                        for attachment in ticket.attachment_ids
                    )
                    
                    if not has_warranty_certificate:
                        raise ValidationError(
                            'Debe adjuntar al menos un documento marcado como "Acta de Garantía" '
                            'antes de finalizar el ticket.'
                        )

    # Validar que los productos seleccionados pertenezcan a la factura
    @api.constrains('product_ids', 'invoice_id')
    def _check_products_from_invoice(self):
        for ticket in self:
            if ticket.product_ids and ticket.invoice_id:
                invoice_products = ticket.invoice_id.invoice_line_ids.mapped('product_id')
                
                invalid_products = ticket.product_ids - invoice_products
                
                if invalid_products:
                    product_names = ', '.join(invalid_products.mapped('name'))
                    raise ValidationError(
                        f'Los siguientes productos no pertenecen a la factura seleccionada: {product_names}. '
                        'Solo puede seleccionar productos que estén en las líneas de la factura.'
                    )

