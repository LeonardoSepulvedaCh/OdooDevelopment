from odoo import models, api, _
from odoo.exceptions import ValidationError


class HelpdeskPactoMixinValidations(models.AbstractModel):
    _inherit = 'helpdesk.pacto.mixin'

    # Validar que la fecha de registro web no sea menor a la fecha de compra.
    @api.constrains('pacto_fecha_registro_web', 'pacto_fecha_compra')
    def _check_fecha_registro_web(self):
        for record in self:
            if record.pacto_fecha_registro_web and record.pacto_fecha_compra:
                if record.pacto_fecha_registro_web < record.pacto_fecha_compra:
                    raise ValidationError(_(
                        'La fecha de registro en la página web no puede ser menor a la fecha de compra. '
                        'Fecha de compra: %s, Fecha de registro web: %s'
                    ) % (
                        record.pacto_fecha_compra.strftime('%d/%m/%Y'),
                        record.pacto_fecha_registro_web.strftime('%d/%m/%Y')
                    ))

    # Sincronizar la descripción de entrega con la descripción hurtada.
    @api.onchange('pacto_descripcion_bicicleta')
    def _onchange_pacto_descripcion_bicicleta(self):
        if self.pacto_descripcion_bicicleta:
            self.pacto_descripcion_entrega = self.pacto_descripcion_bicicleta

