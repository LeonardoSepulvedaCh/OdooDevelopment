from odoo import models, fields, api

class ContactDocument(models.Model):
    _name = 'contact.document'
    _description = 'Documento de Contacto'

    partner_id = fields.Many2one('res.partner', string='Contacto', required=True)
    document_type_id = fields.Many2one('document.type', string='Tipo de Documento', required=True, 
                                       domain=[('active', '=', True)])
    file = fields.Binary(string='Archivo', required=True, attachment=True)
    file_name = fields.Char(string='Nombre del Archivo')
    state = fields.Selection(selection=[
        ('new', 'Nuevo'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], default='new', required=True)

    # Al modificar un campo, el estado se establece como nuevo
    @api.onchange('partner_id', 'document_type_id', 'file', 'file_name')
    def _onchange_document_fields(self):
        self.state = 'new'

    def action_approve(self):
        self.state = 'approved'

    def action_reject(self):
        self.state = 'rejected'
