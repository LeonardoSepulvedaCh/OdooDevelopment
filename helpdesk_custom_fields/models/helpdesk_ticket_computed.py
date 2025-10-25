from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Calcular el número de adjuntos
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for ticket in self:
            ticket.attachment_count = len(ticket.attachment_ids)
    
    # Calcular el tiempo de resolución
    @api.depends('create_date', 'date_closed')
    def _compute_resolution_time(self):
        for ticket in self:
            if ticket.create_date and ticket.date_closed:
                # Calcular la diferencia en segundos
                delta = ticket.date_closed - ticket.create_date
                total_seconds = delta.total_seconds()
                
                # Convertir a horas y días
                ticket.resolution_time_hours = total_seconds / 3600
                ticket.resolution_time_days = total_seconds / 86400
            else:
                ticket.resolution_time_hours = 0.0
                ticket.resolution_time_days = 0.0

