# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.report import ReportController


class PosCashReportController(ReportController):

    @http.route(['/report/pdf/pos_cash_report.report_cash_closing/<int:session_id>'], 
                type='http', auth="user", website=True)
    def report_cash_closing_pdf(self, session_id, **kwargs):
        """Genera el reporte PDF de cierre de caja para una sesión específica"""
        try:
            session = request.env['pos.session'].browse(session_id)
            
            # Verificar permisos
            if not session.exists():
                return request.not_found()
            
            # Verificar que el usuario tenga permisos para ver la sesión
            session.check_access_rights('read')
            session.check_access_rule('read')
            
            # Generar el reporte
            report = request.env.ref('pos_cash_report.action_cash_report')
            pdf_content, content_type = report._render_qweb_pdf([session_id])
            
            # Nombre del archivo
            filename = f"Cierre_Caja_{session.name}_{session.stop_at.strftime('%Y%m%d_%H%M') if session.stop_at else 'actual'}.pdf"
            
            # Retornar el PDF
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', f'inline; filename="{filename}"')
            ]
            
            return request.make_response(pdf_content, headers=pdfhttpheaders)
            
        except Exception as e:
            # Log del error
            request.env['ir.logging'].sudo().create({
                'name': 'pos_cash_report.controller',
                'type': 'server',
                'level': 'ERROR',
                'message': f'Error generando reporte de cierre: {str(e)}',
                'path': 'pos_cash_report.controllers.main',
                'func': 'report_cash_closing_pdf',
                'line': '1',
            })
            return request.not_found()

    @http.route(['/pos/cash_report/generate/<int:session_id>'], 
                type='jsonrpc', auth="user", methods=['POST'])
    def generate_cash_report_json(self, session_id, **kwargs):
        """Endpoint JSON para generar el reporte desde el frontend"""
        try:
            session = request.env['pos.session'].browse(session_id)
            
            if not session.exists():
                return {'error': 'Sesión no encontrada'}
            
            # Verificar permisos
            session.check_access_rights('read')
            session.check_access_rule('read')
            
            # Generar URL del reporte
            report_url = f'/report/pdf/pos_cash_report.report_cash_closing/{session_id}'
            
            return {
                'success': True,
                'report_url': report_url,
                'session_name': session.name,
                'message': 'Reporte generado exitosamente'
            }
            
        except Exception as e:
            return {
                'error': f'Error al generar el reporte: {str(e)}'
            }
