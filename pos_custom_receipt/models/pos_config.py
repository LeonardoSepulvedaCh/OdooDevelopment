from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    use_custom_receipt = fields.Boolean(
        string='Usar recibo personalizado',
        default=False,
        help='Activa el uso del recibo personalizado con diseño mejorado, información adicional y estilos modernos'
    )
    
    custom_receipt_header = fields.Text(
        string='Encabezado personalizado',
        help='Contenido personalizado para el encabezado del recibo. Se mostrará cuando esté habilitado el recibo personalizado.'
    )
    
    custom_receipt_footer = fields.Text(
        string='Pie de página personalizado',
        help='Contenido personalizado para el pie de página del recibo. Se mostrará cuando esté habilitado el recibo personalizado.'
    )