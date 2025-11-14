from odoo import models
import logging

_logger = logging.getLogger(__name__)


class SaleCommissionAchievementReport(models.Model):
    _inherit = "sale.commission.achievement.report"

    # Agregar el campo target_amount y public_categ_id a las reglas
    def _select_rules(self):
        base_rules = super()._select_rules()
        return base_rules + ", scpa.target_amount, scpa.public_categ_id"

    def _get_config_params_safely(self):
        """
        Obtiene y valida los parámetros de configuración de categoría obligatoria.

        Este método lee los parámetros del sistema relacionados con la categoría obligatoria:
        - mandatory_category_enabled: Si está habilitada la validación de categoría obligatoria
        - mandatory_category_id: ID de la categoría obligatoria
        - mandatory_category_percentage: Porcentaje mínimo que debe alcanzarse (0-100)

        Todos los valores son validados y sanitizados antes de retornarlos. En caso de error,
        se retornan valores seguros por defecto.

        Returns:
            dict: Diccionario con las siguientes claves:
                - mandatory_enabled (bool): Si está habilitada la validación
                - mandatory_category_id (int|None): ID validado de la categoría obligatoria
                - priority_category_id (int|None): Alias del mandatory_category_id
                - mandatory_percentage (float): Porcentaje normalizado (0.0-1.0)
        """
        try:
            IrConfigParam = self.env["ir.config_parameter"].sudo()

            # Obtener parámetros de configuración
            mandatory_enabled_str = IrConfigParam.get_param(
                "sale_commission_achievement_target.mandatory_category_enabled", "False"
            )
            mandatory_category_id_str = IrConfigParam.get_param(
                "sale_commission_achievement_target.mandatory_category_id", False
            )
            mandatory_percentage_str = IrConfigParam.get_param(
                "sale_commission_achievement_target.mandatory_category_percentage",
                "100",
            )

            # Validar y convertir con manejo de errores
            mandatory_enabled_bool = False
            try:
                mandatory_enabled_bool = str(mandatory_enabled_str).strip().lower() in (
                    "true",
                    "1",
                    "yes",
                )
            except (AttributeError, ValueError) as e:
                _logger.warning(
                    "Error al procesar mandatory_category_enabled: %s. Usando False por defecto.",
                    e,
                )

            # Validar mandatory_category_id - debe ser un entero válido
            mandatory_category_id_int = None
            priority_category_id = None
            if mandatory_category_id_str:
                try:
                    # Limpiar y validar que sea un entero válido
                    cleaned_id = str(mandatory_category_id_str).strip()
                    if cleaned_id.isdigit() and int(cleaned_id) > 0:
                        mandatory_category_id_int = int(cleaned_id)
                        priority_category_id = mandatory_category_id_int

                        # Verificar que la categoría existe en la BD
                        category_exists = (
                            self.env["product.public.category"]
                            .sudo()
                            .search_count([("id", "=", mandatory_category_id_int)])
                        )
                        if not category_exists:
                            _logger.warning(
                                "La categoría obligatoria con ID %s no existe. Se ignorará la configuración.",
                                mandatory_category_id_int,
                            )
                            mandatory_category_id_int = None
                            priority_category_id = None
                    else:
                        _logger.warning(
                            "El ID de categoría obligatoria '%s' no es válido. Debe ser un entero positivo.",
                            cleaned_id,
                        )
                except (AttributeError, ValueError, TypeError) as e:
                    _logger.warning(
                        "Error al procesar mandatory_category_id '%s': %s. Se ignorará la configuración.",
                        mandatory_category_id_str,
                        e,
                    )

            # Validar mandatory_percentage - debe estar entre 0 y 100
            mandatory_percentage_float = 1.0
            if mandatory_percentage_str:
                try:
                    percentage_val = float(str(mandatory_percentage_str).strip())
                    if 0 <= percentage_val <= 100:
                        mandatory_percentage_float = percentage_val / 100.0
                    else:
                        _logger.warning(
                            "El porcentaje de categoría obligatoria %s está fuera de rango (0-100). Usando 100%%.",
                            percentage_val,
                        )
                except (AttributeError, ValueError, TypeError) as e:
                    _logger.warning(
                        "Error al procesar mandatory_category_percentage '%s': %s. Usando 100%% por defecto.",
                        mandatory_percentage_str,
                        e,
                    )

            return {
                "mandatory_enabled": mandatory_enabled_bool,
                "mandatory_category_id": mandatory_category_id_int,
                "priority_category_id": priority_category_id,
                "mandatory_percentage": mandatory_percentage_float,
            }

        except Exception as e:
            _logger.error(
                "Error crítico al obtener parámetros de configuración: %s",
                e,
                exc_info=True,
            )
            # Retornar valores seguros por defecto
            return {
                "mandatory_enabled": False,
                "mandatory_category_id": None,
                "priority_category_id": None,
                "mandatory_percentage": 1.0,
            }

    # Sobrescribir para agregar condición que verifica si se alcanzó el target_amount. Si no se alcanzó el objetivo, el rate será 0.
    # Además, valida si hay una categoría obligatoria y si el usuario cumplió con ella.
    # Implementa lógica de prioridad: productos en categoría obligatoria se contabilizan solo en esa categoría.
    def _rate_to_case(self, rates):
        is_sales = any("_sold" in rate for rate in rates)
        is_invoices = any("_invoiced" in rate for rate in rates)

        # Obtener parámetros de configuración de forma segura
        config_params = self._get_config_params_safely()
        mandatory_enabled_bool = config_params["mandatory_enabled"]
        mandatory_category_id_int = config_params["mandatory_category_id"]
        priority_category_id = config_params["priority_category_id"]
        mandatory_percentage_float = config_params["mandatory_percentage"]

        # Construir la condición de categoría obligatoria si está habilitada
        mandatory_check_sales = ""
        mandatory_check_invoices = ""

        if mandatory_enabled_bool and mandatory_category_id_int:
            # SEGURIDAD: Los IDs ya están validados como enteros positivos en _get_config_params_safely()
            # Usar conversión explícita a str() solo después de validación para evitar SQL injection
            # Validar nuevamente antes de construir SQL para máxima seguridad
            validated_mandatory_id = str(int(mandatory_category_id_int))
            validated_percentage = str(float(mandatory_percentage_float))

            # Construir exclusión de categoría prioritaria para la validación de categoría obligatoria
            priority_exclusion_mandatory = ""
            if (
                priority_category_id
                and mandatory_category_id_int != priority_category_id
            ):
                # Conversión explícita después de validación
                validated_priority_id = str(int(priority_category_id))
                priority_exclusion_mandatory = (
                    "\n                                  AND NOT EXISTS (\n"
                    "                                    SELECT 1 FROM product_public_category_product_template_rel ppcrel_priority_mand\n"
                    "                                    WHERE ppcrel_priority_mand.product_template_id = pt_check.id\n"
                    "                                      AND ppcrel_priority_mand.product_public_category_id = "
                    + validated_priority_id
                    + "\n"
                    "                                  )\n                                "
                )

            # Para ventas - construcción segura con validación explícita
            mandatory_check_sales = (
                "\n                        -- Validación de categoría obligatoria\n"
                "                        WHEN " + validated_mandatory_id + " NOT IN (\n"
                "                            SELECT scpa_check.public_categ_id\n"
                "                            FROM sale_commission_plan_achievement scpa_check\n"
                "                            WHERE scpa_check.plan_id = scp.id\n"
                "                              AND scpa_check.public_categ_id = "
                + validated_mandatory_id
                + "\n"
                "                              AND scpa_check.target_amount > 0\n"
                "                              AND (\n"
                "                                SELECT COALESCE(SUM(sol_check.price_subtotal / fo_check.currency_rate), 0)\n"
                "                                FROM sale_order fo_check\n"
                "                                JOIN sale_order_line sol_check ON sol_check.order_id = fo_check.id\n"
                "                                LEFT JOIN product_product pp_check ON sol_check.product_id = pp_check.id\n"
                "                                LEFT JOIN product_template pt_check ON pp_check.product_tmpl_id = pt_check.id\n"
                "                                WHERE fo_check.user_id = scpu.user_id\n"
                "                                  AND fo_check.state = 'sale'\n"
                "                                  AND fo_check.company_id = scp.company_id\n"
                "                                  AND fo_check.date_order BETWEEN COALESCE(scpu.date_from, scp.date_from) AND COALESCE(scpu.date_to, scp.date_to)\n"
                "                                  AND EXISTS (\n"
                "                                    SELECT 1 FROM product_public_category_product_template_rel ppcrel\n"
                "                                    WHERE ppcrel.product_template_id = pt_check.id\n"
                "                                      AND ppcrel.product_public_category_id = "
                + validated_mandatory_id
                + "\n"
                "                                  )"
                + priority_exclusion_mandatory
                + "                                  AND sol_check.display_type IS NULL\n"
                "                                  AND COALESCE(sol_check.is_expense, false) = false\n"
                "                                  AND COALESCE(sol_check.is_downpayment, false) = false\n"
                "                              ) >= (scpa_check.target_amount * "
                + validated_percentage
                + ")\n"
                "                        ) THEN 0\n            "
            )

            # Para facturas - construcción segura con validación explícita
            mandatory_check_invoices = (
                "\n                        -- Validación de categoría obligatoria\n"
                "                        WHEN " + validated_mandatory_id + " NOT IN (\n"
                "                            SELECT scpa_check.public_categ_id\n"
                "                            FROM sale_commission_plan_achievement scpa_check\n"
                "                            WHERE scpa_check.plan_id = scp.id\n"
                "                              AND scpa_check.public_categ_id = "
                + validated_mandatory_id
                + "\n"
                "                              AND scpa_check.target_amount > 0\n"
                "                              AND (\n"
                "                                SELECT COALESCE(SUM(\n"
                "                                    CASE\n"
                "                                        WHEN fm_check.move_type = 'out_invoice' THEN aml_check.price_subtotal / fm_check.invoice_currency_rate\n"
                "                                        WHEN fm_check.move_type = 'out_refund' THEN -1 * aml_check.price_subtotal / fm_check.invoice_currency_rate\n"
                "                                        ELSE 0\n"
                "                                    END\n"
                "                                ), 0)\n"
                "                                FROM account_move fm_check\n"
                "                                JOIN account_move_line aml_check ON aml_check.move_id = fm_check.id\n"
                "                                LEFT JOIN product_product pp_check ON aml_check.product_id = pp_check.id\n"
                "                                LEFT JOIN product_template pt_check ON pp_check.product_tmpl_id = pt_check.id\n"
                "                                WHERE fm_check.invoice_user_id = scpu.user_id\n"
                "                                  AND fm_check.state = 'posted'\n"
                "                                  AND fm_check.move_type IN ('out_invoice', 'out_refund')\n"
                "                                  AND fm_check.company_id = scp.company_id\n"
                "                                  AND fm_check.date BETWEEN COALESCE(scpu.date_from, scp.date_from) AND COALESCE(scpu.date_to, scp.date_to)\n"
                "                                  AND EXISTS (\n"
                "                                    SELECT 1 FROM product_public_category_product_template_rel ppcrel\n"
                "                                    WHERE ppcrel.product_template_id = pt_check.id\n"
                "                                      AND ppcrel.product_public_category_id = "
                + validated_mandatory_id
                + "\n"
                "                                  )"
                + priority_exclusion_mandatory
                + "                                  AND aml_check.display_type = 'product'\n"
                "                              ) >= (scpa_check.target_amount * "
                + validated_percentage
                + ")\n"
                "                        ) THEN 0\n            "
            )

        if is_sales:
            # Construir la condición de exclusión de productos en categoría prioritaria
            priority_exclusion = ""
            if priority_category_id:
                # SEGURIDAD: Conversión explícita después de validación
                validated_priority_id = str(int(priority_category_id))
                priority_exclusion = (
                    "\n                              -- Lógica de prioridad: Si este achievement NO es categoría prioritaria, excluir productos que estén en categoría prioritaria\n"
                    "                              AND (\n"
                    "                                scpa.public_categ_id = "
                    + validated_priority_id
                    + " OR\n"
                    "                                NOT EXISTS (\n"
                    "                                    SELECT 1 FROM product_public_category_product_template_rel ppcrel_priority\n"
                    "                                    WHERE ppcrel_priority.product_template_id = pt_check.id\n"
                    "                                      AND ppcrel_priority.product_public_category_id = "
                    + validated_priority_id
                    + "\n"
                    "                                )\n"
                    "                              )\n                "
                )

            case_template = """
            CASE 
                WHEN scpa.type = '%%s' THEN
                    CASE%s
                        WHEN scpa.target_amount IS NULL OR scpa.target_amount = 0 THEN rate
                        WHEN (
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
                              AND (
                                scpa.public_categ_id IS NULL OR 
                                EXISTS (
                                    SELECT 1 FROM product_public_category_product_template_rel ppcrel
                                    WHERE ppcrel.product_template_id = pt_check.id
                                      AND ppcrel.product_public_category_id = scpa.public_categ_id
                                )
                              )
                              AND (scpa.product_categ_id IS NULL OR scpa.public_categ_id IS NOT NULL OR scpa.product_categ_id = pt_check.categ_id)%s
                              AND sol_check.display_type IS NULL
                              AND COALESCE(sol_check.is_expense, false) = false
                              AND COALESCE(sol_check.is_downpayment, false) = false
                        ) >= scpa.target_amount THEN rate
                        ELSE 0
                    END
                ELSE 0 
            END AS %%s
            """ % (
                mandatory_check_sales,
                priority_exclusion,
            )
        elif is_invoices:
            # Construir la condición de exclusión de productos en categoría prioritaria
            priority_exclusion_inv = ""
            if priority_category_id:
                # SEGURIDAD: Conversión explícita después de validación
                validated_priority_id_inv = str(int(priority_category_id))
                priority_exclusion_inv = (
                    "\n                              -- Lógica de prioridad: Si este achievement NO es categoría prioritaria, excluir productos que estén en categoría prioritaria\n"
                    "                              AND (\n"
                    "                                scpa.public_categ_id = "
                    + validated_priority_id_inv
                    + " OR\n"
                    "                                NOT EXISTS (\n"
                    "                                    SELECT 1 FROM product_public_category_product_template_rel ppcrel_priority\n"
                    "                                    WHERE ppcrel_priority.product_template_id = pt_check.id\n"
                    "                                      AND ppcrel_priority.product_public_category_id = "
                    + validated_priority_id_inv
                    + "\n"
                    "                                )\n"
                    "                              )\n                "
                )

            case_template = """
            CASE 
                WHEN scpa.type = '%%s' THEN
                    CASE%s
                        WHEN scpa.target_amount IS NULL OR scpa.target_amount = 0 THEN rate
                        WHEN (
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
                              AND (
                                scpa.public_categ_id IS NULL OR 
                                EXISTS (
                                    SELECT 1 FROM product_public_category_product_template_rel ppcrel
                                    WHERE ppcrel.product_template_id = pt_check.id
                                      AND ppcrel.product_public_category_id = scpa.public_categ_id
                                )
                              )
                              AND (scpa.product_categ_id IS NULL OR scpa.public_categ_id IS NOT NULL OR scpa.product_categ_id = pt_check.categ_id)%s
                              AND aml_check.display_type = 'product'
                        ) >= scpa.target_amount THEN rate
                        ELSE 0
                    END
                ELSE 0 
            END AS %%s
            """ % (
                mandatory_check_invoices,
                priority_exclusion_inv,
            )
        else:
            return super()._rate_to_case(rates)

        return ",\n".join(
            case_template % (rate_type, rate_type + "_rate") for rate_type in rates
        )
