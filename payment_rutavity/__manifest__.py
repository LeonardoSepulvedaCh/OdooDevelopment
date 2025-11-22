{
    "name": "Rutavity - Payment Gateway",
    "version": "1.0.0",
    "category": "Rutavity/Payment",
    "sequence": 350,
    "summary": "Rutavity Payment Gateway",
    "description": "Rutavity payment gateway that supports PSE (Pagos Seguros en Línea) method.",
    "author": "Sebastián Rodríguez",
    "depends": [
        "website_sale",
        "payment",
        "account_payment",
        "contacts_name_split",
        "portal_invoice_partner_grouping",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        # Views
        "views/payment_rutavity_templates.xml",
        "views/payment_provider_views.xml",
        "views/payment_transaction_views.xml",
        "views/invoice_portal_templates.xml",
        "views/account_portal_templates.xml",
        "views/portal_templates.xml",
        # Data
        "data/payment_provider_data.xml",
        "data/payment_method_data.xml",
        "data/payment_cron.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "payment_rutavity/static/src/interactions/payment_form.js",
            "payment_rutavity/static/src/interactions/invoice_portal_bulk_selection.js",
            "payment_rutavity/static/src/interactions/invoice_payment_overdue.js",
            "payment_rutavity/static/src/interactions/invoice_search.js",
            "payment_rutavity/static/src/scss/invoice_portal_bulk_selection.scss",
            "payment_rutavity/static/src/scss/invoice_payment_overdue.scss",
        ],
    },
    "images": ["static/description/icon.png"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "license": "LGPL-3",
    "installable": True,
    "external_dependencies": {"python": ["requests"]},
}
