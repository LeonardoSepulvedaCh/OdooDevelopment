from odoo import http
from odoo.http import request


class WarrantyPrintController(http.Controller):
    
    @http.route('/helpdesk/warranty/print/<int:ticket_id>', type='http', auth='user')
    def print_warranty(self, ticket_id, **kw):
        ticket = request.env['helpdesk.ticket'].browse(ticket_id)
        if not ticket.exists():
            return request.not_found()
        
        # Generar la URL del PDF del reporte
        pdf_url = '/report/pdf/helpdesk_custom_fields.report_warranty_certificate/%s' % ticket_id
        
        return request.render('helpdesk_custom_fields.print_warranty_template', {
            'pdf_url': pdf_url,
            'ticket': ticket,
        })

