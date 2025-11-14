from odoo import models, fields, _
import logging

_logger = logging.getLogger(__name__)


class SaleCommissionCollectionReport(models.Model):
    """
    Commission Report Based on Collections.

    This model generates a report of commissions earned based on payment reconciliations
    instead of invoices or sales. It calculates:
    - Base commission (0.7%) for on-time payments
    - Additional category-based commissions when targets are met
    - Validates mandatory promotion category requirements
    - Prorates partial payments across invoice products by category
    """

    _name = "sale.commission.collection.report"
    _description = "Commission Report Based on Collections"
    _auto = False
    _order = "payment_date desc, id desc"

    # ==== Identification Fields ====
    partial_reconcile_id = fields.Many2one(
        "account.partial.reconcile", string="Partial reconciliation", readonly=True
    )
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True)
    payment_id = fields.Many2one("account.payment", string="Payment", readonly=True)

    # ==== Plan and User Fields ====
    plan_id = fields.Many2one(
        "sale.commission.plan", string="Commission plan", readonly=True
    )
    user_id = fields.Many2one("res.users", string="Salesperson", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Customer", readonly=True)

    # ==== Amount Fields ====
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    collected_amount = fields.Monetary(
        string="Collected amount",
        currency_field="currency_id",
        readonly=True,
        help="Collected amount in this reconciliation prorated by category",
    )
    on_time_commission_amount = fields.Monetary(
        string="On-time commission",
        currency_field="currency_id",
        readonly=True,
        help="Commission if the payment was on time",
    )
    target_commission_amount = fields.Monetary(
        string="Target commission",
        currency_field="currency_id",
        readonly=True,
        help="Additional commission for achieving the target category",
    )
    total_commission = fields.Monetary(
        string="Total commission",
        currency_field="currency_id",
        readonly=True,
        help="Sum of on-time commission + target commission",
    )

    # ==== Category Fields ====
    public_categ_id = fields.Many2one(
        "product.public.category", string="Category", readonly=True
    )
    category_collected_amount = fields.Monetary(
        string="Collected amount by category",
        currency_field="currency_id",
        readonly=True,
        help="Total collected amount in this category (to validate targets)",
    )
    target_amount = fields.Monetary(
        string="Target amount",
        currency_field="currency_id",
        readonly=True,
        help="Target amount defined for this category in the plan",
    )
    target_achieved = fields.Boolean(
        string="Target achieved",
        readonly=True,
        help="Indicates if the target was achieved for this category",
    )
    commission_rate = fields.Float(
        string="Target commission rate",
        readonly=True,
        help="Commission rate for achieving the target category",
    )

    # ==== Date and Time Control Fields ====
    payment_date = fields.Date(string="Payment date", readonly=True)
    invoice_date_due = fields.Date(string="Original due date", readonly=True)
    effective_due_date = fields.Date(
        string="Effective due date",
        readonly=True,
        help="Effective due date + grace days",
    )
    is_on_time = fields.Boolean(
        string="On-time payment",
        readonly=True,
        help="Indicates if the payment was made before the effective due date",
    )

    # ==== Promotion Category Validation ====
    promotion_requirement_met = fields.Boolean(
        string="Promotion requirement met",
        readonly=True,
        help="Indicates if the promotion requirement was met (mandatory)",
    )

    @property
    def _table_query(self):
        """
        Generate the SQL query for the virtual table.

        This property returns the complete SQL query that defines the structure
        and data of this report model. Uses CTEs for better performance and
        readability.

        Returns:
            str: SQL query as string
        """
        return self._get_collection_commission_query()

    def _get_collection_commission_query(self):
        """
        Build the complete SQL query for commission calculations based on collections.

        The query uses Common Table Expressions (CTEs) to:
        1. Get payment reconciliations with invoice data
        2. Calculate product weight distribution per invoice
        3. Categorize products by public category
        4. Calculate base on-time commission (parametrizable 0.7%)
        5. Validate category targets achievement
        6. Validate mandatory promotion category requirement
        7. Calculate final commissions

        Returns:
            str: Complete SQL query as string
        """
        IrConfigParam = self.env["ir.config_parameter"].sudo()

        # Get configuration parameters
        on_time_rate_str = IrConfigParam.get_param(
            "sale_commission_achievement_target.on_time_commission_rate", "0.007"
        )
        grace_days_str = IrConfigParam.get_param(
            "sale_commission_achievement_target.collection_grace_days", "7"
        )

        try:
            on_time_rate = float(on_time_rate_str)
            if on_time_rate < 0 or on_time_rate > 1:
                _logger.warning(
                    "On-time commission rate %s is out of range (0-1), using 0.007",
                    on_time_rate,
                )
                on_time_rate = 0.007
        except (ValueError, TypeError) as e:
            _logger.warning(
                "Invalid on-time commission rate '%s': %s. Using default 0.007",
                on_time_rate_str,
                e,
            )
            on_time_rate = 0.007

        try:
            grace_days = int(grace_days_str)
            if grace_days < 0:
                _logger.warning("Grace days %s is negative, using 0", grace_days)
                grace_days = 0
        except (ValueError, TypeError) as e:
            _logger.warning(
                "Invalid grace days '%s': %s. Using default 7", grace_days_str, e
            )
            grace_days = 7

        # Get mandatory category ID
        mandatory_category_id_str = IrConfigParam.get_param(
            "sale_commission_achievement_target.mandatory_category_id", False
        )

        mandatory_category_id = None
        if mandatory_category_id_str:
            try:
                cleaned_id = str(mandatory_category_id_str).strip()
                if cleaned_id.isdigit() and int(cleaned_id) > 0:
                    mandatory_category_id = int(cleaned_id)
                    # Verify category exists
                    category_exists = (
                        self.env["product.public.category"]
                        .sudo()
                        .search_count([("id", "=", mandatory_category_id)])
                    )
                    if not category_exists:
                        _logger.warning(
                            "Mandatory category ID %s does not exist. Ignoring.",
                            mandatory_category_id,
                        )
                        mandatory_category_id = None
            except (ValueError, TypeError) as e:
                _logger.warning(
                    "Invalid mandatory category ID '%s': %s. Ignoring.",
                    mandatory_category_id_str,
                    e,
                )

        # Build promotion validation SQL
        promotion_validation_sql = ""
        if mandatory_category_id:
            validated_mandatory_id = str(int(mandatory_category_id))
            promotion_validation_sql = f"""
                , promotion_category_validation AS (
                    SELECT
                        ca.plan_id,
                        ca.user_id,
                        BOOL_AND(
                            CASE
                                WHEN ca.public_categ_id = {validated_mandatory_id}
                                THEN ca.target_achieved
                                ELSE true
                            END
                        ) as promotion_requirement_met
                    FROM category_achievement ca
                    GROUP BY ca.plan_id, ca.user_id
                )
            """

        # Validated parameters for SQL
        validated_on_time_rate = str(float(on_time_rate))
        validated_grace_days = str(int(grace_days))

        query = (
            f"""
            WITH 
            -- Get active commission plans with their date ranges
            active_plans AS (
                SELECT
                    scp.id as plan_id,
                    scp.company_id,
                    scp.date_from,
                    scp.date_to,
                    scp.currency_id
                FROM sale_commission_plan scp
                WHERE scp.active = true
                  AND scp.state = 'approved'
                  AND scp.type = 'achieve'
            ),
            -- Get plan users with their specific date ranges
            plan_users AS (
                SELECT
                    scpu.plan_id,
                    scpu.user_id,
                    COALESCE(scpu.date_from, ap.date_from) as date_from,
                    COALESCE(scpu.date_to, ap.date_to) as date_to
                FROM sale_commission_plan_user scpu
                JOIN active_plans ap ON ap.plan_id = scpu.plan_id
            ),
            -- Get invoice details with effective due date
            invoice_details AS (
                SELECT
                    am.id as invoice_id,
                    am.invoice_user_id as user_id,
                    am.partner_id,
                    am.company_id,
                    rc.id as currency_id,
                    am.invoice_date_due,
                    -- Calculate effective due date: invoice_date_due + grace_days
                    am.invoice_date_due + INTERVAL '{validated_grace_days} days' as effective_due_date,
                    am.move_type,
                    am.state
                FROM account_move am
                JOIN res_company rcomp ON am.company_id = rcomp.id
                JOIN res_currency rc ON rcomp.currency_id = rc.id
                WHERE am.move_type IN ('out_invoice', 'out_refund')
                  AND am.state = 'posted'
            ),
            -- Get payment reconciliations with invoice and payment data
            -- Note: This assumes standard Odoo reconciliation pattern where:
            --   - Invoices (out_invoice): credit_move_id contains the receivable account line
            --   - Payments (inbound): debit_move_id contains the receivable account line
            --   - Credit notes (out_refund) are handled in the on_time_commission CTE
            -- For more complex scenarios (e.g., credit note reconciliations), consider using
            -- dynamic move identification based on account_type checks on both sides.
            payment_reconciliations AS (
                SELECT
                    apr.id as partial_reconcile_id,
                    apr.amount as reconcile_amount,
                    apr.company_id,
                    apr.debit_move_id,
                    apr.credit_move_id,
                    apr.max_date as payment_date,
                    payment_aml.move_id as payment_move_id,
                    invoice_aml.move_id as invoice_id,
                    invoice_aml.account_id
                FROM account_partial_reconcile apr
                JOIN account_move_line payment_aml ON apr.debit_move_id = payment_aml.id
                JOIN account_move_line invoice_aml ON apr.credit_move_id = invoice_aml.id
                JOIN account_account aa ON invoice_aml.account_id = aa.id
                WHERE aa.account_type = 'asset_receivable'
                  AND apr.amount > 0
            ),
            -- Calculate product weight distribution per invoice
            invoice_product_distribution AS (
                SELECT
                    aml.move_id as invoice_id,
                    aml.product_id,
                    pp.product_tmpl_id,
                    aml.price_subtotal,
                    SUM(aml.price_subtotal) OVER (PARTITION BY aml.move_id) as invoice_total,
                    CASE
                        WHEN SUM(aml.price_subtotal) OVER (PARTITION BY aml.move_id) = 0 THEN 0
                        ELSE aml.price_subtotal / NULLIF(SUM(aml.price_subtotal) OVER (PARTITION BY aml.move_id), 0)
                    END as product_weight
                FROM account_move_line aml
                JOIN product_product pp ON aml.product_id = pp.id
                WHERE aml.display_type = 'product'
                  AND aml.price_subtotal != 0
            ),
            -- Categorize products by public category
            product_categories AS (
                SELECT
                    ipd.invoice_id,
                    ipd.product_id,
                    ipd.product_tmpl_id,
                    ppcrel.product_public_category_id as public_categ_id,
                    ipd.product_weight,
                    ipd.price_subtotal
                FROM invoice_product_distribution ipd
                JOIN product_template pt ON ipd.product_tmpl_id = pt.id
                JOIN product_public_category_product_template_rel ppcrel 
                    ON pt.id = ppcrel.product_template_id
            ),
            -- Calculate on-time commission and prorate amounts by category
            on_time_commission AS (
                SELECT
                    pr.partial_reconcile_id,
                    inv.invoice_id,
                    pr.payment_move_id,
                    pr.payment_date,
                    inv.user_id,
                    inv.partner_id,
                    pr.company_id,
                    inv.invoice_date_due,
                    inv.effective_due_date,
                    pc.public_categ_id,
                    -- Prorate reconciled amount by product weight
                    CASE
                        WHEN inv.move_type = 'out_refund' THEN -1 * pr.reconcile_amount * pc.product_weight
                        ELSE pr.reconcile_amount * pc.product_weight
                    END as category_collected_amount,
                    -- Check if payment is on time
                    CASE
                        WHEN pr.payment_date <= inv.effective_due_date THEN true
                        ELSE false
                    END as is_on_time,
                    -- Calculate on-time commission (0.007)
                    CASE
                        WHEN pr.payment_date <= inv.effective_due_date THEN
                            CASE
                                WHEN inv.move_type = 'out_refund' THEN -1 * pr.reconcile_amount * pc.product_weight * {validated_on_time_rate}
                                ELSE pr.reconcile_amount * pc.product_weight * {validated_on_time_rate}
                            END
                        ELSE 0
                    END as on_time_commission
                FROM payment_reconciliations pr
                JOIN invoice_details inv ON pr.payment_move_id = inv.invoice_id
                JOIN product_categories pc ON pc.invoice_id = inv.invoice_id
            ),
            -- Aggregate collected amounts by user and category
            user_category_totals AS (
                SELECT
                    otc.user_id,
                    otc.public_categ_id,
                    otc.company_id,
                    SUM(otc.category_collected_amount) as total_collected
                FROM on_time_commission otc
                JOIN plan_users pu ON pu.user_id = otc.user_id
                WHERE otc.payment_date BETWEEN pu.date_from AND pu.date_to
                GROUP BY otc.user_id, otc.public_categ_id, otc.company_id
            ),
            -- Validate category targets achievement
            category_achievement AS (
                SELECT
                    scpa.plan_id,
                    scpa.public_categ_id,
                    scpa.target_amount,
                    scpa.rate as commission_rate,
                    pu.user_id,
                    COALESCE(uct.total_collected, 0) as total_collected,
                    CASE
                        WHEN COALESCE(uct.total_collected, 0) >= scpa.target_amount
                        THEN true
                        ELSE false
                    END as target_achieved
                FROM sale_commission_plan_achievement scpa
                JOIN active_plans ap ON ap.plan_id = scpa.plan_id
                JOIN plan_users pu ON pu.plan_id = ap.plan_id
                LEFT JOIN user_category_totals uct 
                    ON uct.user_id = pu.user_id 
                    AND uct.public_categ_id = scpa.public_categ_id
                    AND uct.company_id = ap.company_id
                WHERE scpa.public_categ_id IS NOT NULL
                  AND scpa.target_amount > 0
            ){promotion_validation_sql}
            -- Final commission calculation
            SELECT
                -- Generate unique ID
                (otc.partial_reconcile_id::bigint * 1000000 + 
                 COALESCE(otc.public_categ_id, 0)::bigint * 100 + 
                 COALESCE(pu.plan_id, 0)::bigint)::bigint as id,
                otc.partial_reconcile_id,
                otc.invoice_id,
                -- Get payment_id from payment move if it exists
                (SELECT ap.id FROM account_payment ap WHERE ap.move_id = otc.payment_move_id LIMIT 1) as payment_id,
                pu.plan_id,
                otc.user_id,
                otc.partner_id,
                otc.company_id,
                inv.currency_id,
                otc.category_collected_amount as collected_amount,
                otc.on_time_commission as on_time_commission_amount,
                -- Calculate target commission
                CASE
                    WHEN ca.target_achieved"""
            + (f" AND pcv.promotion_requirement_met" if mandatory_category_id else "")
            + f"""
                        AND otc.is_on_time = true
                    THEN otc.category_collected_amount * ca.commission_rate
                    ELSE 0
                END as target_commission_amount,
                -- Calculate total commission
                otc.on_time_commission + 
                CASE
                    WHEN ca.target_achieved"""
            + (f" AND pcv.promotion_requirement_met" if mandatory_category_id else "")
            + f"""
                        AND otc.is_on_time = true
                    THEN otc.category_collected_amount * ca.commission_rate
                    ELSE 0
                END as total_commission,
                otc.public_categ_id,
                COALESCE(uct.total_collected, 0) as category_collected_amount,
                COALESCE(ca.target_amount, 0) as target_amount,
                COALESCE(ca.target_achieved, false) as target_achieved,
                COALESCE(ca.commission_rate, 0) as commission_rate,
                otc.payment_date,
                otc.invoice_date_due,
                otc.effective_due_date,
                otc.is_on_time,
                """
            + (
                f"COALESCE(pcv.promotion_requirement_met, false)"
                if mandatory_category_id
                else "true"
            )
            + f""" as promotion_requirement_met
            FROM on_time_commission otc
            JOIN plan_users pu ON pu.user_id = otc.user_id
            JOIN invoice_details inv ON otc.invoice_id = inv.invoice_id
            LEFT JOIN category_achievement ca 
                ON ca.user_id = otc.user_id 
                AND ca.public_categ_id = otc.public_categ_id
                AND ca.plan_id = pu.plan_id
            LEFT JOIN user_category_totals uct
                ON uct.user_id = otc.user_id
                AND uct.public_categ_id = otc.public_categ_id
                AND uct.company_id = inv.company_id
            """
            + (
                f"LEFT JOIN promotion_category_validation pcv ON pcv.user_id = otc.user_id AND pcv.plan_id = pu.plan_id"
                if mandatory_category_id
                else ""
            )
            + f"""
            WHERE otc.payment_date BETWEEN pu.date_from AND pu.date_to
        """
        )

        return query

    def init(self):
        """
        Create database indexes for better performance.

        Creates indexes on key fields used in the query joins and filters.
        """
        self.env.cr.execute(
            """
            CREATE INDEX IF NOT EXISTS account_partial_reconcile_amount_idx 
            ON account_partial_reconcile (amount) WHERE amount > 0;
            
            CREATE INDEX IF NOT EXISTS account_move_line_reconcile_idx 
            ON account_move_line (move_id, account_id) WHERE reconciled = false;
        """
        )
        super().init()
