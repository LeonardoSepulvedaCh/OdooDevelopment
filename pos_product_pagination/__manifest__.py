{
    'name': 'POS - Paginación de Productos',
    'version': '1.0.0',
    'category': 'Rutavity/Point of Sale',
    'summary': 'Agrega paginación configurable de productos en el POS con mejoras visuales',
    'description': """
        Este módulo agrega paginación en la pantalla principal del POS:
        - Número de productos por página configurable (por defecto 20)
        - Ordena los productos por los más vendidos
        - La búsqueda funciona en todos los productos
        - Controles de navegación visualmente atractivos fijos en la parte inferior
        - Mejoras en las tarjetas de productos:
          * Nombres truncados con puntos suspensivos (ellipsis)
          * Muestra el precio del producto con impuestos incluidos
          * Respeta posición fiscal y lista de precios
          * Mejor uso del espacio disponible
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_product_pagination/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}
