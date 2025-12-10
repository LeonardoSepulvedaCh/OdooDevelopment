# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nCoForeignType(models.Model):
    _name = 'l10n_co.foreign.type'
    _description = 'Tipo de Extranjero (Colombia)'
    _order = 'code'
    _rec_name = 'display_name_complete'
    
    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        copy=False,
        help='Código del tipo de extranjero'
    )
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
        help='Nombre del tipo de extranjero'
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si el tipo de extranjero está activo'
    )
    
    display_name_complete = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name_complete',
        store=True
    )
    
    @api.depends('name', 'code')
    def _compute_display_name_complete(self):
        for foreign_type in self:
            if foreign_type.name and foreign_type.code:
                foreign_type.display_name_complete = f"{foreign_type.code} - {foreign_type.name}"
            elif foreign_type.code:
                foreign_type.display_name_complete = foreign_type.code
            else:
                foreign_type.display_name_complete = foreign_type.name or ''
    
    @api.constrains('code')
    def _check_code_unique(self):
        for foreign_type in self:
            if foreign_type.code:
                existing = self.search([
                    ('code', '=', foreign_type.code),
                    ('id', '!=', foreign_type.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        _('El código "%s" ya existe. El código del tipo de extranjero debe ser único.') % foreign_type.code
                    )

