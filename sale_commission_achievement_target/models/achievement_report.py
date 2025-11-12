import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class SaleCommissionAchievementReport(models.Model):
    _inherit = 'sale.commission.achievement.report'

    def _create_temp_invoice_table(self, users=None, teams=None):
        """Override para agregar debug de los datos cargados"""
        result = super()._create_temp_invoice_table(users, teams)
        
        # Debug: Verificar qué datos se cargaron en la tabla temporal
        _logger.info("=== DEBUG TABLA TEMPORAL invoices_rules ===")
        
        # Primero verificar qué columnas existen
        self.env.cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'invoices_rules'
        """)
        columns = [row[0] for row in self.env.cr.fetchall()]
        _logger.info(f"Columnas disponibles en invoices_rules: {columns}")
        
        # Query ajustada solo con columnas de facturas
        self.env.cr.execute("""
            SELECT 
                plan_id,
                user_id,
                product_categ_id,
                target_amount,
                amount_invoiced_rate,
                qty_invoiced_rate
            FROM invoices_rules 
            WHERE target_amount IS NOT NULL AND target_amount > 0
            LIMIT 10
        """)
        rules_with_target = self.env.cr.fetchall()
        _logger.info(f"Reglas con target_amount > 0: {rules_with_target}")
        _logger.info(f"Formato: (plan_id, user_id, product_categ_id, target_amount, amount_invoiced_rate, qty_invoiced_rate)")
        
        # Debug: Ver TODAS las reglas
        self.env.cr.execute("""
            SELECT 
                plan_id,
                user_id,
                product_categ_id,
                target_amount,
                amount_invoiced_rate,
                qty_invoiced_rate
            FROM invoices_rules 
            LIMIT 20
        """)
        all_rules = self.env.cr.fetchall()
        _logger.info(f"Todas las reglas (primeras 20): {all_rules}")
        
        return result

    def _select_rules(self):
        """Agregar el campo target_amount a las reglas"""
        base_rules = super()._select_rules()
        result = base_rules + ", scpa.target_amount"
        _logger.info("=== SALE COMMISSION TARGET DEBUG ===")
        _logger.info(f"_select_rules result: {result}")
        return result

    def _rate_to_case(self, rates):
        """
        Sobrescribir para agregar condición que verifica si se alcanzó el target_amount.
        Si no se alcanzó el objetivo, el rate será 0.
        Además, valida si hay una categoría obligatoria y si el usuario cumplió con ella.
        """
        _logger.info("=== RATE TO CASE DEBUG ===")
        _logger.info(f"Rates recibidos: {rates}")
        
        # Determinar si estamos procesando ventas o facturas basándonos en los tipos de rates
        is_sales = any('_sold' in rate for rate in rates)
        is_invoices = any('_invoiced' in rate for rate in rates)
        
        _logger.info(f"is_sales: {is_sales}, is_invoices: {is_invoices}")
        
        # Obtener configuración de categoría obligatoria desde parámetros del sistema
        mandatory_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'sale_commission_achievement_target.mandatory_category_enabled', 'False'
        )
        mandatory_category_id = self.env['ir.config_parameter'].sudo().get_param(
            'sale_commission_achievement_target.mandatory_category_id', False
        )
        
        # Convertir a valores apropiados
        mandatory_enabled_bool = mandatory_enabled == 'True'
        mandatory_category_id_int = int(mandatory_category_id) if mandatory_category_id and mandatory_category_id.isdigit() else None
        
        _logger.info(f"Categoría obligatoria habilitada: {mandatory_enabled_bool}")
        _logger.info(f"ID categoría obligatoria: {mandatory_category_id_int}")
        
        # Obtener el ID de la moneda de la compañía actual para conversiones
        company_currency_id = self.env.company.currency_id.id
        
        # Construir la condición de categoría obligatoria si está habilitada
        mandatory_check_sales = ""
        mandatory_check_invoices = ""
        
        if mandatory_enabled_bool and mandatory_category_id_int:
            # Para ventas
            mandatory_check_sales = f"""
                        -- Validación de categoría obligatoria
                        WHEN {mandatory_category_id_int} NOT IN (
                            SELECT scpa_check.product_categ_id
                            FROM sale_commission_plan_achievement scpa_check
                            WHERE scpa_check.plan_id = scp.id
                              AND scpa_check.product_categ_id = {mandatory_category_id_int}
                              AND scpa_check.target_amount > 0
                              AND (
                                SELECT COALESCE(SUM(sol_check.price_subtotal / fo_check.currency_rate), 0)
                                FROM sale_order fo_check
                                JOIN sale_order_line sol_check ON sol_check.order_id = fo_check.id
                                LEFT JOIN product_product pp_check ON sol_check.product_id = pp_check.id
                                LEFT JOIN product_template pt_check ON pp_check.product_tmpl_id = pt_check.id
                                WHERE fo_check.user_id = scpu.user_id
                                  AND fo_check.state = 'sale'
                                  AND fo_check.company_id = scp.company_id
                                  AND fo_check.date_order BETWEEN COALESCE(scpu.date_from, scp.date_from) AND COALESCE(scpu.date_to, scp.date_to)
                                  AND pt_check.categ_id = {mandatory_category_id_int}
                                  AND sol_check.display_type IS NULL
                                  AND COALESCE(sol_check.is_expense, false) = false
                                  AND COALESCE(sol_check.is_downpayment, false) = false
                              ) >= scpa_check.target_amount
                        ) THEN 0
            """
            
            # Para facturas
            mandatory_check_invoices = f"""
                        -- Validación de categoría obligatoria
                        WHEN {mandatory_category_id_int} NOT IN (
                            SELECT scpa_check.product_categ_id
                            FROM sale_commission_plan_achievement scpa_check
                            WHERE scpa_check.plan_id = scp.id
                              AND scpa_check.product_categ_id = {mandatory_category_id_int}
                              AND scpa_check.target_amount > 0
                              AND (
                                SELECT COALESCE(SUM(
                                    CASE
                                        WHEN fm_check.move_type = 'out_invoice' THEN aml_check.price_subtotal / fm_check.invoice_currency_rate
                                        WHEN fm_check.move_type = 'out_refund' THEN -1 * aml_check.price_subtotal / fm_check.invoice_currency_rate
                                        ELSE 0
                                    END
                                ), 0)
                                FROM account_move fm_check
                                JOIN account_move_line aml_check ON aml_check.move_id = fm_check.id
                                LEFT JOIN product_product pp_check ON aml_check.product_id = pp_check.id
                                LEFT JOIN product_template pt_check ON pp_check.product_tmpl_id = pt_check.id
                                WHERE fm_check.invoice_user_id = scpu.user_id
                                  AND fm_check.state = 'posted'
                                  AND fm_check.move_type IN ('out_invoice', 'out_refund')
                                  AND fm_check.company_id = scp.company_id
                                  AND fm_check.date BETWEEN COALESCE(scpu.date_from, scp.date_from) AND COALESCE(scpu.date_to, scp.date_to)
                                  AND pt_check.categ_id = {mandatory_category_id_int}
                                  AND aml_check.display_type = 'product'
                              ) >= scpa_check.target_amount
                        ) THEN 0
            """
        
        if is_sales:
            # Para ventas (sale orders)
            _logger.info("Generando CASE template para VENTAS con validación de target_amount")
            case_template = f"""
            -- DEBUG: Validación de target_amount para ventas
            CASE 
                WHEN scpa.type = '%s' THEN
                    CASE{mandatory_check_sales}
                        -- Si no hay target_amount, aplicar rate normal
                        WHEN scpa.target_amount IS NULL OR scpa.target_amount = 0 THEN rate
                        -- Si hay target_amount, verificar que se alcanzó
                        WHEN (
                            -- DEBUG: Calculando monto total vendido por usuario/categoría
                            SELECT COALESCE(SUM(
                                sol_check.price_subtotal / fo_check.currency_rate
                            ), 0)
                            FROM sale_order fo_check
                            JOIN sale_order_line sol_check ON sol_check.order_id = fo_check.id
                            LEFT JOIN product_product pp_check ON sol_check.product_id = pp_check.id
                            LEFT JOIN product_template pt_check ON pp_check.product_tmpl_id = pt_check.id
                            WHERE fo_check.user_id = scpu.user_id
                              AND fo_check.state = 'sale'
                              AND fo_check.company_id = scp.company_id
                              AND fo_check.date_order BETWEEN COALESCE(scpu.date_from, scp.date_from) AND COALESCE(scpu.date_to, scp.date_to)
                              AND (scpa.product_id IS NULL OR scpa.product_id = sol_check.product_id)
                              AND (scpa.product_categ_id IS NULL OR scpa.product_categ_id = pt_check.categ_id)
                              AND sol_check.display_type IS NULL
                              AND COALESCE(sol_check.is_expense, false) = false
                              AND COALESCE(sol_check.is_downpayment, false) = false
                        ) >= scpa.target_amount THEN rate
                        -- Si no alcanzó el target_amount, rate = 0
                        ELSE 0
                    END
                ELSE 0 
            END AS %s
            """
        elif is_invoices:
            # Para facturas (invoices)
            _logger.info("Generando CASE template para FACTURAS con validación de target_amount")
            case_template = f"""
            -- DEBUG: Validación de target_amount para facturas
            CASE 
                WHEN scpa.type = '%s' THEN
                    CASE{mandatory_check_invoices}
                        -- Si no hay target_amount, aplicar rate normal
                        WHEN scpa.target_amount IS NULL OR scpa.target_amount = 0 THEN rate
                        -- Si hay target_amount, verificar que se alcanzó
                        WHEN (
                            -- DEBUG: Calculando monto total facturado por usuario/categoría
                            SELECT COALESCE(SUM(
                                CASE
                                    WHEN fm_check.move_type = 'out_invoice' THEN aml_check.price_subtotal / fm_check.invoice_currency_rate
                                    WHEN fm_check.move_type = 'out_refund' THEN -1 * aml_check.price_subtotal / fm_check.invoice_currency_rate
                                    ELSE 0
                                END
                            ), 0)
                            FROM account_move fm_check
                            JOIN account_move_line aml_check ON aml_check.move_id = fm_check.id
                            LEFT JOIN product_product pp_check ON aml_check.product_id = pp_check.id
                            LEFT JOIN product_template pt_check ON pp_check.product_tmpl_id = pt_check.id
                            WHERE fm_check.invoice_user_id = scpu.user_id
                              AND fm_check.state = 'posted'
                              AND fm_check.move_type IN ('out_invoice', 'out_refund')
                              AND fm_check.company_id = scp.company_id
                              AND fm_check.date BETWEEN COALESCE(scpu.date_from, scp.date_from) AND COALESCE(scpu.date_to, scp.date_to)
                              AND (scpa.product_id IS NULL OR scpa.product_id = aml_check.product_id)
                              AND (scpa.product_categ_id IS NULL OR scpa.product_categ_id = pt_check.categ_id)
                              AND aml_check.display_type = 'product'
                        ) >= scpa.target_amount THEN rate
                        -- Si no alcanzó el target_amount, rate = 0
                        ELSE 0
                    END
                ELSE 0 
            END AS %s
            """
        else:
            # Caso por defecto (usar el método original)
            _logger.info("Usando método padre (sin validación de target_amount)")
            return super()._rate_to_case(rates)
        
        result = ",\n".join(case_template % (rate_type, rate_type + '_rate') for rate_type in rates)
        _logger.info("=== SQL CASE GENERADO ===")
        _logger.info(result)
        _logger.info("=== FIN SQL CASE ===")
        return result

