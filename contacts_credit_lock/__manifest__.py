{
    'name': 'Contactos - Bloqueo por mora',
    'version': '1.0.0',
    'category': 'Rutavity/Contacts',
    'summary': 'Bloquear ventas de clientes que tengan deuda en mora',
    'description': """
    Este módulo permite bloquear las ventas a clientes que tengan deuda en mora.
    
    Características:
    - Calcula automáticamente la deuda en mora (facturas vencidas hace más de 30 días)
    - Bloquea la confirmación de órdenes de venta para clientes con mora
    - Permite bloqueo manual de clientes
    - Muestra alertas visuales en el formulario de venta y contacto
    - Indica el monto exacto de la deuda en mora
    """,
    'author': '@LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['sale', 'contacts', 'account'],
    'data': [
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}