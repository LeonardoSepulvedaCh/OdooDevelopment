{
    'name': 'Contactos - Alerta de Cumpleaños',
    'version': '1.0',
    'category': 'Milan/Contactos',
    'summary': 'Añade contactos adicionales y funcionalidad de cumpleaños',
    'description': """
        Este módulo permite añadir:
        - Contactos adicionales relacionados (solo para información)
        - Fecha de nacimiento en los contactos
        - Notificaciones de cumpleaños
        - Campo para codigo de contacto CNL (Cliente), PNL (Proveedor), E (Empleado)
    """,
    'author': '@LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['base', 'contacts', 'mail', 'bus', 'stock', 'hr'],
    'data': [
        'data/ir_cron_data.xml',
        'views/res_partner_views.xml',
        'views/contacts_filter_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
