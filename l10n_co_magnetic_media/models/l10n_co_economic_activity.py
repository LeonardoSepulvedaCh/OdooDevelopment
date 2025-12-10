# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nCoEconomicActivity(models.Model):
    _name = 'l10n_co.economic.activity'
    _description = 'Actividad Económica (Colombia)'
    _order = 'sequence, code'
    _rec_name = 'display_name_complete'
    
    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        copy=False,
        help='Código CIIU de la actividad económica'
    )
    name = fields.Char(
        string='Descripción',
        required=True,
        translate=True,
        help='Descripción de la actividad económica'
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de visualización'
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si la actividad económica está activa'
    )
    
    display_name_complete = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name_complete',
        store=True
    )
    
    @api.depends('name', 'code')
    def _compute_display_name_complete(self):
        for activity in self:
            if activity.name and activity.code:
                activity.display_name_complete = f"[{activity.code}] {activity.name}"
            elif activity.code:
                activity.display_name_complete = activity.code
            else:
                activity.display_name_complete = activity.name or ''
    
    @api.constrains('code')
    def _check_code_unique(self):
        for activity in self:
            if activity.code:
                existing = self.search([
                    ('code', '=', activity.code),
                    ('id', '!=', activity.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        _('El código "%s" ya existe. El código de la actividad económica debe ser único.') % activity.code
                    )

