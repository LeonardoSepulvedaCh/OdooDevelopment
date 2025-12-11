from odoo import fields, models, api

class HelpdeskPactoWizard(models.TransientModel):
    _name = 'helpdesk.pacto.wizard'
    _inherit = 'helpdesk.pacto.mixin'
    _description = 'Liquidador Pacto de Reposición'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        readonly=True
    )
    
    datos_completos = fields.Boolean(
        string='Datos Completos',
        compute='_compute_datos_completos',
        store=False
    )
    
    is_pacto_stage_critical = fields.Boolean(
        string='Etapa Crítica',
        related='ticket_id.is_pacto_stage_critical',
        store=False,
        help='Indica si el ticket está en una etapa crítica para mostrar los botones de imprimir/enviar'
    )

    # Sobrescribir campos del mixin para hacerlos requeridos en el wizard
    pacto_fecha_envio_comercial = fields.Date(required=True)
    pacto_almacen_venta = fields.Char(required=True)
    pacto_descripcion_bicicleta = fields.Char(required=True)
    pacto_cod_base_liquidacion = fields.Char(required=True)
    pacto_fecha_compra = fields.Date(required=True)
    pacto_fecha_registro_web = fields.Date(required=True)
    pacto_descripcion_entrega = fields.Char(required=True)
    pacto_registro_web_30dias = fields.Selection(required=True)
    pacto_factura_legal = fields.Selection(required=True)
    pacto_documento_identidad = fields.Selection(required=True)
    pacto_testigos_hurto = fields.Selection(required=True)
    pacto_carta_datos_personales = fields.Selection(required=True)
    pacto_firma_pacto_vigente = fields.Selection(required=True)
    pacto_presenta_denuncio = fields.Selection(required=True)
    pacto_tiempo_reporte = fields.Selection(required=True)
    pacto_hurto_con_violencia = fields.Selection(required=True)
    pacto_valor_factura_iva = fields.Monetary(required=True)
    pacto_pvp_actual_iva = fields.Monetary(required=True)

    # Calcular si todos los datos del liquidador están completos.
    @api.depends(
        'pacto_fecha_envio_comercial', 'pacto_almacen_venta', 'pacto_descripcion_bicicleta',
        'pacto_cod_base_liquidacion', 'pacto_fecha_compra', 'pacto_fecha_registro_web',
        'pacto_descripcion_entrega', 'pacto_registro_web_30dias', 'pacto_factura_legal',
        'pacto_documento_identidad', 'pacto_testigos_hurto', 'pacto_carta_datos_personales',
        'pacto_firma_pacto_vigente', 'pacto_presenta_denuncio', 'pacto_tiempo_reporte',
        'pacto_hurto_con_violencia', 'pacto_valor_factura_iva', 'pacto_pvp_actual_iva'
    )
    def _compute_datos_completos(self):
        for record in self:
            record.datos_completos = record._check_datos_completos_liquidador()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        ticket_id = self.env.context.get('active_id')
        force_default = self.env.context.get('force_default_values', False)
        
        if ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(ticket_id)
            res['ticket_id'] = ticket.id
            
            # Si force_default_values está en True o no hay datos guardados, cargar datos básicos
            if force_default or not ticket.pacto_fecha_envio_comercial:
                res.update(self._cargar_datos_basicos_ticket(ticket, fields_list))
            else:
                # Si el ticket ya tiene datos del pacto, cargarlos
                res.update(self._get_datos_ticket_to_wizard(ticket))
                # Asegurar que la descripción de entrega esté sincronizada con la hurtada
                if (ticket.pacto_descripcion_bicicleta and 'pacto_descripcion_entrega' in fields_list and
                    (not ticket.pacto_descripcion_entrega or ticket.pacto_descripcion_entrega != ticket.pacto_descripcion_bicicleta)):
                    res['pacto_descripcion_entrega'] = ticket.pacto_descripcion_bicicleta
        
        return res

    # Cargar datos básicos del ticket para pre-llenar el wizard
    def _cargar_datos_basicos_ticket(self, ticket, fields_list):
        datos = {}
        datos.update(self._cargar_datos_partner(ticket, fields_list))
        datos.update(self._cargar_fechas_ticket(ticket, fields_list))
        datos.update(self._cargar_datos_producto(ticket, fields_list))
        datos.update(self._cargar_valor_factura(ticket, fields_list))
        return datos
    
    # Cargar datos del partner
    def _cargar_datos_partner(self, ticket, fields_list):
        datos = {}
        if not ticket.partner_id:
            return datos
        
        partner_name = ticket.partner_id.name
        if 'pacto_nombre_cliente' in fields_list:
            datos['pacto_nombre_cliente'] = partner_name
        if 'pacto_almacen_venta' in fields_list:
            datos['pacto_almacen_venta'] = partner_name
        return datos
    
    # Cargar fechas del ticket
    def _cargar_fechas_ticket(self, ticket, fields_list):
        datos = {}
        
        # Fecha de envío a comercial
        if ticket.create_date and 'pacto_fecha_envio_comercial' in fields_list:
            fecha_creacion = ticket.create_date.date() if hasattr(ticket.create_date, 'date') else ticket.create_date
            datos['pacto_fecha_envio_comercial'] = fecha_creacion
        
        # Fecha de compra desde la factura
        if ticket.invoice_id and ticket.invoice_id.invoice_date and 'pacto_fecha_compra' in fields_list:
            datos['pacto_fecha_compra'] = ticket.invoice_id.invoice_date
        
        return datos
    
    # Cargar datos del producto
    def _cargar_datos_producto(self, ticket, fields_list):
        datos = {}
        if not (ticket.product_id and 'pacto_descripcion_bicicleta' in fields_list):
            return datos
        
        producto_nombre = ticket.product_id.name
        datos['pacto_descripcion_bicicleta'] = producto_nombre
        
        # La descripción de entrega es la misma que la hurtada
        if 'pacto_descripcion_entrega' in fields_list:
            datos['pacto_descripcion_entrega'] = producto_nombre
        
        return datos
    
    # Cargar valor de factura con IVA
    def _cargar_valor_factura(self, ticket, fields_list):
        datos = {}
        if not (ticket.invoice_id and ticket.product_id and 'pacto_valor_factura_iva' in fields_list):
            return datos
        
        valor_iva = self._calcular_valor_producto_con_iva(ticket)
        if valor_iva > 0:
            datos['pacto_valor_factura_iva'] = valor_iva
        
        return datos

    # Calcular el valor con IVA del producto seleccionado en la factura
    def _calcular_valor_producto_con_iva(self, ticket):
        if not ticket.invoice_id or not ticket.product_id:
            return 0.0
        
        # Buscar la línea de factura que corresponde al producto seleccionado
        invoice_line = ticket.invoice_id.invoice_line_ids.filtered(
            lambda line: line.product_id == ticket.product_id
        )
        
        if not invoice_line:
            return 0.0
        
        # Si hay múltiples líneas con el mismo producto, tomar la primera
        invoice_line = invoice_line[0]
        
        # Obtener el precio unitario con IVA
        if invoice_line.quantity > 0:
            precio_unitario_con_iva = invoice_line.price_total / invoice_line.quantity
        else:
            return 0.0
        
        # Calcular el valor total basado en la cantidad del ticket
        cantidad_ticket = ticket.product_qty if ticket.product_qty else 1.0
        valor_total_con_iva = precio_unitario_con_iva * cantidad_ticket
        
        return valor_total_con_iva

    # Obtener los datos del ticket para cargarlos en el wizard.
    def _get_datos_ticket_to_wizard(self, ticket):
        return {
            'pacto_fecha_envio_comercial': ticket.pacto_fecha_envio_comercial,
            'pacto_nombre_cliente': ticket.pacto_nombre_cliente,
            'pacto_almacen_venta': ticket.pacto_almacen_venta,
            'pacto_descripcion_bicicleta': ticket.pacto_descripcion_bicicleta,
            'pacto_cod_base_liquidacion': ticket.pacto_cod_base_liquidacion,
            'pacto_fecha_compra': ticket.pacto_fecha_compra,
            'pacto_fecha_registro_web': ticket.pacto_fecha_registro_web,
            'pacto_descripcion_entrega': ticket.pacto_descripcion_entrega,
            'pacto_registro_web_30dias': ticket.pacto_registro_web_30dias,
            'pacto_factura_legal': ticket.pacto_factura_legal,
            'pacto_documento_identidad': ticket.pacto_documento_identidad,
            'pacto_testigos_hurto': ticket.pacto_testigos_hurto,
            'pacto_carta_datos_personales': ticket.pacto_carta_datos_personales,
            'pacto_firma_pacto_vigente': ticket.pacto_firma_pacto_vigente,
            'pacto_presenta_denuncio': ticket.pacto_presenta_denuncio,
            'pacto_tiempo_reporte': ticket.pacto_tiempo_reporte,
            'pacto_hurto_con_violencia': ticket.pacto_hurto_con_violencia,
            'pacto_valor_factura_iva': ticket.pacto_valor_factura_iva,
            'pacto_pvp_actual_iva': ticket.pacto_pvp_actual_iva,
        }

    # Obtener los datos del wizard para guardarlos en el ticket.
    def _get_datos_wizard_to_ticket(self):
        self.ensure_one()
        return {
            'pacto_fecha_envio_comercial': self.pacto_fecha_envio_comercial,
            'pacto_nombre_cliente': self.pacto_nombre_cliente,
            'pacto_almacen_venta': self.pacto_almacen_venta,
            'pacto_descripcion_bicicleta': self.pacto_descripcion_bicicleta,
            'pacto_cod_base_liquidacion': self.pacto_cod_base_liquidacion,
            'pacto_fecha_compra': self.pacto_fecha_compra,
            'pacto_fecha_registro_web': self.pacto_fecha_registro_web,
            'pacto_descripcion_entrega': self.pacto_descripcion_entrega,
            'pacto_registro_web_30dias': self.pacto_registro_web_30dias,
            'pacto_factura_legal': self.pacto_factura_legal,
            'pacto_documento_identidad': self.pacto_documento_identidad,
            'pacto_testigos_hurto': self.pacto_testigos_hurto,
            'pacto_carta_datos_personales': self.pacto_carta_datos_personales,
            'pacto_firma_pacto_vigente': self.pacto_firma_pacto_vigente,
            'pacto_presenta_denuncio': self.pacto_presenta_denuncio,
            'pacto_tiempo_reporte': self.pacto_tiempo_reporte,
            'pacto_hurto_con_violencia': self.pacto_hurto_con_violencia,
            'pacto_valor_factura_iva': self.pacto_valor_factura_iva,
            'pacto_pvp_actual_iva': self.pacto_pvp_actual_iva,
        }
