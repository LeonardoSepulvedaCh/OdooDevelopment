from . import models
from . import controllers


def uninstall_hook(env):
    """
    Uninstallation hook to remove POS store payment method from Rutavity provider.
    
    :param env: Odoo environment
    :return: None
    """
    # Remove POS store payment method from Rutavity provider
    rutavity_provider = env.ref('payment_rutavity.payment_provider_rutavity', raise_if_not_found=False)
    pos_store_method = env.ref('payment_pos_store.payment_method_pos_store', raise_if_not_found=False)
    
    if rutavity_provider and pos_store_method:
        rutavity_provider.write({
            'payment_method_ids': [(3, pos_store_method.id)]
        })

