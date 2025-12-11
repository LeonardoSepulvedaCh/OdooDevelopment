from odoo import fields, models


class HelpdeskPactoMixin(models.AbstractModel):
    _name = 'helpdesk.pacto.mixin'
    _description = 'Mixin para Pacto de Reposición - Campos Base'

    # ========== DATOS GENERALES ==========
    pacto_fecha_envio_comercial = fields.Date(string='Fecha de envío a comercial')
    pacto_almacen_venta = fields.Char(string='Almacén de venta')
    
    pacto_nombre_cliente = fields.Char(
        string='Nombre del cliente único'
    )
    
    pacto_descripcion_bicicleta = fields.Char(string='Descripción bicicleta hurtada')  
    pacto_cod_base_liquidacion = fields.Char(string='Código base de liquidación', help='Código de la bicicleta hurtada al cliente (Código de Barras).')
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
        help='Porcentaje de aprobación del pacto de reposición basado en la puntuación obtenida (máximo 2600 puntos)'
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
        default=lambda self: self._get_puntos_maximos_default(),
        readonly=True,
        help='Puntuación máxima posible del pacto de reposición'
    )

    # Calcular el valor por defecto de los puntos máximos.
    def _get_puntos_maximos_default(self):
        return (
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
