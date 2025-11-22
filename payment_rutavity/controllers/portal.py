from odoo import _, http
from odoo.http import request
from odoo.exceptions import AccessError
from odoo.addons.account_payment.controllers import portal as account_payment_portal
from odoo.addons.payment.controllers.portal import PaymentPortal
from datetime import datetime, timedelta


class PortalAccount(account_payment_portal.PortalAccount):
    # Rate limiting: track requests per IP
    _rate_limit_cache = {}
    _max_requests_per_minute = 10
    _max_invoices_per_request = 20


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

        Security measures:
        - Rate limiting per IP

        :param invoice_ids: Comma-separated list of specific invoice IDs to pay (optional)
        :param access_token: Access token for authentication
        :return: Rendered payment page
        """
        # Get client IP for rate limiting
        client_ip = request.httprequest.remote_addr
        
        # Rate limiting check
        if not self._check_rate_limit(client_ip):
            return request.redirect("/my/invoices")

        # If specific invoice_ids are provided, use them instead of overdue invoices
        if invoice_ids:
            try:
                invoice_id_list = [int(inv_id) for inv_id in invoice_ids.split(",")]
                invoices = request.env["account.move"].sudo().browse(invoice_id_list).exists()

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
        logged_partner = request.env.user.partner_id
        invoice_company = invoices_data["company"] or request.env.company

        availability_report = {}

        # Get compatible providers
        providers_sudo = (
            request.env["payment.provider"]
            .sudo()
            ._get_compatible_providers(
                invoice_company.id,
                logged_partner.id,
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
                logged_partner.id,
                currency_id=invoices_data["currency"].id,
                report=availability_report,
                **kwargs,  # Pass kwargs so payment methods can filter based on context
            )
        )

        tokens_sudo = (
            request.env["payment.token"]
            .sudo()
            ._get_available_tokens(providers_sudo.ids, logged_partner.id)
        )

        # Make sure that the partner's company matches the invoice's company.
        company_mismatch = not PaymentPortal._can_partner_pay_in_company(
            logged_partner, invoice_company
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
            "partner_id": logged_partner.id,
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

    @http.route(
        ["/pagos"],
        type="http",
        auth="public",
        methods=["GET"],
        website=True,
    )
    def portal_invoice_search_page(self, **kw):
        """
        Public invoice search page where users can search invoices by number.

        :return: Rendered invoice search page
        """
        values = {
            "page_name": "invoice_search",
            "page_title": _("Search Invoices"),
        }
        return request.render("payment_rutavity.portal_invoice_search_page", values)

    @http.route(
        ["/invoice/search/results"],
        type="jsonrpc",
        auth="public",
        methods=["POST"],
        csrf=True,
    )
    def portal_invoice_search_results(self, invoice_numbers=None, **kw):
        """
        Search invoices by number with security measures.
        Returns JSON with invoice data for display.

        Security measures:
        - Rate limiting per IP
        - Maximum invoices per request
        - CSRF token validation
        - Access control for invoices

        :param list invoice_numbers: List of invoice numbers to search
        :return: JSON response with invoices data or error
        """
        try:
            # Get client IP for rate limiting
            client_ip = request.httprequest.remote_addr
            
            # Rate limiting check
            if not self._check_rate_limit(client_ip):
                return {
                    "success": False,
                    "error": _("Too many requests. Please wait a moment and try again."),
                }

            # Validate input
            if not invoice_numbers or not isinstance(invoice_numbers, list):
                return {
                    "success": False,
                    "error": _("Please provide at least one invoice number"),
                }

            # Clean and prepare invoice numbers
            invoice_numbers = [num.strip() for num in invoice_numbers if num.strip()]

            if not invoice_numbers:
                return {
                    "success": False,
                    "error": _("Please provide valid invoice numbers"),
                }

            # Limit number of invoices per request to prevent abuse
            if len(invoice_numbers) > self._max_invoices_per_request:
                return {
                    "success": False,
                    "error": _("Maximum %(max)s invoices per search. Please split your request.",
                              max=self._max_invoices_per_request),
                }

            # Search for invoices with security domain
            domain = [
                ("name", "in", invoice_numbers),
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
            ]

            # Use regular search (not sudo) to respect access rights
            invoices = request.env["account.move"].search(domain)

            if not invoices:
                return {
                    "success": False,
                    "error": _("No invoices found with the provided numbers"),
                }

            # Filter only invoices that need payment
            payable_invoices = invoices.filtered(lambda inv: inv._has_to_be_paid())

            if not payable_invoices:
                return {
                    "success": False,
                    "error": _("All invoices found are already paid or cancelled"),
                }

            # Prepare invoice data for response
            invoice_data = []
            for invoice in payable_invoices:
                invoice_data.append(
                    {
                        "id": invoice.id,
                        "name": invoice.name,
                        "amount_due": invoice._get_invoice_next_payment_values().get('amount_due'),
                        "currency": invoice.currency_id.name,
                        "currency_symbol": invoice.currency_id.symbol,
                    }
                )

            # Generate payment URL
            invoice_ids_str = ",".join(str(inv.id) for inv in payable_invoices)
            payment_url = f"/my/invoices/overdue?invoice_ids={invoice_ids_str}"

            return {
                "success": True,
                "invoices": invoice_data,
                "invoice_count": len(payable_invoices),
                "total_amount": sum(inv._get_invoice_next_payment_values().get('amount_due') for inv in payable_invoices),
                "payment_url": payment_url,
            }

        except AccessError:
            return {
                "success": False,
                "error": _("Access denied. You don't have permission to view these invoices."),
            }
        except Exception as e:
            return {
                "success": False,
                "error": _("An error occurred while searching invoices: %s") % str(e),
            }

    def _check_rate_limit(self, client_ip):
        """
        Check if the client IP has exceeded rate limit.
        Uses a simple in-memory cache with timestamp tracking.

        :param str client_ip: Client IP address
        :return: True if request is allowed, False if rate limit exceeded
        :rtype: bool
        """
        current_time = datetime.now()
        
        # Clean old entries (older than 1 minute)
        self._clean_rate_limit_cache(current_time)
        
        # Get or initialize IP tracking
        if client_ip not in self._rate_limit_cache:
            self._rate_limit_cache[client_ip] = []
        
        # Get recent requests for this IP
        ip_requests = self._rate_limit_cache[client_ip]
        
        # Count requests in last minute
        one_minute_ago = current_time - timedelta(minutes=1)
        recent_requests = [req for req in ip_requests if req > one_minute_ago]
        
        # Check if limit exceeded
        if len(recent_requests) >= self._max_requests_per_minute:
            return False
        
        # Add current request
        recent_requests.append(current_time)
        self._rate_limit_cache[client_ip] = recent_requests
        
        return True

    def _clean_rate_limit_cache(self, current_time):
        """
        Clean expired entries from rate limit cache.
        Removes entries older than 2 minutes.

        :param datetime current_time: Current timestamp
        """
        two_minutes_ago = current_time - timedelta(minutes=2)
        
        # Remove expired IPs
        expired_ips = []
        for ip, requests in self._rate_limit_cache.items():
            # Keep only recent requests
            recent = [req for req in requests if req > two_minutes_ago]
            if recent:
                self._rate_limit_cache[ip] = recent
            else:
                expired_ips.append(ip)
        
        # Clean up expired IPs
        for ip in expired_ips:
            del self._rate_limit_cache[ip]

    def _get_account_searchbar_filters(self):
        """
        Override of 'account' to change the label of the vendor bills and customer invoices filters
        """
        values = super()._get_account_searchbar_filters()
        values['bills']['label'] = _('Vendor Bills')
        values['invoices']['label'] = _('Customer Invoices')
        return values

    def _get_account_searchbar_sortings(self):
        """
        Override of 'account' to add the most overdue sorting
        """
        values = super()._get_account_searchbar_sortings()
        values.update({
            'most_overdue': {'label': _('Most Overdue'), 'order': 'invoice_date_due asc'},
        })
        return values

    @staticmethod
    def _validate_transaction_kwargs(kwargs, additional_allowed_keys=()):
        """
        Override of 'payment' to add documents_data to the allowed keys.

        :param dict kwargs: The transaction route's kwargs to verify.
        :param tuple additional_allowed_keys: The keys of kwargs that are contextually allowed.
        :return: None
        :raise BadRequest: If some kwargs keys are rejected.
        """
        additional_allowed_keys = additional_allowed_keys + ("documents_data",)
        return PaymentPortal._validate_transaction_kwargs(kwargs, additional_allowed_keys=additional_allowed_keys)
