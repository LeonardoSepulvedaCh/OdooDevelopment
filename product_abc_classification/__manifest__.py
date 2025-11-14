{
    'name': 'Inventario - Clasificación ABC de Productos',
    'version': '1.0.0',
    'category': 'Rutavity/Inventory',
    'summary': 'Clasificación automática ABC de productos basada en valor de ventas facturadas',
    'description': '''
        
        Este módulo añade funcionalidades para la clasificación ABC de productos
        basándose en el valor de ventas facturadas, con cálculo optimizado para grandes volúmenes utilizando pandas y numpy.
        
        **Clasificación ABC en 5 Niveles:**
          - Clasificación automática en 5 categorías (AAA, AA, A, B, C)
          - Basada en valor de ventas facturadas de los últimos 12 meses
          - Considera notas de crédito y devoluciones
          - Cálculo optimizado con pandas/numpy desde el inicio para +10,000 productos
          - ABC Global (todas las bodegas) y ABC por Bodega individual
          - Actualización masiva de productos sin ventas en una sola operación
        
        **ABC Global y por Bodega:**
          - ABC Global: Clasificación basada en ventas totales de todas las bodegas
          - ABC por Bodega: Clasificación individual para cada almacén/bodega
          - Permite identificar productos críticos por ubicación
          - Vista detallada de clasificación por bodega en el producto
        
        **Configuración Personalizable:**
          - Umbrales de clasificación configurables por nivel
          - AAA: 0% → 51.2% del valor total (productos críticos)
          - AA:  51.2% → 64% del valor total
          - A:   64% → 80% del valor total
          - B:   80% → 95% del valor total
          - C:   95% → 100% del valor total + productos sin ventas
          - Período de análisis ajustable (por defecto 12 meses)
          - Opción de incluir/excluir productos sin ventas
        
        **Automatización y Programación:**
          - Cron job automático diario configurable
          - Cálculo manual bajo demanda desde la configuración
          - Actualización automática de estadísticas de rendimiento
          - Notificaciones de finalización con resumen de clasificación
        
        **Cálculo de Ventas:**
          - Solo facturas de cliente confirmadas (out_invoice)
          - Resta automática de notas de crédito (out_refund)
          - Considera devoluciones en el cálculo neto
          - Filtrado por productos almacenables (type='consu', is_storable=True)
          - Cálculo por SKU/plantilla de producto
          - Uso de pandas desde el inicio (sin loops FOR) para máximo rendimiento
        
        **Historial y Trazabilidad:**
          - ABC guardado en líneas de factura al momento de validar
          - Trazabilidad del ABC que tenía el producto al momento de venta
          - Histórico eficiente sin crear tablas adicionales
          - Filtros por producto, clasificación, bodega y fecha
          - Reducción significativa de registros en base de datos
        
    ''',
    'author': 'Kevin Prada',
    'depends': ['product', 'stock', 'account', 'sale'],
    'external_dependencies': {
        'python': ['pandas', 'numpy'],
    },
    'data': [
        'security/abc_classification_security.xml',
        'security/ir.model.access.csv',
        'data/abc_classification_config_data.xml',
        'data/ir_cron_data.xml',
        'views/abc_classification_config_views.xml',
        'views/product_abc_warehouse_views.xml',
        'views/account_move_line_views.xml',
        'views/account_move_views.xml',
        'views/product_template_views.xml',
        'views/abc_classification_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

