{
    'name': 'Metas Comerciales',
    'version': '19.0.1.0.0',
    'category': 'Rutavity/Sales',
    'summary': 'Asignación de metas comerciales mensuales a vendedores',
    'description': """
        Módulo para gestionar metas comerciales:
        - Asignación de metas mensuales a vendedores
        - Asignación masiva de metas
        - Seguimiento de cumplimiento basado en facturación
        - Reportes de desempeño por vendedor
        - Grupos de seguridad personalizados:
          · Usuario: Solo lectura
          · Gestor: Crear y modificar metas
          · Administrador: Acceso total incluyendo eliminación
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': [
        'base',
        'mail',
        'product',
        'sale',
        'sales_team',
        'account',
    ],
    'data': [
        'security/sales_targets_security.xml',
        'security/ir.model.access.csv',
        'views/sales_target_actions.xml',
        'views/product_category_views.xml',
        'views/res_users_views.xml',
        'views/sales_target_list_form_views.xml',
        'views/sales_target_line_views.xml',
        'views/sales_target_kanban_views.xml',
        'views/sales_target_report_views.xml',
        'wizard/sales_target_mass_assign_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

