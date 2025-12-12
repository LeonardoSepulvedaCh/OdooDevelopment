{
    'name': 'POS - Ordenes del ecommerce',
    'version': '1.0.0',
    'category': 'Rutavity/Point of Sale',
    'summary': 'Corrige el comportamiento del POS al cargar órdenes de venta desde el backend',
    'description': """
        
        Este módulo corrige el comportamiento del POS cuando se carga una orden de venta 
        desde el backend para procesar el pago.
        
        Problema corregido:
        - Antes: Los productos de la orden de venta se agregaban a la orden activa en el POS.
        - Ahora: Se crea una nueva orden independiente, evitando que los productos se mezclen.
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': ['pos_sale', 'pos_cashiers_salespeople'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_sale_order_ecommerce/static/src/app/services/pos_store.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

