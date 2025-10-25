from odoo import fields, models, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # ==================== RETORNO DEL CLIENTE AL ALMACÉN ====================
    
    has_return = fields.Boolean(
        string='¿Hubo retorno?',
        default=False,
        help='Indica si el artículo fue retornado del cliente al almacén para evaluación'
    )

    return_dispatch_method = fields.Selection(
        [
            ('customer_pickup', 'RETORNO CLIENTE'),
            ('carrier', 'TRANSPORTADORA'),
            ('independent', 'INDEPENDIENTE'),
            ('own_transport', 'TRANSPORTE PROPIO'),
            ('cash_on_delivery', 'CONTRA ENTREGA'),
            ('not_applicable', 'NO APLICA')
        ],
        string='Medio de transporte (retorno)'
    )

    return_carrier_name = fields.Many2one(
        'res.partner',
        string='Transportador (retorno)',
        domain="[('category_id.name', 'in', ['Transportadora', 'Transportadora independiente'])]",
        help='Empresa transportadora para el retorno'
    )

    return_carrier_guide_number = fields.Char(
        string='N° Guía Transportador (retorno)',
        help='Número de guía del transportador para el retorno'
    )

    return_vehicle_plate = fields.Char(
        string='Placa Vehículo (retorno)',
        help='Placa del vehículo que realiza el retorno'
    )

    return_package_count = fields.Integer(
        string='Número Paquetes (retorno)',
        default=0,
        help='Cantidad de paquetes en el retorno'
    )

    return_freight_value = fields.Float(
        string='Valor Flete (retorno)',
        digits=(16, 2),
        default=0.0,
        help='Valor del flete de retorno del cliente al almacén'
    )

    return_declared_merchandise_value = fields.Float(
        string='Valor mercancía declarado (retorno)',
        digits=(16, 2),
        default=0.0,
        help='Valor declarado de la mercancía para el retorno'
    )

    # ==================== DESPACHO DEL ALMACÉN AL CLIENTE ====================
    
    is_dispatched = fields.Boolean(
        string='¿Fue despachado?',
        default=False,
        help='Indica si el artículo en garantía fue despachado al cliente'
    )

    dispatch_method = fields.Selection(
        [
            ('customer_pickup', 'RECOGE CLIENTE'),
            ('carrier', 'TRANSPORTADORA'),
            ('independent', 'INDEPENDIENTE'),
            ('own_transport', 'TRANSPORTE PROPIO'),
            ('cash_on_delivery', 'CONTRA ENTREGA'),
            ('not_applicable', 'NO APLICA')
        ],
        string='Medio de transporte (despacho)'
    )

    carrier_name = fields.Many2one(
        'res.partner',
        string='Transportador (despacho)',
        domain="[('category_id.name', 'in', ['Transportadora', 'Transportadora independiente'])]",
        help='Empresa transportadora para el despacho'
    )

    carrier_guide_number = fields.Char(
        string='N° Guía Transportador (despacho)',
        help='Número de guía del transportador'
    )

    vehicle_plate = fields.Char(
        string='Placa Vehículo (despacho)',
        help='Placa del vehículo que realiza el transporte'
    )

    package_count = fields.Integer(
        string='Número Paquetes (despacho)',
        default=0,
        help='Cantidad de paquetes enviados'
    )

    freight_value = fields.Float(
        string='Valor Flete (despacho)',
        digits=(16, 2),
        default=0.0,
        help='Valor del flete de transporte'
    )

    declared_merchandise_value = fields.Float(
        string='Valor mercancía declarado (despacho)',
        digits=(16, 2),
        default=0.0,
        help='Valor declarado de la mercancía para el transporte'
    )

    # Onchange para limpiar todos los campos de retorno cuando se desmarca has_return
    @api.onchange('has_return')
    def _onchange_has_return(self):
        if not self.has_return:
            self.return_dispatch_method = False
            self.return_carrier_name = False
            self.return_carrier_guide_number = False
            self.return_vehicle_plate = False
            self.return_package_count = 0
            self.return_freight_value = 0.0
            self.return_declared_merchandise_value = 0.0

    # Onchange para limpiar campos de retorno cuando no es transportadora o independiente
    @api.onchange('return_dispatch_method')
    def _onchange_return_dispatch_method(self):
        if self.return_dispatch_method not in ('carrier', 'independent'):
            self.return_carrier_name = False
            self.return_carrier_guide_number = False
            self.return_vehicle_plate = False
            self.return_package_count = 0
            self.return_freight_value = 0.0
            self.return_declared_merchandise_value = 0.0

    # Onchange para limpiar todos los campos de despacho cuando se desmarca is_dispatched
    @api.onchange('is_dispatched')
    def _onchange_is_dispatched(self):
        if not self.is_dispatched:
            self.dispatch_method = False
            self.carrier_name = False
            self.carrier_guide_number = False
            self.vehicle_plate = False
            self.package_count = 0
            self.freight_value = 0.0
            self.declared_merchandise_value = 0.0

    # Onchange para limpiar campos de despacho cuando no es transportadora o independiente
    @api.onchange('dispatch_method')
    def _onchange_dispatch_method(self):
        if self.dispatch_method not in ('carrier', 'independent'):
            self.carrier_name = False
            self.carrier_guide_number = False
            self.vehicle_plate = False
            self.package_count = 0
            self.freight_value = 0.0
            self.declared_merchandise_value = 0.0

