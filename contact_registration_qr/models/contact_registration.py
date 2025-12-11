from odoo import models, fields, api
import secrets
import qrcode
import io
import base64

RES_PARTNER_MODEL = 'res.partner'


class ContactRegistration(models.Model):
    _name = 'contact.registration'
    _description = 'Registro de Contactos mediante QR'
    _order = 'create_date desc'

    name = fields.Char(
        string='Nombre del Registro',
        required=True,
        default='Registro QR'
    )
    token = fields.Char(
        string='Token Único',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self._generate_token()
    )
    qr_code = fields.Binary(
        string='Código QR',
        compute='_compute_qr_code',
        store=True
    )
    registration_url = fields.Char(
        string='URL de Registro',
        compute='_compute_registration_url',
        store=True
    )
    partner_ids = fields.One2many(
        RES_PARTNER_MODEL,
        'registration_id',
        string='Contactos Registrados'
    )
    partner_count = fields.Integer(
        string='Total Registrados',
        compute='_compute_partner_count'
    )
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    pos_config_id = fields.Many2one(
        'pos.config',
        string='Punto de Venta',
        help='POS que se asignará automáticamente a los contactos registrados mediante este QR'
    )

    # Genera un token único seguro
    @api.model
    def _generate_token(self):
        return secrets.token_urlsafe(32)

    # Calcula la URL de registro basada en el token
    @api.depends('token')
    def _compute_registration_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.registration_url = f"{base_url}/contact/register/{record.token}"

    # Genera el código QR con la URL de registro
    @api.depends('registration_url')
    def _compute_qr_code(self):
        for record in self:
            if record.registration_url:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(record.registration_url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                record.qr_code = base64.b64encode(buffer.getvalue())
            else:
                record.qr_code = False

    # Cuenta los contactos registrados
    def _compute_partner_count(self):
        # Usar read_group para evitar acceso N+1
        partner_data = self.env[RES_PARTNER_MODEL].sudo().read_group(
            domain=[('registration_id', 'in', self.ids)],
            fields=['registration_id'],
            groupby=['registration_id']
        )
        
        # Crear diccionario con los conteos
        counts = {data['registration_id'][0]: data['registration_id_count'] for data in partner_data}
        
        # Asignar conteos a cada registro
        for record in self:
            record.partner_count = counts.get(record.id, 0)

    # Acción para ver los contactos registrados
    def action_view_partners(self):
        self.ensure_one()
        return {
            'name': 'Contactos Registrados',
            'type': 'ir.actions.act_window',
            'res_model': RES_PARTNER_MODEL,
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('registration_id', '=', self.id)],
            'context': {'default_registration_id': self.id},
            'target': 'current',
        }

    # Acción para descargar el código QR como imagen PNG
    def action_download_qr(self):
        self.ensure_one()
        if not self.qr_code:
            return False
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/contact/qr/download/{self.id}',
            'target': 'self',
        }
