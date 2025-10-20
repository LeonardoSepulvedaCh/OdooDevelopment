from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.http import request
from odoo.addons.account_payment.controllers import portal as account_payment_portal
import json


class PaymentPortalRutavity(account_payment_portal.PaymentPortal):

    @http.route("/invoice/transaction/overdue", type="jsonrpc", auth="public")
    def overdue_invoices_transaction(
        self, payment_reference, invoice_amounts_detail=None, **kwargs
    ):
        """
        Override to support custom payment amounts per invoice.

        :param str payment_reference: The reference to the current payment
        :param str invoice_amounts_detail: JSON string with custom amounts per invoice (optional)
        :param dict kwargs: Additional data passed to _create_transaction
        :return: The mandatory values for the processing of the transaction
        :rtype: dict
        :raise: ValidationError if user is not logged in or validation fails
        """
        partner = request.env.user.partner_id

        # If custom amounts are provided, filter invoices based on them
        if invoice_amounts_detail:
            # Parse the invoice_amounts_detail to get the invoice IDs
            invoice_ids = self._extract_invoice_ids_from_amounts(invoice_amounts_detail)
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
        custom_amounts = None
        if invoice_amounts_detail:
            custom_amounts = self._process_invoice_amounts_detail(
                invoice_amounts_detail, overdue_invoices
            )

            # Calculate total from custom amounts (array format)
            total_amount = sum(item["amount"] for item in custom_amounts)
            kwargs["amount"] = total_amount

        # Validate transaction kwargs
        self._validate_transaction_kwargs(kwargs)

        # Prepare custom create values with invoice_amounts_detail
        custom_create_values = {
            "invoice_ids": [Command.set(overdue_invoices.ids)],
        }

        # Add invoice amounts detail if provided
        if custom_amounts:
            custom_create_values["invoice_amounts_detail"] = custom_amounts

        # Merge with any existing custom_create_values from kwargs
        if "custom_create_values" in kwargs:
            existing_custom = kwargs.pop("custom_create_values")
            custom_create_values.update(existing_custom)

        # Update kwargs for transaction creation
        kwargs.update(
            {
                "currency_id": currencies[0].id,
                "partner_id": partner.id,
                "reference_prefix": payment_reference,
            }
        )

        # Create transaction with custom values
        tx_sudo = self._create_transaction(
            custom_create_values=custom_create_values,
            **kwargs,
        )

        return tx_sudo._get_processing_values()

    def _extract_invoice_ids_from_amounts(self, invoice_amounts_detail):
        """
        Extract invoice IDs from the invoice_amounts_detail parameter.

        :param invoice_amounts_detail: JSON string or dict with invoice amounts
        :return: List of invoice IDs
        :rtype: list
        """
        # Parse JSON string if provided
        if isinstance(invoice_amounts_detail, str):
            try:
                custom_amounts = json.loads(invoice_amounts_detail)
            except (json.JSONDecodeError, TypeError):
                return []
        elif isinstance(invoice_amounts_detail, dict):
            custom_amounts = invoice_amounts_detail
        else:
            return []

        # Extract invoice IDs (keys can be strings or ints)
        invoice_ids = []
        for key in custom_amounts.keys():
            try:
                invoice_ids.append(int(key))
            except (ValueError, TypeError):
                continue

        return invoice_ids

    def _process_invoice_amounts_detail(self, invoice_amounts_detail, invoices):
        """
        Process and validate custom payment amounts for invoices.

        :param str invoice_amounts_detail: JSON string with custom amounts
        :param recordset invoices: Invoice recordset
        :return: List of dicts with invoice payment details
        :rtype: list
        :raises ValidationError: If validation fails
        """

        # Parse JSON string if provided
        if isinstance(invoice_amounts_detail, str):
            try:
                custom_amounts = json.loads(invoice_amounts_detail)
            except (json.JSONDecodeError, TypeError):
                raise ValidationError(_("Invalid payment amounts data format"))
        elif isinstance(invoice_amounts_detail, dict):
            custom_amounts = invoice_amounts_detail
        else:
            # If no custom amounts provided, use full amounts
            custom_amounts = {}
            for invoice in invoices:
                custom_amounts[str(invoice.id)] = {
                    "amount": invoice.amount_residual,
                    "currency_id": invoice.currency_id.id,
                }

        # Validate custom amounts and build array
        validated_amounts = []
        for invoice in invoices:
            invoice_id_str = str(invoice.id)

            # Try to find the invoice amount (key could be string or int)
            amount_data = None
            if invoice_id_str in custom_amounts:
                amount_data = custom_amounts[invoice_id_str]
            elif invoice.id in custom_amounts:
                amount_data = custom_amounts[invoice.id]

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

            # Add to array with new format
            validated_amounts.append(
                {
                    "type": "invoice",
                    "id": invoice.id,
                    "amount": amount,
                    "currency_id": currency_id,
                }
            )

        return validated_amounts
