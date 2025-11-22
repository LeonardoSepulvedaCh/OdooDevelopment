{
    'name': 'Cartera - Prórrogas en fecha de vencimiento',
    'version': '1.0.0',
    'category': 'Rutavity/Accounting',
    'summary': 'Gestión de prórrogas en fechas de vencimiento de facturas',
    'description': """
        Módulo para gestionar prórrogas en la fecha de vencimiento de facturas de venta.
        
        Características:
        - Añade un campo de fecha de vencimiento extendida
        - No altera la fecha de vencimiento original
        - No afecta los asientos contables
        - Permite validar vencimientos con la fecha extendida cuando esté definida
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['account', 'mail', 'approvals', 'portal_invoice_partner_grouping'],
    'data': [
        'security/account_invoice_extension_security.xml',
        'data/sequence_data.xml',
        'data/approval_category_data.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_extension_views.xml',
        'views/account_move_views.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

