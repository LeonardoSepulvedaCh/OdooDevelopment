from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    cashier_user_ids = fields.Many2many(
        'res.users',
        'pos_config_cashier_rel',
        'pos_config_id',
        'user_id',
        string='Cajeros',
        help='Usuarios que pueden actuar como cajeros en este POS',
        domain=[('active', '=', True)],
        default=lambda self: []
    )
    
    salesperson_user_ids = fields.Many2many(
        'res.users',
        'pos_config_salesperson_rel',
        'pos_config_id',
        'user_id',
        string='Vendedores',
        help='Usuarios que pueden actuar como vendedores en este POS',
        domain=[('active', '=', True)],
        default=lambda self: []
    )

    @api.constrains('cashier_user_ids')
    def _check_cashier_users_active(self):
        for record in self:
            inactive_users = record.cashier_user_ids.filtered(lambda u: not u.active)
            if inactive_users:
                raise ValidationError(
                    _('Los siguientes usuarios cajeros no están activos: %s') % 
                    ', '.join(inactive_users.mapped('name'))
                )

    @api.constrains('salesperson_user_ids')
    def _check_salesperson_users_active(self):
        for record in self:
            inactive_users = record.salesperson_user_ids.filtered(lambda u: not u.active)
            if inactive_users:
                raise ValidationError(
                    _('Los siguientes usuarios vendedores no están activos: %s') % 
                    ', '.join(inactive_users.mapped('name'))
                )

    def get_cashier_users(self):
        self.ensure_one()
        return self.cashier_user_ids

    def get_salesperson_users(self):
        self.ensure_one()
        return self.salesperson_user_ids

    def is_user_cashier(self, user_id=None):
        self.ensure_one()
        if not user_id:
            user_id = self.env.user.id
        return user_id in self.cashier_user_ids.ids

    def is_user_salesperson(self, user_id=None):
        self.ensure_one()
        if not user_id:
            user_id = self.env.user.id
        return user_id in self.salesperson_user_ids.ids

