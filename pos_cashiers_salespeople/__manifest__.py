{
    'name': 'POS - Cajeros y Vendedores',
    'version': '18.5.0.0.1',
    'category': 'Milan/POS',
    'summary': 'Configuración de cajeros y vendedores por POS',
    'description': '''
        Este módulo extiende la configuración del POS para permitir definir:
        - Usuarios que pueden actuar como cajeros
        - Usuarios que pueden actuar como vendedores
        
        Características:
        - Campos Many2many para seleccionar cajeros y vendedores por POS
        - Integración con la vista de configuración del POS
        - Validaciones para asegurar que los usuarios seleccionados estén activos
    ''',
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_cashiers_salespeople/static/src/app/screens/product_screen/product_screen.js',
            'pos_cashiers_salespeople/static/src/app/screens/product_screen/product_screen.xml',
            'pos_cashiers_salespeople/static/src/app/components/navbar/navbar.js',
            'pos_cashiers_salespeople/static/src/app/components/navbar/navbar.xml',
            'pos_cashiers_salespeople/static/src/app/screens/pending_orders/pending_orders.js',
            'pos_cashiers_salespeople/static/src/app/screens/pending_orders/pending_orders.xml',
            'pos_cashiers_salespeople/static/src/app/screens/pending_orders/pending_orders.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
