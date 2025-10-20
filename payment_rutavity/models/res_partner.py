import re
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    anonymized_name = fields.Char(
        string="Anonymized Name",
        compute="_compute_anonymized_name",
        store=False,
    )

    @api.depends("name")
    def _compute_anonymized_name(self):
        """
        Compute anonymized name showing only first 3 characters of each word.
        Rest of characters are replaced with asterisks.
        """
        for partner in self:
            if not partner.name:
                partner.anonymized_name = ""
                continue

            words = partner.name.split()
            anonymized_words = []

            for word in words:
                if len(word) <= 3:
                    # If word has 3 or fewer characters, show it as is
                    anonymized_words.append(word)
                else:
                    # Show first 3 characters + asterisks for the rest
                    anonymized_word = word[:3] + ("*" * (len(word) - 3))
                    anonymized_words.append(anonymized_word)

            partner.anonymized_name = " ".join(anonymized_words)

    def _format_phone_number(self):
        """
        Format phone number by removing country code and special characters.
        :return: The formatted phone number without country code and spaces
        """
        self.ensure_one()

        if not self.phone:
            return ""

        # Remove all spaces and special characters
        formatted_phone = (
            self.phone.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        # Remove country code if present (e.g., +57, +1, etc.)
        if formatted_phone.startswith("+"):
            # Common country codes with their lengths
            # 1 digit: +1 (US/Canada)
            # 2 digits: +57 (Colombia), +52 (Mexico), +34 (Spain), +44 (UK), etc.
            # 3 digits: +593 (Ecuador), +507 (Panama), etc.
            # Try to match known patterns, prioritizing shorter codes
            if re.match(
                r"^\+1\d{10}", formatted_phone
            ):  # US/Canada format: +1 followed by 10 digits
                formatted_phone = formatted_phone[2:]
            elif re.match(
                r"^\+\d{2}\d{10}", formatted_phone
            ):  # 2-digit code + 10 digits
                formatted_phone = formatted_phone[3:]
            elif re.match(r"^\+\d{3}\d{9}", formatted_phone):  # 3-digit code + 9 digits
                formatted_phone = formatted_phone[4:]
            elif re.match(
                r"^\+\d{2}", formatted_phone
            ):  # Fallback: assume 2-digit code
                formatted_phone = formatted_phone[3:]
            elif re.match(
                r"^\+\d{3}", formatted_phone
            ):  # Fallback: assume 3-digit code
                formatted_phone = formatted_phone[4:]
            else:  # Generic fallback: remove + and first digit
                formatted_phone = formatted_phone[2:]

        return formatted_phone

    def _format_document_type(self):
        """
        Map Colombian identification type to Rutavity PSE document type code.
        :return: The mapped document type code (CC, CE, NIT, PPN) or empty string
        """
        self.ensure_one()

        # Mapping of Colombian document codes to Rutavity PSE codes
        DOCUMENT_TYPE_MAPPING = {
            "rut": "NIT",
            "vat": "NIT",
            "national_citizen_id": "CC",
            "foreign_resident_card": "CE",
            "foreign_id_card": "CE",
            "passport": "PPN",
        }

        # Safe access to l10n_co_document_code with proper field existence check
        document_code = (
            self.l10n_latam_identification_type_id.l10n_co_document_code
            if (
                hasattr(self, 'l10n_latam_identification_type_id')
                and self.l10n_latam_identification_type_id
                and hasattr(
                    self.l10n_latam_identification_type_id, "l10n_co_document_code"
                )
            )
            else None
        )

        return DOCUMENT_TYPE_MAPPING.get(document_code, "")
