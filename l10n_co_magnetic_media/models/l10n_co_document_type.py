# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nCoDocumentType(models.Model):
    """
    Modelo para gestionar los Tipos de Documento de Colombia.
    
    Este modelo almacena los diferentes tipos de documento de identificación
    definidos por la DIAN para la clasificación de personas y entidades.
    """
    _name = 'l10n_co.document.type'
    _description = 'Tipo de Documento Colombia'
    _order = 'sequence, code'
    
    # Campos básicos
    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        help='Código numérico del tipo de documento (11, 12, 13, etc.)'
    )
    
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
        help='Nombre descriptivo del tipo de documento'
    )
    
    document_code = fields.Char(
        string='Código Documento',
        help='Código corto del documento (RC, TI, CC, CE, NIT, PA, PEP, PPT)'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de visualización en listas'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está inactivo, no se mostrará en las selecciones'
    )
    
    # Campo computado para mostrar información completa
    display_name_complete = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name_complete',
        store=True
    )
    
    @api.depends('code', 'name', 'document_code')
    def _compute_display_name_complete(self):
        """Calcula el nombre completo con código y nombre"""
        for doc_type in self:
            parts = []
            if doc_type.code:
                parts.append(f"[{doc_type.code}]")
            if doc_type.name:
                parts.append(doc_type.name)
            if doc_type.document_code:
                parts.append(f"({doc_type.document_code})")
            
            doc_type.display_name_complete = ' '.join(parts) if parts else ''
    
    # Constraint Python para código único (Odoo 19 best practice)
    @api.constrains('code')
    def _check_code_unique(self):
        """Verifica que el código sea único"""
        for doc_type in self:
            if doc_type.code:
                existing = self.search([
                    ('code', '=', doc_type.code),
                    ('id', '!=', doc_type.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        _('El código "%s" ya existe. El código del tipo de documento debe ser único.') % doc_type.code
                    )

