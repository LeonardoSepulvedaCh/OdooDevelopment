{
    'name': 'Contactos Adicionales',
    'version': '19.0.0.0.0',
    'category': 'Milan/Contactos',
    'summary': 'Añade personas de contacto adicionales a los contactos',
    'description': """
        Este módulo permite añadir personas de contacto adicionales a los contactos.
    """,
    'author': '@LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/contact_persons_views.xml',
        'views/res_partner_views.xml',
        'views/menu_contact_persons.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}