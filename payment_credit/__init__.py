from . import models
from . import controllers


def uninstall_hook(env):
    """
    Uninstallation hook to remove credit payment method from Rutavity provider.
    
    :param env: Odoo environment
    :return: None
    """
    # Remove credit payment method from Rutavity provider
    rutavity_provider = env.ref('payment_rutavity.payment_provider_rutavity', raise_if_not_found=False)
    credit_method = env.ref('payment_credit.payment_method_credit', raise_if_not_found=False)
    
    if rutavity_provider and credit_method:
        rutavity_provider.write({
            'payment_method_ids': [(3, credit_method.id)]
        })
