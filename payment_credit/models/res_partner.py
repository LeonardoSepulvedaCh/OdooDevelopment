# Author: Sebastián Rodríguez
from odoo import models
from odoo.tools import formatLang

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_available_credit(self, formatted=False):
        """
        Get the available credit for a partner.

        :param formatted: Whether to return the credit in a formatted string.
        :type formatted: bool
        :return: The available credit.
        :rtype: float
        """
        self.ensure_one()
        partner = self
        resolved_limit = 0.0
        limit_holder = False

        # Search for the first limit (> 0) upwards in the hierarchy
        while partner:
            if partner.use_partner_credit_limit and partner.credit_limit > 0:
                resolved_limit = partner.credit_limit
                limit_holder = partner
                break
            partner = partner.parent_id

        # Exposure (debt): accumulated if there's a limit in hierarchy, otherwise only current
        if limit_holder:
            # Include the limit_holder itself plus all its children
            group_partners = self.env['res.partner'].search([
                '|',
                ('id', '=', limit_holder.id),
                ('id', 'child_of', limit_holder.id),
            ])
            exposure_credit = abs(sum(group_partners.mapped('credit') or [0.0]))
            exposure_to_invoice = abs(sum(group_partners.mapped('credit_to_invoice') or [0.0]))
            exposure = exposure_credit + exposure_to_invoice
        else:
            exposure = (self.credit or 0.0) + (self.credit_to_invoice or 0.0)

        available_credit = resolved_limit - exposure
        if formatted:
            return formatLang(self.env, available_credit, currency_obj=self.currency_id)
        return available_credit

    def _has_sufficient_credit(self, amount=0.0):
        """
        Check if a partner has sufficient credit.

        :param amount: The amount to check.
        :type amount: float
        :return: Whether the partner has sufficient credit.
        :rtype: bool
        """
        self.ensure_one()
        return self._get_available_credit() >= amount
