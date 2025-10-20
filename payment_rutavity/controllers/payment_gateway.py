# -*- coding: utf-8 -*-

import logging

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentGatewayController(http.Controller):

    @http.route(
        "/payment/gateway/get_bank_list",
        type="jsonrpc",
        auth="public",
        website=True,
        csrf=True,
    )
    def get_rutavity_gateway_bank_list(self):
        """
        Get the list of available banks.

        :return: JSON response with the list of available banks
        :rtype: dict
        """
        try:
            gateway = request.env["payment.gateway"]
            return gateway.get_bank_list()
        except Exception as e:
            return {"error": str(e)}

    @http.route(
        "/payment/gateway/check_pending_transactions",
        type="jsonrpc",
        auth="public",
        website=True,
        csrf=True,
    )
    def check_pending_transactions(
        self, document_type: str, document_model: str, document_ids: list
    ):
        """
        Check if there are pending transactions for given documents (sale orders or invoices).

        :param str document_type: The transaction type ('single_invoice', 'single_order', 'multiple_invoices')
        :param str document_model: The Odoo model name ('sale.order' or 'account.move')
        :param list document_ids: List of document IDs to check
        :return: dict with has_pending flag
        :rtype: dict
        """
        try:
            # Validate document model
            if document_model not in ["sale.order", "account.move"]:
                return {"success": False, "error": "Invalid document model"}

            # Validate document_ids is a list
            if not isinstance(document_ids, list) or not document_ids:
                return {"success": False, "error": "Invalid document IDs"}

            # Get the documents (sale orders or invoices)
            documents = request.env[document_model].sudo().browse(document_ids)

            if not documents.exists():
                return {
                    "success": True,
                    "has_pending": False,
                }

            if not documents.transaction_ids:
                return {
                    "success": True,
                    "has_pending": False,
                }

            # Filter pending transactions
            pending_transactions = documents.transaction_ids.filtered(
                lambda tx: (
                    tx.state in ["pending", "draft"] and tx.gateway_status == "3"
                )
            )

            return {
                "success": True,
                "has_pending": bool(pending_transactions),
            }
        except Exception as e:
            _logger.error(
                "Error checking pending transactions for %s %s %s: %s",
                document_type,
                document_model,
                document_ids,
                str(e),
            )
            return {"success": False, "error": str(e)}

    @http.route(
        "/payment/gateway/create_transaction",
        type="jsonrpc",
        auth="public",
        website=True,
        csrf=True,
    )
    def create_rutavity_payment_transaction(self, payment_data):
        """
        Create a payment transaction with Rutavity gateway.

        :param dict payment_data: Payment data including amount, currency, reference, etc.
        :return: dict with success status, transaction_id and payment_url or error message
        :raises ValidationError: if the payment data is invalid
        """
        try:
            # Search for existing transaction by reference
            transaction = (
                request.env["payment.transaction"]
                .sudo()
                ._search_by_reference(payment_data.get("txProviderCode"), payment_data)
            )

            if not transaction:
                raise ValidationError(_("Transaction not found"))
            return transaction.create_rutavity_payment_transaction(payment_data)
        except Exception as e:
            return {"error": str(e)}

    @http.route(
        "/payment/gateway/confirmation",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def process_rutavity_gateway_confirmation(self, **post):
        """
        Process the transaction confirmation data from Rutavity gateway.

        :param dict post: POST data containing transaction confirmation data from Rutavity gateway
        :return: HTTP JSON response with success status and message
        """
        try:
            transaction_id = post.get("x_extra1", None)
            if not transaction_id:
                raise ValidationError(_("Transaction ID not found"))

            # Search for existing transaction by ID
            transaction = (
                request.env["payment.transaction"].sudo().browse(int(transaction_id))
            )

            # Check if the transaction exists
            if not transaction.exists():
                raise ValidationError(_("Transaction not found"))

            # Process the transaction
            transaction._process("rutavity", post)

            return request.make_json_response(
                {"success": True, "message": _("Transaction processed successfully")}
            )

        except Exception as e:
            _logger.error(
                "Error processing Rutavity Payment Gateway confirmation: %s", str(e)
            )
            return request.make_json_response({"success": False, "message": str(e)})
