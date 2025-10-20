import logging
import requests
import hashlib
from datetime import datetime, timedelta
from odoo import api, models, _
from odoo.exceptions import ValidationError
from typing import Literal

_logger = logging.getLogger(__name__)


class PaymentGateway(models.AbstractModel):
    """
    Gateway handler for payment API integration.

    This model encapsulates all authentication and communication logic with payment API,
    including token management, caching, and automatic re-authentication.
    """

    _name = "payment.gateway"
    _description = "Payment Gateway Handler"

    # Payment API Configuration
    API_BASE_URL = "https://apify.epayco.co"
    TOKEN_EXPIRATION_MINUTES = 20
    TOKEN_SAFETY_MARGIN_MINUTES = 2  # Refresh token 2 minutes before expiration
    GET_BANK_LIST_ENDPOINT = "payment/pse/banks"

    def _get_credentials(self):
        """
        Get payment gateway credentials from payment provider.

        :return: tuple (username, password)
        :raises GatewayException: if credentials are not configured
        """
        payment_provider = (
            self.env["payment.provider"]
            .sudo()
            .search([("code", "=", "rutavity")], limit=1)
        )
        username = payment_provider.epayco_public_key
        password = payment_provider.epayco_private_key

        if not username or not password:
            raise ValidationError(_("Payment gateway credentials not configured."))

        return username, password

    def _get_stored_token_data(self):
        """
        Retrieve stored token and expiration time from database.

        :return: tuple (token, expiration_datetime) or (None, None) if not found
        """
        IrConfigParam = self.env["ir.config_parameter"].sudo()
        token = IrConfigParam.get_param("payment_rutavity.payment_gateway_token")
        expiration_str = IrConfigParam.get_param(
            "payment_rutavity.payment_gateway_token_expiration"
        )

        if not token or not expiration_str:
            return None, None

        try:
            expiration = datetime.fromisoformat(expiration_str)
            return token, expiration
        except (ValueError, TypeError):
            _logger.warning("Invalid token expiration format in database")
            return None, None

    def _store_token_data(self, token, expiration_datetime):
        """
        Store token and expiration time in database.

        :param token: authentication token from payment gateway
        :param expiration_datetime: datetime when token expires
        """
        IrConfigParam = self.env["ir.config_parameter"].sudo()
        IrConfigParam.set_param("payment_rutavity.payment_gateway_token", token)
        IrConfigParam.set_param(
            "payment_rutavity.payment_gateway_token_expiration",
            expiration_datetime.isoformat(),
        )
        _logger.info(
            "Payment gateway token stored successfully, expires at %s",
            expiration_datetime,
        )

    def _is_token_valid(self, expiration_datetime):
        """
        Check if token is still valid considering safety margin.

        :param expiration_datetime: datetime when token expires
        :return: True if token is valid, False otherwise
        """
        if not expiration_datetime:
            return False

        now = datetime.now()
        safety_expiration = expiration_datetime - timedelta(
            minutes=self.TOKEN_SAFETY_MARGIN_MINUTES
        )

        return now < safety_expiration

    def _authenticate(self):
        """
        Authenticate with payment gateway API using Basic Auth.

        :return: authentication token
        :raises GatewayException: if authentication fails
        """
        username, password = self._get_credentials()
        url = f"{self.API_BASE_URL}/login"

        _logger.info("Authenticating with payment gateway API at %s", url)

        try:
            response = requests.post(
                url,
                auth=(username, password),
                timeout=30,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                response_data = response.json()
                token = response_data.get("token")

                if not token:
                    _logger.error(
                        "Payment gateway API authentication failed", response_data
                    )
                    raise ValidationError("Payment gateway API authentication failed")

                # Calculate expiration time
                expiration = datetime.now() + timedelta(
                    minutes=self.TOKEN_EXPIRATION_MINUTES
                )

                # Store token in database
                self._store_token_data(token, expiration)

                _logger.info("Successfully authenticated with payment gateway API")
                return token

            else:
                error_msg = (
                    _("Payment gateway authentication failed with status %s"),
                    response.status_code,
                )
                try:
                    error_data = response.json()
                    error_msg += _(": %s"), error_data
                except Exception:
                    error_msg += _(": %s"), response.text

                raise ValidationError(error_msg)

        except requests.exceptions.RequestException as e:
            raise ValidationError(
                _("Error connecting to payment gateway API: %s"), str(e)
            )

    def _get_valid_token(self):
        """
        Get a valid authentication token, using cached token if available or authenticating if needed.

        :return: valid authentication token
        """
        # Check if we have a valid stored token
        token, expiration = self._get_stored_token_data()

        if token and self._is_token_valid(expiration):
            _logger.info(
                "Using cached payment gateway token (expires at %s)", expiration
            )
            return token

        # Token is expired or not found, authenticate
        _logger.info("Token expired or not found, authenticating with payment gateway")
        return self._authenticate()

    @api.model
    def validate_transaction_signature(self, signature: str, data: dict):
        """
        Check if the signature key is valid.

        :param signature: signature key
        :param data: data to check
        :return: True if signature is valid, False otherwise
        """
        if not signature or not data:
            return False

        return signature == self.make_transaction_signature(data)

    @api.model
    def make_transaction_signature(self, data: dict):
        """
        Make the signature key of the data.

        :param data: data to make signature key
        :return: signature key
        :raises GatewayException: if credentials are not configured
        """
        payment_provider = (
            self.env["payment.provider"]
            .sudo()
            .search([("code", "=", "rutavity")], limit=1)
        )
        p_key = payment_provider.epayco_p_key
        cust_id = payment_provider.epayco_cust_id

        if not p_key or not cust_id:
            raise ValidationError(_("Payment gateway credentials not configured."))

        x_ref_payco = data.get('x_ref_payco')
        x_transaction_id = data.get('x_transaction_id')
        x_amount = data.get('x_amount')
        x_currency_code = data.get('x_currency_code')
        hash_str_bytes = bytes('%s^%s^%s^%s^%s^%s' % (
            cust_id,
            p_key,
            x_ref_payco,
            x_transaction_id,
            x_amount,
            x_currency_code), 'utf-8')
        hash_object = hashlib.sha256(hash_str_bytes)
        return hash_object.hexdigest()

    @api.model
    def get_auth_token(self):
        """
        Public method to get a valid authentication token.

        This method handles token caching and automatic re-authentication.

        :return: valid authentication token
        :raises GatewayException: if authentication fails
        """
        return self._get_valid_token()

    @api.model
    def make_api_request(self, endpoint, method: Literal["GET", "POST"] = "GET", data=None, headers=None):
        """
        Make an authenticated API request to payment gateway.

        :param endpoint: API endpoint (without base URL)
        :param method: HTTP method (GET, POST)
        :param data: request payload (dict)
        :param headers: additional headers (dict)
        :return: response JSON data
        :raises GatewayException: if request fails
        """
        token = self._get_valid_token()
        url = f'{self.API_BASE_URL}/{endpoint.lstrip("/")}'

        # Prepare headers
        request_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if headers:
            request_headers.update(headers)

        _logger.info("Making %s request to payment gateway: %s", method, url)

        try:
            response = requests.request(
                method=method, url=url, json=data, headers=request_headers, timeout=30
            )

            if response.status_code in (200, 201):
                return response.json()
            else:
                error_msg = (
                    _("Payment gateway API request failed with status %s"),
                    response.status_code,
                )
                try:
                    error_data = response.json()
                    error_msg += _(": %s"), error_data
                except Exception:
                    error_msg += _(": %s"), response.text

                raise ValidationError(error_msg)

        except requests.exceptions.RequestException as e:
            raise ValidationError(
                _("Error connecting to payment gateway API: %s"), str(e)
            )

    @api.model
    def clear_token_cache(self):
        """
        Clear stored token from cache.

        Useful for testing or forcing re-authentication.
        """
        IrConfigParam = self.env["ir.config_parameter"].sudo()
        IrConfigParam.set_param("payment_rutavity.payment_gateway_token", False)
        IrConfigParam.set_param(
            "payment_rutavity.payment_gateway_token_expiration", False
        )
        _logger.info("Payment gateway token cache cleared")

    @api.model
    def get_bank_list(self):
        """
        Get the list of available banks.
        """
        return self.make_api_request(endpoint=self.GET_BANK_LIST_ENDPOINT, method="GET")
