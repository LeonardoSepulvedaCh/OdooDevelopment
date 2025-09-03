{
    'name': 'POS - Recibo Personalizado',
    'version': '18.5.0.0.1',
    'category': 'Milan/POS',
    'summary': 'Personalización completa del recibo de venta del POS',
    'description': '''
        Módulo para personalizar completamente el recibo de venta del Punto de Venta (POS) de Odoo.
        
        Características:
        - Encabezado personalizado con diseño atractivo
        - Pie de página con información de contacto y redes sociales
        - Estilos CSS personalizados para mejor presentación
        - Información adicional como horarios de atención
        - Mensajes promocionales y de fidelización
        - Soporte para temas claros y oscuros
        - Optimizado para impresión
        
        Permite modificar fácilmente todos los elementos del recibo para adaptarlo
        a las necesidades específicas de cada negocio.
    ''',
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_views.xml',
        'data/pos_config_data.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_custom_receipt/static/src/app/screens/receipt_screen/receipt/order_receipt.js',
            'pos_custom_receipt/static/src/app/screens/receipt_screen/receipt/order_receipt.xml',
            'pos_custom_receipt/static/src/app/screens/receipt_screen/receipt/order_receipt.scss',
            'pos_custom_receipt/static/src/app/screens/receipt_screen/receipt/receipt_header/receipt_header.js',
            'pos_custom_receipt/static/src/app/screens/receipt_screen/receipt/receipt_header/receipt_header.xml',
            'pos_custom_receipt/static/src/app/screens/receipt_screen/receipt/receipt_header/receipt_header.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'OPL-1',
}