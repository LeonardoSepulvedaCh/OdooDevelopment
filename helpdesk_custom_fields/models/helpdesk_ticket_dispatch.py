from odoo import fields, models, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # ==================== RETORNO DEL CLIENTE AL ALMACÉN ====================
    
    has_return = fields.Boolean(
        string='¿Hubo retorno?',
        default=False,
        help='Indica si el artículo fue retornado del cliente al almacén para evaluación',
        tracking=True
    )

    return_dispatch_method = fields.Selection(
        [
            ('customer_pickup', 'RETORNO CLIENTE'),
            ('carrier', 'TRANSPORTADORA'),
            ('independent', 'INDEPENDIENTE'),
            ('own_transport', 'TRANSPORTE PROPIO'),
            ('cash_on_delivery', 'CONTRA ENTREGA')
        ],
        string='Medio de transporte (retorno)',
        tracking=True
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
        help='Indica si el artículo en garantía fue despachado al cliente',
        tracking=True
    )

    dispatch_method = fields.Selection(
        [
            ('customer_pickup', 'RECOGE CLIENTE'),
            ('carrier', 'TRANSPORTADORA'),
            ('independent', 'INDEPENDIENTE'),
            ('own_transport', 'TRANSPORTE PROPIO'),
            ('cash_on_delivery', 'CONTRA ENTREGA')
        ],
        string='Medio de transporte (despacho)',
        tracking=True
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