{
    'name': 'POS - Cierre de caja ciego',
    'version': '19.0.0.0.0',
    'category': 'Milan/POS',
    'summary': 'Cierre de caja ciego',
    'description': """
    Este módulo permite ocultar el resumen de cierre de caja en el POS. Mostrando unicamente el campo para ingresar el monto de cierre de caja.
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': ['point_of_sale'],
    'license': 'OPL-1',
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_blind_cash/static/src/xml/closing_popup.xml',
        ],
    }
}