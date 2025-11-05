{
    'name': 'Helpdesk - Pacto Reposición',
    'version': '1.0.0',
    'category': 'Rutavity/Helpdesk',
    'summary': 'Módulo para gestionar el Pacto Reposición un ticket de Garantía',
    'description': 'Módulo para gestionar el Pacto Reposición un ticket de Garantía',
    'author': '@LeonardoSepulvedaCh',
    'depends': ['helpdesk', 'helpdesk_custom_fields', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'report/helpdesk_pacto_carta_report.xml',
        'report/helpdesk_pacto_carta_report_action.xml',
        'views/helpdesk_pacto_wizard_views.xml',
        'views/helpdesk_pacto_venta_wizard_views.xml',
        'views/helpdesk_ticket_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'helpdesk_pacto_reposicion/static/src/scss/pacto_carta_report.scss',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}