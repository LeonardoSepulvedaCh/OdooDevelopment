# Author: Sebastián Rodríguez
from odoo.http import Controller, request, route


class PosStoreController(Controller):
    """
    Controller to handle POS store payment transactions.
    """

    _process_url = "/payment/pos_store/process"

    @route(
        _process_url,
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        website=True,
    )
    def pos_store_process_transaction(self, reference=None, **post):
        """
        Process the offline POS store transaction and redirect to confirmation.
        Confirms the sale order using _process/_apply_updates.

        :param str reference: The transaction reference
        :param dict post: The transaction data
        :return: Redirect to shop confirmation
        """
        if reference:
            # Find the transaction by reference
            tx_sudo = (
                request.env["payment.transaction"]
                .sudo()
                .search([("reference", "=", reference)], limit=1)
            )

            if tx_sudo and tx_sudo.payment_method_code == "pos_store":
                if tx_sudo.state in ("draft", "pending"):
                    tx_sudo._process(
                        "pos_store",
                        {
                            "reference": tx_sudo.reference,
                        },
                    )

                # Ensure we have the sale order in the session for confirmation page
                if tx_sudo.sale_order_ids:
                    sale_order = tx_sudo.sale_order_ids[0]
                    request.session["sale_last_order_id"] = sale_order.id

                # Clean cart session but keep sale_last_order_id
                request.website.sale_reset()

                # Redirect to confirmation
                return request.redirect("/shop/confirmation")

        # Fallback: redirect to shop home
        return request.redirect("/shop")
