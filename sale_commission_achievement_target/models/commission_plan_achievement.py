from odoo import models, fields, api


class SaleCommissionPlanAchievement(models.Model):
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

    @api.depends('product_id', 'product_categ_id', 'type', 'target_amount')
    def _compute_display_name(self):
        """Extiende el display_name para incluir el monto objetivo"""
        for record in self:
            product_name = record.product_id.name or ""
            product_categ_id_name = record.product_categ_id.name or ""
            labels = dict(self._fields['type']._description_selection(self.env))
            record_type = record.type and labels.get(record.type, "") or ""
            
            target_info = ""
            if record.target_amount:
                target_info = f" (Objetivo: {record.currency_id.symbol}{record.target_amount:,.2f})"
            
            record.display_name = f"{record.plan_id.name} - {record_type} {product_name} {product_categ_id_name}{target_info}"

