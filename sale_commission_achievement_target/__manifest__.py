{
    "name": "Ventas - Comisiones por Asesor",
    "version": "1.0.0",
    "category": "Rutavity/Commission",
    "summary": "Sistema de comisiones por recaudo con metas y categorías jerárquicas",
    "description": """
        Extiende la funcionalidad de comisiones de ventas con:
        - Comisiones basadas en recaudos (pagos reconciliados) en lugar de ventas/facturas
        - Comisión base del 0.7% sobre pagos a tiempo (antes de vencimiento + 7 días gabela)
        - Comisiones adicionales por cumplimiento de metas por categoría de producto
        - Cálculo jerárquico de categorías de eCommerce (incluye categorías padre e hijas automáticamente)
        - Validación de categoría Promociones obligatoria
        - Prorrateo de pagos parciales entre productos por categoría
        - Reporte completo de comisiones por recaudo
    """,
    "author": "@LeonardoSepulvedaCh",
    "website": "https://github.com/LeonardoSepulvedaCh",
    "depends": [
        "sale_commission",
        "sale_commission_margin",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "views/commission_plan_achievement_views.xml",
        "report/commission_collection_report_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "OEEL-1",
}
