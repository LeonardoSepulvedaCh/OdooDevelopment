# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.website_helpdesk.controllers.main import WebsiteForm
from odoo.exceptions import ValidationError, UserError
from werkzeug.exceptions import Forbidden


class WebsiteHelpdeskFormCustom(WebsiteForm):
    # Sobrescribir el método _handle_website_form para agregar la validación de autenticación
    def _handle_website_form(self, model_name, **kwargs):
        if model_name == 'helpdesk.ticket':
            team_id = request.params.get('team_id')
            
            if team_id:
                try:
                    team_id = int(team_id)
                except (ValueError, TypeError):
                    team_id = None
                
                if team_id:
                    team = request.env['helpdesk.team'].sudo().browse(team_id)
                    
                    if team.exists() and team.is_warranty_team:
                        if request.env.user._is_public():
                            raise Forbidden(_(
                                'Para crear un ticket de garantías debe iniciar sesión primero. '
                                'Por favor, inicie sesión e intente nuevamente.'
                            ))
        
        return super()._handle_website_form(model_name, **kwargs)

    # Sobrescribir el método insert_record para agregar la validación de autenticación a nivel de inserción del registro.
    def insert_record(self, request, model_sudo, values, custom, meta=None):
        if model_sudo.model == 'helpdesk.ticket':
            team_id = values.get('team_id')
            
            if team_id:
                team = request.env['helpdesk.team'].sudo().browse(team_id)
                
                if team.exists() and team.is_warranty_team:
                    if request.env.user._is_public():
                        raise ValidationError(_(
                            'No puede crear tickets de garantías sin estar autenticado. '
                            'Por favor, inicie sesión primero.'
                        ))
        
        return super().insert_record(request, model_sudo, values, custom, meta=meta)
    
    # Endpoint JSON-RPC que devuelve las facturas del partner asociado al usuario actual.
    @http.route('/helpdesk/warranty/get_partner_invoices', type='jsonrpc', auth='user', methods=['POST'], website=True, csrf=False)
    def get_partner_invoices(self, **kw):
        if request.env.user._is_public():
            return {'error': 'Usuario no autenticado'}
        
        partner = request.env.user.partner_id
        
        invoices = request.env['account.move'].sudo().search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ], order='invoice_date desc')
        
        invoice_data = []
        for invoice in invoices:
            invoice_data.append({
                'id': invoice.id,
                'name': invoice.name or 'Borrador',
                'display_name': f"{invoice.name} - {invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else 'Sin fecha'}",
                'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else False,
                'amount_total': invoice.amount_total,
            })
        
        return {'invoices': invoice_data}
    
    # Endpoint JSON-RPC que devuelve los productos de una factura específica.
    @http.route('/helpdesk/warranty/get_invoice_products', type='jsonrpc', auth='user', methods=['POST'], website=True, csrf=False)
    def get_invoice_products(self, invoice_id, **kw):
        if request.env.user._is_public():
            return {'error': 'Usuario no autenticado'}
        
        if not invoice_id:
            return {'error': 'ID de factura no proporcionado'}
        
        try:
            invoice_id = int(invoice_id)
        except (ValueError, TypeError):
            return {'error': 'ID de factura inválido'}
        
        partner = request.env.user.partner_id
        
        invoice = request.env['account.move'].sudo().browse(invoice_id)
        
        if not invoice.exists():
            return {'error': 'Factura no encontrada'}
        
        if invoice.partner_id.id != partner.id:
            return {'error': 'No tiene permiso para acceder a esta factura'}
        
        products_data = []
        for line in invoice.invoice_line_ids:
            if line.product_id:
                products_data.append({
                    'id': line.product_id.id,
                    'name': line.product_id.display_name,
                    'default_code': line.product_id.default_code or '',
                    'quantity': line.quantity,
                })
        
        return {'products': products_data}

