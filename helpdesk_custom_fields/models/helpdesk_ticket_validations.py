from odoo import api, models
from odoo.exceptions import ValidationError


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

