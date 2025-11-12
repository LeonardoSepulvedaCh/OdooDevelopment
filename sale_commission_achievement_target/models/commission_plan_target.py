# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class SaleCommissionPlanTarget(models.Model):
    _inherit = 'sale.commission.plan.target'

    total_target_by_category = fields.Monetary(
        string='Objetivo Total por Categorías',
        compute='_compute_total_target_by_category',
        currency_field='currency_id',
        store=False,
        help='Suma de todos los montos objetivo configurados en los logros por categoría'
    )

    @api.depends('plan_id.achievement_ids.target_amount')
    def _compute_total_target_by_category(self):
        """Calcular la suma de todos los target_amount de los achievements del plan"""
        for target in self:
            if target.plan_id and target.plan_id.achievement_ids:
                # Sumar solo los target_amount que están configurados (> 0)
                total = sum(
                    achievement.target_amount 
                    for achievement in target.plan_id.achievement_ids 
                    if achievement.target_amount
                )
                target.total_target_by_category = total
            else:
                target.total_target_by_category = 0.0

