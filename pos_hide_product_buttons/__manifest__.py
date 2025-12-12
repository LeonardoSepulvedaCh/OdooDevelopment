{
    'name': 'POS - No editar y crear productos',
    'version': '1.0.0',
    'category': 'Rutavity/Point of Sale',
    'summary': 'Oculta los botones de crear y editar productos en el POS',
    'description': """
        Este módulo oculta los siguientes botones en el POS:
        - Botón de editar producto en el popup de información del producto
        - Botón de crear producto en el menú del navbar
        - Botón de crear producto manualmente en la pantalla de productos
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_hide_product_buttons/static/src/js/**/*.js',
            'pos_hide_product_buttons/static/src/xml/**/*.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

