from odoo import models


class SaleCommissionPlan(models.Model):
    """
    Inherits sale.commission.plan to override the action_open_commission method
    and open the custom commission collection report view.
    """
    _inherit = "sale.commission.plan"

    def action_open_commission(self):
        """
        Override the native action to open the commission collection report
        with the custom views and filters applied.
        
        :return: dict with the action configuration
        """
        self.ensure_one()
        
        action = self.env.ref(
            'sale_commission_achievement_target.action_commission_collection_report'
        ).read()[0]
        
        action.update({
            'domain': [('plan_id', '=', self.id)],
            'context': {
                'search_default_group_user': 1,
                'default_plan_id': self.id,
            },
        })
        
        return action
