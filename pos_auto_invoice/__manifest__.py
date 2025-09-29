{
    'name': 'POS - Facturación Automática por Venta',
    'version': '19.1.0.0.0',
    'category': 'Milan/POS',
    'summary': 'Facturación Automática por Venta',
    'description': 'Agregar una opción en la configuración del POS para que se la opcion de facturar, siempre este activada.',
    'author': '@LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_auto_invoice/static/src/screens/payment_screen/payment_screen.js',
            'pos_auto_invoice/static/src/screens/payment_screen/payment_screen.scss',
        ],
    },
}