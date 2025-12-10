# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nCoFiscalRegime(models.Model):
    _name = 'l10n_co.fiscal.regime'
    _description = 'Régimen Fiscal (Colombia - Facturación Electrónica)'
    _order = 'code'
    _rec_name = 'display_name_complete'
    
    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        copy=False,
        help='Código del régimen fiscal según DIAN'
    )
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
        help='Nombre del régimen fiscal'
    )
    vigencia_desde = fields.Date(
        string='Vigencia desde',
        help='Fecha desde la cual el régimen fiscal está vigente'
    )
    vigencia_hasta = fields.Date(
        string='Vigencia hasta',
        help='Fecha hasta la cual el régimen fiscal está vigente. Si está vacío, está activo indefinidamente.'
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si el régimen fiscal está activo'
    )
    
    display_name_complete = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name_complete',
        store=True
    )
    
    @api.depends('name', 'code')
    def _compute_display_name_complete(self):
        for fiscal_regime in self:
            if fiscal_regime.name and fiscal_regime.code:
                fiscal_regime.display_name_complete = f"[{fiscal_regime.code}] {fiscal_regime.name}"
            elif fiscal_regime.code:
                fiscal_regime.display_name_complete = fiscal_regime.code
            else:
                fiscal_regime.display_name_complete = fiscal_regime.name or ''
    
    @api.constrains('code')
    def _check_code_unique(self):
        for fiscal_regime in self:
            if fiscal_regime.code:
                existing = self.search([
                    ('code', '=', fiscal_regime.code),
                    ('id', '!=', fiscal_regime.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        _('El código "%s" ya existe. El código del régimen fiscal debe ser único.') % fiscal_regime.code
                    )
    
    @api.constrains('vigencia_desde', 'vigencia_hasta')
    def _check_vigencia_dates(self):
        """Valida que la fecha de vigencia hasta sea mayor que la fecha de vigencia desde"""
        for fiscal_regime in self:
            if fiscal_regime.vigencia_desde and fiscal_regime.vigencia_hasta:
                if fiscal_regime.vigencia_hasta < fiscal_regime.vigencia_desde:
                    raise ValidationError(
                        _('La fecha "Vigencia hasta" debe ser mayor o igual a la fecha "Vigencia desde".')
                    )

