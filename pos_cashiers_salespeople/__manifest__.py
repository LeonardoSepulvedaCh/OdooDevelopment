{
    'name': 'POS - Cajeros y Vendedores',
    'version': '1.0.2',
    'category': 'Rutavity/Point of Sale',
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
            # Servicios primero (para evitar problemas de dependencias)
            'pos_cashiers_salespeople/static/src/app/services/user_role_service.js',
            'pos_cashiers_salespeople/static/src/app/services/pos_store.js',
            # Modelos
            'pos_cashiers_salespeople/static/src/app/models/pos_order.js',
            # Pantallas y componentes
            'pos_cashiers_salespeople/static/src/app/screens/product_screen/product_screen.js',
            'pos_cashiers_salespeople/static/src/app/screens/product_screen/product_screen.xml',
            'pos_cashiers_salespeople/static/src/app/components/navbar/navbar.js',
            'pos_cashiers_salespeople/static/src/app/components/navbar/navbar.xml',
            'pos_cashiers_salespeople/static/src/app/components/navbar/navbar.scss',
            'pos_cashiers_salespeople/static/src/app/screens/pending_orders/pending_orders.js',
            'pos_cashiers_salespeople/static/src/app/screens/pending_orders/pending_orders.xml',
            'pos_cashiers_salespeople/static/src/app/screens/pending_orders/pending_orders.scss',
            # Control buttons (dependen del servicio)
            'pos_cashiers_salespeople/static/src/app/screens/product_screen/control_buttons/control_buttons.js',
            'pos_cashiers_salespeople/static/src/app/screens/product_screen/control_buttons/control_buttons.xml',
            'pos_cashiers_salespeople/static/src/app/screens/product_screen/control_buttons/select_salesperson_button/select_salesperson_button.js',
            'pos_cashiers_salespeople/static/src/app/screens/product_screen/control_buttons/select_salesperson_button/select_salesperson_button.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
