from datetime import date
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Campos básicos del contacto
    birth_date = fields.Date(
        string="Fecha de Nacimiento", 
        help="Fecha de nacimiento del contacto"
    )
    card_code = fields.Char(
        string="Código de Contacto", 
        help="Código del contacto",  
        store=True, 
        index=True
    )
    mobile = fields.Char(
        string="Celular", 
        help="Celular del contacto"
    )
    age = fields.Integer(
        string="Edad", 
        compute="_compute_age", 
        store=False, 
        help="Edad calculada desde la fecha de nacimiento"
    )

    # Método para calcular la edad
    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                today = date.today()
                born = record.birth_date
                record.age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            else:
                record.age = 0
