{
    "name": "Multiple Early Payment Discounts",
    "version": "1.0.0",
    "category": "Rutavity/Payment Terms",
    "author": "Miller Contreras",
    "summary": "Support for multiple early payment discounts in payment terms",
    "description": """
        This module extends the default payment terms to support multiple early payment discounts.
        It allows defining multiple discount percentages based on different payment timeframes.
    """,
    "depends": ["account", "account_epd_partial_payment"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_payment_term_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
