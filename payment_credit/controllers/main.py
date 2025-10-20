# Author: Sebastián Rodríguez
from odoo.http import Controller, request, route


class CreditController(Controller):
    """
    Controller to handle credit payment transactions.
    """
    _process_url = '/payment/credit/process'

    @route(_process_url, type='http', auth='public', methods=['POST'], csrf=False)
    def credit_process_transaction(self, **post):
        """
        Process the offline credit transaction and redirect to the payment status.
        
        :param dict post: The transaction data
        :return: Redirect to shop confirmation
        """
        # Process the transaction as provider 'rutavity' with credit method
        request.env['payment.transaction'].sudo()._process('rutavity', post)
        return request.redirect('/shop/confirmation')
