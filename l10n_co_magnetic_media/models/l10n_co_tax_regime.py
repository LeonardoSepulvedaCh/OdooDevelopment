# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nCoTaxRegime(models.Model):
    """
    Modelo para gestionar los Regímenes Tributarios de Colombia.
    
    Este modelo almacena los diferentes tipos de régimen tributario
    definidos por la DIAN para la clasificación de contribuyentes.
    """
    _name = 'l10n_co.tax.regime'
    _description = 'Régimen Tributario Colombia'
    _order = 'sequence, code'
    
    # Campos básicos
    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        help='Código del régimen tributario (EE, EX, GC, RC, etc.)'
    )
    
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
        help='Nombre descriptivo del régimen tributario'
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
    
    # Campos de retenciones (Boolean)
    retencion_fuente = fields.Boolean(
        string='Retención Fuente',
        default=False,
        help='Indica si aplica retención en la fuente'
    )
    
    retencion_cree = fields.Boolean(
        string='Retención CREE',
        default=False,
        help='Indica si aplica retención CREE'
    )
    
    retencion_iva = fields.Boolean(
        string='Retención IVA',
        default=False,
        help='Indica si aplica retención de IVA'
    )
    
    retencion_timbre = fields.Boolean(
        string='Retención Timbre',
        default=False,
        help='Indica si aplica retención de timbre'
    )
    
    retencion_ica = fields.Boolean(
        string='Retención ICA',
        default=False,
        help='Indica si aplica retención de ICA (Industria y Comercio)'
    )
    
    # Campo tipo factura electrónica (Integer)
    tipo_factura_electronica = fields.Integer(
        string='Tipo Factura Electrónica',
        default=0,
        help='Tipo de factura electrónica asociado al régimen (0, 2, etc.)'
    )
    
    # Campo computado para mostrar información completa
    display_name_complete = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name_complete',
        store=True
    )
    
    @api.depends('code', 'name')
    def _compute_display_name_complete(self):
        """Calcula el nombre completo con código y nombre"""
        for regime in self:
            if regime.code and regime.name:
                regime.display_name_complete = f"[{regime.code}] {regime.name}"
            elif regime.code:
                regime.display_name_complete = regime.code
            else:
                regime.display_name_complete = regime.name or ''
    
    # Constraint Python para código único (Odoo 19 best practice)
    @api.constrains('code')
    def _check_code_unique(self):
        """Verifica que el código sea único"""
        for regime in self:
            if regime.code:
                existing = self.search([
                    ('code', '=', regime.code),
                    ('id', '!=', regime.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        _('El código "%s" ya existe. El código del régimen tributario debe ser único.') % regime.code
                    )

