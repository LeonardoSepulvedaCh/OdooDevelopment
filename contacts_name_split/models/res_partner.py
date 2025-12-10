from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    first_name = fields.Char(
        string='Primer Nombre',
        tracking=True
    )
    second_name = fields.Char(
        string='Segundo Nombre',
        tracking=True
    )
    first_surname = fields.Char(
        string='Primer Apellido',
        tracking=True
    )
    second_surname = fields.Char(
        string='Segundo Apellido',
        tracking=True
    )

    name = fields.Char(
        string='Nombre',
        store=True,
        readonly=False,
        tracking=True,
        index=True
    )

    is_legal_person = fields.Boolean(
        string='Es Persona Jurídica',
        compute='_compute_is_company',
        store=True
    )

    @api.onchange('first_name', 'second_name', 'first_surname', 'second_surname', 'is_company')
    def _onchange_name_parts(self):
        if not self.is_company:
            name_parts = []
            
            if self.first_name:
                name_parts.append(self.first_name)
            if self.second_name:
                name_parts.append(self.second_name)
            if self.first_surname:
                name_parts.append(self.first_surname)
            if self.second_surname:
                name_parts.append(self.second_surname)
            
            if name_parts:
                self.name = ' '.join(name_parts)

    @api.depends('is_company')
    def _compute_is_company(self):
        for partner in self:
            partner.is_company = partner.is_company
            if partner.is_company:
                partner.is_legal_person = True
            else:
                partner.is_legal_person = False

    """ @api.constrains('first_name', 'first_surname', 'is_company')
    def _check_required_fields_for_company(self):
        
        for partner in self:
            if partner.is_company:
                if not partner.first_name:
                    raise ValidationError("El campo 'Primer Nombre' es obligatorio para compañías.")
                if not partner.first_surname:
                    raise ValidationError("El campo 'Primer Apellido' es obligatorio para compañías.") """



