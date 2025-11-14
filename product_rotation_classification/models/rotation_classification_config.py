# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RotationClassificationConfig(models.Model):
    """
    Modelo para configurar los parámetros de clasificación por rotación de inventario.
    Permite definir los umbrales de meses para cada nivel de clasificación.
    """
    _name = 'rotation.classification.config'
    _description = 'Rotation Classification Configuration'
    _rec_name = 'id'

    # Umbrales de clasificación (en meses)
    threshold_high = fields.Float(
        string='High Rotation Threshold (months)',
        default=7.0,
        required=True,
        help='Products with stock duration ≤ this value are classified as HIGH rotation'
    )
    threshold_low = fields.Float(
        string='Low Rotation Threshold (months)',
        default=24.0,
        required=True,
        help='Products with stock duration ≤ this value (and > high) are classified as LOW rotation'
    )
    threshold_bone = fields.Float(
        string='Bone Rotation Threshold (months)',
        default=60.0,
        required=True,
        help='Products with stock duration < this value (and > low) are classified as BONE rotation'
    )

    # Parámetros de análisis
    analysis_period_months = fields.Integer(
        string='Analysis Period (months)',
        default=12,
        required=True,
        help='Number of months to analyze for consumption calculation'
    )
    include_zero_stock = fields.Boolean(
        string='Include Products without Stock',
        default=True,
        help='Include products with zero stock in classification (DEPLETED)'
    )
    include_no_consumption = fields.Boolean(
        string='Include Products without Consumption',
        default=True,
        help='Include products with stock but no consumption in classification (INFINITE)'
    )

    # Estadísticas del último cálculo
    last_calculation = fields.Datetime(
        string='Last Calculation',
        readonly=True
    )
    last_calculation_products = fields.Integer(
        string='Products Calculated',
        readonly=True
    )
    last_calculation_duration = fields.Float(
        string='Calculation Duration (seconds)',
        readonly=True
    )

    active = fields.Boolean(default=True)

    @api.constrains('threshold_high', 'threshold_low', 'threshold_bone')
    def _check_thresholds(self):
        """Valida que los umbrales estén en orden ascendente."""
        for record in self:
            if record.threshold_high <= 0:
                raise ValidationError(_('High rotation threshold must be greater than 0'))
            if record.threshold_low <= record.threshold_high:
                raise ValidationError(_('Low rotation threshold must be greater than high threshold'))
            if record.threshold_bone <= record.threshold_low:
                raise ValidationError(_('Bone rotation threshold must be greater than low threshold'))

    @api.constrains('analysis_period_months')
    def _check_analysis_period(self):
        """Valida que el período de análisis sea válido."""
        for record in self:
            if record.analysis_period_months < 1:
                raise ValidationError(_('Analysis period must be at least 1 month'))
            if record.analysis_period_months > 60:
                raise ValidationError(_('Analysis period cannot exceed 60 months'))

    def action_calculate_rotation_now(self):
        """Ejecuta el cálculo de clasificación por rotación inmediatamente."""
        self.ensure_one()
        product_template = self.env['product.template']
        return product_template.action_calculate_rotation_classification()

