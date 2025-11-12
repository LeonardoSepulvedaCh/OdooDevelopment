from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SalesTargetLine(models.Model):
    _name = 'sales.target.line'
    _description = 'Línea de Meta por Categoría'
    _inherit = ['sales.target.mixin']
    _order = 'category_id'

    target_id = fields.Many2one(
        'sales.target',
        string='Meta',
        required=True,
        ondelete='cascade',
        index=True,
    )
    
    category_id = fields.Many2one(
        'product.category',
        string='Categoría de Producto',
        required=True,
        domain=[('active_for_targets', '=', True)],
        index=True,
    )
    
    target_amount = fields.Monetary(
        string='Monto Objetivo',
        required=True,
        currency_field='currency_id',
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
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='target_id.currency_id',
        readonly=True,
        store=True,
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='target_id.company_id',
        store=True,
        index=True,
    )

    @api.depends('target_id.salesperson_id', 'target_id.year', 'target_id.month', 'category_id')
    def _compute_invoiced_amount(self):
        for record in self:
            if not record.target_id or not record.category_id:
                record.invoiced_amount = 0.0
                continue
            
            target = record.target_id
            if not target.salesperson_id or not target.year or not target.month:
                record.invoiced_amount = 0.0
                continue
            
            # Usar método del mixin para obtener fechas del periodo
            date_from, date_to = self.get_period_dates(target.year, target.month)
            
            # Usar método del mixin para construir el dominio de búsqueda
            domain = record._get_invoice_domain(
                target.salesperson_id.id,
                date_from,
                date_to,
                target.company_id.id
            )
            
            # Buscar facturas del vendedor en el periodo
            invoices = self.env['account.move'].search(domain)
            
            total = 0.0
            for invoice in invoices:
                # Filtrar líneas de factura por categoría
                invoice_lines = invoice.invoice_line_ids.filtered(
                    lambda line: line.product_id.categ_id == record.category_id
                )
                
                # Calcular total usando método del mixin
                for line in invoice_lines:
                    total += self.calculate_line_total(line, invoice.move_type)
            
            record.invoiced_amount = total

    @api.depends('target_amount', 'invoiced_amount')
    def _compute_achievement_percentage(self):
        for record in self:
            # Usar método del mixin para calcular el porcentaje
            record.achievement_percentage = self.calculate_achievement_percentage(
                record.target_amount,
                record.invoiced_amount
            )

    @api.constrains('target_amount')
    def _check_target_amount(self):
        for record in self:
            if record.target_amount < 0:
                raise ValidationError('El monto objetivo no puede ser negativo.')

    @api.constrains('target_id', 'category_id')
    def _check_unique_category(self):
        for record in self:
            if record.target_id and record.category_id:
                duplicate = self.search([
                    ('target_id', '=', record.target_id.id),
                    ('category_id', '=', record.category_id.id),
                    ('id', '!=', record.id),
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        f'La categoría "{record.category_id.display_name}" ya está asignada a esta meta.'
                    )

