{
    'name': 'Ventas - Comisiones por Asesor',
    'version': '1.0.0',
    'category': 'Rutavity/Commission',
    'summary': 'Agrega monto objetivo a los logros de comisiones por categoría',
    'description': """
        Extiende la funcionalidad de logros de comisiones permitiendo definir
        un monto objetivo que debe alcanzarse para obtener el porcentaje de
        comisión establecido por categoría de producto.
    """,
    'author': '@LeonardoSepulvedaCh',
    'website': 'https://github.com/LeonardoSepulvedaCh',
    'depends': [
        'sale_commission',
        'sale_commission_margin',
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'views/commission_plan_achievement_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}

