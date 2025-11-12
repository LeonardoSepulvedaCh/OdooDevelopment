# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class SaleCommissionPlanAchievementDebug(models.Model):
    _inherit = 'sale.commission.plan.achievement'

    @api.model
    def debug_target_amounts(self):
        """Método de debug para verificar los target_amounts configurados"""
        _logger.info("=" * 80)
        _logger.info("=== DEBUG: VERIFICANDO TARGET AMOUNTS EN BD ===")
        
        # Primero mostrar TODOS los achievements
        all_achievements = self.search([])
        _logger.info(f"Total de achievements en el sistema: {len(all_achievements)}")
        
        achievements_without_target = self.search([('target_amount', '<=', 0)])
        _logger.info(f"Achievements SIN target_amount (o con 0): {len(achievements_without_target)}")
        
        achievements = self.search([('target_amount', '>', 0)])
        _logger.info(f"Achievements CON target_amount > 0: {len(achievements)}")
        
        # Mostrar achievements SIN target
        if achievements_without_target:
            _logger.info("\n" + "=" * 80)
            _logger.info("=== ACHIEVEMENTS SIN TARGET_AMOUNT (ESTOS DARÁN COMISIÓN SIEMPRE) ===")
            for ach in achievements_without_target:
                _logger.info("-" * 60)
                _logger.info(f"Plan: {ach.plan_id.name}")
                _logger.info(f"Type: {ach.type}")
                _logger.info(f"Product: {ach.product_id.name if ach.product_id else 'Todos'}")
                _logger.info(f"Category: {ach.product_categ_id.name if ach.product_categ_id else 'Todas'}")
                _logger.info(f"Rate: {ach.rate * 100}%")
                _logger.info(f"TARGET_AMOUNT: {ach.target_amount} (NO CONFIGURADO - DARÁ COMISIÓN SIEMPRE)")
        
        _logger.info("\n" + "=" * 80)
        _logger.info("=== ACHIEVEMENTS CON TARGET_AMOUNT ===")
        _logger.info(f"Total de achievements con target_amount > 0: {len(achievements)}")
        
        for achievement in achievements:
            _logger.info("-" * 60)
            _logger.info(f"Plan: {achievement.plan_id.name}")
            _logger.info(f"Type: {achievement.type}")
            _logger.info(f"Product: {achievement.product_id.name if achievement.product_id else 'Todos'}")
            _logger.info(f"Category: {achievement.product_categ_id.name if achievement.product_categ_id else 'Todas'}")
            _logger.info(f"Rate: {achievement.rate * 100}%")
            _logger.info(f"TARGET_AMOUNT: {achievement.target_amount} {achievement.currency_id.symbol}")
            
            # Buscar usuarios asignados a este plan
            plan_users = self.env['sale.commission.plan.user'].search([
                ('plan_id', '=', achievement.plan_id.id)
            ])
            _logger.info(f"Usuarios en este plan: {[u.user_id.name for u in plan_users]}")
            
            # Verificar ventas de estos usuarios
            for plan_user in plan_users[:3]:  # Solo primeros 3 para no saturar el log
                user = plan_user.user_id
                sale_orders = self.env['sale.order'].search([
                    ('user_id', '=', user.id),
                    ('state', '=', 'sale'),
                    ('date_order', '>=', plan_user.date_from or achievement.plan_id.date_from),
                    ('date_order', '<=', plan_user.date_to or achievement.plan_id.date_to),
                ])
                
                total_by_category = 0
                for order in sale_orders:
                    for line in order.order_line:
                        # Verificar si la línea coincide con el achievement
                        if achievement.product_id and line.product_id.id != achievement.product_id.id:
                            continue
                        if achievement.product_categ_id and line.product_id.categ_id.id != achievement.product_categ_id.id:
                            continue
                        
                        total_by_category += line.price_subtotal
                
                _logger.info(f"  Usuario: {user.name}")
                _logger.info(f"    Ventas en categoría: {total_by_category}")
                _logger.info(f"    Target requerido: {achievement.target_amount}")
                _logger.info(f"    ¿Alcanzó objetivo?: {total_by_category >= achievement.target_amount}")
        
        _logger.info("=" * 80)
        return True

