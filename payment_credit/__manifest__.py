{
    'name': 'Rutavity - Payment with Credit',
    'version': '1.0.0',
    'category': 'Rutavity/Payment',
    'sequence': 350,
    'summary': """Enable the "pay with credit" feature""",
    'depends': ['payment_rutavity', 'account'],
    'author': 'Sebastián Rodríguez',
    'data': [
        # Views.
        'views/payment_rutavity_templates.xml',
        'views/sale_order_views.xml',

        # Record data.
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
    'installable': True,
}
