from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class HelpdeskPactoMixin(models.AbstractModel):
    """
    Mixin que contiene toda la lógica compartida del Pacto de Reposición
    entre el ticket y el wizard.
    """
    _name = 'helpdesk.pacto.mixin'
    _description = 'Mixin para Pacto de Reposición'

    # ========== DATOS GENERALES ==========
    pacto_fecha_envio_comercial = fields.Date(string='Fecha de envío a comercial')
    pacto_almacen_venta = fields.Char(string='Almacén de venta')
    
    pacto_nombre_cliente = fields.Char(
        string='Nombre del cliente único'
    )
    
    pacto_descripcion_bicicleta = fields.Char(string='Descripción bicicleta hurtada')  
    pacto_cod_base_liquidacion = fields.Char(string='Código base de liquidación')
    pacto_fecha_compra = fields.Date(string='Fecha de compra')
    pacto_fecha_registro_web = fields.Date(string='Fecha registro en página web')
    pacto_descripcion_entrega = fields.Char(string='Descripción bicicleta a entregar')

    # ========== CRITERIOS DE VALIDACIÓN ==========
    pacto_registro_web_30dias = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Registra su Optimus en página web <30 días?')
    pacto_factura_legal = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Presenta la factura legal de compra?')
    pacto_documento_identidad = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Presenta documento de identidad?')
    pacto_testigos_hurto = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3')], string='Testigos del hurto en denuncio')
    pacto_carta_datos_personales = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Carta con datos personales y detalle bicicleta?')
    pacto_firma_pacto_vigente = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Firma Pacto vigente en señal de conocimiento?')
    pacto_presenta_denuncio = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Presenta denuncio entidad competente?')
    pacto_tiempo_reporte = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Tiempo reporte autoridades inferior a 24h?')
    pacto_hurto_con_violencia = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Se cataloga como hurto con violencia?')

    # ========== PUNTOS CALCULADOS ==========
    pacto_puntos_registro_web = fields.Integer(
        string='Puntos Registro Web',
        compute='_compute_pacto_puntos',
        store=True
    )
    
    pacto_puntos_factura = fields.Integer(
        string='Puntos Factura',
        compute='_compute_pacto_puntos',
        store=True
    )
    
    pacto_puntos_documento = fields.Integer(
        string='Puntos Documento',
        compute='_compute_pacto_puntos',
        store=True
    )
    
    pacto_puntos_testigos = fields.Integer(
        string='Puntos Testigos',
        compute='_compute_pacto_puntos',
        store=True
    )
    
    pacto_puntos_carta = fields.Integer(
        string='Puntos Carta',
        compute='_compute_pacto_puntos',
        store=True
    )
    
    pacto_puntos_firma = fields.Integer(
        string='Puntos Firma',
        compute='_compute_pacto_puntos',
        store=True
    )
    
    pacto_puntos_denuncio = fields.Integer(
        string='Puntos Denuncio',
        compute='_compute_pacto_puntos',
        store=True
    )
    
    pacto_puntos_tiempo = fields.Integer(
        string='Puntos Tiempo Reporte',
        compute='_compute_pacto_puntos',
        store=True
    )
    
    pacto_puntos_violencia = fields.Integer(
        string='Puntos Violencia',
        compute='_compute_pacto_puntos',
        store=True
    )

    # ========== TOTALES ==========
    pacto_puntuacion_obtenida = fields.Integer(
        string='Puntuación obtenida',
        compute='_compute_pacto_puntuacion_total',
        store=True
    )
    
    pacto_porcentaje_aprobacion = fields.Float(
        string='Porcentaje de aprobación',
        compute='_compute_pacto_porcentaje',
        store=True,
        digits=(16, 2),
        help='Porcentaje de aprobación del pacto de reposición basado en la puntuación obtenida'
    )

    # ========== VALORES MONETARIOS ==========
    pacto_valor_factura_iva = fields.Monetary(string='Valor factura cliente CON IVA', currency_field='currency_id')
    
    pacto_pvp_actual_iva = fields.Monetary(string='PVP actual CON IVA', currency_field='currency_id')
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )

    # ========== PUNTOS MÁXIMOS ==========
    pacto_puntos_maximos = fields.Integer(
        string='Puntos máximos',
        compute='_compute_pacto_puntos_maximos',
        store=True,
        readonly=True,
        help='Puntuación máxima posible del pacto de reposición'
    )

    # ========== CONFIGURACIÓN DE PUNTOS ==========
    PUNTOS_REGISTRO_WEB = 400
    PUNTOS_FACTURA = 300
    PUNTOS_DOCUMENTO = 200
    PUNTOS_TESTIGOS = {'0': 0, '1': 200, '2': 350, '3': 700}
    PUNTOS_CARTA = 200
    PUNTOS_FIRMA = 200
    PUNTOS_DENUNCIO = 200
    PUNTOS_TIEMPO = 200
    PUNTOS_VIOLENCIA = 200

    def _compute_pacto_puntos_maximos(self):
        """Calcula los puntos máximos posibles del pacto de reposición."""
        for record in self:
            record.pacto_puntos_maximos = (
                self.PUNTOS_REGISTRO_WEB +
                self.PUNTOS_FACTURA +
                self.PUNTOS_DOCUMENTO +
                max(self.PUNTOS_TESTIGOS.values()) +
                self.PUNTOS_CARTA +
                self.PUNTOS_FIRMA +
                self.PUNTOS_DENUNCIO +
                self.PUNTOS_TIEMPO +
                self.PUNTOS_VIOLENCIA
            )

    # Calcular los puntos por cada criterio de validación
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

    # Calcular la puntuación total obtenida
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

    @api.depends('pacto_puntuacion_obtenida', 'pacto_puntos_maximos')
    def _compute_pacto_porcentaje(self):
        for record in self:
            if record.pacto_puntos_maximos > 0:
                porcentaje = ((record.pacto_puntuacion_obtenida / record.pacto_puntos_maximos) * 100) / 2
                record.pacto_porcentaje_aprobacion = round(porcentaje)
            else:
                record.pacto_porcentaje_aprobacion = 0.0
            _logger.info(f"=> Puntuación obtenida: {record.pacto_puntuacion_obtenida}, Puntos máximos: {record.pacto_puntos_maximos}, Porcentaje de aprobación: {record.pacto_porcentaje_aprobacion}")

    # Validar que la fecha de registro web no sea menor a la fecha de compra
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

    # Sincronizar la descripción de entrega con la descripción hurtada
    @api.onchange('pacto_descripcion_bicicleta')
    def _onchange_pacto_descripcion_bicicleta(self):
        if self.pacto_descripcion_bicicleta:
            self.pacto_descripcion_entrega = self.pacto_descripcion_bicicleta

