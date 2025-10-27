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
                delta = ticket.date_closed - ticket.create_date
                total_seconds = delta.total_seconds()
                
                ticket.resolution_time_hours = total_seconds / 3600
                ticket.resolution_time_days = total_seconds / 86400
            else:
                ticket.resolution_time_hours = 0.0
                ticket.resolution_time_days = 0.0

    # Calcular productos disponibles de la factura
    @api.depends('invoice_id', 'invoice_id.invoice_line_ids', 'invoice_id.invoice_line_ids.product_id')
    def _compute_available_products(self):
        for ticket in self:
            if ticket.invoice_id and ticket.invoice_id.invoice_line_ids:
                products = ticket.invoice_id.invoice_line_ids.mapped('product_id')
                ticket.available_product_ids = [(6, 0, products.ids)]
            else:
                ticket.available_product_ids = [(5, 0, 0)]

