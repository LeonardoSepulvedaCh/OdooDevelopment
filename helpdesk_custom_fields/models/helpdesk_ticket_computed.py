from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Calcular el número de adjuntos
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for ticket in self:
            ticket.attachment_count = len(ticket.attachment_ids)

