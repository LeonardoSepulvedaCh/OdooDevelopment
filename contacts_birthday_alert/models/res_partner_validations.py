from datetime import date
from odoo import models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('birth_date')
    def _check_age_limits(self):
        for record in self:
            if not record.birth_date:
                continue
            
            # Obtener parámetros del sistema
            min_age = int(self.env['ir.config_parameter'].sudo().get_param(
                'contacts_birthday_alert.edad_minima', 
                default='0'
            ))
            max_age = int(self.env['ir.config_parameter'].sudo().get_param(
                'contacts_birthday_alert.edad_maxima', 
                default='120'
            ))
            
            # Calcular edad
            today = date.today()
            born = record.birth_date
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            
            # Validar límites
            if age < min_age:
                raise ValidationError(
                    _('La edad del contacto (%d años) es menor a la edad mínima permitida (%d años).') % (age, min_age)
                )
            
            if age > max_age:
                raise ValidationError(
                    _('La edad del contacto (%d años) es mayor a la edad máxima permitida (%d años).') % (age, max_age)
                )

