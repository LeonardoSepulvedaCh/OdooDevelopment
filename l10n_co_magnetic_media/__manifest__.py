# -*- coding: utf-8 -*-
{
    'name': 'Colombia - Medios Magnéticos',
    'version': '1.0.0',
    'category': 'Rutavity/Localization',
    'summary': 'Gestión de Medios Magnéticos e Informes de Exógenas para Colombia',
    'description': """
        Medios Magnéticos - Localización Colombiana
        ============================================
        
        Este módulo extiende la funcionalidad de contactos para gestionar
        la información requerida en los reportes de Medios Magnéticos
        (Informes de Exógenas) según normativa DIAN de Colombia.
        
        Características principales:
        ----------------------------
        - Reorganización de campos tributarios en pestaña "Medios Magnéticos"
        - Integración con campos de nombres y apellidos separados
        - Preparado para agregar información tributaria colombiana
        - Compatible con multicompañía
        - Cumple con normativa DIAN
        
        Dependencias:
        -------------
        - contacts_name_split: Para gestión de nombres y apellidos separados
        - l10n_co: Localización colombiana base
        - l10n_latam_base: Base de localización LATAM
        
        Autor: john ramirez
        Versión: Odoo 19.0
    """,
    'author': 'john ramirez',
    'website': 'https://www.rutavity.com',
    'license': 'OPL-1',
    'depends': [
        'base',
        'contacts',
        'account',
        'l10n_co',
        'l10n_co_edi',
        'l10n_latam_base',
        'contacts_name_split',
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        
        # Datos
        'data/l10n_co_tax_regime_data.xml',
        'data/l10n_co_document_type_data.xml',
        'data/l10n_co_economic_activity_data.xml',
        'data/l10n_co_entity_type_data.xml',
        'data/l10n_co_nationality_data.xml',
        'data/l10n_co_foreign_type_data.xml',
        'data/l10n_co_fiscal_regime_data.xml',
        'data/l10n_co_discount_code_data.xml',
        
        # Vistas
        'views/l10n_co_tax_regime_views.xml',
        'views/l10n_co_document_type_views.xml',
        'views/l10n_co_economic_activity_views.xml',
        'views/l10n_co_entity_type_views.xml',
        'views/l10n_co_nationality_views.xml',
        'views/l10n_co_foreign_type_views.xml',
        'views/l10n_co_fiscal_regime_views.xml',
        'views/l10n_co_discount_code_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

