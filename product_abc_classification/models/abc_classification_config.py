# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ABCClassificationConfig(models.Model):
    """Configuración de umbrales para clasificación ABC"""
    _name = 'abc.classification.config'
    _description = 'ABC Classification Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        default='ABC Configuration',
        required=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Only one configuration can be active'
    )
    
    # Umbrales de clasificación (porcentajes acumulados)
    threshold_aaa = fields.Float(
        string='AAA Threshold (%)',
        default=51.2,
        required=True,
        help='Cumulative percentage for AAA classification (e.g. 51.2 = 51.2%)'
    )
    
    threshold_aa = fields.Float(
        string='AA Threshold (%)',
        default=64.0,
        required=True,
        help='Cumulative percentage for AA classification (e.g. 64.0 = 64%)'
    )
    
    threshold_a = fields.Float(
        string='A Threshold (%)',
        default=80.0,
        required=True,
        help='Cumulative percentage for A classification (e.g. 80.0 = 80%)'
    )
    
    threshold_b = fields.Float(
        string='B Threshold (%)',
        default=95.0,
        required=True,
        help='Cumulative percentage for B classification (e.g. 95.0 = 95%)'
    )
    
    # threshold_c sería 100%, no hace falta configurarlo
    
    # Período de análisis
    analysis_period_months = fields.Integer(
        string='Analysis Period (months)',
        default=12,
        required=True,
        help='Number of months back to calculate sales'
    )
    
    # Opciones adicionales
    include_zero_sales = fields.Boolean(
        string='Include Products without Sales',
        default=True,
        help='If checked, products without sales are classified as C'
    )
    
    # Información del último cálculo
    last_calculation_date = fields.Datetime(
        string='Last Execution',
        readonly=True,
        help='Date and time of the last ABC calculation execution'
    )
    
    products_calculated = fields.Integer(
        string='Products Calculated',
        readonly=True,
        help='Number of products included in the last calculation'
    )
    
    calculation_time = fields.Float(
        string='Calculation Time (sec)',
        readonly=True,
        help='Time taken for the last calculation in seconds'
    )
    
    @api.constrains('threshold_aaa', 'threshold_aa', 'threshold_a', 'threshold_b')
    def _check_thresholds(self):
        """Validar que los umbrales estén en orden ascendente"""
        for config in self:
            if not (0 < config.threshold_aaa < config.threshold_aa < config.threshold_a < config.threshold_b <= 100):
                raise ValidationError(_(
                    'Thresholds must be in ascending order:\n'
                    '0 < AAA < AA < A < B <= 100\n'
                    'Current values: AAA=%.1f, AA=%.1f, A=%.1f, B=%.1f'
                ) % (config.threshold_aaa, config.threshold_aa, config.threshold_a, config.threshold_b))
    
    @api.constrains('analysis_period_months')
    def _check_analysis_period(self):
        """Validar que el período de análisis sea válido"""
        for config in self:
            if config.analysis_period_months < 1:
                raise ValidationError(_('The analysis period must be at least 1 month'))
    
    @api.constrains('active')
    def _check_only_one_active(self):
        """Asegurar que solo haya una configuración activa"""
        if self.active:
            other_active = self.search([('id', '!=', self.id), ('active', '=', True)])
            if other_active:
                raise ValidationError(_(
                    'Only one configuration can be active. '
                    'Deactivate the configuration "%s" first.'
                ) % other_active[0].name)
    
    @api.model
    def get_active_config(self):
        """Obtener la configuración activa"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            # Crear configuración por defecto si no existe
            config = self.create({
                'name': 'Default ABC Configuration',
                'active': True,
            })
        return config
    
    def action_calculate_abc_now(self):
        """Botón para ejecutar el cálculo ABC manualmente"""
        self.ensure_one()
        ProductTemplate = self.env['product.template']
        return ProductTemplate.action_calculate_abc_classification()

