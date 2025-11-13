from odoo import models, fields, api


class SaleCommissionPlanTarget(models.Model):
    """
    Extensión del modelo de objetivos de planes de comisión.
    
    Agrega un campo computado que suma todos los montos objetivo definidos
    en los logros (achievements) asociados al plan de comisiones, permitiendo
    visualizar el objetivo total acumulado por todas las categorías configuradas.
    """
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
        """
        Calcula la suma total de todos los montos objetivo de los logros del plan.
        
        Recorre todos los achievements asociados al plan de comisiones y suma
        los valores de target_amount configurados. Solo considera montos mayores
        a cero para evitar contar logros sin objetivo definido.
        
        El resultado se almacena en el campo total_target_by_category y se muestra
        en la moneda del plan de comisiones.
        
        Returns:
            None: El método actualiza el campo computado directamente en cada registro.
        """
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

