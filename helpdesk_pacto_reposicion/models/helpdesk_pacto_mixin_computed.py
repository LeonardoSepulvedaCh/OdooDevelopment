from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class HelpdeskPactoMixinComputed(models.AbstractModel):
    _inherit = 'helpdesk.pacto.mixin'

    # Calcula los puntos por cada criterio de validación.
    @api.depends(
        'pacto_registro_web_30dias', 'pacto_factura_legal', 'pacto_documento_identidad', 'pacto_testigos_hurto', 'pacto_carta_datos_personales',
        'pacto_firma_pacto_vigente', 'pacto_presenta_denuncio', 'pacto_tiempo_reporte', 'pacto_hurto_con_violencia'
    )
    def _compute_pacto_puntos(self):
        for record in self:
            record.pacto_puntos_registro_web = (
                self.PUNTOS_REGISTRO_WEB if record.pacto_registro_web_30dias == 'si' else 0
            )
            record.pacto_puntos_factura = (
                self.PUNTOS_FACTURA if record.pacto_factura_legal == 'si' else 0
            )
            record.pacto_puntos_documento = (
                self.PUNTOS_DOCUMENTO if record.pacto_documento_identidad == 'si' else 0
            )
            record.pacto_puntos_testigos = self.PUNTOS_TESTIGOS.get(record.pacto_testigos_hurto, 0)
            record.pacto_puntos_carta = (
                self.PUNTOS_CARTA if record.pacto_carta_datos_personales == 'si' else 0
            )
            record.pacto_puntos_firma = (
                self.PUNTOS_FIRMA if record.pacto_firma_pacto_vigente == 'si' else 0
            )
            record.pacto_puntos_denuncio = (
                self.PUNTOS_DENUNCIO if record.pacto_presenta_denuncio == 'si' else 0
            )
            record.pacto_puntos_tiempo = (
                self.PUNTOS_TIEMPO if record.pacto_tiempo_reporte == 'si' else 0
            )
            record.pacto_puntos_violencia = (
                self.PUNTOS_VIOLENCIA if record.pacto_hurto_con_violencia == 'si' else 0
            )

    # Calcula la puntuación total obtenida.
    @api.depends(
        'pacto_puntos_registro_web', 'pacto_puntos_factura', 'pacto_puntos_documento', 'pacto_puntos_testigos',
        'pacto_puntos_carta', 'pacto_puntos_firma', 'pacto_puntos_denuncio', 'pacto_puntos_tiempo', 'pacto_puntos_violencia'
    )
    def _compute_pacto_puntuacion_total(self):
        for record in self:
            record.pacto_puntuacion_obtenida = sum([
                record.pacto_puntos_registro_web,
                record.pacto_puntos_factura,
                record.pacto_puntos_documento,
                record.pacto_puntos_testigos,
                record.pacto_puntos_carta,
                record.pacto_puntos_firma,
                record.pacto_puntos_denuncio,
                record.pacto_puntos_tiempo,
                record.pacto_puntos_violencia
            ])

    # Calcula el porcentaje de aprobación.
    @api.depends('pacto_puntuacion_obtenida')
    def _compute_pacto_porcentaje(self):
        PUNTOS_MAXIMOS = 2600  # Valor fijo: suma de todos los puntos posibles
        for record in self:
            if record.pacto_puntuacion_obtenida > 0:
                porcentaje = ((record.pacto_puntuacion_obtenida / PUNTOS_MAXIMOS) * 100) / 2
                record.pacto_porcentaje_aprobacion = round(porcentaje)
            else:
                record.pacto_porcentaje_aprobacion = 0.0
            _logger.info(f"=> Puntuación obtenida: {record.pacto_puntuacion_obtenida}, Puntos máximos: {PUNTOS_MAXIMOS}, Porcentaje de aprobación: {record.pacto_porcentaje_aprobacion}")

