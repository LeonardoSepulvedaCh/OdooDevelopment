{
    "name": "Cartera - Cupo de credito",
    "version": "1.0",
    "category": "Milan/Cartera",
    "summary": "Modulo para gestionar el cupo de credito de los clientes.",
    "description": """
    Este módulo permite gestionar el cupo de credito de los clientes, donde se cargara la información necesaria para la gestion del cupo de credito.
    """,
    "author": "@LeonardoSepulvedaCh",
    "license": "OPL-1",
    "depends": ["sale", "contacts", "mail", "contacts_birthday_alert", "documents"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/sale_credit_quota_document_wizard_views.xml",
        "views/sale_credit_quota_views.xml",
        "views/sale_credit_quota_menu.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}