from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    verification_digit = fields.Char(string='Digito Verificador', compute='_compute_verification_digit', store=True)

    def _calculate_verification_digit(self, vat_number):
        if not vat_number:
            return None
            
        # Pesos según la DIAN para documentos de hasta 15 dígitos
        pesos = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
        
        # Limpiar el VAT, solo mantener dígitos
        vat_clean = ''.join(ch for ch in vat_number if ch.isdigit())
        
        if not vat_clean:
            return None
            
        # Rellenar con ceros a la izquierda hasta completar 15 posiciones
        vat_padded = vat_clean.zfill(15)
        
        # Verificar que no exceda 15 dígitos
        if len(vat_padded) > 15:
            return None
            
        # Calcular la suma de productos
        suma = 0
        for i in range(len(vat_padded)):
            suma += int(vat_padded[i]) * pesos[i]
        
        # Calcular el residuo
        residuo = suma % 11
        
        # Determinar el dígito de verificación
        if residuo == 0:
            return '0'
        elif residuo == 1:
            return '1'
        else:
            return str(11 - residuo)

    @api.depends('vat')
    def _compute_verification_digit(self):
        for partner in self:
            vat = partner.vat or ''
            
            # Si el VAT ya contiene un guión, extraer solo la parte numérica
            if '-' in vat:
                vat_number = vat.split('-')[0]
            else:
                vat_number = vat
            
            # Calcular el dígito verificador
            digito = self._calculate_verification_digit(vat_number)
            
            if digito:
                partner.verification_digit = digito
            else:
                partner.verification_digit = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'vat' in vals and vals['vat']:
                formatted_vat = self._format_vat_with_digit(vals['vat'])
                if formatted_vat != vals['vat']:
                    vals['vat'] = formatted_vat
        return super().create(vals_list)

    def write(self, vals):
        if 'vat' in vals and vals['vat']:
            formatted_vat = self._format_vat_with_digit(vals['vat'])
            if formatted_vat != vals['vat']:
                vals['vat'] = formatted_vat
        return super().write(vals)
    

    def _format_vat_with_digit(self, vat_value):
        if not vat_value:
            return vat_value
            
        # Si ya contiene un guión, extraer solo la parte numérica
        if '-' in vat_value:
            vat_number = vat_value.split('-')[0]
        else:
            vat_number = vat_value
        
        # Calcular el dígito verificador
        digito = self._calculate_verification_digit(vat_number)
        
        if digito:
            vat_clean = ''.join(ch for ch in vat_number if ch.isdigit())
            return f'{vat_clean}-{digito}'
        else:
            return vat_value

        