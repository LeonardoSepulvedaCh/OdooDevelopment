from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleCreditCodeudor(models.Model):
    _name = 'sale.credit.codeudor'
    _description = 'Codeudor de Solicitud de Crédito'
    _rec_name = 'name'
    _order = 'sequence, name'

    # Campos de control
    sequence = fields.Integer(string='Secuencia', default=10)
    application_id = fields.Many2one('sale.credit.quota.application', string='Solicitud', required=True, ondelete='cascade', index=True)
    
    # Relación con el partner (codeudor)
    partner_id = fields.Many2one('res.partner',string='Codeudor', required=True, index=True, domain=[('is_company', '=', False)], help='Contacto que actuará como codeudor')

    # Campos relacionados desde res.partner (se prellenan automáticamente)
    name = fields.Char(string='Nombres y Apellidos', related='partner_id.name', store=True, readonly=False)
    vat = fields.Char(string='Documento de Identidad', related='partner_id.vat', store=True, readonly=False)
    phone = fields.Char(string='Teléfono', related='partner_id.phone', store=True, readonly=False)
    email = fields.Char(string='Correo Electrónico', related='partner_id.email', store=True, readonly=False)

    # Campos adicionales específicos del codeudor (no en res.partner estándar)
    residence_address = fields.Char(string='Dirección de Residencia', related='partner_id.street', store=True, readonly=False)
    residence_municipality = fields.Char(string='Municipio de Residencia', related='partner_id.city', store=True, readonly=False)

    relationship = fields.Selection(
        string='Parentesco',
        selection=[
            ('spouse', 'Cónyuge'),
            ('parent', 'Padre/Madre'),
            ('child', 'Hijo/Hija'),
            ('sibling', 'Hermano/Hermana'),
            ('relative', 'Otro Familiar'),
            ('friend', 'Amigo'),
            ('business_partner', 'Socio Comercial'),
            ('other', 'Otro')
        ],
        help='Relación del codeudor con el cliente'
    )
    birth_date = fields.Date(string='Fecha de Nacimiento', related='partner_id.birth_date', store=True, readonly=False)
    
    # Campo calculado para edad
    age = fields.Integer(string='Edad (Años)', compute='_compute_age', store=True, help='Edad calculada a partir de la fecha de nacimiento')

    # Validaciones
    @api.constrains('birth_date')
    def _check_birth_date(self):
        """Valida que la fecha de nacimiento sea válida"""
        for record in self:
            if record.birth_date:
                if record.birth_date > fields.Date.today():
                    raise ValidationError(
                        _('La fecha de nacimiento no puede ser futura.')
                    )
                # Validar edad mínima (18 años)
                age = (fields.Date.today() - record.birth_date).days / 365.25
                if age < 18:
                    raise ValidationError(
                        _('El codeudor debe ser mayor de edad (18 años).')
                    )

    @api.constrains('partner_id', 'application_id')
    def _check_unique_codeudor(self):
        """Evita que el mismo partner sea codeudor múltiples veces en la misma solicitud"""
        for record in self:
            if record.partner_id and record.application_id:
                domain = [
                    ('id', '!=', record.id),
                    ('application_id', '=', record.application_id.id),
                    ('partner_id', '=', record.partner_id.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        _('El codeudor %s ya está agregado a esta solicitud.') % record.partner_id.name
                    )

    @api.constrains('partner_id', 'application_id')
    def _check_codeudor_not_customer(self):
        """Evita que el cliente sea su propio codeudor"""
        for record in self:
            if record.partner_id and record.application_id:
                if record.partner_id == record.application_id.customer_id:
                    raise ValidationError(
                        _('El cliente no puede ser su propio codeudor.')
                    )

    # Computed fields
    @api.depends('birth_date')
    def _compute_age(self):
        """Calcula la edad del codeudor"""
        for record in self:
            if record.birth_date:
                today = fields.Date.today()
                record.age = int((today - record.birth_date).days / 365.25)
            else:
                record.age = 0

    # Onchange methods
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Prellenar datos del codeudor cuando se selecciona"""
        if self.partner_id:
            # Los campos related se llenan automáticamente
            # Prellenar otros campos si existen en el partner
            if self.partner_id.street and not self.residence_address:
                self.residence_address = self.partner_id.street
            if self.partner_id.city and not self.residence_municipality:
                self.residence_municipality = self.partner_id.city

