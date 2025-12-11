{
    "name": "Rutavity - Payment POS Store",
    "version": "1.0.0",
    "category": "Rutavity/Payment",
    "sequence": 350,
    "summary": "Enable payment in store (POS) for website orders",
    "description": """
        Payment POS Store
        =================
        This module allows customers to pay for their online orders at physical POS locations.
        
        Features:
        ---------
        * Payment method only available for POS customers
        * Validates customer has assigned POS configurations
        * Only works for sale orders (not invoices)
        * Shows available POS locations during checkout
        * Allows customers to add order comments
    """,
    "author": "Sebastián Rodríguez",
    "license": "LGPL-3",
    "depends": [
        "payment_rutavity",
        "website_sale",
        "pos_partner_visibility",
        "pos_sale",
    ],
    "data": [
        # Views
        "views/payment_rutavity_templates.xml",
        "views/sale_order_views.xml",
        # Data
        "data/payment_method_data.xml",
        "data/payment_provider_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "payment_pos_store/static/src/interactions/payment_form.js",
            "payment_pos_store/static/src/interactions/express_checkout.js",
        ],
        "point_of_sale._assets_pos": [
            "payment_pos_store/static/src/app/components/screens/product_screen/control_buttons/control_buttons.js",
        ],
    },
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
