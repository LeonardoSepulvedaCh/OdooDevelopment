from odoo import models, fields, api


class SaleCommissionPlanAchievement(models.Model):
    """
    Extensión del modelo de logros de comisiones para agregar montos objetivo por categoría.
    
    Este modelo extiende 'sale.commission.plan.achievement' para permitir definir un monto
    objetivo que debe alcanzarse en ventas/facturas para obtener el porcentaje de comisión
    configurado. También agrega soporte para categorías públicas de eCommerce.
    """
    _inherit = 'sale.commission.plan.achievement'

    target_amount = fields.Monetary(
        string='Monto Objetivo',
        currency_field='currency_id',
        help='Monto que debe venderse en esta categoría para obtener la tasa de comisión especificada'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='plan_id.currency_id',
        store=True,
        readonly=True
    )
    
    # Campo para categorías de ecommerce (product.public.category)
    public_categ_id = fields.Many2one(
        'product.public.category',
        string='Categoría de eCommerce',
        help='Categoría pública de eCommerce para filtrar productos'
    )

    @api.depends('product_id', 'product_categ_id', 'public_categ_id', 'type', 'target_amount', 'plan_id')
    def _compute_display_name(self):
        """
        Calcula el nombre de visualización del logro incluyendo información del objetivo.
        
        Construye un nombre descriptivo que incluye:
        - Nombre del plan de comisiones
        - Tipo de logro (amount_sold, qty_sold, amount_invoiced, qty_invoiced)
        - Nombre del producto (si aplica)
        - Nombre de la categoría (pública o interna)
        - Monto objetivo formateado con símbolo de moneda (si está definido)
        
        Ejemplo de resultado:
        "Plan Q1 2024 - Monto Vendido Laptops (Objetivo: $50,000.00)"
        """
        for record in self:
            # Verificar que el plan existe antes de acceder a su nombre
            plan_name = record.plan_id.name if record.plan_id else "Sin Plan"
            product_name = record.product_id.name or ""
            category_name = record.public_categ_id.name or record.product_categ_id.name or ""
            labels = dict(self._fields['type']._description_selection(self.env))
            record_type = record.type and labels.get(record.type, "") or ""
            
            target_info = ""
            if record.target_amount and record.currency_id:
                target_info = f" (Objetivo: {record.currency_id.symbol}{record.target_amount:,.2f})"
            
            record.display_name = f"{plan_name} - {record_type} {product_name} {category_name}{target_info}"

