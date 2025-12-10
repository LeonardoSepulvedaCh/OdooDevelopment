from odoo import http
from odoo.http import request
import json
import base64
import logging

_logger = logging.getLogger(__name__)

CONTACT_REGISTRATION_MODEL = 'contact.registration'
COUNTRY_CODE_FIELD = 'country_id.code'


class ContactRegistrationController(http.Controller):

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
                return request.redirect('/contact/register/%s?error=missing_fields' % post.get('token', 'generic'))
            
            # Construir nombre completo concatenando los campos
            name_parts = []
            if post.get('first_name'):
                name_parts.append(post.get('first_name').strip())
            if post.get('second_name'):
                name_parts.append(post.get('second_name').strip())
            if post.get('first_surname'):
                name_parts.append(post.get('first_surname').strip())
            if post.get('second_surname'):
                name_parts.append(post.get('second_surname').strip())
            
            full_name = ' '.join(name_parts)
            
            # Preparar valores para crear el contacto
            partner_vals = {
                'name': full_name,
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
            
            # Vincular con el registro QR si existe
            token = post.get('token')
            if token and token != 'generic':
                registration = request.env[CONTACT_REGISTRATION_MODEL].sudo().search([
                    ('token', '=', token),
                    ('active', '=', True)
                ], limit=1)
                if registration:
                    partner_vals['registration_id'] = registration.id
            
            # Crear el contacto
            request.env['res.partner'].sudo().create(partner_vals)
            
            # Redirigir con mensaje de éxito
            return request.redirect('/contact/register/%s?success=1' % (token or 'generic'))
            
        except Exception as e:
            # Registrar la excepción detallada en el servidor
            _logger.exception("Error al crear contacto desde formulario público: %s", e)
            
            # Revertir la transacción de la base de datos
            request.env.cr.rollback()
            
            # Redirigir con código de error controlado (sin exponer detalles)
            return request.redirect('/contact/register/%s?error=registration_failed' % post.get('token', 'generic'))

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

