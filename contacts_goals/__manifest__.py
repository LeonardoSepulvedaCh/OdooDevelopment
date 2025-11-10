{
    'name': 'Metas de Clientes',
    'version': '1.0.0',
    'category': 'Rutavity/Sales',
    'summary': 'Gestión de metas comerciales por cliente',
    'description': """
        Módulo para gestionar metas comerciales de clientes
        =====================================================
        
        Funcionalidades:
        ----------------
        * Asignación de metas comerciales a clientes
        * Un cliente solo puede tener una meta activa
        * Múltiples líneas de objetivos por meta
        * Configuración de salario mínimo como parámetro base
        * Metas expresadas en múltiplos de salario mínimo
        * Seguimiento de cumplimiento en tiempo real
        * Reportes y gráficos de cumplimiento por cliente
        * Filtros por periodo y estado de cumplimiento
        * Grupos de seguridad personalizados:
          - Usuario: Solo lectura
          - Gestor: Crear y modificar metas
          - Administrador: Acceso total incluyendo eliminación
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'license': 'OPL-1',
    'depends': ['sale', 'contacts', 'mail'],
    'data': [
        'data/ir_config_parameter.xml',
        'security/contacts_goals_security.xml',
        'security/ir.model.access.csv',
        'views/customer_goal_views.xml',
        'views/res_partner_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

