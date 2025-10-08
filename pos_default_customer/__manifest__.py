{
    'name': 'POS - Cliente Predeterminado',
    'version': '1.0.0',
    'category': 'Milan/POS',
    'summary': 'Cliente Predeterminado en el POS',
    'description': 'Elegir un cliente que se mostrará por defecto en el POS al seleccionar un cliente',
    'author': '@LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['point_of_sale','pos_partner_visibility'],
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_default_customer/static/src/js/pos_default_customer.js',
        ],
    },
}