from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    is_warranty_certificate = fields.Boolean(
        string='Es acta de garantía',
        default=False,
        help='Marca este adjunto como acta de garantía del ticket'
    )

