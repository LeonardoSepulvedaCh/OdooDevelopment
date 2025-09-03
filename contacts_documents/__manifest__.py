{
    'name': 'Documentos en Contactos',
    'version': '18.5.0.0.1',
    'category': 'Milan/Contactos',
    'summary': 'Gestión de documentos asociados a contactos y empresas en Odoo',
    'description': '''
        Este módulo permite agregar documentos relacionados con contactos y empresas en Odoo, donde cada documento pertenece a una categoría.
        
        Características principales:
        - Gestión de tipos de documento (activos/inactivos)
        - Solo se muestran tipos de documento activos al crear documentos
        - Estados de aprobación para documentos (nuevo, aprobado, rechazado)
        - Integración completa con la vista de contactos
    ''',
    'author': '@LeonardoSecha',
    'license': 'OPL-1',
    'depends': ['base', 'contacts'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/document_type_data.xml',
        'views/contact_document_views.xml',
        'views/document_type_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}