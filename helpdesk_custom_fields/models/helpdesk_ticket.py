from odoo import fields, models, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Campo relacionado para controlar visibilidad
    is_warranty_team = fields.Boolean(
        string='Es equipo de garantías',
        related='team_id.is_warranty_team',
        readonly=True
    )

    client_type = fields.Selection(
        [('wholesaler', 'Mayorista'),
         ('end_consumer', 'Consumidor Final'),
         ('hypermarket', 'Hipermercado'),
         ('tender', 'Licitación'),
         ('other', 'Otro')],
        string='Tipo de cliente'
    )
    
    branch_id = fields.Many2one('stock.warehouse', string='Sucursal')

    origin = fields.Selection(
        [('rutavity', 'Rutavity'),
         ('call_center', 'Call Center'),
         ('email', 'Correo'),
         ('sales_person', 'Asesor'),
         ('other', 'Otro')],
        string='Origen'
    )

    serie = fields.Selection(
        [('pqrs', 'PQRS'),
         ('ticket', 'Ticket'),
         ('other', 'Otro')],
        string='Serie'
    )
    
    consecutive_number = fields.Integer(
        string='Consecutivo',
        readonly=True,
        copy=False,
        help='Número consecutivo único por serie. Este número es irrecuperable una vez asignado.'
    )

    warranty_comment = fields.Text(string='Comentario del área de garantías', tracking=True)
    
    # Campo para relacionar factura
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        domain="[('partner_id', '=', partner_id)]",
        help='Factura relacionada con este ticket de garantía',
        tracking=True
    )
    
    # Productos disponibles de la factura (computed para dominio dinámico)
    available_product_ids = fields.Many2many(
        'product.product',
        string='Productos disponibles',
        compute='_compute_available_products',
        store=False,
        help='Productos disponibles en las líneas de la factura seleccionada'
    )
    
    # Producto asociado al ticket (solo uno)
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        help='Producto relacionado con este ticket de garantía',
        tracking=True
    )
    
    # Cantidad del producto
    product_qty = fields.Float(
        string='Cantidad',
        default=1.0,
        digits='Product Unit of Measure',
        help='Cantidad del producto en garantía (no debe exceder la cantidad facturada)',
        tracking=True
    )
    
    # Cantidad disponible del producto en la factura
    product_qty_available = fields.Float(
        string='Cantidad disponible en factura',
        compute='_compute_product_qty_available',
        store=False,
        help='Cantidad disponible del producto seleccionado en la factura'
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_attachment_rel',
        'ticket_id',
        'attachment_id',
        string='Adjuntos',
        help='Documentos, imágenes y otros archivos adjuntos al ticket',
        tracking=True
    )
    
    attachment_count = fields.Integer(
        string='Número de adjuntos',
        compute='_compute_attachment_count',
        store=True
    )
    
    # Campos para seguimiento de tiempo de resolución
    date_closed = fields.Datetime(
        string='Fecha de finalización',
        readonly=True,
        copy=False,
        help='Fecha y hora en que el ticket fue cerrado/finalizado'
    )
    
    resolution_time_seconds = fields.Integer(
        string='Tiempo de resolución (segundos)',
        compute='_compute_resolution_time',
        store=True,
        help='Tiempo total en segundos desde la creación hasta la finalización del ticket'
    )
    
    resolution_time_hours = fields.Float(
        string='Tiempo de resolución (horas)',
        compute='_compute_resolution_time',
        store=True,
        help='Tiempo transcurrido desde la creación hasta la finalización del ticket en horas'
    )
    
    resolution_time_days = fields.Float(
        string='Tiempo de resolución (días)',
        compute='_compute_resolution_time',
        store=True,
        help='Tiempo transcurrido desde la creación hasta la finalización del ticket en días'
    )
    
    resolution_time_working_seconds = fields.Integer(
        string='Tiempo de resolución laboral (segundos)',
        compute='_compute_resolution_time',
        store=True,
        help='Tiempo en segundos considerando solo horas laborales desde la creación hasta la finalización'
    )

    # Mapeo de series a códigos de secuencia
    _SERIE_SEQUENCE_MAP = {
        'pqrs': 'helpdesk.ticket.pqrs',
        'ticket': 'helpdesk.ticket.ticket',
        'other': 'helpdesk.ticket.other',
    }

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        # Limpiar producto seleccionado cuando cambia la factura
        self.product_id = False
        self.product_qty = 1.0
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        # Resetear cantidad al cambiar de producto
        if self.product_id:
            self.product_qty = 1.0
        else:
            self.product_qty = 0.0
