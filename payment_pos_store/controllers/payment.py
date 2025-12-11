# Author: Sebastián Rodríguez
from odoo.addons.website_sale.controllers import payment as website_payment_portal
from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request


class PaymentPortalPosStore(website_payment_portal.PaymentPortal):
    """
    Extension of PaymentPortal to add POS store validation and order data handling.
    """

    @http.route(
        "/payment/pos_store/get_salespeople",
        type="jsonrpc",
        auth="user",
        website=True,
    )
    def pos_store_get_salespeople(self, partner_id: int):
        """
        Get available salespeople for a POS customer.

        :param int partner_id: The partner id
        :return: List of available salespeople
        :rtype: list of dict
        """
        sale_order = self._get_current_sale_order()
        if partner_id != sale_order.partner_id.id:
            raise ValidationError(_("Partner does not match the sale order partner"))
        
        return request.env["res.partner"].sudo().get_available_salespeople(partner_id)

    @http.route(
        "/payment/pos_store/save_order_data",
        type="jsonrpc",
        auth="user",
        website=True,
    )
    def pos_store_save_order_data(self, salesperson_id=None, comments=None):
        """
        Save POS store order data (salesperson, team, POS configs, and comments) to the current sale order.

        :param int salesperson_id: The selected salesperson user id
        :param str comments: The comments to save (max 255 characters)
        :return: Success status
        :rtype: bool
        """
        sale_order = self._get_current_sale_order()
        partner = sale_order.partner_id

        values_to_write = {}
        
        # Process salesperson
        if salesperson_id:
            self._validate_and_add_salesperson(
                values_to_write, salesperson_id, partner
            )

        # Add POS configs
        self._add_pos_configs(values_to_write, partner)

        # Add sales team
        self._add_sales_team(values_to_write)

        # Add comments
        if comments:
            self._add_normalized_comments(values_to_write, comments)

        # Save to order
        if values_to_write:
            sale_order.write(values_to_write)

        return True

    def _get_current_sale_order(self):
        """
        Get the current sale order from session.

        :return: Sale order record
        :rtype: recordset
        :raise ValidationError: If sale order not found
        """
        sale_order_id = request.session.get("sale_order_id")
        if not sale_order_id:
            raise ValidationError(_("No sale order found in session"))

        sale_order = request.env["sale.order"].sudo().browse(sale_order_id)
        if not sale_order.exists():
            raise ValidationError(_("Sale order not found"))

        return sale_order

    def _validate_and_add_salesperson(self, values_dict, salesperson_id, partner):
        """
        Validate salesperson and add to values dict.

        :param dict values_dict: Dictionary to add values to
        :param int salesperson_id: Salesperson user id
        :param partner: Partner record
        :raise ValidationError: If salesperson invalid
        """
        salesperson = request.env["res.users"].sudo().browse(salesperson_id)
        if not salesperson.exists():
            raise ValidationError(_("Salesperson not found"))

        if not (partner.pos_customer and partner.pos_config_ids):
            return

        allowed_salesperson_ids = partner.pos_config_ids.mapped(
            "salesperson_user_ids"
        ).ids
        
        if salesperson_id not in allowed_salesperson_ids:
            raise ValidationError(
                _("Selected salesperson is not available for this customer")
            )

        values_dict["user_id"] = salesperson_id

    def _add_pos_configs(self, values_dict, partner):
        """
        Add POS configurations to values dict.

        :param dict values_dict: Dictionary to add values to
        :param partner: Partner record
        """
        if partner.pos_customer and partner.pos_config_ids:
            values_dict["pos_config_ids"] = [(6, 0, partner.pos_config_ids.ids)]

    def _add_sales_team(self, values_dict):
        """
        Add POS sales team to values dict.

        :param dict values_dict: Dictionary to add values to
        """
        pos_sales_team = request.env.ref(
            "sales_team.pos_sales_team", raise_if_not_found=False
        )
        values_dict["team_id"] = pos_sales_team.id

    def _add_normalized_comments(self, values_dict, comments):
        """
        Normalize and add comments to values dict.

        :param dict values_dict: Dictionary to add values to
        :param str comments: Raw comments
        """
        # Replace line breaks with spaces and normalize whitespace
        normalized_comments = " ".join(comments.split())
        # Trim and limit to 255 characters (client_order_ref is Char field)
        normalized_comments = normalized_comments[:255].strip()
        
        if normalized_comments:
            values_dict["client_order_ref"] = normalized_comments

    def _create_transaction(
        self,
        provider_id,
        payment_method_id,
        token_id,
        amount,
        currency_id,
        partner_id,
        flow,
        tokenization_requested,
        landing_route,
        reference_prefix=None,
        is_validation=False,
        custom_create_values=None,
        **kwargs
    ):
        """
        Override of `payment` to add a POS store validation step for Rutavity POS store payments.

        :param int provider_id: The provider of the provider payment method or token, as a
                                `payment.provider` id.
        :param int|None payment_method_id: The payment method, if any, as a `payment.method` id.
        :param int|None token_id: The token, if any, as a `payment.token` id.
        :param float|None amount: The amount to pay, or `None` if in a validation operation.
        :param int|None currency_id: The currency of the amount, as a `res.currency` id, or `None`
                                     if in a validation operation.
        :param int partner_id: The partner making the payment, as a `res.partner` id.
        :param str flow: The online payment flow of the transaction: 'redirect', 'direct' or 'token'.
        :param bool tokenization_requested: Whether the user requested that a token is created.
        :param str landing_route: The route the user is redirected to after the transaction.
        :param str reference_prefix: The custom prefix to compute the full reference.
        :param bool is_validation: Whether the operation is a validation.
        :param dict custom_create_values: Additional create values overwriting the default ones.
        :param dict kwargs: Locally unused data passed to `_is_tokenization_required` and
                            `_compute_reference`.
        :return: The sudoed transaction that was created.
        :rtype: payment.transaction
        """
        provider_sudo = request.env["payment.provider"].sudo().browse(provider_id)
        payment_method_sudo = (
            request.env["payment.method"].sudo().browse(payment_method_id)
        )

        # If payment is with rutavity pos_store, check partner POS configuration
        if provider_sudo.code == "rutavity" and payment_method_sudo.code == "pos_store":
            partner = request.env["res.partner"].sudo().browse(partner_id)

            # Validate partner has pos_customer enabled
            if not partner.pos_customer:
                raise ValidationError(
                    _("POS store payment is only available for POS customers.")
                )

            # Validate partner has at least one POS configuration
            if not partner.pos_config_ids:
                raise ValidationError(
                    _("No POS configuration assigned to this customer.")
                )

        return super()._create_transaction(
            provider_id,
            payment_method_id,
            token_id,
            amount,
            currency_id,
            partner_id,
            flow,
            tokenization_requested,
            landing_route,
            reference_prefix=reference_prefix,
            is_validation=is_validation,
            custom_create_values=custom_create_values,
            **kwargs
        )
