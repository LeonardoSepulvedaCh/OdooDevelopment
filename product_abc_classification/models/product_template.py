# -*- coding: utf-8 -*-
import logging
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ABC Global (para toda la empresa)
    abc_classification_global = fields.Selection([
        ('aaa', 'AAA'),
        ('aa', 'AA'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='ABC Classification (Global)',
       index=True,
       help='Global ABC classification based on invoiced sales value across all warehouses')
    
    # ABC principal (mantener para compatibilidad - será la del almacén principal)
    abc_classification = fields.Selection([
        ('aaa', 'AAA'),
        ('aa', 'AA'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='ABC Classification',
        index=True,
       help='ABC classification based on invoiced sales value')
    
    abc_sales_value = fields.Float(
        string='ABC Sales Value',
        readonly=True,
        help='Total invoiced sales value used for ABC classification'
    )
    
    abc_sales_value_global = fields.Float(
        string='ABC Sales Value (Global)',
        readonly=True,
        help='Total invoiced sales value across all warehouses'
    )
    
    abc_last_calculation = fields.Datetime(
        string='Last ABC Classification',
        help='Date and time of the last ABC classification'
    )
    
    # Relación One2many con ABC por bodega
    abc_warehouse_ids = fields.One2many(
        comodel_name='product.abc.warehouse',
        inverse_name='product_tmpl_id',
        string='ABC by Warehouse',
        help='ABC classification for each warehouse'
    )
    
    # Selector de bodega para ver ABC específico
    abc_selected_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='View ABC for Warehouse',
        help='Select a warehouse to view its specific ABC classification'
    )
    
    # ABC de la bodega seleccionada (computado)
    abc_selected_warehouse_classification = fields.Selection([
        ('aaa', 'AAA'),
        ('aa', 'AA'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='ABC (Selected Warehouse)',
       compute='_compute_abc_selected_warehouse',
       help='ABC classification for the selected warehouse')
    
    abc_selected_warehouse_sales = fields.Float(
        string='Sales Value (Selected Warehouse)',
        compute='_compute_abc_selected_warehouse',
        help='Sales value for the selected warehouse'
    )
    
    @api.depends('abc_selected_warehouse_id', 'abc_warehouse_ids.classification', 'abc_warehouse_ids.sales_value')
    def _compute_abc_selected_warehouse(self):
        """Calcular ABC de la bodega seleccionada"""
        for product in self:
            if product.abc_selected_warehouse_id:
                abc_record = product.abc_warehouse_ids.filtered(
                    lambda r: r.warehouse_id == product.abc_selected_warehouse_id
                )
                if abc_record:
                    product.abc_selected_warehouse_classification = abc_record[0].classification
                    product.abc_selected_warehouse_sales = abc_record[0].sales_value
                else:
                    product.abc_selected_warehouse_classification = False
                    product.abc_selected_warehouse_sales = 0.0
            else:
                product.abc_selected_warehouse_classification = False
                product.abc_selected_warehouse_sales = 0.0
    
    @api.model
    def action_calculate_abc_classification(self, product_ids=None):
        """
        Calcular clasificación ABC para todos o algunos productos
        Calcula ABC Global y ABC por cada Bodega
        Optimizado con pandas desde el inicio
        """
        if pd is None or np is None:
            raise UserError(_(
                'Las librerías pandas y numpy no están instaladas.\n'
                'Instale con: pip install pandas numpy'
            ))
        
        start_time = time.time()
        _logger.info('Iniciando cálculo de clasificación ABC (Global y por Bodega)...')
        
        # Obtener configuración
        config = self.env['abc.classification.config'].get_active_config()
        
        # Calcular período
        date_to = fields.Date.today()
        date_from = date_to - relativedelta(months=config.analysis_period_months)
        
        # Filtrar productos almacenables
        domain = [
            ('type', '=', 'consu'),
            ('is_storable', '=', True),
        ]
        if product_ids:
            domain.append(('id', 'in', product_ids))
        
        products = self.search(domain)
        
        if not products:
            return self._show_notification(_('Sin productos'), 
                                          _('No hay productos almacenables para clasificar'), 
                                          'warning')
        
        # Calcular ABC Global (todas las bodegas)
        _logger.info('Calculando ABC Global...')
        self._calculate_abc_global(products.ids, config, date_from, date_to)
        
        # Calcular ABC por cada bodega
        _logger.info('Calculando ABC por Bodega...')
        warehouses = self.env['stock.warehouse'].search([])
        for warehouse in warehouses:
            _logger.info(f'  - Procesando bodega: {warehouse.name}')
            self._calculate_abc_by_warehouse(products.ids, config, date_from, date_to, warehouse)
        
        # Actualizar estadísticas en configuración
        elapsed = time.time() - start_time
        config.write({
            'last_calculation_date': fields.Datetime.now(),
            'products_calculated': len(products),
            'calculation_time': elapsed,
        })
        
        _logger.info(f'✓ ABC completado: {len(products)} productos, {len(warehouses)} bodegas en {elapsed:.2f}s')
        
        return self._show_notification(
            _('Clasificación ABC Completada'),
            _('Se clasificaron %d productos en %d bodegas en %.2f segundos.') % (len(products), len(warehouses), elapsed),
            'success'
        )
    
    @api.model
    def _calculate_abc_global(self, product_ids, config, date_from, date_to):
        """Calcular ABC Global (todas las bodegas sumadas)"""
        
        # Obtener datos de ventas con pandas optimizado
        sales_df = self._get_sales_data_with_pandas(product_ids, date_from, date_to, warehouse_id=None)
        
        if sales_df.empty:
            # Sin ventas: todos clasificación C
            if config.include_zero_sales:
                self._classify_products_without_sales_global(product_ids)
            return
        
        # Aplicar clasificación ABC
        classified_df = self._apply_abc_classification(sales_df, config)
        
        # Guardar resultados globales
        self._save_abc_results_global(classified_df)
        
        # Clasificar productos sin ventas como C
        products_with_sales = set(classified_df['product_id'].tolist())
        products_without_sales_ids = [pid for pid in product_ids if pid not in products_with_sales]
        
        if products_without_sales_ids and config.include_zero_sales:
            self._classify_products_without_sales_global(products_without_sales_ids)
    
    @api.model
    def _calculate_abc_by_warehouse(self, product_ids, config, date_from, date_to, warehouse):
        """Calcular ABC para una bodega específica"""
        
        # Obtener datos de ventas de esta bodega con pandas optimizado
        sales_df = self._get_sales_data_with_pandas(product_ids, date_from, date_to, warehouse_id=warehouse.id)
        
        if sales_df.empty:
            # Sin ventas en esta bodega
            if config.include_zero_sales:
                self._classify_products_without_sales_warehouse(product_ids, warehouse)
            return
        
        # Aplicar clasificación ABC
        classified_df = self._apply_abc_classification(sales_df, config)
        
        # Guardar resultados por bodega
        self._save_abc_results_warehouse(classified_df, warehouse)
        
        # Clasificar productos sin ventas como C en esta bodega
        products_with_sales = set(classified_df['product_id'].tolist())
        products_without_sales_ids = [pid for pid in product_ids if pid not in products_with_sales]
        
        if products_without_sales_ids and config.include_zero_sales:
            self._classify_products_without_sales_warehouse(products_without_sales_ids, warehouse)
    
    @api.model
    def _get_sales_data_with_pandas(self, product_ids, date_from, date_to, warehouse_id=None):
        """
        Obtener datos de ventas con pandas DESDE EL INICIO
        warehouse_id: None = todas las bodegas, int = bodega específica
        
        Optimización: Uso de pandas desde la consulta inicial, sin loops FOR
        """
        
        # Construir dominio base
        domain_invoice = [
            ('move_id.move_type', '=', 'out_invoice'),
            ('move_id.state', '=', 'posted'),
            ('move_id.invoice_date', '>=', date_from),
            ('move_id.invoice_date', '<=', date_to),
            ('product_id.product_tmpl_id', 'in', product_ids),
            ('display_type', '=', 'product'),
        ]
        
        domain_refund = [
            ('move_id.move_type', '=', 'out_refund'),
            ('move_id.state', '=', 'posted'),
            ('move_id.invoice_date', '>=', date_from),
            ('move_id.invoice_date', '<=', date_to),
            ('product_id.product_tmpl_id', 'in', product_ids),
            ('display_type', '=', 'product'),
        ]
        
        # Obtener líneas de factura
        invoice_lines = self.env['account.move.line'].search(domain_invoice)
        refund_lines = self.env['account.move.line'].search(domain_refund)
        
        # Si se filtra por bodega, crear mapeo línea->bodega en UNA SOLA consulta (optimizado)
        line_warehouse_map = {}
        if warehouse_id:
            # Obtener todas las relaciones sale.order.line -> invoice_lines de golpe
            all_line_ids = invoice_lines.ids + refund_lines.ids
            if all_line_ids:
                sale_lines = self.env['sale.order.line'].search([
                    ('invoice_lines', 'in', all_line_ids)
                ])
                
                # Crear mapeo: invoice_line_id -> warehouse_id
                for sale_line in sale_lines:
                    if sale_line.order_id.warehouse_id:
                        for inv_line in sale_line.invoice_lines:
                            line_warehouse_map[inv_line.id] = sale_line.order_id.warehouse_id.id
        
        # Extraer datos a listas para pandas (optimizado)
        invoice_data = []
        for line in invoice_lines:
            if line.product_id and line.product_id.product_tmpl_id:
                # Filtrar por bodega si se especifica
                if warehouse_id:
                    line_wh = line_warehouse_map.get(line.id)
                    if line_wh != warehouse_id:
                        continue  # Saltar líneas de otras bodegas
                
                invoice_data.append({
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'quantity': line.quantity,
                    'price_subtotal': line.price_subtotal,
                })
        
        refund_data = []
        for line in refund_lines:
            if line.product_id and line.product_id.product_tmpl_id:
                # Filtrar por bodega si se especifica
                if warehouse_id:
                    line_wh = line_warehouse_map.get(line.id)
                    if line_wh != warehouse_id:
                        continue  # Saltar líneas de otras bodegas
                
                refund_data.append({
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'quantity': line.quantity,
                    'price_subtotal': line.price_subtotal,
                })
        
        # Crear DataFrames y agrupar con pandas (sin loops adicionales)
        if invoice_data:
            df_invoices = pd.DataFrame(invoice_data)
            # Agrupar con pandas (sin FOR loops)
            sales_agg = df_invoices.groupby('product_tmpl_id').agg({
                'quantity': 'sum',
                'price_subtotal': 'sum'
            }).reset_index()
            sales_agg.columns = ['product_id', 'quantity', 'sales_value']
        else:
            sales_agg = pd.DataFrame(columns=['product_id', 'quantity', 'sales_value'])
        
        if refund_data:
            df_refunds = pd.DataFrame(refund_data)
            # Agrupar con pandas (sin FOR loops)
            refunds_agg = df_refunds.groupby('product_tmpl_id').agg({
                'quantity': 'sum',
                'price_subtotal': 'sum'
            }).reset_index()
            refunds_agg.columns = ['product_id', 'quantity_refunded', 'refund_value']
        else:
            refunds_agg = pd.DataFrame(columns=['product_id', 'quantity_refunded', 'refund_value'])
        
        # Merge de DataFrames (sin FOR loops)
        if not sales_agg.empty:
            df = sales_agg.merge(refunds_agg, on='product_id', how='left')
            # Usar infer_objects + fillna para evitar FutureWarning de pandas
            df = df.infer_objects(copy=False)
            df['quantity_refunded'] = df['quantity_refunded'].fillna(0)
            df['refund_value'] = df['refund_value'].fillna(0)
            
            # Calcular valores netos con pandas vectorizado
            df['net_sales_value'] = df['sales_value'] - df['refund_value']
            df['net_quantity'] = df['quantity'] - df['quantity_refunded']
            
            # Filtrar productos con ventas netas positivas
            df = df[df['net_sales_value'] > 0].reset_index(drop=True)
            
            return df
        
        return pd.DataFrame()
    
    @api.model
    def _apply_abc_classification(self, df, config):
        """
        Aplicar clasificación ABC usando pandas
        """
        # Ordenar por valor de ventas (mayor a menor)
        df = df.sort_values('net_sales_value', ascending=False).reset_index(drop=True)
        
        # Calcular total de ventas
        total_sales = df['net_sales_value'].sum()
        
        # Calcular porcentaje acumulado (como decimal para widget percentage)
        df['cumulative_value'] = df['net_sales_value'].cumsum()
        df['cumulative_percentage'] = (df['cumulative_value'] / total_sales)
        
        # Asignar ranking
        df['rank'] = range(1, len(df) + 1)
        
        # Aplicar clasificación basada en umbrales
        conditions = [
            df['cumulative_percentage'] <= (config.threshold_aaa / 100),
            df['cumulative_percentage'] <= (config.threshold_aa / 100),
            df['cumulative_percentage'] <= (config.threshold_a / 100),
            df['cumulative_percentage'] <= (config.threshold_b / 100),
        ]
        choices = ['aaa', 'aa', 'a', 'b']
        df['classification'] = np.select(conditions, choices, default='c')
        
        return df
    
    @api.model
    def _save_abc_results_global(self, df):
        """Guardar resultados de ABC Global en product.template"""
        calculation_date = fields.Datetime.now()
        
        # Actualización masiva con pandas
        for idx, row in df.iterrows():
            product = self.browse(int(row['product_id']))
            product.write({
                'abc_classification_global': row['classification'],
                'abc_sales_value_global': float(row['net_sales_value']),
                'abc_last_calculation': calculation_date,
                # Actualizar también el campo abc_classification con el global
                'abc_classification': row['classification'],
                'abc_sales_value': float(row['net_sales_value']),
            })
    
    @api.model
    def _save_abc_results_warehouse(self, df, warehouse):
        """Guardar resultados de ABC por Bodega en product.abc.warehouse"""
        calculation_date = fields.Datetime.now()
        ABCWarehouse = self.env['product.abc.warehouse']
        
        for idx, row in df.iterrows():
            product_id = int(row['product_id'])
            
            # Buscar o crear registro ABC para este producto-bodega
            abc_record = ABCWarehouse.search([
                ('product_tmpl_id', '=', product_id),
                ('warehouse_id', '=', warehouse.id)
            ], limit=1)
            
            values = {
                'classification': row['classification'],
                'sales_value': float(row['net_sales_value']),
                'cumulative_percentage': float(row['cumulative_percentage']),
                'rank': int(row['rank']),
                'last_calculation': calculation_date,
            }
            
            if abc_record:
                abc_record.write(values)
            else:
                values.update({
                    'product_tmpl_id': product_id,
                    'warehouse_id': warehouse.id,
                })
                ABCWarehouse.create(values)
    
    @api.model
    def _classify_products_without_sales_global(self, product_ids):
        """Clasificar productos sin ventas como C (Global)"""
        products = self.browse(product_ids)
        calculation_date = fields.Datetime.now()
        
        products.write({
            'abc_classification_global': 'c',
            'abc_sales_value_global': 0.0,
            'abc_classification': 'c',
            'abc_sales_value': 0.0,
            'abc_last_calculation': calculation_date,
        })
    
    @api.model
    def _classify_products_without_sales_warehouse(self, product_ids, warehouse):
        """Clasificar productos sin ventas como C (por Bodega)"""
        ABCWarehouse = self.env['product.abc.warehouse']
        calculation_date = fields.Datetime.now()
        
        for product_id in product_ids:
            abc_record = ABCWarehouse.search([
                ('product_tmpl_id', '=', product_id),
                ('warehouse_id', '=', warehouse.id)
            ], limit=1)
            
            values = {
                'classification': 'c',
                'sales_value': 0.0,
                'cumulative_percentage': 1.0,
                'rank': 0,
                'last_calculation': calculation_date,
            }
            
            if abc_record:
                abc_record.write(values)
            else:
                values.update({
                    'product_tmpl_id': product_id,
                    'warehouse_id': warehouse.id,
                })
                ABCWarehouse.create(values)
    
    @api.model
    def _show_notification(self, title, message, notification_type):
        """Mostrar notificación al usuario"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': False,
            }
        }
    
    def update_abc_on_invoice_lines(self):
        """
        Actualizar ABC en líneas de factura al validar
        Este método será llamado desde account.move al validar facturas
        """
        self.ensure_one()
        
        # Obtener ABC actual del producto (por bodega si aplica)
        abc_classification = self.abc_classification or 'c'
        abc_sales_value = self.abc_sales_value or 0.0
        
        return {
            'abc_classification_at_sale': abc_classification,
            'abc_sales_value_at_sale': abc_sales_value,
        }
