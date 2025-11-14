# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    """Extensión de líneas de factura para guardar clasificación ABC al momento de la venta"""
    _inherit = 'account.move.line'
    
    abc_classification_at_sale = fields.Selection([
        ('aaa', 'AAA'),
        ('aa', 'AA'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='ABC at Sale', 
       readonly=True,
       index=True,
       help='ABC classification of the product at the time of invoice validation')
    
    abc_sales_value_at_sale = fields.Float(
        string='ABC Sales Value at Sale',
        readonly=True,
        help='Total sales value used for ABC calculation at the time of invoice validation'
    )
    
    abc_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='ABC Warehouse',
        readonly=True,
        index=True,
        help='Warehouse used for ABC classification calculation'
    )
    
    # Campo almacenado para guardar clasificación ABC global al momento de la venta
    abc_classification_global_at_sale = fields.Selection([
        ('aaa', 'AAA'),
        ('aa', 'AA'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='ABC Global at Sale', 
       readonly=True,
       index=True,
       help='Global ABC classification of the product at the time of invoice validation')
    
    # Campo almacenado para guardar el costo del producto al momento de la venta
    product_cost_at_sale = fields.Float(
        string='Product Cost at Sale',
        readonly=True,
        digits='Product Price',
        help='Standard cost of the product at the time of invoice validation'
    )

