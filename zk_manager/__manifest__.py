{
    'name': 'ZK Manager',
    'version': '1.0.0',
    'category': 'Rutavity/HR',
    'summary': 'Gestión de dispositivos de huella dactilar ZKTECO',
    'description': '''
        Módulo para gestionar dispositivos de huella dactilar ZKTECO.
    ''',
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['base', 'hr'],
    'data': [
        'data/zk_config.xml',
        'security/zk_manager_security.xml',
        'security/ir.model.access.csv',
        'wizards/zk_attendance_wizard_views.xml',
        'views/zk_device_views.xml',
        'views/zk_user_views.xml',
        'views/zk_attendance_views.xml',
        'views/hr_employee_views.xml',
        'views/zk_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'zk_manager/static/src/css/zk_user_kanban.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}