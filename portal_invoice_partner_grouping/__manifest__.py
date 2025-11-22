# -*- coding: utf-8 -*-
{
    'name': 'Portal Invoice Partner Grouping',
    'version': '1.0.0',
    'category': 'Rutavity/Accounting',
    'summary': 'Agrupa las facturas del portal por contacto de empresa (B2B)',
    'description': """
        Portal Invoice Partner Grouping
        ================================
        
        Este módulo extiende la vista del portal de facturas (/my/invoices) para 
        agrupar visualmente las facturas por partner_id en escenarios B2B.
        
        Características:
        ----------------
        * Agrupación visual por contacto/empresa
        * Compatible con paginación, filtros y ordenamiento
        
    """,
    'author': 'Rutavity',
    'website': 'https://www.rutavity.com',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'portal',
    ],
    'data': [
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_invoice_partner_grouping/static/src/scss/portal_styles.scss',
            'portal_invoice_partner_grouping/static/src/js/grouped_invoice_selection.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}

