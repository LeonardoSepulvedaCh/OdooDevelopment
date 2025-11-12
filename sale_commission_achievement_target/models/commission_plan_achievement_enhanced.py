# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class SaleCommissionPlanAchievementEnhanced(models.Model):
    _inherit = 'sale.commission.plan.achievement'

    actual_amount = fields.Monetary(
        string='Monto Real Alcanzado',
        compute='_compute_actual_amount',
        currency_field='currency_id',
        store=False,
        help='Monto real vendido/facturado en esta categoría según el tipo de logro seleccionado'
    )
    
    achievement_percentage = fields.Float(
        string='% Alcanzado',
        compute='_compute_achievement_percentage',
        store=False,
        help='Porcentaje alcanzado del monto objetivo'
    )

    @api.depends('plan_id', 'type', 'product_id', 'product_categ_id', 'plan_id.date_from', 'plan_id.date_to')
    def _compute_actual_amount(self):
        """Calcular el monto real vendido/facturado según el tipo de achievement"""
        for achievement in self:
            if not achievement.plan_id:
                achievement.actual_amount = 0.0
                continue
            
            plan = achievement.plan_id
            domain_base = [
                ('company_id', '=', plan.company_id.id),
            ]
            
            # Filtros de producto/categoría
            product_domain = []
            if achievement.product_id:
                product_domain = [('product_id', '=', achievement.product_id.id)]
            elif achievement.product_categ_id:
                product_domain = [('product_id.categ_id', '=', achievement.product_categ_id.id)]
            
            total = 0.0
            
            # Obtener usuarios del plan
            plan_users = self.env['sale.commission.plan.user'].search([
                ('plan_id', '=', plan.id)
            ])
            
            if achievement.type in ['amount_sold', 'qty_sold']:
                # Calcular desde órdenes de venta
                for plan_user in plan_users:
                    date_from = plan_user.date_from or plan.date_from
                    date_to = plan_user.date_to or plan.date_to
                    
                    order_domain = domain_base + [
                        ('user_id', '=', plan_user.user_id.id),
                        ('state', '=', 'sale'),
                        ('date_order', '>=', date_from),
                        ('date_order', '<=', date_to),
                    ]
                    
                    orders = self.env['sale.order'].search(order_domain)
                    
                    for order in orders:
                        for line in order.order_line.filtered(
                            lambda l: l.display_type is False and 
                                    not l.is_expense and 
                                    not l.is_downpayment
                        ):
                            # Aplicar filtros de producto/categoría
                            if achievement.product_id and line.product_id.id != achievement.product_id.id:
                                continue
                            if achievement.product_categ_id and line.product_id.categ_id.id != achievement.product_categ_id.id:
                                continue
                            
                            if achievement.type == 'amount_sold':
                                # Convertir a moneda de la compañía
                                total += line.price_subtotal / (order.currency_rate or 1.0)
                            elif achievement.type == 'qty_sold':
                                total += line.product_uom_qty
            
            elif achievement.type in ['amount_invoiced', 'qty_invoiced']:
                # Calcular desde facturas
                for plan_user in plan_users:
                    date_from = plan_user.date_from or plan.date_from
                    date_to = plan_user.date_to or plan.date_to
                    
                    move_domain = domain_base + [
                        ('invoice_user_id', '=', plan_user.user_id.id),
                        ('state', '=', 'posted'),
                        ('move_type', 'in', ['out_invoice', 'out_refund']),
                        ('date', '>=', date_from),
                        ('date', '<=', date_to),
                    ]
                    
                    moves = self.env['account.move'].search(move_domain)
                    
                    for move in moves:
                        sign = 1 if move.move_type == 'out_invoice' else -1
                        
                        for line in move.invoice_line_ids.filtered(
                            lambda l: l.display_type == 'product'
                        ):
                            # Aplicar filtros de producto/categoría
                            if achievement.product_id and line.product_id.id != achievement.product_id.id:
                                continue
                            if achievement.product_categ_id and line.product_id.categ_id.id != achievement.product_categ_id.id:
                                continue
                            
                            if achievement.type == 'amount_invoiced':
                                # Convertir a moneda de la compañía
                                total += sign * (line.price_subtotal / (move.invoice_currency_rate or 1.0))
                            elif achievement.type == 'qty_invoiced':
                                total += sign * line.quantity
            
            achievement.actual_amount = total

    @api.depends('actual_amount', 'target_amount')
    def _compute_achievement_percentage(self):
        """Calcular el porcentaje alcanzado del objetivo"""
        for achievement in self:
            if achievement.target_amount and achievement.target_amount > 0:
                achievement.achievement_percentage = (achievement.actual_amount / achievement.target_amount) * 100
            else:
                achievement.achievement_percentage = 0.0

