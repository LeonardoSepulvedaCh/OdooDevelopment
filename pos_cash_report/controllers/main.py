import logging
import re

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.report import ReportController

_logger = logging.getLogger(__name__)


def sanitize_filename(filename):
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    filename = filename.replace('"', '').replace("'", '').replace('\\', '')
    filename = re.sub(r'[;\r\n]', '', filename)
    filename = re.sub(r'[^\w\s\-\.]', '_', filename)
    if len(filename) > 200:
        filename = filename[:200]
    return filename.strip()


# Validación contra IDOR: verificar acceso legítimo
def validate_session_access(session):
    if not session or not session.exists():
        return False
    
    user = request.env.user
    
    # Verificar que la sesión pertenezca a una compañía accesible por el usuario
    if session.config_id.company_id.id not in user.company_ids.ids:
        _logger.warning(
            "Usuario %s (ID: %s) intentó acceder a sesión %s de compañía no autorizada %s",
            user.login, user.id, session.id, session.config_id.company_id.name
        )
        return False
    
    # Verificar que el usuario tenga acceso al POS de la sesión
    # Los usuarios deben tener acceso a través de grupos de POS o ser managers
    has_pos_access = user.has_group('point_of_sale.group_pos_user') or \
                     user.has_group('point_of_sale.group_pos_manager')
    
    if not has_pos_access:
        _logger.warning(
            "Usuario %s (ID: %s) sin permisos de POS intentó acceder a sesión %s",
            user.login, user.id, session.id
        )
        return False
    
    return True


class PosCashReportController(ReportController):

    @http.route(['/report/pdf/pos_cash_report.report_cash_closing/<int:session_id>'], 
                type='http', auth="user", website=True)
    def report_cash_closing_pdf(self, session_id, **kwargs):
        """Genera el reporte PDF de cierre de caja para una sesión específica"""
        try:
            session = request.env['pos.session'].browse(session_id)
            
            # Verificar existencia de la sesión
            if not session.exists():
                return request.not_found()
            
            # Validación contra IDOR: verificar acceso legítimo
            if not validate_session_access(session):
                _logger.warning(
                    "Acceso denegado a sesión %s para usuario %s",
                    session_id, request.env.user.login
                )
                return request.not_found()
            
            # Verificar permisos estándar de Odoo
            session.check_access_rights('read')
            session.check_access_rule('read')
            
            # Generar el reporte
            report = request.env.ref('pos_cash_report.action_cash_report')
            pdf_content, _ = report._render_qweb_pdf([session_id])
            
            # Nombre del archivo con sanitización de seguridad
            safe_session_name = sanitize_filename(session.name)
            date_str = session.stop_at.strftime('%Y%m%d_%H%M') if session.stop_at else 'actual'
            filename = f"Cierre_Caja_{safe_session_name}_{date_str}.pdf"
            
            # Retornar el PDF
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', f'inline; filename="{filename}"')
            ]
            
            return request.make_response(pdf_content, headers=pdfhttpheaders)
            
        except Exception:
            _logger.exception("Error generando reporte de cierre de caja para sesión ID: %s", session_id)
            return request.not_found()

    @http.route(['/pos/cash_report/generate/<int:session_id>'], 
                type='jsonrpc', auth="user", methods=['POST'])
    def generate_cash_report_json(self, session_id, **kwargs):
        """Endpoint JSON para generar el reporte desde el frontend"""
        try:
            session = request.env['pos.session'].browse(session_id)
            
            if not session.exists():
                return {'error': 'Sesión no encontrada'}
            
            # Validación contra IDOR: verificar acceso legítimo
            if not validate_session_access(session):
                _logger.warning(
                    "Acceso denegado a sesión %s para usuario %s",
                    session_id, request.env.user.login
                )
                return {'error': 'No tiene permisos para acceder a esta sesión'}
            
            # Verificar permisos estándar de Odoo
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
            
        except Exception:
            _logger.exception("Error generando URL de reporte para sesión ID: %s", session_id)
            return {
                'error': 'Error al generar el reporte. Contacte al administrador.'
            }
