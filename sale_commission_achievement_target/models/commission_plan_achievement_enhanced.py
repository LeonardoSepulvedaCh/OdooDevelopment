from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleCommissionPlanAchievementEnhanced(models.Model):
    """
    Extensión avanzada del modelo de logros para cálculo de montos reales alcanzados.
    
    Calcula automáticamente el monto real vendido/facturado comparándolo con el objetivo
    definido. Implementa lógica de categorías prioritarias y validación de cumplimiento
    de objetivos usando consultas SQL optimizadas con CTEs para máximo rendimiento.
    
    NOTA IMPORTANTE - Dependencias de Parámetros de Configuración:
    Este modelo depende de parámetros de configuración del sistema (ir.config_parameter):
    - mandatory_category_enabled: Habilita validación de categoría obligatoria
    - mandatory_category_id: ID de la categoría obligatoria
    - mandatory_category_percentage: Porcentaje mínimo requerido
    
    Dado que @api.depends no puede detectar cambios en ir.config_parameter,
    los campos computados usan store=False para asegurar recálculo en cada acceso.
    Esto garantiza que los valores siempre reflejen la configuración actual del sistema.
    """
    _inherit = 'sale.commission.plan.achievement'

    actual_amount = fields.Monetary(
        string='Monto Real Alcanzado',
        compute='_compute_actual_amount',
        currency_field='currency_id',
        store=False,  # No almacenar para asegurar recálculo con parámetros actualizados
        help='Monto real vendido/facturado en esta categoría según el tipo de logro seleccionado. '
             'Se recalcula en cada acceso para reflejar cambios en parámetros de configuración.'
    )
    
    achievement_percentage = fields.Float(
        string='% Alcanzado',
        compute='_compute_achievement_percentage',
        store=False,  # No almacenar para recalcular siempre basado en actual_amount actualizado
        help='Porcentaje alcanzado del monto objetivo'
    )

    def _get_priority_category_safely(self):
        """
        Obtiene la categoría prioritaria configurada en los parámetros del sistema.
        
        Este método lee el parámetro 'mandatory_category_id' de la configuración del sistema,
        valida que sea un ID válido y que la categoría exista en la base de datos.
        
        Returns:
            product.public.category: Registro de la categoría prioritaria si existe y es válida.
            None: Si no hay categoría configurada, el ID es inválido o la categoría no existe.
        """
        try:
            mandatory_category_id_str = self.env['ir.config_parameter'].sudo().get_param(
                'sale_commission_achievement_target.mandatory_category_id', False
            )
            
            if not mandatory_category_id_str:
                return None
            
            try:
                # Validar que sea un entero válido
                cleaned_id = str(mandatory_category_id_str).strip()
                if cleaned_id.isdigit() and int(cleaned_id) > 0:
                    category_id = int(cleaned_id)
                    priority_category = self.env['product.public.category'].sudo().browse(category_id)
                    
                    # Verificar que existe
                    if priority_category.exists():
                        return priority_category
                    else:
                        _logger.warning(
                            "La categoría prioritaria con ID %s no existe en la base de datos.", 
                            category_id
                        )
                        return None
                else:
                    _logger.warning(
                        "El ID de categoría prioritaria '%s' no es válido. Debe ser un entero positivo.",
                        cleaned_id
                    )
                    return None
            except (ValueError, TypeError, AttributeError) as e:
                _logger.warning(
                    "Error al procesar el ID de categoría prioritaria '%s': %s",
                    mandatory_category_id_str, e
                )
                return None
                
        except Exception as e:
            _logger.error(
                "Error crítico al obtener la categoría prioritaria: %s", 
                e, exc_info=True
            )
            return None

    # Calcular el monto real vendido/facturado según el tipo de achievement
    def _compute_actual_amount_sql(self, achievement, priority_category_id):

        if not achievement.plan_id:
            return 0.0
        
        plan = achievement.plan_id
        
        # Validar que el plan tenga las fechas necesarias
        if not plan.date_from or not plan.date_to:
            _logger.warning(
                "Plan %s no tiene date_from o date_to configurado. No se puede calcular actual_amount.",
                plan.name
            )
            return 0.0
        
        cr = self.env.cr
        
        # Construir condición de prioridad de forma segura
        # Si este achievement NO es la categoría prioritaria, excluir productos que estén en la categoría prioritaria
        priority_condition = ""
        priority_params = []
        if priority_category_id and achievement.public_categ_id:
            if achievement.public_categ_id.id != priority_category_id:
                # Solo incluir productos que NO estén en la categoría prioritaria
                priority_condition = """
                    AND NOT EXISTS (
                        SELECT 1 FROM product_public_category_product_template_rel ppcrel_priority
                        WHERE ppcrel_priority.product_template_id = pt.id
                          AND ppcrel_priority.product_public_category_id = %s
                    )
                """
                priority_params = [priority_category_id]
        
        if achievement.type in ['amount_sold', 'qty_sold']:
            # Query para ventas - usar CTE para mejor performance
            query = """
                WITH plan_user_dates AS (
                    SELECT 
                        scpu.user_id,
                        COALESCE(scpu.date_from, %s) as date_from,
                        COALESCE(scpu.date_to, %s) as date_to
                    FROM sale_commission_plan_user scpu
                    WHERE scpu.plan_id = %s
                )
                SELECT 
                    COALESCE(SUM(
                        CASE 
                            WHEN %s = 'amount_sold' THEN sol.price_subtotal / COALESCE(NULLIF(so.currency_rate, 0), 1.0)
                            WHEN %s = 'qty_sold' THEN sol.product_uom_qty
                            ELSE 0
                        END
                    ), 0) as total
                FROM sale_order so
                JOIN sale_order_line sol ON sol.order_id = so.id
                JOIN plan_user_dates pud ON pud.user_id = so.user_id
                LEFT JOIN product_product pp ON sol.product_id = pp.id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                WHERE so.state = 'sale'
                  AND so.company_id = %s
                  AND so.date_order BETWEEN pud.date_from AND pud.date_to
                  AND sol.display_type IS NULL
                  AND COALESCE(sol.is_expense, false) = false
                  AND COALESCE(sol.is_downpayment, false) = false
                  AND (%s IS NULL OR sol.product_id = %s)
                  AND (
                    %s IS NULL OR 
                    EXISTS (
                        SELECT 1 FROM product_public_category_product_template_rel ppcrel
                        WHERE ppcrel.product_template_id = pt.id
                          AND ppcrel.product_public_category_id = %s
                    )
                  )
                  AND (%s IS NULL OR %s IS NOT NULL OR pt.categ_id = %s)
                  {priority_cond}
            """.format(priority_cond=priority_condition)
            
            params = [
                plan.date_from,
                plan.date_to,
                plan.id,
                achievement.type,
                achievement.type,
                plan.company_id.id,
                achievement.product_id.id or None,
                achievement.product_id.id or None,
                achievement.public_categ_id.id or None,
                achievement.public_categ_id.id or None,
                achievement.product_categ_id.id or None,
                achievement.public_categ_id.id or None,
                achievement.product_categ_id.id or None,
            ]
            
            # Agregar parámetros de prioridad si existen
            params.extend(priority_params)
            
            cr.execute(query, params)
            result = cr.fetchone()
            return result[0] if result else 0.0
            
        elif achievement.type in ['amount_invoiced', 'qty_invoiced']:
            # Query para facturas - usar CTE para mejor performance
            query = """
                WITH plan_user_dates AS (
                    SELECT 
                        scpu.user_id,
                        COALESCE(scpu.date_from, %s) as date_from,
                        COALESCE(scpu.date_to, %s) as date_to
                    FROM sale_commission_plan_user scpu
                    WHERE scpu.plan_id = %s
                )
                SELECT 
                    COALESCE(SUM(
                        CASE 
                            WHEN %s = 'amount_invoiced' THEN
                                CASE
                                    WHEN am.move_type = 'out_invoice' THEN aml.price_subtotal / COALESCE(NULLIF(am.invoice_currency_rate, 0), 1.0)
                                    WHEN am.move_type = 'out_refund' THEN -1 * aml.price_subtotal / COALESCE(NULLIF(am.invoice_currency_rate, 0), 1.0)
                                    ELSE 0
                                END
                            WHEN %s = 'qty_invoiced' THEN
                                CASE
                                    WHEN am.move_type = 'out_invoice' THEN aml.quantity
                                    WHEN am.move_type = 'out_refund' THEN -1 * aml.quantity
                                    ELSE 0
                                END
                            ELSE 0
                        END
                    ), 0) as total
                FROM account_move am
                JOIN account_move_line aml ON aml.move_id = am.id
                JOIN plan_user_dates pud ON pud.user_id = am.invoice_user_id
                LEFT JOIN product_product pp ON aml.product_id = pp.id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                WHERE am.state = 'posted'
                  AND am.move_type IN ('out_invoice', 'out_refund')
                  AND am.company_id = %s
                  AND am.date BETWEEN pud.date_from AND pud.date_to
                  AND aml.display_type = 'product'
                  AND (%s IS NULL OR aml.product_id = %s)
                  AND (
                    %s IS NULL OR 
                    EXISTS (
                        SELECT 1 FROM product_public_category_product_template_rel ppcrel
                        WHERE ppcrel.product_template_id = pt.id
                          AND ppcrel.product_public_category_id = %s
                    )
                  )
                  AND (%s IS NULL OR %s IS NOT NULL OR pt.categ_id = %s)
                  {priority_cond}
            """.format(priority_cond=priority_condition)
            
            params = [
                plan.date_from,
                plan.date_to,
                plan.id,
                achievement.type,
                achievement.type,
                plan.company_id.id,
                achievement.product_id.id or None,
                achievement.product_id.id or None,
                achievement.public_categ_id.id or None,
                achievement.public_categ_id.id or None,
                achievement.product_categ_id.id or None,
                achievement.public_categ_id.id or None,
                achievement.product_categ_id.id or None,
            ]
            
            # Agregar parámetros de prioridad si existen
            params.extend(priority_params)
            
            cr.execute(query, params)
            result = cr.fetchone()
            return result[0] if result else 0.0
        
        return 0.0

    @api.depends('plan_id', 'type', 'product_id', 'product_categ_id', 'public_categ_id', 
                 'plan_id.date_from', 'plan_id.date_to')
    def _compute_actual_amount(self):
        """
        Calcula el monto real alcanzado en ventas o facturas según el tipo de logro.
        
        Este método usa consultas SQL optimizadas con CTEs (Common Table Expressions) para
        calcular eficientemente el monto alcanzado considerando:
        - Tipo de logro (amount_sold, qty_sold, amount_invoiced, qty_invoiced)
        - Filtros de producto y categoría
        - Rango de fechas del plan
        - Lógica de categoría prioritaria (de parámetros de configuración)
        
        IMPORTANTE - Dependencia de Parámetros de Configuración:
        Este método lee el parámetro 'mandatory_category_id' mediante _get_priority_category_safely().
        Como @api.depends no puede detectar cambios en ir.config_parameter, el campo usa
        store=False para asegurar que se recalcula en cada acceso, reflejando siempre la
        configuración actual del sistema.
        
        Para forzar recálculo después de cambiar parámetros de configuración, se puede:
        1. Recargar la vista (F5) - el campo se recalculará automáticamente
        2. Invalidar caché: self.env['sale.commission.plan.achievement'].invalidate_cache()
        
        Returns:
            None: Actualiza el campo actual_amount de cada registro con el monto calculado.
            
        Optimización:
        Usa SQL directo con CTEs en lugar de iteración Python para procesar miles de
        transacciones de forma eficiente (100-1000x más rápido que ORM puro).
        """
        # Obtener la categoría prioritaria una sola vez para todos los achievements
        # NOTA: Este valor proviene de ir.config_parameter y puede cambiar sin disparar depends
        priority_category = self._get_priority_category_safely()
        priority_category_id = priority_category.id if priority_category else None
        
        for achievement in self:
            # Si el achievement no tiene plan o no está configurado completamente, retornar 0
            if not achievement.plan_id or not achievement.type:
                achievement.actual_amount = 0.0
                continue
            
            # Si el plan no tiene fechas, no se puede calcular
            if not achievement.plan_id.date_from or not achievement.plan_id.date_to:
                achievement.actual_amount = 0.0
                continue
            
            # Usar savepoint para aislar posibles errores SQL sin afectar la transacción principal
            # SEGURIDAD: Usar nombre estático para savepoint en lugar de incluir IDs dinámicos
            savepoint_name = 'compute_actual_amount_savepoint'
            try:
                self.env.cr.execute('SAVEPOINT ' + savepoint_name)
                # Usar método SQL optimizado en lugar de iteración Python
                achievement.actual_amount = self._compute_actual_amount_sql(achievement, priority_category_id)
                self.env.cr.execute('RELEASE SAVEPOINT ' + savepoint_name)
            except Exception as e:
                # Rollback al savepoint sin afectar la transacción principal
                self.env.cr.execute('ROLLBACK TO SAVEPOINT ' + savepoint_name)
                _logger.error(
                    "Error al calcular actual_amount para achievement %s (tipo: %s, plan: %s): %s. "
                    "El achievement se establecerá en 0.0",
                    achievement.id, achievement.type, achievement.plan_id.name if achievement.plan_id else 'N/A', 
                    e, exc_info=True
                )
                # Asignar 0 en caso de error para no romper la UI
                achievement.actual_amount = 0.0

    @api.depends('actual_amount', 'target_amount')
    def _compute_achievement_percentage(self):
        """
        Calcula el porcentaje alcanzado respecto al monto objetivo.
        
        Calcula la relación porcentual entre el monto real alcanzado (actual_amount)
        y el monto objetivo definido (target_amount), permitiendo visualizar de forma
        clara el progreso hacia el cumplimiento del objetivo.
        
        Fórmula: (actual_amount / target_amount) * 100
        
        Args:
            self: Recordset de sale.commission.plan.achievement
            
        Returns:
            None: Actualiza el campo achievement_percentage de cada registro.
            
        Ejemplos:
            - actual_amount=75,000, target_amount=100,000 → 75.0%
            - actual_amount=120,000, target_amount=100,000 → 120.0%
            - target_amount=0 o None → 0.0%
        """
        for achievement in self:
            if achievement.target_amount and achievement.target_amount > 0:
                achievement.achievement_percentage = (achievement.actual_amount / achievement.target_amount) * 100
            else:
                achievement.achievement_percentage = 0.0

