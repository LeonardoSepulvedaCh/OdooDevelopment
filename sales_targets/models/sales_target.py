from odoo import models, fields, api
from odoo.exceptions import ValidationError
from .constants import MONTHS, TARGET_STATES, MIN_YEAR, MAX_YEAR


class SalesTarget(models.Model):
    _name = 'sales.target'
    _description = 'Metas Comerciales de Vendedores'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'sales.target.mixin']
    _order = 'year desc, month desc, salesperson_id'
    _rec_name = 'display_name'

    salesperson_id = fields.Many2one(
        'res.users',
        string='Vendedor',
        required=True,
        domain=[('is_salesperson', '=', True)],
        index=True,
    )
    
    year = fields.Integer(
        string='Año',
        required=True,
        default=lambda self: fields.Date.today().year,
        index=True,
    )
    
    month = fields.Selection(
        selection=MONTHS,
        string='Mes',
        required=True,
        default=lambda self: str(fields.Date.today().month),
        index=True,
    )
    
    target_amount = fields.Monetary(
        string='Monto Objetivo',
        compute='_compute_target_amount',
        store=True,
        readonly=True,
        tracking=True,
        currency_field='currency_id',
        help='Suma automática de las metas por categoría',
    )
    
    target_line_ids = fields.One2many(
        'sales.target.line',
        'target_id',
        string='Metas por Categoría',
        copy=True,
    )
    
    invoiced_amount = fields.Monetary(
        string='Monto Facturado',
        compute='_compute_invoiced_amount',
        store=True,
        currency_field='currency_id',
    )
    
    achievement_percentage = fields.Float(
        string='% Cumplimiento',
        compute='_compute_achievement_percentage',
        store=True,
        digits=(5, 2),
    )
    
    achievement_percentage_display = fields.Char(
        string='Cumplimiento',
        compute='_compute_achievement_percentage_display',
        help='Porcentaje de cumplimiento global como promedio de las líneas (promedio simple)',
        store=False,
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='company_id.currency_id',
        readonly=True,
        store=True,
    )
    
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True,
    )
    
    state = fields.Selection(
        selection=TARGET_STATES,
        string='Estado',
        default='draft',
        required=True,
        tracking=True,
    )
    
    _unique_salesperson_period = models.Constraint(
        'UNIQUE(salesperson_id, year, month, company_id)',
        'Ya existe una meta para este vendedor en el periodo seleccionado.'
    )

    # Calcular el monto objetivo total como suma de las líneas
    @api.depends('target_line_ids.target_amount')
    def _compute_target_amount(self):
        for record in self:
            record.target_amount = sum(record.target_line_ids.mapped('target_amount'))

    # Generar el nombre para mostrar
    @api.depends('salesperson_id', 'year', 'month')
    def _compute_display_name(self):
        month_names = dict(self._fields['month'].selection)
        for record in self:
            if record.salesperson_id and record.year and record.month:
                record.display_name = f"{record.salesperson_id.name} - {month_names.get(record.month, '')} {record.year}"
            else:
                record.display_name = "Nueva Meta"

    # Calcular el monto facturado por el vendedor en el periodo
    @api.depends('salesperson_id', 'year', 'month')
    def _compute_invoiced_amount(self):
        for record in self:
            if not record.salesperson_id or not record.year or not record.month:
                record.invoiced_amount = 0.0
                continue
            
            # Usar método del mixin para obtener fechas del periodo
            date_from, date_to = self.get_period_dates(record.year, record.month)
            
            # Usar método del mixin para construir el dominio de búsqueda
            domain = record._get_invoice_domain(
                record.salesperson_id.id,
                date_from,
                date_to,
                record.company_id.id
            )
            
            invoices = self.env['account.move'].search(domain)
            
            total = sum(self.calculate_invoice_total(invoice) for invoice in invoices)
            
            record.invoiced_amount = total

    # Calcular el porcentaje de cumplimiento global como promedio de las líneas
    @api.depends('target_line_ids.achievement_percentage')
    def _compute_achievement_percentage(self):
        for record in self:
            if record.target_line_ids:
                # Promedio simple: cada categoría tiene el mismo peso
                total_percentage = sum(record.target_line_ids.mapped('achievement_percentage'))
                record.achievement_percentage = total_percentage / len(record.target_line_ids)
            else:
                record.achievement_percentage = 0.0
    
    # Campo computado para mostrar el porcentaje formateado con símbolo %
    @api.depends('achievement_percentage')
    def _compute_achievement_percentage_display(self):
        for record in self:
            record.achievement_percentage_display = f"{int(record.achievement_percentage)}%"

    @api.constrains('target_line_ids')
    def _check_target_lines(self):
        for record in self:
            if record.state != 'draft' and not record.target_line_ids:
                raise ValidationError('Debe agregar al menos una línea de meta por categoría antes de activar.')

    @api.constrains('year')
    def _check_year(self):
        for record in self:
            if record.year < MIN_YEAR or record.year > MAX_YEAR:
                raise ValidationError(f'El año debe estar entre {MIN_YEAR} y {MAX_YEAR}.')

    def action_set_active(self):
        self.write({'state': 'active'})

    def action_set_closed(self):
        self.write({'state': 'closed'})

    # Recalcular el monto facturado
    def action_recalculate(self):
        self._compute_invoiced_amount()
        for line in self.target_line_ids:
            line._compute_invoiced_amount()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Montos facturados recalculados correctamente.',
                'type': 'success',
                'sticky': False,
            }
        }

