from odoo import http
from odoo.http import request
import json
import base64
import logging

_logger = logging.getLogger(__name__)

CONTACT_REGISTRATION_MODEL = 'contact.registration'
COUNTRY_CODE_FIELD = 'country_id.code'


class ContactRegistrationController(http.Controller):

    # Construir nombre completo concatenando los campos de nombre
    def _build_full_name(self, post):
        name_parts = []
        for field in ['first_name', 'second_name', 'first_surname', 'second_surname']:
            value = post.get(field)
            if value:
                name_parts.append(value.strip())
        return ' '.join(name_parts)

    # Preparar valores para crear el contacto
    def _prepare_partner_values(self, post):
        partner_vals = {
            'name': self._build_full_name(post),
            'first_name': post.get('first_name', '').strip(),
            'second_name': post.get('second_name', '').strip(),
            'first_surname': post.get('first_surname', '').strip(),
            'second_surname': post.get('second_surname', '').strip(),
            'email': post.get('email'),
            'vat': post.get('vat'),
            'street': post.get('street', ''),
            'city_id': int(post.get('city_id')) if post.get('city_id') else False,
            'state_id': int(post.get('state_id')) if post.get('state_id') else False,
            'zip': post.get('zip', ''),
            'country_id': int(post.get('country_id')) if post.get('country_id') else False,
            'l10n_latam_identification_type_id': int(post.get('l10n_latam_identification_type_id')),
            'l10n_co_tax_regime_id': int(post.get('l10n_co_tax_regime_id')),
            'pos_customer': True,
        }
        
        # Agregar obligaciones fiscales si fueron seleccionadas
        obligation_ids_raw = request.httprequest.form.getlist('l10n_co_edi_obligation_type_ids')
        if obligation_ids_raw:
            obligation_ids = [int(x) for x in obligation_ids_raw if x]
            partner_vals['l10n_co_edi_obligation_type_ids'] = [(6, 0, obligation_ids)]
        
        return partner_vals

    # Vincular el registro QR y asignar POS si existe
    def _link_registration_and_pos(self, partner_vals, token):
        if not token or token == 'generic':
            return
        
        registration = request.env[CONTACT_REGISTRATION_MODEL].sudo().search([
            ('token', '=', token),
            ('active', '=', True)
        ], limit=1)
        
        if not registration:
            return
        
        partner_vals['registration_id'] = registration.id
        
        # Asignar POS si el registro tiene uno asociado
        if registration.pos_config_id:
            partner_vals['pos_config_ids'] = [(6, 0, [registration.pos_config_id.id])]

    # Ruta para mostrar el formulario de registro de contactos
    @http.route('/contact/register/<string:token>', type='http', auth='public', website=True)
    def contact_registration_form(self, token=None, **kwargs):
        
        # Verificar si el token existe y está activo (opcional)
        registration = None
        if token and token != 'generic':
            registration = request.env[CONTACT_REGISTRATION_MODEL].sudo().search([
                ('token', '=', token),
                ('active', '=', True)
            ], limit=1)
        
        # Obtener países para el formulario
        countries = request.env['res.country'].sudo().search([], order='name')
        
        # Obtener estados/departamentos (inicialmente de Colombia)
        states = request.env['res.country.state'].sudo().search([
            (COUNTRY_CODE_FIELD, '=', 'CO')
        ], order='name')
        
        # Obtener ciudades/municipios (inicialmente de Colombia)
        cities = request.env['res.city'].sudo().search([
            (COUNTRY_CODE_FIELD, '=', 'CO')
        ], order='name')
        
        # Obtener tipos de documento (Colombia)
        id_types = request.env['l10n_latam.identification.type'].sudo().search([
            (COUNTRY_CODE_FIELD, '=', 'CO')
        ])
        
        # Obtener regímenes tributarios (Colombia)
        tax_regimes = request.env['l10n_co.tax.regime'].sudo().search([])
        
        # Obtener obligaciones fiscales (Colombia)
        obligation_types = request.env['l10n_co_edi.type_code'].sudo().search([])
        
        return request.render('contact_registration_qr.registration_form', {
            'token': token,
            'registration': registration,
            'countries': countries,
            'states': states,
            'cities': cities,
            'id_types': id_types,
            'tax_regimes': tax_regimes,
            'obligation_types': obligation_types,
            'success': kwargs.get('success', False),
            'error': kwargs.get('error', False),
        })

    # Ruta para procesar el envío del formulario de registro
    @http.route('/contact/register/submit', type='http', auth='public', methods=['POST'], csrf=True, website=True)
    def contact_registration_submit(self, **post):
        try:
            # Validar campos requeridos
            required_fields = ['first_name', 'first_surname', 'email', 'vat', 
                             'l10n_latam_identification_type_id', 'l10n_co_tax_regime_id']
            missing_fields = [f for f in required_fields if not post.get(f)]
            
            if missing_fields:
                token = post.get('token', 'generic')
                return request.redirect(f'/contact/register/{token}?error=missing_fields')
            
            # Preparar valores del contacto
            partner_vals = self._prepare_partner_values(post)
            
            # Vincular con el registro QR y asignar POS
            token = post.get('token')
            self._link_registration_and_pos(partner_vals, token)
            
            # Crear el contacto
            request.env['res.partner'].sudo().create(partner_vals)
            
            # Redirigir con mensaje de éxito
            return request.redirect(f'/contact/register/{token or "generic"}?success=1')
            
        except Exception as e:
            _logger.exception("Error al crear contacto desde formulario público: %s", e)
            request.env.cr.rollback()
            token = post.get('token', 'generic')
            return request.redirect(f'/contact/register/{token}?error=registration_failed')

    # Ruta genérica de registro sin token específico
    @http.route('/contact/register/generic', type='http', auth='public', website=True)
    def contact_registration_generic(self, **kwargs):
        return self.contact_registration_form(token='generic', **kwargs)

    # Ruta para descargar el código QR como archivo PNG
    @http.route('/contact/qr/download/<int:registration_id>', type='http', auth='user')
    def download_qr_code(self, registration_id, **kwargs):
        registration = request.env['contact.registration'].browse(registration_id)
        
        if not registration.exists() or not registration.qr_code:
            return request.not_found()
        
        # Decodificar la imagen base64
        qr_image = base64.b64decode(registration.qr_code)
        
        # Generar nombre de archivo
        filename = f"QR_{registration.name.replace(' ', '_')}.png"
        
        # Retornar la imagen como descarga
        return request.make_response(
            qr_image,
            headers=[
                ('Content-Type', 'image/png'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
                ('Content-Length', len(qr_image))
            ]
        )

