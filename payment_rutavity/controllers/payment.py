from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.http import request
from odoo.addons.account_payment.controllers import portal as account_payment_portal


class PaymentPortalRutavity(account_payment_portal.PaymentPortal):

    @http.route("/invoice/transaction/overdue", type="jsonrpc", auth="public")
    def overdue_invoices_transaction(
        self, payment_reference, documents_data=None, **kwargs
    ):
        """
        Override to support custom payment amounts per invoice.

        :param str payment_reference: The reference to the current payment
        :param str documents_data: JSON string with custom amounts per invoice (optional)
        :param dict kwargs: Additional data passed to _create_transaction
        :return: The mandatory values for the processing of the transaction
        :rtype: dict
        :raise: ValidationError if user is not logged in or validation fails
        """
        # If custom amounts are provided, filter invoices based on them
        if (
            documents_data
            and documents_data.get("type") == "multiple_invoices"
            and documents_data.get("data")
        ):
            # Extract the document ids from the documents_data
            invoice_ids = self._extract_document_ids_from_documents_data(
                documents_data.get("data")
            )
            overdue_invoices = request.env["account.move"].browse(invoice_ids).exists()

            # Validate that invoices has to be paid
            overdue_invoices = overdue_invoices.filtered(
                lambda inv: inv._has_to_be_paid()
            )

            if not overdue_invoices:
                raise ValidationError(_("No valid invoices found for payment"))
        else:
            # Use all overdue invoices (original behavior)
            overdue_invoices = request.env["account.move"].search(
                self._get_overdue_invoices_domain()
            )

        # Validate currencies
        currencies = overdue_invoices.mapped("currency_id")
        if not all(currency == currencies[0] for currency in currencies):
            raise ValidationError(
                _(
                    "Impossible to pay all the overdue invoices if they don't share the same currency."
                )
            )

        # Process custom amounts if provided
        if (
            documents_data
            and documents_data.get("type") == "multiple_invoices"
            and documents_data.get("data")
        ):
            self._validate_documents_data(documents_data.get("data"), overdue_invoices)
            custom_create_values = {
                "documents_data": documents_data,
                "landing_route": "/payment/confirmation",
            }

        # Validate transaction kwargs
        self._validate_transaction_kwargs(kwargs)

        # Prepare custom create values with documents_data
        custom_create_values["invoice_ids"] = [Command.set(overdue_invoices.ids)]

        # Merge with any existing custom_create_values from kwargs
        if "custom_create_values" in kwargs:
            existing_custom = kwargs.pop("custom_create_values")
            custom_create_values.update(existing_custom)

        # Update kwargs for transaction creation
        kwargs.update(
            {
                "currency_id": currencies[0].id,
                "partner_id": request.env.user.partner_id.id,
                "reference_prefix": payment_reference,
            }
        )

        # Create transaction with custom values
        tx_sudo = self._create_transaction(
            custom_create_values=custom_create_values,
            **kwargs,
        )

        if (
            documents_data
            and documents_data.get("type") == "multiple_invoices"
            and documents_data.get("data")
        ):
            tx_sudo._update_landing_route()

        return tx_sudo._get_processing_values()

    def _extract_document_ids_from_documents_data(self, documents_data):
        """
        Extract document ids from the documents_data parameter.

        :param documents_data: list of dicts with document ids
        :return: List of document ids
        :rtype: list
        """
        return list(map(lambda document: int(document.get("id")), documents_data))

    def _validate_documents_data(self, documents_data, invoices):
        """
        Validate the documents data.

        :param documents_data: list of dicts with invoice data [{"id": int, "amount": float, "currency_id": int}, ...]
        :param recordset invoices: Invoice recordset
        :return: None
        :raises ValidationError: If validation fails
        """
        if not documents_data or not isinstance(documents_data, list):
            raise ValidationError(_("Invalid payment amounts data format"))

        # Convert documents_data list to dict for easier lookup
        documents_dict = {int(doc.get("id")): doc for doc in documents_data}

        for invoice in invoices:
            # Find the document data for this invoice
            amount_data = documents_dict.get(invoice.id)

            if not amount_data:
                raise ValidationError(
                    _("Missing payment amount for invoice %s", invoice.name)
                )

            amount = float(amount_data.get("amount", 0))
            currency_id = int(amount_data.get("currency_id", invoice.currency_id.id))

            # Validate amount is positive
            if amount <= 0:
                raise ValidationError(
                    _(
                        "Payment amount for invoice %s must be greater than zero",
                        invoice.name,
                    )
                )

            # Validate amount doesn't exceed invoice residual
            if amount > invoice.amount_residual:
                raise ValidationError(
                    _(
                        "Payment amount for invoice %s (%(amount)s) cannot exceed the amount due (%(residual)s)",
                        invoice.name,
                        amount=amount,
                        residual=invoice.amount_residual,
                    )
                )

            # Validate currency matches
            if currency_id != invoice.currency_id.id:
                raise ValidationError(
                    _("Currency mismatch for invoice %s", invoice.name)
                )
