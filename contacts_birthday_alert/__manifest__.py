{
    'name': 'Contactos - Alerta de Cumpleaños',
    'version': '1.0.0',
    'category': 'Milan/Contactos',
    'summary': 'Modulo para gestionar el alerta de cumpleaños de los contactos',
    'description': """
        Este módulo permite añadir:
        - Fecha de nacimiento en los contactos
        - Notificaciones de cumpleaños
        - Campo para codigo de contacto CNL
    """,
    'author': '@LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['base', 'contacts', 'mail', 'bus', 'stock', 'hr'],
    'data': [
        'data/ir_config_parameter.xml',
        'data/ir_cron_data.xml',
        'views/res_partner_views.xml',
        'views/contacts_filter_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
