from odoo import models, fields, api
from datetime import timedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    arrears_amount_debt = fields.Float(
        string='Monto de Deuda en Mora (+30 días)',
        digits=(16, 2),
        compute='_compute_arrears_amount_debt',
        store=False,
        help='Monto de deuda en facturas vencidas hace más de 30 días desde la fecha límite de pago'
    )
    
    is_credit_locked = fields.Boolean(
        string='Bloqueado por Cartera',
        default=False,
        help='Marque esta casilla para bloquear manualmente las ventas a este cliente',
        tracking=True,
    )
    
    has_arrears = fields.Boolean(
        string='Tiene Mora',
        compute='_compute_has_arrears',
        store=False,
        help='Indica si el cliente tiene facturas vencidas hace más de 30 días'
    )
    
    parent_has_arrears = fields.Boolean(
        string='Padre con Mora',
        compute='_compute_parent_has_arrears',
        store=False,
        help='Indica si el contacto padre tiene mora'
    )
    
    children_have_arrears = fields.Boolean(
        string='Hijos con Mora',
        compute='_compute_children_have_arrears',
        store=False,
        help='Indica si algún contacto hijo tiene mora'
    )
    
    family_arrears_amount = fields.Float(
        string='Monto Total en Mora (Familia)',
        digits=(16, 2),
        compute='_compute_family_arrears_amount',
        store=False,
        help='Monto total de mora del contacto, padre e hijos combinados'
    )

    # Calcula el monto de deuda en mora del cliente. Facturas vencidas hace más de 30 días desde la fecha límite de pago.
    @api.depends('invoice_ids', 'invoice_ids.payment_state', 'invoice_ids.invoice_date_due')
    def _compute_arrears_amount_debt(self):
        for partner in self:
            if not partner.id:
                partner.arrears_amount_debt = 0.0
                continue
            
            today = fields.Date.today()
            thirty_days_ago = today - timedelta(days=30)
            
            domain = [
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('move_type', 'in', ['out_invoice']),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '!=', False),
                ('invoice_date_due', '<', thirty_days_ago),
            ]
            
            invoices = self.env['account.move'].search(domain)
            total_arrears = sum(invoice.amount_residual for invoice in invoices)
            partner.arrears_amount_debt = total_arrears

    # Determina si el cliente tiene deuda en mora.
    @api.depends('arrears_amount_debt')
    def _compute_has_arrears(self):
        for partner in self:
            partner.has_arrears = partner.arrears_amount_debt > 0

    # Verifica si el padre tiene mora
    @api.depends('parent_id', 'parent_id.arrears_amount_debt', 'parent_id.is_credit_locked')
    def _compute_parent_has_arrears(self):
        for partner in self:
            if partner.parent_id:
                # El padre tiene mora si tiene deuda en mora o está bloqueado manualmente
                partner.parent_has_arrears = (
                    partner.parent_id.arrears_amount_debt > 0 or 
                    partner.parent_id.is_credit_locked
                )
            else:
                partner.parent_has_arrears = False

    # Verifica si algún hijo tiene mora
    @api.depends('child_ids', 'child_ids.arrears_amount_debt', 'child_ids.is_credit_locked')
    def _compute_children_have_arrears(self):
        for partner in self:
            if partner.child_ids:
                # Buscar si algún hijo tiene mora o está bloqueado
                children_with_arrears = partner.child_ids.filtered(
                    lambda c: c.arrears_amount_debt > 0 or c.is_credit_locked
                )
                partner.children_have_arrears = len(children_with_arrears) > 0
            else:
                partner.children_have_arrears = False

    # Calcula el monto total de mora de la familia (contacto + padre + hijos)
    @api.depends('arrears_amount_debt', 'parent_id', 'parent_id.arrears_amount_debt', 
                 'child_ids', 'child_ids.arrears_amount_debt')
    def _compute_family_arrears_amount(self):
        for partner in self:
            total = partner.arrears_amount_debt
            
            # Sumar mora del padre
            if partner.parent_id:
                total += partner.parent_id.arrears_amount_debt
            
            # Sumar mora de los hijos
            if partner.child_ids:
                total += sum(partner.child_ids.mapped('arrears_amount_debt'))
            
            partner.family_arrears_amount = total

    # Verifica si el cliente está bloqueado para ventas (incluyendo jerarquía familiar)
    def is_blocked_for_sale(self):
        self.ensure_one()
        
        # Bloqueo directo (manual o por mora propia)
        if self.is_credit_locked or self.has_arrears:
            return True
        
        # Bloqueo por padre en mora
        if self.parent_id and (self.parent_id.arrears_amount_debt > 0 or self.parent_id.is_credit_locked):
            return True
        
        # Bloqueo por hijos en mora
        if self.child_ids:
            children_with_issues = self.child_ids.filtered(
                lambda c: c.arrears_amount_debt > 0 or c.is_credit_locked
            )
            if children_with_issues:
                return True
        
        return False

