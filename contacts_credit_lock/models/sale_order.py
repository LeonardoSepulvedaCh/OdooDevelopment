from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_is_blocked = fields.Boolean(
        string='Cliente Bloqueado',
        compute='_compute_partner_is_blocked',
        store=False,
        help='Indica si el cliente está bloqueado por mora o manualmente'
    )
    
    partner_arrears_amount = fields.Float(
        string='Monto en Mora del Cliente',
        compute='_compute_partner_arrears_amount',
        store=False,
        digits=(16, 2),
        help='Monto de deuda en mora del cliente'
    )
    
    partner_family_arrears_amount = fields.Float(
        string='Monto Total en Mora (Familia)',
        compute='_compute_partner_family_arrears_amount',
        store=False,
        digits=(16, 2),
        help='Monto total de mora del cliente, padre e hijos'
    )
    
    block_reason = fields.Char(
        string='Razón del Bloqueo',
        compute='_compute_block_reason',
        store=False,
        help='Indica la razón del bloqueo del cliente'
    )

    # Calcula si el cliente de la orden está bloqueado.
    @api.depends('partner_id', 'partner_id.is_credit_locked', 'partner_id.has_arrears')
    def _compute_partner_is_blocked(self):
        for order in self:
            if order.partner_id:
                order.partner_is_blocked = order.partner_id.is_blocked_for_sale()
            else:
                order.partner_is_blocked = False

    # Calcula el monto en mora del cliente.
    @api.depends('partner_id', 'partner_id.arrears_amount_debt')
    def _compute_partner_arrears_amount(self):
        for order in self:
            if order.partner_id:
                order.partner_arrears_amount = order.partner_id.arrears_amount_debt
            else:
                order.partner_arrears_amount = 0.0

    # Calcula el monto total en mora de la familia.
    @api.depends('partner_id', 'partner_id.family_arrears_amount')
    def _compute_partner_family_arrears_amount(self):
        for order in self:
            if order.partner_id:
                order.partner_family_arrears_amount = order.partner_id.family_arrears_amount
            else:
                order.partner_family_arrears_amount = 0.0

    # Determina la razón del bloqueo del cliente.
    @api.depends('partner_id', 'partner_id.is_credit_locked', 'partner_id.has_arrears', 
                 'partner_id.parent_has_arrears', 'partner_id.children_have_arrears')
    def _compute_block_reason(self):
        for order in self:
            if not order.partner_id or not order.partner_id.is_blocked_for_sale():
                order.block_reason = ''
                continue
            
            reasons = []
            
            # Verificar bloqueo manual
            if order.partner_id.is_credit_locked:
                reasons.append('Cliente bloqueado manualmente por Cartera')
            
            # Verificar mora propia
            if order.partner_id.has_arrears:
                reasons.append('Cliente con deuda en mora propia')
            
            # Verificar mora del padre
            if order.partner_id.parent_has_arrears:
                reasons.append('Contacto padre con mora o bloqueado')
            
            # Verificar mora de hijos
            if order.partner_id.children_have_arrears:
                reasons.append('Contactos hijos con mora o bloqueados')
            
            order.block_reason = ' | '.join(reasons) if reasons else ''

    # Sobrescribe el método de confirmación de orden para validar si el cliente está bloqueado por mora.
    def action_confirm(self):
        for order in self:
            if order.partner_id and order.partner_id.is_blocked_for_sale():
                partner = order.partner_id
                
                # Construir mensaje detallado de la razón del bloqueo
                reasons = []
                
                if partner.is_credit_locked:
                    reasons.append('• Cliente bloqueado manualmente por Cartera')
                
                if partner.has_arrears:
                    reasons.append(f'• Cliente con deuda en mora propia: ${partner.arrears_amount_debt:,.2f}')
                
                if partner.parent_has_arrears:
                    parent_amount = partner.parent_id.arrears_amount_debt if partner.parent_id else 0
                    if parent_amount > 0:
                        reasons.append(f'• Contacto padre ({partner.parent_id.name}) con mora: ${parent_amount:,.2f}')
                    else:
                        reasons.append(f'• Contacto padre ({partner.parent_id.name}) bloqueado manualmente')
                
                if partner.children_have_arrears:
                    children_with_issues = partner.child_ids.filtered(
                        lambda c: c.arrears_amount_debt > 0 or c.is_credit_locked
                    )
                    for child in children_with_issues:
                        if child.arrears_amount_debt > 0:
                            reasons.append(f'• Contacto hijo ({child.name}) con mora: ${child.arrears_amount_debt:,.2f}')
                        else:
                            reasons.append(f'• Contacto hijo ({child.name}) bloqueado manualmente')
                
                # Calcular monto total
                total_family_arrears = partner.family_arrears_amount
                
                # Construir mensaje de error
                error_parts = [
                    _('NO SE PUEDE CONFIRMAR LA ORDEN DE VENTA'),
                    '',
                    _('Razones del bloqueo:'),
                ]
                error_parts.extend(reasons)
                
                if total_family_arrears > 0:
                    error_parts.extend([
                        '',
                        f'Monto Total en Mora (Familia): ${total_family_arrears:,.2f}',
                    ])
                
                error_parts.extend([
                    '',
                    _('Por favor, regularice la situación crediticia antes de continuar.'),
                ])
                
                raise UserError('\n'.join(error_parts))
        
        return super(SaleOrder, self).action_confirm()

