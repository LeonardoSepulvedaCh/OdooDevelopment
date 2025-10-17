{
    'name': 'Contactos - Nombres y Apellidos',
    'version': '1.0.0',
    'category': 'Rutavity/Contacts',
    'summary': 'Separa el nombre completo en primer nombre, segundo nombre, primer apellido y segundo apellido',
    'description': """
        Este módulo extiende el modelo de contactos (res.partner) para separar 
        el nombre completo en:
        - Primer Nombre
        - Segundo Nombre
        - Primer Apellido
        - Segundo Apellido
        
        El campo 'name' nativo de Odoo se convierte en un campo calculado que 
        concatena automáticamente estos campos.
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['contacts', 'account'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

