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

        # Build firstName from first_name and second_name
        first_name_parts = []
        if partner.first_name:
            first_name_parts.append(partner.first_name)
        if partner.second_name:
            first_name_parts.append(partner.second_name)
        first_name = " ".join(first_name_parts) if first_name_parts else partner.name

        # Build lastName from first_surname and second_surname
        last_name_parts = []
        if partner.first_surname:
            last_name_parts.append(partner.first_surname)
        if partner.second_surname:
            last_name_parts.append(partner.second_surname)
        last_name = " ".join(last_name_parts) if last_name_parts else partner.name

        return {
            "partner_data": {
                "firstName": first_name.title(),
                "lastName": last_name.title(),
                "email": partner.email or "",
                "phone": partner._format_phone_number(),
                "documentType": partner._format_document_type(),
                "address": partner.contact_address_complete or "",
                "documentNumber": partner.vat or "",
            },
        }
