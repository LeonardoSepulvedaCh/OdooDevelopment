"""
Author: Sebastián Rodríguez
Payment transaction model for Rutavity Gateway
"""

from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.http import request
import json


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    # === FIELDS ===#
    # https://docs.epayco.com/docs/paginas-de-respuestas#c%C3%B3digos-de-respuesta
    gateway_status = fields.Selection(
        string="Gateway Status",
        selection=[
            ("0", "Draft"),
            ("1", "Approved"),  # Approved - Transaction approved
            ("2", "Rejected"),  # Rejected - Transaction rejected
            ("3", "Pending"),  # Pending - Pending approval (up to 20 min for PSE)
            ("4", "Failed"),  # Failed - Transaction failed
            ("6", "Reversed"),  # Reversed - Money refunded to customer
            ("7", "Held"),  # Held - Held by audit area
            ("8", "Initiated"),  # Initiated - Transaction started
            ("9", "Expired"),  # Expired - Transaction expired (cash/SafetyPay)
            ("10", "Abandoned"),  # Abandoned - User closed browser
            ("11", "Cancelled"),  # Cancelled - User cancelled the process
        ],
        copy=False,
        help="Payment gateway transaction status.",
    )
    gateway_response_message = fields.Char(
        string="Gateway Response Message",
        readonly=True,
        help="Gateway message from the payment gateway.",
    )
    gateway_response_data = fields.Json(
        string="Gateway Response Data",
        readonly=True,
        help="Gateway response data from the payment gateway.",
    )
    gateway_franchise = fields.Char(
        string="Gateway Franchise",
        compute="_compute_gateway_franchise",
        help="Gateway franchise from the payment gateway.",
    )
    gateway_bank = fields.Char(
        string="Gateway Bank",
        compute="_compute_gateway_bank",
        help="Gateway bank from the payment gateway.",
    )
    invoice_amounts_detail = fields.Json(
        string="Invoice Amounts Detail",
        copy=False,
        help="Detailed breakdown of custom amounts to pay for each invoice. "
             "Format: [{'type': 'invoice', 'id': int, 'amount': float, 'currency_id': int}, ...]",
    )
    has_custom_invoice_amounts = fields.Boolean(
        string="Has Custom Invoice Amounts",
        compute="_compute_has_custom_invoice_amounts",
        help="Technical field to indicate if custom amounts are defined for invoices",
    )

    # === CONSTANTS ===#
    PSE_TRANSACTION_ENDPOINT = "payment/process/pse"

    # === COMPUTE METHODS ===#
    @api.depends("invoice_amounts_detail")
    def _compute_has_custom_invoice_amounts(self):
        """
        Compute if the transaction has custom invoice amounts defined.
        """
        for record in self:
            record.has_custom_invoice_amounts = bool(
                record.invoice_amounts_detail 
                and isinstance(record.invoice_amounts_detail, list)
                and len(record.invoice_amounts_detail) > 0
            )

    @api.depends("gateway_response_data")
    def _compute_gateway_franchise(self):
        """
        Compute the gateway franchise for the transaction.
        """
        for record in self:
            if record.gateway_response_data and isinstance(
                record.gateway_response_data, dict
            ):
                record.gateway_franchise = record.gateway_response_data.get(
                    "x_franchise", False
                )
            else:
                record.gateway_franchise = False

    @api.depends("gateway_response_data")
    def _compute_gateway_bank(self):
        """
        Compute the gateway bank for the transaction.
        """
        for record in self:
            if record.gateway_response_data and isinstance(
                record.gateway_response_data, dict
            ):
                record.gateway_bank = record.gateway_response_data.get(
                    "x_bank_name", False
                )
            else:
                record.gateway_bank = False

    # === BUSINESS METHODS ===#
    def _get_specific_rendering_values(self, processing_values):
        """
        Override of `payment` to return Rutavity-specific rendering values.

        Note: `self.ensure_one()` from `_get_rendering_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        rendering_values = super()._get_specific_rendering_values(processing_values)
        
        if self.provider_code == 'rutavity':
            # Add payment_method_code to rendering values for redirect/inline form templates
            rendering_values.update({
                'payment_method_code': self.payment_method_code,
            })

        return rendering_values

    def _set_rutavity_gateway_response(
        self, status: str, message: str, response_data: dict
    ):
        """
        Set the gateway status, message and response data for the transaction.

        :param str status: The status of the transaction
        :param str message: The message of the transaction
        :param dict response_data: The response data of the transaction
        """
        self.ensure_one()
        self.write(
            {
                "gateway_status": status,
                "gateway_response_message": message,
                "gateway_response_data": response_data,
            }
        )

    def create_rutavity_payment_transaction(self, payment_data: dict):
        """
        Create a payment transaction with Rutavity gateway.

        :param dict payment_data: Payment data including amount, currency, reference, etc.
        :return: dict with success status, transaction_id and payment_url or error message
        """
        try:
            if payment_data.get("txProviderCode") != "rutavity":
                raise ValidationError(_("This payment provider is not supported for creating gateway transactions"))

            if payment_data.get("txPaymentMethodCode") != "pse":
                raise ValidationError(_("This payment method is not supported for creating gateway transactions"))

            # Get a singleton gateway
            gateway = self.env["payment.gateway"].sudo()

            # Make the payload for the transaction
            payload = self._make_rutavity_transaction_payload(payment_data)

            # Make API request to create payment
            response = gateway.make_api_request(
                endpoint=self.PSE_TRANSACTION_ENDPOINT, method="POST", data=payload
            )

            # Check response
            if response.get("success"):
                response_data = response.get("data", {})
                reference = response_data.get("ref_payco")
                redirect_url = response_data.get("urlbanco")

                # Update provider reference
                self.write({"provider_reference": reference})

                # Update gateway status
                self._set_rutavity_gateway_response(
                    str(response_data.get("cod_respuesta", "0")),
                    response_data.get("respuesta", _("Unknown message")),
                    response_data,
                )

                return {
                    "success": True,
                    "redirect_url": redirect_url,
                }
            else:
                error_msg = response.get("textResponse", _("Unknown error"))
                data = response.get("data", {})

                # Extract errors from different possible structures
                errors = data.get("errors") or data.get("error", {}).get("errores", [])
                for error in errors:
                    error_msg += f".\n• {error.get('errorMessage', _('Unknown error'))}"

                self._set_rutavity_gateway_response(
                    "4",
                    error_msg,
                    response.get("data", {}),
                )

                # Set transaction state to 'error'
                self._set_error(error_msg)

                return {
                    "success": False,
                    "error": error_msg,
                }

        except Exception as e:
            self._log_message_on_linked_documents(
                _(
                    "Error creating payment gateway transaction in the transaction %(ref)s: %(error)s",
                    ref=self._get_html_link(),
                    error=str(e),
                )
            )
            return {"success": False, "error": str(e)}

    def _make_rutavity_transaction_payload(self, payment_data: dict):
        """
        Make the payload for the transaction.

        :param payment_data: The payment data
        :return: The payload for the transaction
        :rtype: dict
        """
        # Ensure single transaction
        self.ensure_one()

        transaction_type = self._determine_transaction_type(translate=False)

        if transaction_type == "invoice":
            transaction_documents = self.invoice_ids
        else:
            transaction_documents = self.sale_order_ids

        transaction_documents_ids = ",".join(map(str, transaction_documents.ids))

        # Get base URL dynamically
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")

        # Prepare the API request payload
        return {
            "bank": payment_data.get("bank"),
            "value": str(self.amount),
            "description": self._make_rutavity_payment_description(
                self._determine_transaction_type(), transaction_documents
            ),
            "invoice": self.reference,
            "currency": self.currency_id.name,
            "typePerson": "1" if payment_data.get("documentType") == "NIT" else "0",
            "docType": payment_data.get("documentType"),
            "docNumber": payment_data.get("documentNumber"),
            "name": payment_data.get("firstName"),
            "lastname": payment_data.get("lastName"),
            "email": payment_data.get("email"),
            "cellPhone": payment_data.get("phone"),
            "address": payment_data.get("address"),
            "ip": request.httprequest.remote_addr,
            "extra1": str(self.id),
            "extra2": transaction_documents_ids,
            "extra3": transaction_type,
            "extra4": json.dumps(self.invoice_amounts_detail) if self.invoice_amounts_detail else '',
            "methodConfimation": "POST",
            "testMode": False if self.provider_id.state == "enabled" else True,
            "urlResponse": f"{base_url}/payment/status",
            "urlConfirmation": f"{base_url}/payment/gateway/confirmation",
        }

    def _determine_transaction_type(self, translate: bool = True):
        """
        Determine the type of transaction.

        :return: The type of transaction
        :rtype: str
        :raises ValidationError: If the transaction type is invalid
        """
        self.ensure_one()
        if self.sale_order_ids_nbr > 0:
            return _("order") if translate else "order"
        elif self.invoices_count > 0:
            return _("invoice") if translate else "invoice"
        else:
            raise ValidationError(_("Invalid transaction type"))

    @api.model
    def _make_rutavity_payment_description(
        self, payment_type: str, transaction_documents: models.Model
    ):
        """
        Make a payment description for the transaction.

        :param str payment_type: The type of payment (order, invoice, etc.)
        :param models.Model transaction_documents: The transaction documents
        :return: The payment description
        :rtype: str
        """
        transaction_document_names = ", ".join(transaction_documents.mapped('name'))
        return _(
            "Rutavity %(payment_type)s payment - %(payment_reference)s",
            payment_type=payment_type,
            payment_reference=transaction_document_names,
        )

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Override of `payment` to extract the reference from the payment data.

        :param str provider_code: The code of the provider handling the transaction.
        :param dict payment_data: The payment data sent by the provider.
        :return: The transaction reference.
        :rtype: str
        """
        if provider_code != "rutavity":
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get("reference") or payment_data.get("x_id_invoice")

    def _extract_amount_data(self, payment_data):
        """Override of `payment` to extract the amount and currency from the payment data.

        :param dict payment_data: The payment data sent by the provider.
        :return: The amount data, in the {amount: float, currency_code: str} format.
        :rtype: dict|None
        """
        self.ensure_one()

        if self.provider_code != "rutavity" and self.payment_method_code != "pse":
            return super()._extract_amount_data(payment_data)

        return {
            "amount": float(payment_data.get("x_amount")),
            "currency_code": payment_data.get("x_currency_code"),
        }

    def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data received from the provider.
        
        :param dict payment_data: The payment data sent by the provider.
        :return: None
        """
        self.ensure_one()
        if self.provider_code != "rutavity" and self.payment_method_code != "pse":
            return super()._apply_updates(payment_data)

        self._process_rutavity_gateway_confirmation(payment_data)

    def _process_rutavity_gateway_confirmation(self, confirmation_data: dict):
        """
        Process transaction status confirmation from Rutavity gateway.
        This method handles notifications about approved or rejected transactions.

        :param dict confirmation_data: Dictionary containing transaction status from Rutavity
        :return: None
        :rtype: None
        :raises ValidationError: If the transaction is invalid
        :raises Exception: If an error occurs while processing the transaction
        """
        self.ensure_one()

        try:
            # Check if the transaction is valid
            self._validate_rutavity_gateway_transaction(confirmation_data)

            status = str(confirmation_data.get("x_cod_response"))
            self._set_rutavity_gateway_response(
                status,
                confirmation_data.get("x_response_reason_text"),
                confirmation_data,
            )

            # Process transaction based on status
            if status == "1":  # Approved
                self._process_rutavity_success_transaction()
            elif status == "3":  # Pending
                self._process_rutavity_pending_transaction()
            elif status in [
                "2",
                "4",
                "9",
                "10",
                "11",
            ]:  # Rejected, Failed, Expired, Abandoned, Cancelled
                self._process_rutavity_canceled_transaction()
            else:  # Other statuses are considered as failed
                self._process_rutavity_failed_transaction()

        except Exception as e:
            self._log_message_on_linked_documents(
                _(
                    "Error processing then transaction %(ref)s: %(error)s",
                    ref=self._get_html_link(),
                    error=str(e),
                )
            )
            raise Exception(e)

    def _validate_rutavity_gateway_transaction(self, confirmation_data: dict):
        """
        Validate the transaction from Rutavity Gateway.

        :param dict confirmation_data: Dictionary containing transaction status
        :return: None
        :rtype: None
        """
        self.ensure_one()

        # Get a singleton gateway
        gateway = self.env["payment.gateway"].sudo()

        # Validate signature
        if not gateway.validate_transaction_signature(
            confirmation_data.get("x_signature"), confirmation_data
        ):
            raise ValidationError(_("Invalid signature"))

        if self.provider_reference != confirmation_data.get("x_ref_payco"):
            raise ValidationError(
                _(
                    "Transaction reference %(ref)s does not match with the saved reference",
                    ref=confirmation_data.get("x_ref_payco"),
                )
            )

        # Check if the transaction documents match
        if self._determine_transaction_type(translate=False) == "invoice":
            transaction_documents_ids = self.invoice_ids.ids
        else:
            transaction_documents_ids = self.sale_order_ids.ids

        if ",".join(map(str, transaction_documents_ids)) != str(
            confirmation_data.get("x_extra2")
        ):
            raise ValidationError(
                _(
                    "Requested transaction documents: %(requested)s does not match with the saved transaction documents",
                    requested=str(confirmation_data.get("x_extra2")),
                )
            )

    def _process_rutavity_success_transaction(self):
        """
        Process the transaction successfully.
        """
        self.ensure_one()
        if self.state != "done":
            # Confirm transaction
            self._set_done(state_message=self.gateway_response_message)

    def _process_rutavity_pending_transaction(self):
        """
        Process the transaction pending.
        """
        self.ensure_one()
        self.write({"state_message": self.gateway_response_message})

    def _process_rutavity_canceled_transaction(self):
        """
        Process the transaction canceled.
        """
        self.ensure_one()
        self._set_canceled(state_message=self.gateway_response_message)

    def _process_rutavity_failed_transaction(self):
        """
        Process the transaction failed.
        """
        self.ensure_one()
        self._set_error(state_message=self.gateway_response_message)
    
    def _create_payment(self, **extra_create_values):
        """
        Override of `payment` to create individual payments for custom amounts per invoice.
        
        When invoice_amounts_detail is present, creates one payment per invoice
        with its specific amount. Otherwise uses standard Odoo behavior.
        
        Note: This approach creates multiple account.payment records because Odoo's
        standard reconciliation doesn't support partial reconciliation with different
        amounts per invoice in a single payment.
        
        :param extra_create_values: Optional extra create values
        :return: The created payment (first one for backward compatibility)
        :rtype: recordset of `account.payment`
        """
        self.ensure_one()
        
        # If no custom amounts or no invoices, use standard behavior
        if not self.has_custom_invoice_amounts or not self.invoice_ids:
            return super()._create_payment(**extra_create_values)
        
        # Parse custom amounts
        invoice_amounts_map = self._parse_invoice_amounts_detail()
        
        # If no valid custom amounts, use standard behavior
        if not invoice_amounts_map:
            return super()._create_payment(**extra_create_values)
        
        # Validate that we have custom amounts for linked invoices
        linked_invoice_ids = set(self.invoice_ids.ids)
        custom_invoice_ids = set(invoice_amounts_map.keys())
        
        if not linked_invoice_ids.intersection(custom_invoice_ids):
            # No matching invoices, use standard behavior
            return super()._create_payment(**extra_create_values)
        
        # Create individual payments with custom amounts
        return self._create_multiple_payments_with_custom_amounts(invoice_amounts_map, **extra_create_values)
    
    def _create_multiple_payments_with_custom_amounts(self, invoice_amounts_map, **extra_create_values):
        """
        Create multiple payments, one per invoice with its custom amount.
        
        This method creates individual account.payment records for each invoice
        with its specific custom amount, ensuring proper reconciliation and tracking.
        
        :param invoice_amounts_map: Dictionary mapping invoice_id to custom amount
        :param extra_create_values: Extra values for payment creation
        :return: The first created payment (for backward compatibility)
        :rtype: recordset of `account.payment`
        """
        self.ensure_one()
        
        # Post draft invoices first
        self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()
        
        # Get payment method line
        payment_method_line = self.provider_id.journal_id.inbound_payment_method_line_ids.filtered(
            lambda l: l.payment_provider_id == self.provider_id
        )
        
        if not payment_method_line:
            # Fallback to first available inbound payment method
            payment_method_line = self.provider_id.journal_id.inbound_payment_method_line_ids[:1]
        
        if not payment_method_line:
            raise ValidationError(_("No inbound payment method line found for journal %s", self.provider_id.journal_id.name))
        
        # Get destination account from invoices
        payment_term_lines = self.invoice_ids.line_ids.filtered(
            lambda line: line.display_type == 'payment_term'
        )
        destination_account_id = payment_term_lines[0].account_id.id if payment_term_lines else False
        
        # Prepare reference
        reference = f'{self.reference} - {self.provider_reference or ""}'
        
        # Calculate and validate total amount
        total_custom_amount = sum(invoice_amounts_map.values())
        if abs(total_custom_amount - abs(self.amount)) > 0.01:  # Allow 0.01 difference for rounding
            raise ValidationError(
                _("Sum of custom invoice amounts (%(custom)s) does not match transaction amount (%(transaction)s)",
                  custom=total_custom_amount,
                  transaction=abs(self.amount))
            )
        
        # Create individual payments
        created_payments = self.env['account.payment']
        
        for invoice in self.invoice_ids.filtered(lambda inv: inv.state == 'posted'):
            custom_amount = invoice_amounts_map.get(invoice.id)
            
            if not custom_amount or custom_amount <= 0:
                continue
            
            # Validate amount doesn't exceed residual
            if custom_amount > invoice.amount_residual:
                self._log_message_on_linked_documents(
                    _("Warning: Custom amount %(custom)s for invoice %(invoice)s exceeds residual %(residual)s. Using residual amount.",
                      custom=custom_amount,
                      invoice=invoice.name,
                      residual=invoice.amount_residual)
                )
                custom_amount = invoice.amount_residual
            
            # Create payment for this specific invoice
            payment_values = {
                'amount': custom_amount,
                'payment_type': 'inbound' if custom_amount > 0 else 'outbound',
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.commercial_partner_id.id,
                'partner_type': 'customer',
                'journal_id': self.provider_id.journal_id.id,
                'company_id': self.provider_id.company_id.id,
                'payment_method_line_id': payment_method_line.id,
                'payment_token_id': self.token_id.id if self.token_id else False,
                'payment_transaction_id': self.id,
                'memo': f"{reference} - {invoice.name}",
                'invoice_ids': [(6, 0, [invoice.id])],  # Link payment to this specific invoice
                **extra_create_values,
            }
            
            if destination_account_id:
                payment_values['destination_account_id'] = destination_account_id
            
            # Create and post payment
            payment = self.env['account.payment'].create(payment_values)
            payment.action_post()
            
            # Reconcile with this specific invoice
            self._reconcile_payment_with_invoice(payment, invoice)
            
            # Log message on invoice and payment (like native Odoo does)
            message = _(
                "The payment related to transaction %(ref)s has been posted: %(link)s",
                ref=self._get_html_link(),
                link=payment._get_html_link(),
            )
            # Log on this specific invoice
            invoice.message_post(body=message)
            # Log on the payment itself
            payment.message_post(body=message)
            
            created_payments |= payment
        
        # Return first payment (Odoo expects single payment for backward compatibility)
        return created_payments[:1] if created_payments else self.env['account.payment']
    
    def _reconcile_payment_with_invoice(self, payment, invoice):
        """
        Reconcile a payment with a specific invoice.
        
        Uses Odoo's standard reconciliation mechanism to properly
        match the payment with the invoice.
        
        :param payment: The payment record
        :param invoice: The invoice to reconcile with
        :return: None
        """
        self.ensure_one()
        
        # Ensure both payment and invoice moves are posted
        if payment.move_id.state != 'posted':
            raise ValidationError(_("Payment move must be posted before reconciliation"))
        if invoice.state != 'posted':
            raise ValidationError(_("Invoice must be posted before reconciliation"))
        
        # Get payment move lines on receivable/payable account
        payment_lines = payment.move_id.line_ids.filtered(
            lambda line: line.account_id == payment.destination_account_id
            and not line.reconciled
        )
        
        # Get invoice move lines on receivable/payable account
        invoice_lines = invoice.line_ids.filtered(
            lambda line: line.account_id == payment.destination_account_id
            and not line.reconciled
            and line.display_type == 'payment_term'
        )
        
        if not payment_lines:
            self._log_message_on_linked_documents(
                _("Warning: No payment lines found to reconcile for payment %(payment)s",
                  payment=payment.name)
            )
            return
        
        if not invoice_lines:
            self._log_message_on_linked_documents(
                _("Warning: No invoice lines found to reconcile for invoice %(invoice)s",
                  invoice=invoice.name)
            )
            return
        
        # Combine lines and reconcile
        lines_to_reconcile = payment_lines + invoice_lines
        
        try:
            # Let Odoo handle the reconciliation (including partial amounts automatically)
            lines_to_reconcile.reconcile()
        except Exception as e:
            # Log error but don't fail the transaction
            self._log_message_on_linked_documents(
                _("Error reconciling payment %(payment)s with invoice %(invoice)s: %(error)s",
                  payment=payment.name,
                  invoice=invoice.name,
                  error=str(e))
            )
            raise
    
    def _parse_invoice_amounts_detail(self):
        """
        Parse invoice_amounts_detail JSON field into a usable dictionary.
        
        Supports both list and dict formats:
        - List format: [{'id': 2, 'type': 'invoice', 'amount': 1000.0, 'currency_id': 8}, ...]
        - Dict format: {'2': {'amount': 1000.0, 'currency_id': 8}, ...}
        
        :return: Dictionary mapping invoice_id to payment amount
        :rtype: dict
        """
        self.ensure_one()
        
        invoice_amounts_map = {}
        
        if not self.invoice_amounts_detail:
            return invoice_amounts_map
        
        try:
            # Handle list format: [{'id': 2, 'amount': 1000.0, ...}, ...]
            if isinstance(self.invoice_amounts_detail, list):
                for item in self.invoice_amounts_detail:
                    if not isinstance(item, dict):
                        continue
                    
                    invoice_id = item.get('id')
                    amount = item.get('amount')
                    item_type = item.get('type')
                    
                    # Validate it's an invoice type entry
                    if item_type != 'invoice':
                        continue
                    
                    if invoice_id and amount:
                        try:
                            invoice_amounts_map[int(invoice_id)] = float(amount)
                        except (ValueError, TypeError):
                            continue
            
            # Handle dict format: {'123': {'amount': 500.0, ...}, ...}
            elif isinstance(self.invoice_amounts_detail, dict):
                for invoice_id_str, details in self.invoice_amounts_detail.items():
                    if not isinstance(details, dict):
                        continue
                    
                    try:
                        invoice_id = int(invoice_id_str)
                        amount = float(details.get('amount', 0))
                        
                        if amount > 0:
                            invoice_amounts_map[invoice_id] = amount
                    except (ValueError, TypeError):
                        continue
        
        except Exception as e:
            # Log error but don't fail - will fall back to standard behavior
            self._log_message_on_linked_documents(
                _("Error parsing invoice_amounts_detail: %(error)s. Using standard payment behavior.",
                  error=str(e))
            )
            return {}
        
        return invoice_amounts_map

    def _log_message_on_linked_documents(self, message):
        """
        Override of `payment` to log messages on the payment and the invoices linked to the transaction.

        Note: self.ensure_one()

        :param str message: The message to be logged
        :return: None
        """
        self.ensure_one()

        if not message.startswith("The payment related to transaction"):
            return super()._log_message_on_linked_documents(message)
        