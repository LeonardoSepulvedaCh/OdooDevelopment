# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductRotationWarehouse(models.Model):
    """Clasificación por Rotación de un producto (global o por bodega específica)"""
    _name = 'product.rotation.warehouse'
    _description = 'Product Rotation Classification (Global or per Warehouse)'
    _order = 'warehouse_id, rotation_classification, rotation_months'
    _rec_name = 'product_tmpl_id'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Producto',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Bodega',
        required=False,  # Permitir NULL para clasificación global
        ondelete='cascade',
        index=True,
        help='Bodega específica. Si está vacío, representa la clasificación global.'
    )
    
    rotation_classification = fields.Selection([
        ('HIGH', 'ALTA'),
        ('LOW', 'BAJA'),
        ('BONE', 'HUESO'),
        ('FEMUR', 'FEMUR'),
        ('DEPLETED', 'AGOTADO'),
        ('INFINITE', 'INFINITO'),
    ], string='Clasificación por Rotación', 
       required=True, 
       index=True,
       help='Clasificación de rotación para este producto (global si no hay bodega, o por bodega específica)')
    
    rotation_months = fields.Float(
        string='Duración (meses)',
        help='Duración estimada del stock en meses'
    )
    
    stock_qty = fields.Float(
        string='Cantidad en Stock',
        help='Cantidad en mano al momento del cálculo'
    )
    
    monthly_consumption = fields.Float(
        string='Consumo Mensual',
        help='Consumo mensual promedio basado en ventas (promedio simple de 12 meses)'
    )
    
    monthly_consumption_top10 = fields.Float(
        string='Consumo Mensual Top 10',
        help='Consumo mensual promedio de los 10 meses más altos (descartando los 2 meses más bajos)'
    )
    
    # Consumos mensuales individuales (últimos 12 meses)
    consumption_m0 = fields.Float(string='M0', help='Consumo del mes actual')
    consumption_m1 = fields.Float(string='M-1', help='Consumo del mes pasado')
    consumption_m2 = fields.Float(string='M-2', help='Consumo de hace 2 meses')
    consumption_m3 = fields.Float(string='M-3', help='Consumo de hace 3 meses')
    consumption_m4 = fields.Float(string='M-4', help='Consumo de hace 4 meses')
    consumption_m5 = fields.Float(string='M-5', help='Consumo de hace 5 meses')
    consumption_m6 = fields.Float(string='M-6', help='Consumo de hace 6 meses')
    consumption_m7 = fields.Float(string='M-7', help='Consumo de hace 7 meses')
    consumption_m8 = fields.Float(string='M-8', help='Consumo de hace 8 meses')
    consumption_m9 = fields.Float(string='M-9', help='Consumo de hace 9 meses')
    consumption_m10 = fields.Float(string='M-10', help='Consumo de hace 10 meses')
    consumption_m11 = fields.Float(string='M-11', help='Consumo de hace 11 meses')
    
    last_calculation = fields.Datetime(
        string='Último Cálculo',
        readonly=True,
        help='Fecha y hora cuando esta rotación fue calculada por última vez'
    )
    
    # Constraints SQL (Odoo 19+)
    # Constraint 1: Único por producto cuando hay bodega específica
    class Constraint(models.Constraint):
        _sql = "UNIQUE(product_tmpl_id, warehouse_id)"
        _name = "unique_product_warehouse_rotation"
        _message = "La clasificación por rotación debe ser única por producto y bodega!"
    
    # Constraint 2: Solo un registro global (warehouse_id=NULL) por producto
    class ConstraintGlobal(models.Constraint):
        _sql = "UNIQUE(product_tmpl_id) WHERE warehouse_id IS NULL"
        _name = "unique_product_global_rotation"
        _message = "Solo puede haber una clasificación global por producto!"
    
    def name_get(self):
        """Nombre personalizado para el modelo"""
        result = []
        for record in self:
            classification_label = dict(self._fields['rotation_classification'].selection).get(record.rotation_classification, '')
            warehouse_name = record.warehouse_id.name if record.warehouse_id else 'Global'
            name = f"{record.product_tmpl_id.name} - {warehouse_name} [{classification_label}]"
            result.append((record.id, name))
        return result

