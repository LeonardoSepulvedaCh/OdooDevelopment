from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class ContactPersons(models.Model):
    _name = 'contact.persons'
    _description = 'Contactos Adicionales de un Contacto Principal'
    _rec_name = 'name'
    _order = 'name'
    
    name = fields.Char(string='Nombre', required=True, index=True)
    phone = fields.Char(string='Teléfono')
    phone2 = fields.Char(string='Teléfono 2')
    mobile = fields.Char(string='Móvil')
    email = fields.Char(string='Correo Electrónico')
    address = fields.Char(string='Dirección')
    position = fields.Char(string='Cargo/Posición')
    notes = fields.Text(string='Notas')
    identity_number = fields.Char(string='Cedula o NIT')
    partner_id = fields.Many2one('res.partner', string='Contacto Principal', ondelete='cascade', required=True, index=True)
    birthdate = fields.Date(string='Fecha de Nacimiento')
    
    
    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email and not self._is_valid_email(record.email):
                raise ValidationError(_("El formato del correo electrónico no es válido."))
    
    def _is_valid_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @api.constrains('birthdate')
    def _check_birthdate(self):
        for record in self:
            if record.birthdate and record.birthdate > fields.Date.today():
                raise ValidationError(_("La fecha de nacimiento no puede ser futura."))
    
