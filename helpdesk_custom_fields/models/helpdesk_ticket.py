from odoo import fields, models, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Campo relacionado para controlar visibilidad
    is_warranty_team = fields.Boolean(
        string='Es equipo de garantías',
        related='team_id.is_warranty_team',
        readonly=True
    )

    card_code = fields.Char(
        string='Código del cliente',
        help='Código del cliente'
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
         ('ticket_cuc', 'Ticket Cucuta'),
         ('ticket_med', 'Ticket Medellín'),
         ('ticket_bog', 'Ticket Bogotá'),
         ('ticket_bga', 'Ticket Bucaramanga'),
         ('ticket_baq', 'Ticket Barranquilla'),
         ('ticket_cal', 'Ticket Cali'),
         ('other', 'Otro')],
        string='Serie'
    )
    
    consecutive_number = fields.Integer(
        string='Consecutivo',
        readonly=True,
        copy=False,
        help='Número consecutivo único por serie. Este número es irrecuperable una vez asignado.'
    )

    warranty_comment = fields.Text(string='Comentario del área de garantías')
    
    # Campo para relacionar factura
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        domain="[('partner_id', '=', partner_id)]",
        help='Factura relacionada con este ticket de garantía'
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_attachment_rel',
        'ticket_id',
        'attachment_id',
        string='Adjuntos',
        help='Documentos, imágenes y otros archivos adjuntos al ticket'
    )
    
    attachment_count = fields.Integer(
        string='Número de adjuntos',
        compute='_compute_attachment_count',
        store=True
    )

    # Mapeo de series a códigos de secuencia
    _SERIE_SEQUENCE_MAP = {
        'pqrs': 'helpdesk.ticket.pqrs',
        'ticket_cuc': 'helpdesk.ticket.cuc',
        'ticket_med': 'helpdesk.ticket.med',
        'ticket_bog': 'helpdesk.ticket.bog',
        'ticket_bga': 'helpdesk.ticket.bga',
        'ticket_baq': 'helpdesk.ticket.baq',
        'ticket_cal': 'helpdesk.ticket.cal',
        'other': 'helpdesk.ticket.other',
    }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and self.partner_id.card_code:
            self.card_code = self.partner_id.card_code
        elif not self.partner_id:
            self.card_code = False
