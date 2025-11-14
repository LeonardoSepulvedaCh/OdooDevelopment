# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductABCWarehouse(models.Model):
    """Clasificación ABC de un producto por bodega específica"""
    _name = 'product.abc.warehouse'
    _description = 'Product ABC Classification per Warehouse'
    _order = 'warehouse_id, classification, cumulative_percentage'
    _rec_name = 'product_tmpl_id'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    classification = fields.Selection([
        ('aaa', 'AAA'),
        ('aa', 'AA'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='ABC Classification', 
       required=True, 
       index=True,
       help='ABC classification for this product in this specific warehouse')
    
    sales_value = fields.Float(
        string='Sales Value',
        help='Total sales value for this product in this warehouse'
    )
    
    cumulative_percentage = fields.Float(
        string='Cumulative %',
        help='Cumulative percentage of total sales value in this warehouse'
    )
    
    rank = fields.Integer(
        string='Rank',
        help='Product ranking by sales value in this warehouse (1 = highest value)'
    )
    
    last_calculation = fields.Datetime(
        string='Last Calculation',
        readonly=True,
        help='Date and time when this ABC was last calculated'
    )
    
    # Constraint SQL (Odoo 19+)
    class Constraint(models.Constraint):
        _sql = "UNIQUE(product_tmpl_id, warehouse_id)"
        _name = "unique_product_warehouse"
        _message = "ABC classification must be unique per product and warehouse!"
    
    def name_get(self):
        """Nombre personalizado para el modelo"""
        result = []
        for record in self:
            name = f"{record.product_tmpl_id.name} - {record.warehouse_id.name} [{record.classification.upper()}]"
            result.append((record.id, name))
        return result

