from odoo import fields, models, api
from odoo.exceptions import ValidationError


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
        domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('partner_id', '=', partner_id)]",
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
    
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        """Calcular el número de adjuntos"""
        for ticket in self:
            ticket.attachment_count = len(ticket.attachment_ids)

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

    # Validar que la serie sea obligatoria para equipos de garantías
    @api.constrains('serie', 'team_id')
    def _check_serie_required_for_warranty_team(self):
        for ticket in self:
            if ticket.is_warranty_team and not ticket.serie:
                raise ValidationError(
                    'El campo "Serie" es obligatorio para tickets del equipo de garantías.'
                )
    
    # Validar que la factura sea obligatoria para equipos de garantías
    @api.constrains('invoice_id', 'team_id')
    def _check_invoice_required_for_warranty_team(self):
        for ticket in self:
            if ticket.is_warranty_team and not ticket.invoice_id:
                raise ValidationError(
                    'El campo "Factura" es obligatorio para tickets del equipo de garantías.'
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('partner_id') and not vals.get('card_code'):
                partner = self.env['res.partner'].browse(vals['partner_id'])
                if partner.card_code:
                    vals['card_code'] = partner.card_code
            
            # Generar consecutivo usando secuencias de Odoo si se especifica una serie
            if vals.get('serie'):
                vals['consecutive_number'] = self._get_next_consecutive_number(vals['serie'])
        
        return super().create(vals_list)
    
    # Si se cambia la serie, regenerar el consecutivo. - Esto consumirá el numero de la secuencia anterior (ejem: si esta en la serie de cucuta con el 01 y cambio a bucara, el 01 de cucuta no se reutilizara)
    def write(self, vals):
        if 'serie' in vals:
            for ticket in self:
                # Solo asignar nuevo consecutivo si la serie cambió
                if vals['serie'] != ticket.serie:
                    vals['consecutive_number'] = self._get_next_consecutive_number(vals['serie'])
        
        return super().write(vals)
    
    # Obtener el siguiente número consecutivo usando ir.sequence.
    def _get_next_consecutive_number(self, serie):
        if not serie:
            return 0
        
        sequence_code = self._SERIE_SEQUENCE_MAP.get(serie)
        if not sequence_code:
            return 0
        
        next_number = self.env['ir.sequence'].next_by_code(sequence_code)
        
        if next_number:
            return int(next_number)
        else:
            return 0