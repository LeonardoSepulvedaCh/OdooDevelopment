# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nCoDiscountCode(models.Model):
    _name = 'l10n_co.discount.code'
    _description = 'Código de Descuento (Colombia - Medios Magnéticos)'
    _order = 'code'
    _rec_name = 'display_name_complete'
    
    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        copy=False,
        help='Código del tipo de descuento según clasificación DIAN'
    )
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
        help='Descripción del tipo de descuento'
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si el código de descuento está activo'
    )
    
    display_name_complete = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name_complete',
        store=True
    )
    
    @api.depends('name', 'code')
    def _compute_display_name_complete(self):
        """Genera el nombre completo en formato [Código] Nombre"""
        for discount_code in self:
            if discount_code.name and discount_code.code:
                discount_code.display_name_complete = f"[{discount_code.code}] {discount_code.name}"
            elif discount_code.code:
                discount_code.display_name_complete = discount_code.code
            else:
                discount_code.display_name_complete = discount_code.name or ''
    
    @api.constrains('code')
    def _check_code_unique(self):
        """Valida que el código sea único"""
        for discount_code in self:
            if discount_code.code:
                existing = self.search([
                    ('code', '=', discount_code.code),
                    ('id', '!=', discount_code.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        _('El código "%s" ya existe. El código de descuento debe ser único.') % discount_code.code
                    )

