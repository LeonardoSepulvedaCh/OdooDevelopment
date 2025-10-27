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
    
    # Validar que solo usuarios autorizados puedan mover tickets a etapas finalizadas
    @api.constrains('stage_id')
    def _check_user_can_close_ticket(self):
        for ticket in self:
            if ticket.stage_id:
                closed_stage_name = self.env['ir.config_parameter'].sudo().get_param(
                    'helpdesk_custom_fields.stage_closed_name', 
                    default='Done'
                )
                
                if ticket.stage_id.name == closed_stage_name:
                    current_user = self.env.user
                    # Verificar si el campo existe antes de acceder a él
                    if hasattr(current_user, 'can_close_tickets') and not current_user.can_close_tickets:
                        raise UserError(
                            'No tienes permisos para mover tickets a la etapa de finalización. '
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

