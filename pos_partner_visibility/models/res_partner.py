from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    pos_customer = fields.Boolean(
        string="Cliente POS",
        default=False,
        help="Habilitar para que el cliente sea visible en el POS",
        index=True,
    )

    pos_config_ids = fields.Many2many(
        "pos.config",
        "res_partner_pos_config_rel",
        "partner_id",
        "pos_config_id",
        string="Associated POS",
        help="POS configurations associated with this customer",
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields.append("pos_customer")
        fields.append("pos_config_ids")
        return fields

    @api.onchange("pos_customer")
    def _onchange_pos_customer(self):
        """
        Clear pos_config_ids when pos_customer is disabled.
        """
        if not self.pos_customer:
            self.pos_config_ids = False
