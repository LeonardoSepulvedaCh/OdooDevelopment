from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleCreditCodeudor(models.Model):
    _name = 'sale.credit.codeudor'
    _description = 'Codeudor de Solicitud de Crédito'
    _rec_name = 'name'
    _order = 'sequence, name'

    # Campos de control
    sequence = fields.Integer(string='Secuencia', default=10)
    application_id = fields.Many2one('sale.credit.quota.application', string='Solicitud', required=True, ondelete='cascade', index=True, readonly=True)
    
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
            ('cousin', 'Primo/Prima'),
            ('aunt_uncle', 'Tía/Tío'),
            ('nephew_niece', 'Sobrino/Sobrina'),
            ('brother_in_law', 'Cuñado/Cuñada'),
            ('son_in_law', 'Yerno/Nuera'),
            ('grandparent', 'Abuelo/Abuela'),
            ('grandchild', 'Nieto/Nieta'),
            ('employee', 'Empleado'),
            ('relative', 'Otro Familiar'),
            ('friend', 'Amigo'),
            ('business_partner', 'Socio Comercial'),
            ('legal_representative', 'Representante Legal'),
            ('other', 'Otro')
        ],
        help='Relación del codeudor con el cliente',
        required=True
    )
    birth_date = fields.Date(string='Fecha de Nacimiento', related='partner_id.birth_date', store=True, readonly=False)
    
    # Campo calculado para edad
    age = fields.Integer(string='Edad (Años)', compute='_compute_age', store=True, help='Edad calculada a partir de la fecha de nacimiento')

    # Validaciones
    @api.constrains('name', 'vat', 'email', 'residence_address', 'residence_municipality', 'birth_date')
    def _check_partner_required_fields(self):
        for record in self:
            missing_fields = []
            if not record.name:
                missing_fields.append('Nombres y Apellidos')
            if not record.vat:
                missing_fields.append('Documento de Identidad')
            if not record.email:
                missing_fields.append('Correo Electrónico')
            if not record.residence_address:
                missing_fields.append('Dirección de Residencia')
            if not record.residence_municipality:
                missing_fields.append('Municipio de Residencia')
            if not record.birth_date:
                missing_fields.append('Fecha de Nacimiento')
            
            if missing_fields:
                raise ValidationError(
                    _('El codeudor "%s" no tiene los siguientes campos obligatorios:\n• %s\n\nPor favor, complete estos datos en la solicitud.') % 
                    (record.name or record.partner_id.name or 'Sin nombre', '\n• '.join(missing_fields))
                )

    @api.constrains('birth_date')
    def _check_birth_date(self):
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

    # Evitar que el mismo partner sea codeudor múltiples veces en la misma solicitud
    @api.constrains('partner_id', 'application_id')
    def _check_unique_codeudor(self):
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

    # Evitar que el cliente sea su propio codeudor
    @api.constrains('partner_id', 'application_id')
    def _check_codeudor_not_customer(self):
        for record in self:
            if record.partner_id and record.application_id:
                if record.partner_id == record.application_id.customer_id:
                    raise ValidationError(
                        _('El cliente no puede ser su propio codeudor.')
                    )

    # Calcular la edad del codeudor
    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                today = fields.Date.today()
                record.age = int((today - record.birth_date).days / 365.25)
            else:
                record.age = 0

    # Prellenar datos del codeudor cuando se selecciona
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.street and not self.residence_address:
                self.residence_address = self.partner_id.street
            if self.partner_id.city and not self.residence_municipality:
                self.residence_municipality = self.partner_id.city

