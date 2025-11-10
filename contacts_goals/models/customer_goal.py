from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CustomerGoal(models.Model):
    _name = 'customer.goal'
    _description = 'Meta de Cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, partner_id'
    _rec_name = 'display_name'

    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, domain=[('customer_rank', '>', 0)], index=True, tracking=True)
    date_start = fields.Date(string='Fecha Inicio', required=True, default=fields.Date.today, tracking=True)
    date_end = fields.Date(string='Fecha Fin', required=True, tracking=True)
    
    is_active = fields.Boolean(
        string='Meta Activa',
        default=True,
        tracking=True,
        help='Indica si esta es la meta activa del cliente. Solo puede haber una meta activa por cliente.'
    )
    
    line_ids = fields.One2many(
        'customer.goal.line',
        'goal_id',
        string='Líneas de Objetivos',
        help='Múltiples objetivos dentro de esta meta (ej: 3 salarios, 10 salarios, 50 salarios)'
    )

    minimum_wage_multiplier = fields.Float(
        string='Múltiplo de Salario Mínimo',
         required=False,
         default=1.0,
         help='Cantidad de salarios mínimos que representa el objetivo (DEPRECADO: usar líneas de objetivos)',
         tracking=True
    )
    
    minimum_wage = fields.Monetary(
        string='Salario Mínimo Vigente',
        compute='_compute_minimum_wage',
        store=False,
        currency_field='currency_id',
        tracking=True
    )
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id, tracking=True)
    
    target_amount = fields.Monetary(
        string='Monto Objetivo',
        compute='_compute_target_amount',
        store=True,
        aggregator='sum',
        currency_field='currency_id',
        help='Monto objetivo calculado: Salario Mínimo × Múltiplo'
    )

    achieved_amount = fields.Monetary(
        string='Monto Alcanzado',
        compute='_compute_achieved_amount',
        store=False,
        aggregator='sum',
        currency_field='currency_id',
        help='Suma de ventas confirmadas del cliente en el periodo'
    )

    achievement_percentage = fields.Float(
        string='% Cumplimiento',
        compute='_compute_achievement_percentage',
        store=False,
        digits=(5, 1),
        aggregator='avg',
        help='Porcentaje de cumplimiento de la meta',
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('active', 'Activa'),
        ('achieved', 'Cumplida'),
        ('expired', 'Vencida'),
        ('cancelled', 'Cancelada'),
    ], string='Estado', compute='_compute_state', store=True, tracking=True)
    
    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)
    notes = fields.Text(string='Notas')
    
    # Generar el nombre de la meta
    @api.depends('partner_id', 'date_start', 'date_end')
    def _compute_display_name(self):
        for goal in self:
            if goal.partner_id and goal.date_start and goal.date_end:
                goal.display_name = f"{goal.partner_id.name} - {goal.date_start} a {goal.date_end}"
            else:
                goal.display_name = 'Nueva Meta'
    
    # Obtener el salario mínimo desde los parámetros del sistema
    def _compute_minimum_wage(self):
        minimum_wage = float(self.env['ir.config_parameter'].sudo().get_param(
            'contacts_goals.minimum_wage', default='0.0'
        ))
        for goal in self:
            goal.minimum_wage = minimum_wage
    
    # Calcular el monto objetivo basado en el múltiplo del salario mínimo - Si hay líneas, usa la suma de las líneas, sino usa el campo legacy
    @api.depends('minimum_wage_multiplier', 'minimum_wage', 'line_ids', 'line_ids.target_amount')
    def _compute_target_amount(self):
        for goal in self:
            if goal.line_ids:
                goal.target_amount = sum(goal.line_ids.mapped('target_amount'))
            else:
                goal.target_amount = goal.minimum_wage * goal.minimum_wage_multiplier
    
    # Calcular el monto acumulado de ventas del cliente en el periodo
    def _compute_achieved_amount(self):
        for goal in self:
            if not goal.partner_id or not goal.date_start or not goal.date_end:
                goal.achieved_amount = 0.0
                continue
            
            sales = self.env['sale.order'].search([
                ('partner_id', 'child_of', goal.partner_id.id),
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', goal.date_start),
                ('date_order', '<=', goal.date_end),
            ])
            
            goal.achieved_amount = sum(sales.mapped('amount_total'))
    
    # Calcular el porcentaje de cumplimiento
    @api.depends('line_ids.achievement_percentage', 'target_amount', 'achieved_amount')
    def _compute_achievement_percentage(self):
        for goal in self:
            if goal.line_ids:
                line_percentages = goal.line_ids.mapped('achievement_percentage')
                goal.achievement_percentage = sum(line_percentages) / len(goal.line_ids)
            elif goal.target_amount > 0:
                goal.achievement_percentage = (goal.achieved_amount / goal.target_amount) * 100
            else:
                goal.achievement_percentage = 0.0
    
    # Determinar el estado de la meta
    @api.depends('achievement_percentage', 'line_ids.achievement_percentage', 'achieved_amount', 'target_amount', 'date_end', 'is_active')
    def _compute_state(self):
        today = fields.Date.today()
        for goal in self:
            if not goal.is_active:
                goal.state = 'cancelled'
            elif goal.achievement_percentage >= 100:
                goal.state = 'achieved'
            elif goal.date_end and goal.date_end < today:
                goal.state = 'expired'
            elif goal.is_active:
                goal.state = 'active'
            else:
                goal.state = 'draft'
    
    # Validar que la fecha de fin sea posterior a la fecha de inicio
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for goal in self:
            if goal.date_end and goal.date_start and goal.date_end <= goal.date_start:
                raise ValidationError(
                    _('La fecha de fin debe ser posterior a la fecha de inicio.')
                )
    
    # Validar que el múltiplo sea positivo
    @api.constrains('minimum_wage_multiplier')
    def _check_multiplier(self):
        for goal in self:
            if goal.minimum_wage_multiplier <= 0:
                raise ValidationError(
                    _('El múltiplo de salario mínimo debe ser mayor a cero.')
                )
    
    # Validar que solo exista una meta activa por cliente
    @api.constrains('partner_id', 'is_active')
    def _check_single_active_goal(self):
        for goal in self:
            if goal.is_active:
                active_goals = self.search([
                    ('id', '!=', goal.id),
                    ('partner_id', '=', goal.partner_id.id),
                    ('is_active', '=', True),
                ])
                if active_goals:
                    raise ValidationError(
                        _('El cliente %s ya tiene una meta activa. Solo puede haber una meta activa por cliente.\n'
                          'Debe desactivar la meta actual antes de activar una nueva.') % goal.partner_id.name
                    )
    
    # Activar la meta (desactivando cualquier otra meta activa del cliente)
    def action_activate_goal(self):
        self.ensure_one()
        active_goals = self.search([
            ('partner_id', '=', self.partner_id.id),
            ('is_active', '=', True),
            ('id', '!=', self.id),
        ])
        if active_goals:
            active_goals.write({'is_active': False})
        
        self.write({'is_active': True})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Meta Activada'),
                'message': _('La meta ha sido activada correctamente.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    # Desactivar la meta
    def action_deactivate_goal(self):
        self.ensure_one()
        self.write({'is_active': False})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Meta Desactivada'),
                'message': _('La meta ha sido desactivada.'),
                'type': 'info',
                'sticky': False,
            }
        }
    
    # Acciones para ver las ventas relacionadas con esta meta
    def action_view_sales(self):
        self.ensure_one()
        return {
            'name': _('Ventas del Cliente'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'child_of', self.partner_id.id),
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', self.date_start),
                ('date_order', '<=', self.date_end),
            ],
            'context': {'default_partner_id': self.partner_id.id}
        }

