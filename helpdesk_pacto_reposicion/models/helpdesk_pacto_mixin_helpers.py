from odoo import models
from num2words import num2words
import logging

_logger = logging.getLogger(__name__)


class HelpdeskPactoMixinHelpers(models.AbstractModel):
    _inherit = 'helpdesk.pacto.mixin'

    # Calcular el valor a consignar (PVP actual CON IVA - porcentaje de aprobación).
    def _get_valor_a_consignar(self):
        self.ensure_one()
        if not self.pacto_pvp_actual_iva or not self.pacto_porcentaje_aprobacion:
            return 0.0
        
        # Calcular el descuento
        descuento = self.pacto_pvp_actual_iva * (self.pacto_porcentaje_aprobacion / 100)
        # Valor a consignar = PVP actual - descuento
        valor_consignar = self.pacto_pvp_actual_iva - descuento
        
        return valor_consignar

    # Convertir un valor numérico a texto en español.
    def _get_valor_en_texto(self, valor):
        if not valor:
            return "CERO PESOS"

        try:
            valor_entero = int(valor)
            texto = num2words(valor_entero, lang='es').upper()
            return f"{texto} PESOS"
        except Exception as e:
            _logger.error(f"Error al convertir valor a texto: {e}")
            return "ERROR EN CONVERSIÓN"


    # Verificar si todos los campos requeridos del liquidador están completos.
    def _check_datos_completos_liquidador(self):
        self.ensure_one()
        
        campos_requeridos = [
            'pacto_fecha_envio_comercial',
            'pacto_almacen_venta',
            'pacto_descripcion_bicicleta',
            'pacto_cod_base_liquidacion',
            'pacto_fecha_compra',
            'pacto_fecha_registro_web',
            'pacto_descripcion_entrega',
            'pacto_registro_web_30dias',
            'pacto_factura_legal',
            'pacto_documento_identidad',
            'pacto_testigos_hurto',
            'pacto_carta_datos_personales',
            'pacto_firma_pacto_vigente',
            'pacto_presenta_denuncio',
            'pacto_tiempo_reporte',
            'pacto_hurto_con_violencia',
            'pacto_valor_factura_iva',
            'pacto_pvp_actual_iva',
        ]
        
        for campo in campos_requeridos:
            if not self[campo]:
                return False
        
        return True

