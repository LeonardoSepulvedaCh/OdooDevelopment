# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    """Extensión de líneas de factura para guardar clasificación por rotación al momento de la venta"""
    _inherit = 'account.move.line'
    
    # Campos para almacenar clasificación por rotación al momento de la venta
    rotation_classification_global_at_sale = fields.Selection([
        ('HIGH', 'ALTA'),
        ('LOW', 'BAJA'),
        ('BONE', 'HUESO'),
        ('FEMUR', 'FEMUR'),
        ('DEPLETED', 'AGOTADO'),
        ('INFINITE', 'INFINITO'),
    ], string='Rotación Global al Vender',
       readonly=True,
       index=True,
       help='Clasificación global por rotación del producto al momento de validar la factura')
    
    rotation_classification_at_sale = fields.Selection([
        ('HIGH', 'ALTA'),
        ('LOW', 'BAJA'),
        ('BONE', 'HUESO'),
        ('FEMUR', 'FEMUR'),
        ('DEPLETED', 'AGOTADO'),
        ('INFINITE', 'INFINITO'),
    ], string='Rotación al Vender',
       readonly=True,
       index=True,
       help='Clasificación por rotación de bodega específica al momento de validar la factura')
    
    rotation_months_at_sale = fields.Float(
        string='Meses de Rotación al Vender',
        readonly=True,
        help='Duración estimada del stock en meses al momento de la venta'
    )
    
    rotation_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Bodega de Rotación',
        readonly=True,
        index=True,
        help='Bodega asociada a esta línea para clasificación por rotación'
    )

