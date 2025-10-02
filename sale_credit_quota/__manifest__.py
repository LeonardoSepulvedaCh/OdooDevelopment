{
    "name": "Cartera - Cupo de credito",
    "version": "19.0.0.0.0",
    "category": "Milan/Cartera",
    "summary": "Modulo para gestionar el cupo de credito de los clientes.",
    "description": """
    Este módulo permite gestionar el cupo de credito de los clientes, donde se cargara la información necesaria para la gestion del cupo de credito.
    """,
    "author": "@LeonardoSepulvedaCh",
    "license": "OPL-1",
    "depends": ["sale", "contacts", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_credit_quota_views.xml",
        "views/sale_credit_quota_menu.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}