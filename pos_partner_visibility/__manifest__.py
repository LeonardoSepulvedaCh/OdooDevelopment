{
    'name': 'Contactos - Cliente POS',
    'version': '1.0',
    'category': 'Rutavity/Point of Sale',
    'summary': 'Campo adicional para seleccionar determinar si el cliente es visible en el POS',
    'description': 'Campo adicional para seleccionar determinar si el cliente es visible en el POS',
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': ['point_of_sale', 'sale', 'contacts'],
    'data': [
        'views/res_partner_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_partner_visibility/static/src/js/pos_partner_filter.js',
        ]
    },
        'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False
}