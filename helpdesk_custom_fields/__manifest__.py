{
    'name': 'Helpdesk - Campos Personalizados',
    'version': '1.0.0',
    'category': 'Rutavity/Helpdesk',
    'summary': 'Campos Personalizados para el módulo de Helpdesk adaptados al flujo de trabajo de Rutavity',
    'description': """Campos Personalizados para el módulo de Helpdesk:
    - Código del cliente (Card_Code)
    - Motivo
    - Tipo de cliente
    """,
    'author': '@LeonardoSepulvedaCh',
    'depends': ['helpdesk', 'contacts_birthday_alert', 'account', 'sale_management'],
    'data': [
        'data/helpdesk_sequences.xml',
        'data/helpdesk_tags.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_team_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'helpdesk_custom_fields/static/src/js/attachment_preview_field.js',
            'helpdesk_custom_fields/static/src/xml/attachment_preview_field.xml',
            'helpdesk_custom_fields/static/src/css/attachment_preview_field.css',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}