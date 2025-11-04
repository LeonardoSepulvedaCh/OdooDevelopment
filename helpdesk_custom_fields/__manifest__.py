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
    'depends': ['helpdesk', 'website_helpdesk', 'contacts_birthday_alert', 'account', 'sale_management', 'stock', 'mail'],
    'data': [
        'data/ir_config_parameter.xml',
        'data/helpdesk_sequences.xml',
        'data/helpdesk_tags.xml',
        'data/res_partner_category.xml',
        'report/helpdesk_warranty_report.xml',
        'report/helpdesk_warranty_report_action.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_team_views.xml',
        'views/res_users_views.xml',
        'views/helpdesk_website_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'helpdesk_custom_fields/static/src/js/attachment_preview_field.js',
            'helpdesk_custom_fields/static/src/xml/attachment_preview_field.xml',
            'helpdesk_custom_fields/static/src/scss/attachment_preview_field.scss',
        ],
        'web.assets_frontend': [
            'helpdesk_custom_fields/static/src/js/website_helpdesk_warranty.js',
        ],
        'web.report_assets_common': [
            'helpdesk_custom_fields/static/src/scss/warranty_report.scss',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}