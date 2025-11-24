{
    'name': 'POS - Imágenes del Sitio Web de Productos',
    'version': '1.1.0',
    'category': 'Rutavity/POS',
    'summary': 'Muestra las imágenes del sitio web asociadas a productos en el POS',
    'description': """
        Este módulo extiende el punto de venta de Odoo para mostrar la imagen principal
        y las imágenes adicionales del sitio web (product.image) cuando se consultan los
        detalles de un producto en el POS. Incluye scrollbar personalizado más delgado.
        
        Características:
        - Muestra la imagen principal del producto
        - Muestra todas las imágenes adicionales del sitio web
        - Galería con navegación y miniaturas
        - Scrollbar personalizado y delgado
        - Fallback de descripción: usa description_ecommerce si no hay public_description
    """,
    'author': '@LeonardoSepulvedaCh',
    'depends': [
        'point_of_sale',
        'website_sale',
    ],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_product_website_images/static/src/app/models/product_template.js',
            'pos_product_website_images/static/src/app/popups/product_info_popup/product_info_popup.js',
            'pos_product_website_images/static/src/app/popups/product_info_popup/product_info_popup.xml',
            'pos_product_website_images/static/src/scss/product_info_popup.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}

