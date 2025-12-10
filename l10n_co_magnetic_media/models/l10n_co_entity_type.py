# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nCoEntityType(models.Model):
    _name = 'l10n_co.entity.type'
    _description = 'Tipo de Entidad (Colombia)'
    _order = 'code'
    _rec_name = 'display_name_complete'
    
    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        copy=False,
        help='Código del tipo de entidad (1=Natural, 2=Jurídico)'
    )
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
        help='Nombre del tipo de entidad'
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si el tipo de entidad está activo'
    )
    
    display_name_complete = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name_complete',
        store=True
    )
    
    @api.depends('name', 'code')
    def _compute_display_name_complete(self):
        for entity_type in self:
            if entity_type.name and entity_type.code:
                entity_type.display_name_complete = f"{entity_type.code} - {entity_type.name}"
            elif entity_type.code:
                entity_type.display_name_complete = entity_type.code
            else:
                entity_type.display_name_complete = entity_type.name or ''
    
    @api.constrains('code')
    def _check_code_unique(self):
        for entity_type in self:
            if entity_type.code:
                existing = self.search([
                    ('code', '=', entity_type.code),
                    ('id', '!=', entity_type.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        _('El código "%s" ya existe. El código del tipo de entidad debe ser único.') % entity_type.code
                    )

