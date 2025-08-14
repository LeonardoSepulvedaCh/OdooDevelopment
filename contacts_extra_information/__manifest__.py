{
    'name': 'Información Extra - Contactos',
    'version': '18.0.0.0.1',
    'category': 'Milan/Contactos',
    'summary': 'Añade contactos adicionales y funcionalidad de cumpleaños',
    'description': """
        Este módulo permite añadir:
        - Contactos adicionales relacionados (solo para información)
        - Fecha de nacimiento en los contactos
        - Notificaciones de cumpleaños
    """,
    'author': '@LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['base', 'contacts', 'mail', 'bus'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/res_partner_views.xml',
        'views/related_contact_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
