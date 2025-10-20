from odoo import _, http
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.account_payment.controllers import portal as account_payment_portal
from odoo.addons.payment.controllers.portal import PaymentPortal


class PortalAccount(account_payment_portal.PortalAccount):

    @http.route(
        ["/pagos"],
        type="http",
        auth="public",
        methods=["GET"],
        website=True,
    )
    def portal_public_search_invoices(self, invoice_ids=None, access_token=None, **kw):
        """
        Public entry point to invoice payment page.
        Calls the same logic as /my/invoices/overdue but keeps /pagos URL.
        
        :param invoice_ids: Comma-separated list of invoice IDs to pay
        :param access_token: Access token for authentication
        :return: Rendered payment page with /pagos URL
        """
        # Call the overdue invoices method directly to keep the URL
        return self.portal_my_overdue_invoices(
            invoice_ids=invoice_ids,
            access_token=access_token,
            **kw
        )

    @http.route(
        ["/my/invoices/overdue"],
        type="http",
        auth="public",
        methods=["GET"],
        website=True,
    )
    def portal_my_overdue_invoices(self, invoice_ids=None, access_token=None, **kw):
        """
        Override to support custom invoice selection (not just overdue invoices).
        Public access is allowed via security rules (ir.model.access and ir.rule).

        :param invoice_ids: Comma-separated list of specific invoice IDs to pay (optional)
        :param access_token: Access token for authentication
        :return: Rendered payment page
        """
        # If specific invoice_ids are provided, use them instead of overdue invoices
        if invoice_ids:
            try:
                invoice_id_list = [int(inv_id) for inv_id in invoice_ids.split(",")]
                invoices = request.env["account.move"].browse(invoice_id_list).exists()

                # Filter only invoices that need payment
                invoices = invoices.filtered(lambda inv: inv._has_to_be_paid())

                if not invoices:
                    return request.redirect("/my/invoices")
            except (ValueError, AttributeError):
                return request.redirect("/my/invoices")
        else:
            # Use standard overdue invoices
            invoices = request.env["account.move"].search(
                self._get_overdue_invoices_domain()
            )

        values = self._overdue_invoices_get_page_view_values(invoices, **kw)
        return (
            request.render(
                "payment_rutavity.portal_selected_invoices_payment_page", values
            )
            if "payment" in values
            else request.redirect("/my/invoices")
        )

    def _overdue_invoices_get_page_view_values(self, invoices, **kwargs):
        """
        Override to add invoice list and support custom amounts.

        :param invoices: Invoice recordset to pay
        :return: Dict of values for the template
        """
        # Call parent to get base values
        values = super()._overdue_invoices_get_page_view_values(invoices, **kwargs)

        # If no payment data, return early
        if "payment" not in values:
            return values

        # Add invoice list for custom amount inputs
        values.update(
            {
                "invoices": invoices,
                "invoice_count": len(invoices),
                "page_title": _(
                    "Payment for %(invoice_count)s %(invoice_singular)s",
                    invoice_count=str(len(invoices)),
                    invoice_singular=(
                        _("invoice") if len(invoices) == 1 else _("invoices")
                    ),
                ),
                "logged_partner": request.env.user.partner_id,
            }
        )

        return values

    def _get_common_page_view_values(self, invoices_data, access_token=None, **kwargs):
        """
        Override to pass context flags to _get_compatible_providers and _get_compatible_payment_methods.

        :param dict invoices_data: Data about the invoices being paid
        :param str access_token: Access token for authentication
        :param bool is_multiple_invoice_payment: Whether this is a custom multiple invoice payment
        :return: View values for the payment form
        :rtype: dict
        """
        # Indicate this is an invoice payment (not a sale order)
        # This helps payment methods like credit filter themselves appropriately
        kwargs["is_invoice_payment"] = True

        # Get base values from parent
        logged_in = not request.env.user._is_public()
        partner_sudo = (
            request.env.user.partner_id if logged_in else invoices_data["partner"]
        )
        invoice_company = invoices_data["company"] or request.env.company

        availability_report = {}

        # Get compatible providers
        providers_sudo = (
            request.env["payment.provider"]
            .sudo()
            ._get_compatible_providers(
                invoice_company.id,
                partner_sudo.id,
                invoices_data["total_amount"],
                currency_id=invoices_data["currency"].id,
                report=availability_report,
                **kwargs,
            )
        )

        # Get compatible payment methods - NOW with kwargs passed
        payment_methods_sudo = (
            request.env["payment.method"]
            .sudo()
            ._get_compatible_payment_methods(
                providers_sudo.ids,
                partner_sudo.id,
                currency_id=invoices_data["currency"].id,
                report=availability_report,
                **kwargs,  # Pass kwargs so payment methods can filter based on context
            )
        )

        tokens_sudo = (
            request.env["payment.token"]
            .sudo()
            ._get_available_tokens(providers_sudo.ids, partner_sudo.id)
        )

        # Make sure that the partner's company matches the invoice's company.
        company_mismatch = not PaymentPortal._can_partner_pay_in_company(
            partner_sudo, invoice_company
        )

        portal_page_values = {
            "company_mismatch": company_mismatch,
            "expected_company": invoice_company,
        }
        payment_form_values = {
            "show_tokenize_input_mapping": PaymentPortal._compute_show_tokenize_input_mapping(
                providers_sudo, **kwargs
            ),
        }
        payment_context = {
            "currency": invoices_data["currency"],
            "partner_id": partner_sudo.id,
            "providers_sudo": providers_sudo,
            "payment_methods_sudo": payment_methods_sudo,
            "tokens_sudo": tokens_sudo,
            "availability_report": availability_report,
            "transaction_route": invoices_data["transaction_route"],
            "landing_route": invoices_data["landing_route"],
            "access_token": access_token,
            "payment_reference": invoices_data.get("payment_reference", False),
        }

        # Merge the dictionaries while allowing the redefinition of keys.
        values = (
            portal_page_values
            | payment_form_values
            | payment_context
            | self._get_extra_payment_form_values(**kwargs)
        )
        return values
