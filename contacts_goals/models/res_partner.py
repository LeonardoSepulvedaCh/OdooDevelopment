from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_goal_ids = fields.One2many(
        'customer.goal', 
        'partner_id', 
        string='Metas Comerciales', 
        tracking=True,
        groups='contacts_goals.group_contacts_goals_user'
    )
    customer_goal_count = fields.Integer(
        string='Cantidad de Metas', 
        compute='_compute_customer_goal_count', 
        tracking=True,
        groups='contacts_goals.group_contacts_goals_user'
    )
    active_goal_count = fields.Integer(
        string='Metas Activas', 
        compute='_compute_active_goal_count', 
        tracking=True,
        groups='contacts_goals.group_contacts_goals_user'
    )
    
    # Computar la cantidad de metas del cliente
    @api.depends('customer_goal_ids')
    def _compute_customer_goal_count(self):
        for partner in self:
            if self.env.user.has_group('contacts_goals.group_contacts_goals_user'):
                partner.customer_goal_count = len(partner.customer_goal_ids)
            else:
                partner.customer_goal_count = 0
    
    # Computar la cantidad de metas activas del cliente
    @api.depends('customer_goal_ids', 'customer_goal_ids.state')
    def _compute_active_goal_count(self):
        for partner in self:
            if self.env.user.has_group('contacts_goals.group_contacts_goals_user'):
                partner.active_goal_count = len(
                    partner.customer_goal_ids.filtered(lambda g: g.state == 'active')
                )
            else:
                partner.active_goal_count = 0
    
    # Acciones para ver las metas del cliente
    def action_view_customer_goals(self):
        self.ensure_one()
        return {
            'name': f'Metas de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'customer.goal',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

