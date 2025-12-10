{
    'name': 'Registro de Contactos mediante QR',
    'version': '1.0.0',
    'category': 'Rutavity/Contacts',
    'summary': 'Permite registrar contactos escaneando un código QR',
    'description': """
        Módulo que permite generar un código QR que al escanearlo
        lleva a una página web pública donde se puede registrar un nuevo contacto
        con campos específicos incluyendo información fiscal colombiana.
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': [
        'base',
        'contacts',
        'l10n_co',
        'l10n_co_magnetic_media',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/contact_registration_views.xml',
        'views/registration_form_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'contact_registration_qr/static/src/css/registration_form.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

