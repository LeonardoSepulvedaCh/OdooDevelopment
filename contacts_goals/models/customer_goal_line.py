from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class CustomerGoalLine(models.Model):
    _name = 'customer.goal.line'
    _description = 'Línea de Objetivo de Meta'
    _order = 'sequence, minimum_wage_multiplier desc'

    goal_id = fields.Many2one('customer.goal', string='Meta', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    
    minimum_wage_multiplier = fields.Float(
        string='Múltiplo de Salario Mínimo',
        required=True,
        default=1.0,
        help='Cantidad de salarios mínimos que representa este objetivo'
    )
    
    minimum_wage = fields.Monetary(
        string='Salario Mínimo Vigente',
        compute='_compute_minimum_wage',
        store=False,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda', 
        related='goal_id.currency_id', 
        store=True, 
        readonly=True
    )
    
    target_amount = fields.Monetary(
        string='Monto Objetivo',
        compute='_compute_target_amount',
        store=True,
        currency_field='currency_id',
        help='Monto objetivo calculado: Salario Mínimo × Múltiplo'
    )
    
    achieved_amount = fields.Monetary(
        string='Monto Alcanzado',
        compute='_compute_achieved_amount',
        store=False,
        aggregator='sum',
        currency_field='currency_id',
        help='Suma de ventas confirmadas del cliente en el periodo para este objetivo'
    )
    
    achievement_percentage = fields.Float(
        string='% Cumplimiento',
        compute='_compute_achievement_percentage',
        store=False,
        digits=(5, 1),
        aggregator='avg',
        help='Porcentaje de cumplimiento de este objetivo'
    )
    
    notes = fields.Text(string='Notas')
    
    # Obtener el salario mínimo desde los parámetros del sistema
    def _compute_minimum_wage(self):
        minimum_wage = float(self.env['ir.config_parameter'].sudo().get_param(
            'contacts_goals.minimum_wage', default='0.0'
        ))
        for line in self:
            line.minimum_wage = minimum_wage
    
    # Calcular el monto objetivo basado en el múltiplo del salario mínimo
    @api.depends('minimum_wage_multiplier', 'minimum_wage')
    def _compute_target_amount(self):
        for line in self:
            line.target_amount = line.minimum_wage * line.minimum_wage_multiplier
    
    # Calcular el monto acumulado de ventas del cliente en el periodo
    @api.depends('goal_id.achieved_amount')
    def _compute_achieved_amount(self):
        for line in self:
            if not line.goal_id or not line.goal_id.partner_id:
                line.achieved_amount = 0.0
                continue
            
            line.achieved_amount = line.goal_id.achieved_amount
    
    # Calcular el porcentaje de cumplimiento
    @api.depends('target_amount', 'achieved_amount', 'goal_id.achieved_amount')
    def _compute_achievement_percentage(self):
        for line in self:
            if line.target_amount > 0:
                line.achievement_percentage = round((line.achieved_amount / line.target_amount) * 100, 1)
                logger.info(f"====Line {line.id}: achieved={line.achieved_amount}, target={line.target_amount}, percentage={line.achievement_percentage}")
            else:
                line.achievement_percentage = 0.0
    
    # Validar que el múltiplo sea positivo
    @api.constrains('minimum_wage_multiplier')
    def _check_multiplier(self):
        for line in self:
            if line.minimum_wage_multiplier <= 0:
                raise ValidationError(
                    _('El múltiplo de salario mínimo debe ser mayor a cero.')
                )

