{
    'name': 'Inventario - Clasificación por Rotación de Productos',
    'version': '1.0.0',
    'category': 'Rutavity/Inventory',
    'summary': 'Clasificación automática de productos por rotación de inventario basada en duración de stock',
    'description': '''
        
        Este módulo añade capacidades avanzadas de clasificación por rotación de inventario
        basándose en la duración estimada del stock actual vs consumo mensual promedio.
        
        **Clasificación por Rotación en 6 Niveles:**
          - Clasificación automática en 6 categorías según duración del stock
          - Rotación Global (todas las bodegas) y Rotación por Bodega individual
          - ALTA: ≤ 7 meses de stock (rotación rápida)
          - BAJA: > 7 y ≤ 24 meses de stock
          - HUESO: > 24 y < 60 meses de stock
          - FEMUR: ≥ 60 meses de stock (rotación muy lenta)
          - AGOTADO: Sin stock disponible
          - INFINITO: Tiene stock pero sin consumo (sin ventas en período)
          - Basada en movimientos reales de stock de ventas de los últimos 12 meses
          - Considera devoluciones de clientes
          - Cálculo optimizado con pandas/numpy para +10,000 productos
          - Rotación guardada en líneas de factura al momento de validar
        
        **Cálculo de Rotación:**
          - Fórmula: Meses de Stock = Stock Actual / Consumo Mensual Promedio
          - Stock actual: qty_available (cantidad en mano)
          - Consumo mensual: ventas reales (stock.move) / número de meses del período
          - Usa movimientos de stock con sale_line_id para capturar ventas reales
          - Excluye ajustes de inventario, consumos internos y transferencias
          - Suma global de todos los almacenes de la empresa
          - Filtrado por productos almacenables (type='consu', is_storable=True)
        
        **Configuración Personalizable:**
          - Umbrales de clasificación configurables por nivel
          - Período de análisis ajustable (por defecto 12 meses)
          - Opciones de inclusión de productos sin stock o sin ventas
          - Configuración de rangos de meses para cada clasificación
        
        **Automatización y Programación:**
          - Cron job automático diario configurable
          - Cálculo manual bajo demanda desde la configuración
          - Actualización automática de estadísticas de rendimiento
          - Notificaciones de finalización con resumen de clasificación
        
        **Cálculo de Consumo Real:**
          - Usa movimientos de stock (stock.move) con sale_line_id
          - Solo ventas confirmadas (state='done') vinculadas a órdenes de venta
          - Distingue automáticamente salidas (ventas) vs entradas (devoluciones)
          - Acceso directo a la bodega de origen sin joins complejos
          - Más preciso que facturas: captura el movimiento físico real
          - Cálculo por SKU/plantilla de producto
          - Promedio mensual basado en período configurado
        
        **Historial y Trazabilidad:**
          - Rotación guardada en líneas de factura al validar (account.move.line)
          - Historial por bodega y global
          - Fecha y hora de cada cálculo
          - Stock actual y consumo mensual por producto y bodega
          - Meses de duración estimada de stock
          - Selector de bodega en formulario de producto para ver rotación específica
          - **Vista Unificada:** Se integra con el módulo ABC para mostrar ambas clasificaciones juntas
          - Historial combinado permite análisis cruzado de ABC y Rotación por producto

    ''',
    'author': 'Kevin Prada',
    'depends': ['product', 'stock', 'account', 'sale', 'sale_stock', 'product_abc_classification'],
    'external_dependencies': {
        'python': ['pandas', 'numpy'],
    },
    'data': [
        'security/rotation_classification_security.xml',
        'security/ir.model.access.csv',
        'data/rotation_classification_config_data.xml',
        'data/ir_cron_data.xml',
        'views/rotation_classification_config_views.xml',
        'views/account_move_views.xml',
        'views/account_move_line_views.xml',
        'views/product_template_views.xml',
        'views/rotation_classification_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

