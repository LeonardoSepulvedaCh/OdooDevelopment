# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import numpy as np
except ImportError:
    _logger.warning("pandas and/or numpy not installed. Rotation classification will not work.")
    pd = None
    np = None


class ProductTemplate(models.Model):
    """
    Extensión del modelo product.template para añadir campos y métodos de
    clasificación por rotación de inventario.
    """
    _inherit = 'product.template'

    # ==================== CAMPOS GLOBALES ====================
    # Campos de clasificación por rotación GLOBAL (todas las bodegas)
    # Computados desde product.rotation.warehouse donde warehouse_id=False
    rotation_classification_global = fields.Selection([
        ('HIGH', 'ALTA'),
        ('LOW', 'BAJA'),
        ('BONE', 'HUESO'),
        ('FEMUR', 'FEMUR'),
        ('DEPLETED', 'AGOTADO'),
        ('INFINITE', 'INFINITO'),
    ], string='Rotación Global', 
       compute='_compute_rotation_global', 
       store=True,
       index=True, 
       readonly=True, 
       copy=False,
       help='Clasificación global considerando todas las bodegas (desde product.rotation.warehouse)')
    
    rotation_months_global = fields.Float(
        string='Duración Global (meses)',
        compute='_compute_rotation_global',
        store=True,
        readonly=True,
        copy=False,
        help='Duración estimada del stock en meses a nivel global'
    )
    
    rotation_stock_qty_global = fields.Float(
        string='Stock Global',
        compute='_compute_rotation_global',
        store=True,
        readonly=True,
        copy=False,
        help='Cantidad total en mano al momento del último cálculo'
    )
    
    rotation_monthly_consumption_global = fields.Float(
        string='Consumo Mensual Global',
        compute='_compute_rotation_global',
        store=True,
        readonly=True,
        copy=False,
        help='Consumo mensual promedio global basado en ventas facturadas (promedio simple de 12 meses)'
    )
    
    rotation_monthly_consumption_top10_global = fields.Float(
        string='Consumo Mensual Top 10 Global',
        compute='_compute_rotation_global',
        store=True,
        readonly=True,
        copy=False,
        help='Consumo mensual promedio de los 10 meses más altos (descartando los 2 meses más bajos)'
    )
    
    # ==================== CAMPOS POR BODEGA ====================
    # Relación One2many con rotación por bodega
    rotation_warehouse_ids = fields.One2many(
        comodel_name='product.rotation.warehouse',
        inverse_name='product_tmpl_id',
        string='Rotación por Bodega',
        help='Clasificaciones de rotación específicas por bodega'
    )
    
    # Selector de bodega para mostrar rotación específica
    rotation_selected_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Bodega Seleccionada',
        help='Seleccione una bodega para ver su rotación específica'
    )
    
    # Campos computados para mostrar rotación de bodega seleccionada
    rotation_selected_warehouse_classification = fields.Selection([
        ('HIGH', 'ALTA'),
        ('LOW', 'BAJA'),
        ('BONE', 'HUESO'),
        ('FEMUR', 'FEMUR'),
        ('DEPLETED', 'AGOTADO'),
        ('INFINITE', 'INFINITO'),
    ], string='Rotación Bodega', compute='_compute_rotation_selected_warehouse', readonly=True,
        help='Rotación de la bodega seleccionada')
    
    rotation_selected_warehouse_months = fields.Float(
        string='Duración Bodega (meses)',
        compute='_compute_rotation_selected_warehouse',
        readonly=True,
        help='Duración en meses para la bodega seleccionada'
    )
    
    # ==================== CAMPOS LEGACY (compatibilidad) ====================
    rotation_classification = fields.Selection([
        ('HIGH', 'High Rotation'),
        ('LOW', 'Low Rotation'),
        ('BONE', 'Bone'),
        ('FEMUR', 'Femur'),
        ('DEPLETED', 'Depleted'),
        ('INFINITE', 'Infinite'),
    ], string='Rotation Classification', index=True, readonly=True, copy=False,
        help='Product classification based on inventory rotation speed')
    
    rotation_months = fields.Float(
        string='Stock Duration (months)',
        readonly=True,
        copy=False,
        help='Estimated months of stock duration: Stock Qty / Monthly Consumption'
    )
    rotation_stock_qty = fields.Float(
        string='Stock Quantity (at calculation)',
        readonly=True,
        copy=False,
        help='Quantity on hand at the time of last rotation calculation'
    )
    rotation_monthly_consumption = fields.Float(
        string='Monthly Consumption',
        readonly=True,
        copy=False,
        help='Average monthly consumption based on invoiced sales'
    )
    rotation_last_calculation = fields.Datetime(
        string='Last Rotation Calculation',
        readonly=True,
        copy=False
    )

    @api.depends('rotation_warehouse_ids.rotation_classification', 
                 'rotation_warehouse_ids.rotation_months',
                 'rotation_warehouse_ids.stock_qty',
                 'rotation_warehouse_ids.monthly_consumption',
                 'rotation_warehouse_ids.monthly_consumption_top10')
    def _compute_rotation_global(self):
        """Calcular campos globales desde product.rotation.warehouse donde warehouse_id=False"""
        for product in self:
            # Buscar registro global (warehouse_id=False)
            rotation_global = self.env['product.rotation.warehouse'].search([
                ('product_tmpl_id', '=', product.id),
                ('warehouse_id', '=', False)
            ], limit=1)
            
            if rotation_global:
                product.rotation_classification_global = rotation_global.rotation_classification
                product.rotation_months_global = rotation_global.rotation_months
                product.rotation_stock_qty_global = rotation_global.stock_qty
                product.rotation_monthly_consumption_global = rotation_global.monthly_consumption
                product.rotation_monthly_consumption_top10_global = rotation_global.monthly_consumption_top10
            else:
                product.rotation_classification_global = False
                product.rotation_months_global = 0.0
                product.rotation_stock_qty_global = 0.0
                product.rotation_monthly_consumption_global = 0.0
                product.rotation_monthly_consumption_top10_global = 0.0

    @api.depends('rotation_selected_warehouse_id', 'rotation_warehouse_ids')
    def _compute_rotation_selected_warehouse(self):
        """Calcular rotación para la bodega seleccionada"""
        for product in self:
            if product.rotation_selected_warehouse_id:
                rotation_wh = self.env['product.rotation.warehouse'].search([
                    ('product_tmpl_id', '=', product.id),
                    ('warehouse_id', '=', product.rotation_selected_warehouse_id.id)
                ], limit=1)
                
                if rotation_wh:
                    product.rotation_selected_warehouse_classification = rotation_wh.rotation_classification
                    product.rotation_selected_warehouse_months = rotation_wh.rotation_months
                else:
                    product.rotation_selected_warehouse_classification = False
                    product.rotation_selected_warehouse_months = 0.0
            else:
                product.rotation_selected_warehouse_classification = False
                product.rotation_selected_warehouse_months = 0.0

    def action_calculate_rotation_classification(self):
        """
        Método principal para calcular la clasificación por rotación:
        - Global (todas las bodegas)
        - Por cada bodega individual
        """
        if pd is None or np is None:
            raise ValueError(_('pandas and numpy libraries are required for rotation calculation'))

        start_time = datetime.now()
        _logger.info("=== INICIO: Cálculo de Clasificación por Rotación ===")

        # Obtener configuración
        config = self.env['rotation.classification.config'].search([], limit=1)
        if not config:
            config = self.env['rotation.classification.config'].create({})

        # Obtener productos almacenables
        products = self.search([
            ('type', '=', 'consu'),
            ('is_storable', '=', True),
        ])
        
        _logger.info(f"Productos a clasificar: {len(products)}")

        if not products:
            return True

        # 1. Calcular rotación GLOBAL
        self._calculate_rotation_global(config, products)
        
        # 2. Calcular rotación POR BODEGA
        self._calculate_rotation_all_warehouses(config, products)
        
        # Actualizar estadísticas
        duration = (datetime.now() - start_time).total_seconds()
        config.write({
            'last_calculation': fields.Datetime.now(),
            'last_calculation_products': len(products),
            'last_calculation_duration': duration,
        })

        _logger.info(f"=== FIN: Clasificación completada en {duration:.2f}s ===")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Rotation Classification Completed'),
                'message': _('%d products classified in %.2f seconds') % (len(products), duration),
                'type': 'success',
                'sticky': False,
            }
        }

    def _calculate_rotation_global(self, config, products):
        """Calcular rotación global (todas las bodegas sumadas)"""
        _logger.info("Calculando rotación GLOBAL...")
        
        # Obtener datos de ventas con pandas (global)
        sales_data_df = self._get_consumption_data_with_pandas(config, products, warehouse_id=None)
        
        # Obtener consumos mensuales individuales
        monthly_consumption_df = self._get_monthly_consumption_data(config, products, warehouse_id=None)
        
        # Combinar datos de ventas totales con consumos mensuales
        combined_df = sales_data_df.merge(monthly_consumption_df, on='product_id', how='left')
        
        # Aplicar clasificación por rotación
        classified_df = self._apply_rotation_classification(combined_df, config)
        
        # Guardar resultados globales
        self._save_rotation_results_global(classified_df)
        
        _logger.info(f"Rotación global calculada para {len(classified_df)} productos")

    def _calculate_rotation_all_warehouses(self, config, products):
        """Calcular rotación para cada bodega individual"""
        warehouses = self.env['stock.warehouse'].search([])
        _logger.info(f"Calculando rotación para {len(warehouses)} bodegas...")
        
        for warehouse in warehouses:
            _logger.debug(f"  Procesando bodega: {warehouse.name}")
            
            # Obtener datos de ventas para esta bodega
            sales_data_df = self._get_consumption_data_with_pandas(config, products, warehouse_id=warehouse.id)
            
            # Obtener consumos mensuales individuales para esta bodega
            monthly_consumption_df = self._get_monthly_consumption_data(config, products, warehouse_id=warehouse.id)
            
            # Combinar datos
            combined_df = sales_data_df.merge(monthly_consumption_df, on='product_id', how='left')
            
            # Aplicar clasificación
            classified_df = self._apply_rotation_classification(combined_df, config)
            
            # Guardar resultados por bodega
            self._save_rotation_results_warehouse(classified_df, warehouse)
        
        _logger.info(f"Rotación por bodega completada")

    def _get_consumption_data_with_pandas(self, config, products, warehouse_id=None):
        """
        Obtiene los datos de consumo REAL usando movimientos de stock de ventas.
        
        Usa stock.move con sale_line_id para capturar solo ventas reales (no ajustes ni consumos internos).
        Más preciso que usar facturas porque:
        - Captura el movimiento físico real del inventario
        - No depende de la facturación
        - Acceso directo a la bodega de origen (location_id)
        
        Args:
            config: Registro de configuración con período de análisis
            products: Recordset de productos a analizar
            warehouse_id: ID de bodega (None para global)
            
        Returns:
            DataFrame con columnas: product_id, stock_qty, qty_invoiced, qty_returned
        """
        _logger.debug(f"Obteniendo datos de consumo de ventas {'global' if not warehouse_id else f'para bodega {warehouse_id}'}...")
        
        # Calcular período de análisis
        period_end = datetime.now().date()
        period_start = period_end - timedelta(days=config.analysis_period_months * 30)
        
        product_ids = products.ids
        
        # Obtener stock actual de productos por bodega
        stock_data = []
        
        if warehouse_id:
            # Para stock por bodega, usar free_qty con context de ubicación
            warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            location = warehouse.lot_stock_id
            
            for product in products:
                # Sumar free_qty de todas las variantes del producto en esa ubicación
                total_free_qty = 0.0
                for variant in product.product_variant_ids:
                    variant_with_loc = variant.with_context(location=location.id)
                    total_free_qty += variant_with_loc.free_qty
                
                stock_data.append({
                    'product_id': product.id,
                    'stock_qty': max(0, total_free_qty),  # Nunca negativo
                })
        else:
            # Stock global (todas las bodegas)
            for product in products:
                # Sumar free_qty de todas las variantes sin filtro de ubicación
                total_free_qty = 0.0
                for variant in product.product_variant_ids:
                    total_free_qty += variant.free_qty
                
                stock_data.append({
                    'product_id': product.id,
                    'stock_qty': max(0, total_free_qty),  # Usar free_qty de variantes + nunca negativo
                })
        
        # Dominio base para movimientos de stock de VENTAS confirmadas
        domain = [
            ('product_id.product_tmpl_id', 'in', product_ids),
            ('state', '=', 'done'),  # Solo movimientos confirmados
            ('date', '>=', period_start),
            ('date', '<=', period_end),
            ('sale_line_id', '!=', False),  # Solo ventas reales (excluye ajustes, consumos internos, etc.)
            '|',
            ('is_out', '=', True),  # Salidas valoradas (ventas/consumos)
            ('is_in', '=', True),   # Entradas valoradas (devoluciones de clientes)
        ]
        
        # Filtrar por bodega si aplica
        if warehouse_id:
            warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            # Movimientos que salen o entran a esta bodega específica
            domain += [
                '|',
                ('location_id', 'child_of', warehouse.lot_stock_id.id),
                ('location_dest_id', 'child_of', warehouse.lot_stock_id.id)
            ]
        
        # Buscar movimientos de ventas (salidas y devoluciones)
        stock_moves = self.env['stock.move'].search(domain)
        
        _logger.debug(f"Movimientos de stock (ventas y devoluciones) encontrados: {len(stock_moves)}")
        
        # Convertir a lista de diccionarios para pandas
        # Usar directamente los campos is_out/is_in que ya están calculados y almacenados
        sales_data = []
        for move in stock_moves:
            if move.is_out:
                # Salida: venta al cliente
                sales_data.append({
                    'product_id': move.product_id.product_tmpl_id.id,
                    'quantity': move.product_uom_qty,
                    'move_type': 'out',
                })
            elif move.is_in:
                # Entrada: devolución de cliente
                sales_data.append({
                    'product_id': move.product_id.product_tmpl_id.id,
                    'quantity': move.product_uom_qty,
                    'move_type': 'in',
                })
        
        # Crear DataFrames
        stock_df = pd.DataFrame(stock_data)
        
        if sales_data:
            sales_df = pd.DataFrame(sales_data)
            
            # Separar salidas (ventas) y entradas (devoluciones)
            out_df = sales_df[sales_df['move_type'] == 'out'].groupby('product_id')['quantity'].sum()
            in_df = sales_df[sales_df['move_type'] == 'in'].groupby('product_id')['quantity'].sum()
            
            # Crear DataFrame con cantidades vendidas y devueltas
            consumption_df = pd.DataFrame({
                'qty_invoiced': out_df,  # Mantener nombre para compatibilidad con código existente
                'qty_returned': in_df,
            }).fillna(0.0)
            
            # Combinar con stock
            result_df = stock_df.merge(consumption_df, left_on='product_id', right_index=True, how='left')
            result_df['qty_invoiced'] = result_df['qty_invoiced'].fillna(0.0)
            result_df['qty_returned'] = result_df['qty_returned'].fillna(0.0)
        else:
            # Si no hay ventas, rellenar con ceros
            stock_df['qty_invoiced'] = 0.0
            stock_df['qty_returned'] = 0.0
            result_df = stock_df
        
        # Agregar metadatos del período
        result_df['period_start'] = period_start
        result_df['period_end'] = period_end
        result_df['period_months'] = config.analysis_period_months
        
        return result_df

    def _get_monthly_consumption_data(self, config, products, warehouse_id=None):
        """
        Calcula consumos mensuales individuales (últimos 12 meses) para cada producto.
        OPTIMIZADO: Carga todos los movimientos una sola vez y agrupa con Pandas.
        
        Args:
            config: Configuración con período de análisis
            products: Recordset de productos
            warehouse_id: ID de bodega (None para global)
            
        Returns:
            DataFrame con columnas: product_id, consumption_m0, ..., consumption_m11
        """
        from dateutil.relativedelta import relativedelta
        
        _logger.debug(f"Calculando consumos mensuales {'global' if not warehouse_id else f'para bodega {warehouse_id}'}...")
        
        today = datetime.now().date()
        product_ids = products.ids
        
        # Calcular fecha de inicio (hace 12 meses)
        start_date = today.replace(day=1) - relativedelta(months=11)
        
        # Dominio optimizado: TODOS los movimientos de TODOS los productos de una sola vez
        domain = [
            ('product_id.product_tmpl_id', 'in', product_ids),
            ('state', '=', 'done'),
            ('sale_line_id', '!=', False),
            ('date', '>=', start_date),
            ('date', '<=', today),
            '|',
            ('is_out', '=', True),
            ('is_in', '=', True),
        ]
        
        # Filtrar por bodega si aplica
        if warehouse_id:
            warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            domain += [
                '|',
                ('location_id', 'child_of', warehouse.lot_stock_id.id),
                ('location_dest_id', 'child_of', warehouse.lot_stock_id.id)
            ]
        
        # UNA SOLA búsqueda para todos los movimientos
        _logger.debug(f"Cargando movimientos de stock desde {start_date} hasta {today}...")
        stock_moves = self.env['stock.move'].search(domain)
        _logger.debug(f"Movimientos cargados: {len(stock_moves)}")
        
        # Convertir a lista de diccionarios para Pandas
        moves_data = []
        for move in stock_moves:
            moves_data.append({
                'product_id': move.product_id.product_tmpl_id.id,
                'date': move.date.date() if hasattr(move.date, 'date') else move.date,
                'quantity': move.product_uom_qty,
                'is_out': move.is_out,
                'is_in': move.is_in,
            })
        
        if not moves_data:
            # Si no hay movimientos, devolver DataFrame con ceros
            return pd.DataFrame([{
                'product_id': p.id,
                **{f'consumption_m{i}': 0.0 for i in range(12)}
            } for p in products])
        
        # Crear DataFrame con TODOS los movimientos
        df = pd.DataFrame(moves_data)
        
        # Agregar columna de mes offset (0 = mes actual, 1 = mes pasado, etc.)
        def get_month_offset(date):
            current_month = today.replace(day=1)
            move_month = date.replace(day=1)
            delta = relativedelta(current_month, move_month)
            return delta.years * 12 + delta.months
        
        df['month_offset'] = df['date'].apply(get_month_offset)
        
        # Filtrar solo los últimos 12 meses
        df = df[df['month_offset'] < 12]
        
        # Calcular consumo neto: +qty si es salida (is_out), -qty si es devolución (is_in)
        df['net_qty'] = df.apply(
            lambda row: row['quantity'] if row['is_out'] else -row['quantity'],
            axis=1
        )
        
        # Agrupar por producto y mes usando Pandas (SUPER RÁPIDO)
        consumption_grouped = df.groupby(['product_id', 'month_offset'])['net_qty'].sum().reset_index()
        
        # Pivotar: filas = productos, columnas = consumption_m0, m1, ... m11
        consumption_pivot = consumption_grouped.pivot(
            index='product_id',
            columns='month_offset',
            values='net_qty'
        ).fillna(0.0)
        
        # Renombrar columnas a consumption_m0, consumption_m1, etc.
        consumption_pivot.columns = [f'consumption_m{int(col)}' for col in consumption_pivot.columns]
        
        # Asegurar que existan todas las columnas M0-M11 (rellenar con 0 si falta algún mes)
        for i in range(12):
            col_name = f'consumption_m{i}'
            if col_name not in consumption_pivot.columns:
                consumption_pivot[col_name] = 0.0
        
        # Resetear index para tener product_id como columna
        consumption_pivot = consumption_pivot.reset_index()
        
        # Asegurar que TODOS los productos estén presentes (incluso sin movimientos)
        all_products_df = pd.DataFrame({'product_id': product_ids})
        result_df = all_products_df.merge(consumption_pivot, on='product_id', how='left').fillna(0.0)
        
        _logger.debug(f"Consumos mensuales calculados para {len(result_df)} productos")
        
        return result_df

    def _apply_rotation_classification(self, consumption_df, config):
        """
        Aplica la lógica de clasificación por rotación usando pandas/numpy.
        
        Lógica de clasificación:
        - DEPLETED: stock_qty = 0
        - INFINITE: stock_qty > 0 AND monthly_consumption = 0
        - HIGH: rotation_months <= threshold_high
        - LOW: rotation_months > threshold_high AND <= threshold_low
        - BONE: rotation_months > threshold_low AND < threshold_bone
        - FEMUR: rotation_months >= threshold_bone
        
        Args:
            consumption_df: DataFrame con datos de consumo y stock
            config: Configuración con umbrales
            
        Returns:
            DataFrame con columna adicional 'rotation_classification'
        """
        _logger.debug("Aplicando clasificación por rotación con pandas...")
        
        # Calcular consumo neto (facturado - devuelto)
        consumption_df['net_consumption'] = consumption_df['qty_invoiced'] - consumption_df['qty_returned']
        
        # Calcular consumo mensual promedio (promedio simple)
        consumption_df['monthly_consumption'] = consumption_df['net_consumption'] / consumption_df['period_months']
        
        # Calcular consumo mensual promedio TOP 10 (si existen los campos mensuales)
        monthly_columns = [f'consumption_m{i}' for i in range(12)]
        if all(col in consumption_df.columns for col in monthly_columns):
            def calculate_top10(row):
                consumptions = [row[col] for col in monthly_columns]
                top_10 = sorted(consumptions, reverse=True)[:10]
                return sum(top_10) / 10.0 if top_10 else 0.0
            
            consumption_df['monthly_consumption_top10'] = consumption_df.apply(calculate_top10, axis=1)
        else:
            # Si no hay consumos mensuales, usar el promedio simple
            consumption_df['monthly_consumption_top10'] = consumption_df['monthly_consumption']
        
        # Calcular meses de stock (evitar división por cero)
        # Reemplazar 0 por un valor muy pequeño para evitar ZeroDivisionError
        consumption_df['monthly_consumption_safe'] = consumption_df['monthly_consumption'].replace(0, 1e-10)
        consumption_df['rotation_months'] = consumption_df['stock_qty'] / consumption_df['monthly_consumption_safe']
        
        # Si el consumo era 0, establecer rotation_months a infinito
        consumption_df.loc[consumption_df['monthly_consumption'] == 0, 'rotation_months'] = np.inf
        
        # Aplicar clasificación usando np.select para mejor rendimiento
        conditions = [
            consumption_df['stock_qty'] == 0,  # DEPLETED
            (consumption_df['stock_qty'] > 0) & (consumption_df['monthly_consumption'] == 0),  # INFINITE
            consumption_df['rotation_months'] <= config.threshold_high,  # HIGH
            (consumption_df['rotation_months'] > config.threshold_high) & 
            (consumption_df['rotation_months'] <= config.threshold_low),  # LOW
            (consumption_df['rotation_months'] > config.threshold_low) & 
            (consumption_df['rotation_months'] < config.threshold_bone),  # BONE
            consumption_df['rotation_months'] >= config.threshold_bone,  # FEMUR
        ]
        
        choices = ['DEPLETED', 'INFINITE', 'HIGH', 'LOW', 'BONE', 'FEMUR']
        
        consumption_df['rotation_classification'] = np.select(conditions, choices, default='INFINITE')
        
        # Ajustar rotation_months para casos especiales
        consumption_df.loc[consumption_df['rotation_classification'] == 'DEPLETED', 'rotation_months'] = 0.0
        consumption_df.loc[consumption_df['rotation_classification'] == 'INFINITE', 'rotation_months'] = 0.0
        
        return consumption_df

    def _save_rotation_results_global(self, classified_df):
        """Guarda los resultados de rotación global en product.rotation.warehouse (con warehouse_id=False)"""
        _logger.debug("Guardando resultados de rotación global en product.rotation.warehouse...")
        
        calculation_date = fields.Datetime.now()
        
        for _, row in classified_df.iterrows():
            product_id = int(row['product_id'])
            
            # Buscar o crear registro de rotación global (warehouse_id=False)
            rotation_global = self.env['product.rotation.warehouse'].search([
                ('product_tmpl_id', '=', product_id),
                ('warehouse_id', '=', False)
            ], limit=1)
            
            values = {
                'product_tmpl_id': product_id,
                'warehouse_id': False,  # NULL = Global
                'rotation_classification': row['rotation_classification'],
                'rotation_months': float(row['rotation_months']),
                'stock_qty': float(row['stock_qty']),
                'monthly_consumption': float(row['monthly_consumption']),
                'monthly_consumption_top10': float(row.get('monthly_consumption_top10', row['monthly_consumption'])),
                'last_calculation': calculation_date,
            }
            
            # Agregar consumos mensuales si existen
            for month_offset in range(12):
                col_name = f'consumption_m{month_offset}'
                if col_name in row:
                    values[col_name] = float(row[col_name])
            
            if rotation_global:
                rotation_global.write(values)
            else:
                self.env['product.rotation.warehouse'].create(values)
            
            # Actualizar campos legacy en product.template para compatibilidad con módulos antiguos
            self.browse(product_id).write({
                'rotation_classification': row['rotation_classification'],
                'rotation_months': float(row['rotation_months']),
                'rotation_stock_qty': float(row['stock_qty']),
                'rotation_monthly_consumption': float(row['monthly_consumption']),
                'rotation_last_calculation': calculation_date,
            })
            
            # Los campos _global se actualizan automáticamente vía compute
        
        _logger.info(f"Actualizados {len(classified_df)} productos con rotación global")

    def _save_rotation_results_warehouse(self, classified_df, warehouse):
        """Guarda los resultados de rotación por bodega en product.rotation.warehouse"""
        _logger.debug(f"Guardando resultados para bodega {warehouse.name}...")
        
        calculation_date = fields.Datetime.now()
        
        for _, row in classified_df.iterrows():
            product_id = int(row['product_id'])
            
            # Buscar o crear registro de rotación por bodega
            rotation_wh = self.env['product.rotation.warehouse'].search([
                ('product_tmpl_id', '=', product_id),
                ('warehouse_id', '=', warehouse.id)
            ], limit=1)
            
            values = {
                'product_tmpl_id': product_id,
                'warehouse_id': warehouse.id,
                'rotation_classification': row['rotation_classification'],
                'rotation_months': float(row['rotation_months']),
                'stock_qty': float(row['stock_qty']),
                'monthly_consumption': float(row['monthly_consumption']),
                'monthly_consumption_top10': float(row.get('monthly_consumption_top10', row['monthly_consumption'])),
                'last_calculation': calculation_date,
            }
            
            # Agregar consumos mensuales si existen
            for month_offset in range(12):
                col_name = f'consumption_m{month_offset}'
                if col_name in row:
                    values[col_name] = float(row[col_name])
            
            if rotation_wh:
                rotation_wh.write(values)
            else:
                self.env['product.rotation.warehouse'].create(values)
