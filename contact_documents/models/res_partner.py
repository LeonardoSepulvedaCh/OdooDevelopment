from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    document_ids = fields.One2many('contact.document', 'partner_id', string='Documentos de Contacto')
    document_count = fields.Integer(string='Número de Documentos', compute='_compute_document_count')

    @api.depends('document_ids')
    def _compute_document_count(self):
        """Compute the number of documents for each partner"""
        for partner in self:
            partner.document_count = len(partner.document_ids)
