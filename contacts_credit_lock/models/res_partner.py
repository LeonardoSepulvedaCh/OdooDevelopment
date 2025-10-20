from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    portfolio_blocked = fields.Boolean(
        string="Cuenta bloqueada por cartera",
        default=False,
        help="Marque esta casilla si el contacto está bloqueado por problemas de cartera.",
        tracking=True,
        copy=False,
    )
    portfolio_block_reason = fields.Text(
        string="Razón del bloqueo",
        help="Especifique la razón por la cual este contacto está bloqueado.",
        tracking=True,
        copy=False,
    )
    
    can_user_block_portfolio = fields.Boolean(
        string="Usuario puede bloquear por cartera",
        compute='_compute_can_user_block_portfolio',
        store=False,
    )
    
    # Verificar si el usuario actual puede bloquear por cartera
    @api.depends_context('uid')
    def _compute_can_user_block_portfolio(self):
        for partner in self:
            # Verifica si el usuario actual tiene el campo can_block_portfolio activado
            partner.can_user_block_portfolio = self.env.user.can_block_portfolio

    # Verificar si un contacto está bloqueado por problemas de cartera y también verifica los contactos padres en la jerarquía.
    def _is_portfolio_blocked(self):
        self.ensure_one()
        partner = self
        
        # Verificar el contacto actual y recorre la jerarquía hacia arriba
        while partner:
            if partner.portfolio_blocked:
                return True
            partner = partner.parent_id
        
        return False

    # Obtener la razoón del bloqueo por cartera.
    def _get_portfolio_block_reason(self):
        self.ensure_one()
        partner = self
        
        # Verificar el contacto actual y recorre la jerarquía hacia arriba
        while partner:
            if partner.portfolio_blocked and partner.portfolio_block_reason:
                return partner.portfolio_block_reason
            partner = partner.parent_id
        
        return ""

