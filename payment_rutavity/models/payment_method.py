from odoo import models, api


class PaymentMethod(models.Model):
    _inherit = "payment.method"

    @api.model
    def get_rutavity_inline_form_data(self, partner_id=None):
        """
        Get the data for the Rutavity inline form.
        
        :param partner_id: The id of the partner
        :return: Dictionary with partner data or empty dictionary if partner is not found
        """
        partner = (
            self.env["res.partner"].sudo().browse(partner_id).exists()
            if partner_id
            else None
        )

        if not partner or partner.is_public:
            return {}

        return {
            "partner_data": {
                "firstName": partner.name or "",
                "lastName": partner.name or "",
                "email": partner.email or "",
                "phone": partner._format_phone_number(),
                "documentType": partner._format_document_type(),
                "address": partner.contact_address_complete or "",
                "documentNumber": partner.vat or "",
            },
        }
