# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nCoNationality(models.Model):
    _name = 'l10n_co.nationality'
    _description = 'Nacionalidad (Colombia)'
    _order = 'code'
    _rec_name = 'display_name_complete'
    
    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        copy=False,
        help='Código de la nacionalidad'
    )
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
        help='Nombre de la nacionalidad'
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si la nacionalidad está activa'
    )
    
    display_name_complete = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name_complete',
        store=True
    )
    
    @api.depends('name', 'code')
    def _compute_display_name_complete(self):
        for nationality in self:
            if nationality.name and nationality.code:
                nationality.display_name_complete = f"{nationality.code} - {nationality.name}"
            elif nationality.code:
                nationality.display_name_complete = nationality.code
            else:
                nationality.display_name_complete = nationality.name or ''
    
    @api.constrains('code')
    def _check_code_unique(self):
        for nationality in self:
            if nationality.code:
                existing = self.search([
                    ('code', '=', nationality.code),
                    ('id', '!=', nationality.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        _('El código "%s" ya existe. El código de nacionalidad debe ser único.') % nationality.code
                    )

