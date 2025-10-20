from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("rutavity", "Rutavity")], ondelete={"rutavity": "set default"}
    )
    epayco_cust_id = fields.Char(string="P_CUST_ID_CLIENTE")
    epayco_public_key = fields.Char(string="PUBLIC_KEY", groups="base.group_system")
    epayco_private_key = fields.Char(string="PRIVATE_KEY", groups="base.group_system")
    epayco_p_key = fields.Char(string="P_KEY", groups="base.group_system")
