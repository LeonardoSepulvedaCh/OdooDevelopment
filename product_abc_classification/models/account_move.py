# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    """Extensión de facturas para guardar ABC al validar"""
    _inherit = 'account.move'
    
    def _post(self, soft=True):
        """
        Override del método _post para guardar ABC en líneas al validar factura
        """
        # Llamar al método original
        posted = super(AccountMove, self)._post(soft=soft)
        
        # Actualizar ABC en líneas de factura de cliente
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund') and move.state == 'posted':
                move._update_abc_on_invoice_lines()
        
        return posted
    
    def _update_abc_on_invoice_lines(self):
        """
        Actualizar campos ABC en líneas de factura al validar
        """
        self.ensure_one()
        
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and line.product_id:
                # Obtener ABC del producto al momento de la venta
                product_template = line.product_id.product_tmpl_id
                
                # Determinar bodega de la línea desde la orden de venta
                warehouse_id = False
                if line.sale_line_ids:
                    # Obtener bodega desde la orden de venta
                    sale_order = line.sale_line_ids[0].order_id
                    if sale_order and sale_order.warehouse_id:
                        warehouse_id = sale_order.warehouse_id.id
                
                # Obtener ABC global del producto
                abc_classification_global = product_template.abc_classification_global or 'c'
                abc_sales_value_global = product_template.abc_sales_value_global or 0.0
                
                # Obtener ABC correspondiente por bodega (si existe)
                abc_classification = 'c'
                abc_sales_value = 0.0
                
                if warehouse_id:
                    abc_warehouse = self.env['product.abc.warehouse'].search([
                        ('product_tmpl_id', '=', product_template.id),
                        ('warehouse_id', '=', warehouse_id)
                    ], limit=1)
                    if abc_warehouse:
                        abc_classification = abc_warehouse.classification
                        abc_sales_value = abc_warehouse.sales_value
                    else:
                        # Si no hay ABC por bodega, usar el global
                        abc_classification = abc_classification_global
                        abc_sales_value = abc_sales_value_global
                else:
                    # Si no hay bodega, usar ABC global
                    abc_classification = abc_classification_global
                    abc_sales_value = abc_sales_value_global
                
                # Obtener costo del producto al momento de la venta
                product = line.product_id.with_company(line.company_id or self.env.company)
                product_cost = product.standard_price
                
                # Convertir a la UoM de la línea si es diferente
                if line.product_uom_id and line.product_uom_id != product.uom_id:
                    product_cost = product.uom_id._compute_price(product_cost, line.product_uom_id)
                
                # Actualizar línea con todos los datos al momento de la venta
                line.write({
                    'abc_classification_global_at_sale': abc_classification_global,
                    'abc_classification_at_sale': abc_classification,
                    'abc_sales_value_at_sale': abc_sales_value,
                    'abc_warehouse_id': warehouse_id,
                    'product_cost_at_sale': product_cost,
                })

