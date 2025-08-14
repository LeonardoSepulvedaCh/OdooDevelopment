from odoo import models, fields, api, _

class RelatedContact(models.Model):
    _name = 'related.contact'
    _description = 'Contacto Adicional Relacionado'
    _rec_name = 'name'
    
    name = fields.Char(string='Nombre', required=True)
    phone = fields.Char(string='Teléfono')
    mobile = fields.Char(string='Móvil')
    email = fields.Char(string='Correo Electrónico')
    position = fields.Char(string='Cargo/Posición')
    notes = fields.Text(string='Notas')
    partner_id = fields.Many2one('res.partner', string='Contacto Principal', ondelete='cascade')
    birthdate = fields.Date(string='Fecha de Nacimiento')
