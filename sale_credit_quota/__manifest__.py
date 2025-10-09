{
    "name": "Cartera - Cupo de credito",
    "version": "1.0.0",
    "category": "Rutavity/Cartera",
    "summary": "Modulo para gestionar el cupo de credito de los clientes.",
    "description": """
    Este módulo permite gestionar el cupo de credito de los clientes, donde se cargara la información necesaria para la gestion del cupo de credito.
    """,
    "author": "@LeonardoSepulvedaCh",
    "license": "OPL-1",
    "depends": ["sale", "contacts", "mail", "contacts_birthday_alert", "documents", "account"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "wizards/sale_credit_quota_document_wizard_views.xml",
        "views/sale_credit_quota_views.xml",
        "views/sale_credit_quota_menu.xml",
        "views/res_partner_views.xml",
        "views/res_users_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}