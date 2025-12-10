from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    registration_id = fields.Many2one(
        'contact.registration',
        string='Registrado desde QR',
        readonly=True,
        ondelete='set null'
    )

