{
    'name': 'Contactos - Bloqueo por cartera',
    'version': '1.0.0',
    'category': 'Rutavity/Contacts',
    'summary': 'Bloquear ventas de clientes que tengan deuda en cartera',
    'description': 'Bloquear ventas a clientes mediante el metodo de pago credito que tengan deuda en cartera',
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': ['payment_credit', 'contacts', 'website_sale'],
    'license': 'OPL-1',
    'data': [
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/website_shop_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'contacts_credit_lock/static/src/scss/contacts_credit_lock.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

