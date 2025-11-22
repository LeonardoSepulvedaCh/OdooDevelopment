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
    
    # Validar que solo usuarios autorizados puedan mover tickets entre etapas
    @api.constrains('stage_id')
    def _check_user_can_move_ticket(self):
        """
        Validación de permisos para mover tickets entre etapas:
        - Usuarios básicos: solo pueden mover de "Nuevo" a "Pendiente de Revisión"
        - Gestores: pueden mover a cualquier etapa
        """
        for ticket in self:
            if not ticket.stage_id:
                continue
                
            current_user = self.env.user
            
            # Verificar si el usuario es gestor (tiene permisos completos)
            has_permission = current_user.has_group('helpdesk_custom_fields.group_helpdesk_custom_manager')
            
            # Si el usuario es gestor, puede mover a cualquier etapa
            if has_permission:
                continue
            
            # Obtener los nombres de las etapas desde los parámetros del sistema
            config_params = self.env['ir.config_parameter'].sudo()
            stage_new_name = config_params.get_param('helpdesk_custom_fields.stage_new_name', default='Nuevo')
            stage_pending_review_name = config_params.get_param('helpdesk_custom_fields.stage_pending_review_name', default='Pendiente de Revisión')
            stage_dispatch_name = config_params.get_param('helpdesk_custom_fields.stage_dispatch_name', default='Por Realizar (Despacho)')
            stage_rejected_name = config_params.get_param('helpdesk_custom_fields.stage_rejected_name', default='Rechazado')
            stage_closed_name = config_params.get_param('helpdesk_custom_fields.stage_closed_name', default='Resuelto')
            
            current_stage_name = ticket.stage_id.name
            
            # Obtener la etapa anterior del ticket (si existe)
            old_stage_name = None
            if ticket.id:
                old_ticket = self.browse(ticket.id)
                if old_ticket.exists() and old_ticket.stage_id:
                    # Usar _origin para obtener el valor anterior del registro
                    old_stage_name = ticket._origin.stage_id.name if ticket._origin.stage_id else None
            
            # Si el usuario NO tiene permisos, solo puede mover de "Nuevo" a "Pendiente de Revisión"
            allowed_transition = (old_stage_name == stage_new_name and current_stage_name == stage_pending_review_name)
            
            # También permitir que el ticket permanezca en "Nuevo" o "Pendiente de Revisión" sin restricciones
            is_allowed_stage = current_stage_name in [stage_new_name, stage_pending_review_name]
            
            # Etapas restringidas que requieren permisos
            restricted_stages = [stage_dispatch_name, stage_rejected_name, stage_closed_name]
            is_restricted_stage = current_stage_name in restricted_stages
            
            # Validar si el usuario está intentando mover a una etapa restringida
            if is_restricted_stage or (not is_allowed_stage and not allowed_transition):
                raise UserError(
                    f'No tienes permisos para mover tickets a la etapa "{current_stage_name}". '
                    'Los usuarios sin permisos especiales solo pueden mover tickets de '
                    f'"{stage_new_name}" a "{stage_pending_review_name}". '
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

