from odoo import models, api


class ResPartner(models.Model):
    """
    Extends res.partner to add methods for POS store payment functionality.
    """

    _inherit = "res.partner"

    @api.model
    def get_available_salespeople(self, partner_id):
        """
        Get available salespeople for a POS customer based on their associated POS configs.

        :param int partner_id: The partner id
        :return: List of salespeople with id and name
        :rtype: list of dict
        """
        partner = self.browse(partner_id).exists()
        if not partner or not partner.pos_customer or not partner.pos_config_ids:
            return []

        # Get all salesperson user ids from associated POS configs
        salespeople = partner.pos_config_ids.mapped("salesperson_user_ids")

        # Return list of dicts with id and name
        return [{"id": user.id, "name": user.name} for user in salespeople]

