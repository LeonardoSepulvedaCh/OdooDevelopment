# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    """Extensión de facturas para guardar rotación al validar"""
    _inherit = 'account.move'
    
    def _post(self, soft=True):
        """
        Override del método _post para guardar rotación en líneas al validar factura
        """
        # Llamar al método original
        posted = super(AccountMove, self)._post(soft=soft)
        
        # Actualizar rotación en líneas de factura de cliente
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund') and move.state == 'posted':
                move._update_rotation_on_invoice_lines()
        
        return posted
    
    def _update_rotation_on_invoice_lines(self):
        """
        Actualizar campos de rotación en líneas de factura al validar
        """
        self.ensure_one()
        
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and line.product_id:
                # Obtener rotación del producto al momento de la venta
                product_template = line.product_id.product_tmpl_id
                
                # Determinar bodega de la línea desde la orden de venta
                warehouse_id = False
                if line.sale_line_ids:
                    # Obtener bodega desde la orden de venta
                    sale_order = line.sale_line_ids[0].order_id
                    if sale_order and sale_order.warehouse_id:
                        warehouse_id = sale_order.warehouse_id.id
                
                # Obtener rotación global del producto
                rotation_classification_global = product_template.rotation_classification_global or 'INFINITE'
                rotation_months_global = product_template.rotation_months_global or 0.0
                
                # Obtener rotación correspondiente por bodega (si existe)
                rotation_classification = 'INFINITE'
                rotation_months = 0.0
                
                if warehouse_id:
                    rotation_warehouse = self.env['product.rotation.warehouse'].search([
                        ('product_tmpl_id', '=', product_template.id),
                        ('warehouse_id', '=', warehouse_id)
                    ], limit=1)
                    if rotation_warehouse:
                        rotation_classification = rotation_warehouse.rotation_classification
                        rotation_months = rotation_warehouse.rotation_months
                    else:
                        # Si no hay rotación por bodega, usar el global
                        rotation_classification = rotation_classification_global
                        rotation_months = rotation_months_global
                else:
                    # Si no hay bodega, usar rotación global
                    rotation_classification = rotation_classification_global
                    rotation_months = rotation_months_global
                
                # Actualizar línea con todos los datos al momento de la venta
                line.write({
                    'rotation_classification_global_at_sale': rotation_classification_global,
                    'rotation_classification_at_sale': rotation_classification,
                    'rotation_months_at_sale': rotation_months,
                    'rotation_warehouse_id': warehouse_id,
                })

