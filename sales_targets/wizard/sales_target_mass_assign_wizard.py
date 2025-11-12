import logging
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class SalesTargetMassAssignWizard(models.TransientModel):
    _name = 'sales.target.mass.assign.wizard'
    _description = 'Wizard para Asignación Masiva de Metas'

    year = fields.Integer(
        string='Año',
        required=True,
        default=lambda self: fields.Date.today().year,
    )
    
    month = fields.Selection(
        [
            ('1', 'Enero'),
            ('2', 'Febrero'),
            ('3', 'Marzo'),
            ('4', 'Abril'),
            ('5', 'Mayo'),
            ('6', 'Junio'),
            ('7', 'Julio'),
            ('8', 'Agosto'),
            ('9', 'Septiembre'),
            ('10', 'Octubre'),
            ('11', 'Noviembre'),
            ('12', 'Diciembre'),
        ],
        string='Mes',
        required=True,
        default=lambda self: str(fields.Date.today().month),
    )
    
    line_ids = fields.One2many(
        'sales.target.mass.assign.wizard.line',
        'wizard_id',
        string='Vendedores',
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
    )
   
    # Recarga las líneas cuando cambia el periodo.
    @api.onchange('year', 'month')
    def _onchange_period(self):
        if self.year and self.month:
            self._load_salespeople()

    # Carga todos los vendedores activos y sus datos.
    def _load_salespeople(self):
        salespeople = self.env['res.users'].search([
            ('is_salesperson', '=', True),
            ('active', '=', True),
        ])
        
        if not salespeople:
            raise UserError(
                'No hay vendedores configurados.\n\n'
                'Por favor, ve a "Metas Comerciales → Vendedores" y marca '
                'los usuarios que son vendedores activando el campo "Es Vendedor".'
            )
        
        active_categories = self.env['product.category'].search([
            ('active_for_targets', '=', True),
        ], order='name')
        
        if not active_categories:
            raise UserError(
                'No hay categorías activas para metas.\n\n'
                'Por favor, ve a "Metas Comerciales → Categorías" y marca '
                'las categorías que quieres usar en las metas.'
            )
        
        lines = []
        for salesperson in salespeople:
            # Verificar si ya existe una meta para este periodo
            existing_target = self.env['sales.target'].search([
                ('salesperson_id', '=', salesperson.id),
                ('year', '=', self.year),
                ('month', '=', self.month),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
            
            # Calcular ventas del mes anterior para referencia
            previous_month_sales = self._get_previous_month_sales(salesperson.id)
            
            # Crear líneas de categoría
            category_lines = []
            for category in active_categories:
                # Si existe meta, buscar el monto de esa categoría
                existing_amount = 0.0
                if existing_target:
                    existing_line = existing_target.target_line_ids.filtered(
                        lambda l: l.category_id == category
                    )
                    if existing_line:
                        existing_amount = existing_line.target_amount
                
                category_lines.append((0, 0, {
                    'category_id': category.id,
                    'target_amount': existing_amount,
                }))
            
            line_vals = {
                'salesperson_id': salesperson.id,
                'existing_target_id': existing_target.id if existing_target else False,
                'previous_month_sales': previous_month_sales,
                'category_line_ids': category_lines,
            }
            lines.append((0, 0, line_vals))
        
        self.line_ids = [(5, 0, 0)]  # Limpiar líneas existentes
        self.line_ids = lines

    # Obtiene las ventas del mes anterior para un vendedor.
    def _get_previous_month_sales(self, salesperson_id):
        year = self.year
        month = int(self.month)
        
        if month == 1:
            previous_year = year - 1
            previous_month = 12
        else:
            previous_year = year
            previous_month = month - 1
        
        # Calcular fechas del periodo anterior
        date_from = fields.Date.from_string(f"{previous_year}-{previous_month:02d}-01")
        
        # Último día del mes anterior
        if previous_month == 12:
            date_to = fields.Date.from_string(f"{previous_year}-12-31")
        else:
            next_month = fields.Date.from_string(f"{previous_year}-{previous_month + 1:02d}-01")
            date_to = fields.Date.subtract(next_month, days=1)
        
        # Buscar facturas
        invoices = self.env['account.move'].search([
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_user_id', '=', salesperson_id),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', '=', self.company_id.id),
        ])
        
        # Sumar montos sin impuestos
        total = 0.0
        for invoice in invoices:
            if invoice.move_type == 'out_invoice':
                total += invoice.amount_untaxed_signed
            else:
                total -= abs(invoice.amount_untaxed_signed)
        
        return total

    # Carga los vendedores al abrir el wizard.
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        if 'line_ids' in fields_list:
            year = res.get('year', fields.Date.today().year)
            month = res.get('month', str(fields.Date.today().month))
            company_id = res.get('company_id', self.env.company.id)
            
            salespeople = self.env['res.users'].search([
                ('is_salesperson', '=', True),
                ('active', '=', True),
            ])
            
            if not salespeople:
                raise UserError(
                    'No hay vendedores configurados.\n\n'
                    'Por favor, ve a "Metas Comerciales → Vendedores" y marca '
                    'los usuarios que son vendedores activando el campo "Es Vendedor".'
                )
            
            active_categories = self.env['product.category'].search([
                ('active_for_targets', '=', True),
            ], order='name')
            
            if not active_categories:
                raise UserError(
                    'No hay categorías activas para metas.\n\n'
                    'Por favor, ve a "Metas Comerciales → Categorías" y marca '
                    'las categorías que quieres usar en las metas.'
                )
            
            lines = []
            for salesperson in salespeople:
                existing_target = self.env['sales.target'].search([
                    ('salesperson_id', '=', salesperson.id),
                    ('year', '=', year),
                    ('month', '=', month),
                    ('company_id', '=', company_id),
                ], limit=1)
                
                previous_month_sales = self._calculate_previous_sales(
                    salesperson.id, year, int(month), company_id
                )
                
                category_lines = []
                for category in active_categories:
                    existing_amount = 0.0
                    if existing_target:
                        existing_line = existing_target.target_line_ids.filtered(
                            lambda l: l.category_id == category
                        )
                        if existing_line:
                            existing_amount = existing_line.target_amount
                    
                    category_lines.append((0, 0, {
                        'category_id': category.id,
                        'target_amount': existing_amount,
                    }))
                
                line_vals = {
                    'salesperson_id': salesperson.id,
                    'existing_target_id': existing_target.id if existing_target else False,
                    'previous_month_sales': previous_month_sales,
                    'category_line_ids': category_lines,
                }
                lines.append((0, 0, line_vals))
            
            res['line_ids'] = lines
        
        return res

    def _calculate_previous_sales(self, salesperson_id, year, month, company_id):
        if month == 1:
            previous_year = year - 1
            previous_month = 12
        else:
            previous_year = year
            previous_month = month - 1
        
        date_from = fields.Date.from_string(f"{previous_year}-{previous_month:02d}-01")
        
        if previous_month == 12:
            date_to = fields.Date.from_string(f"{previous_year}-12-31")
        else:
            next_month = fields.Date.from_string(f"{previous_year}-{previous_month + 1:02d}-01")
            date_to = fields.Date.subtract(next_month, days=1)
        
        invoices = self.env['account.move'].search([
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_user_id', '=', salesperson_id),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', '=', company_id),
        ])
        
        total = 0.0
        for invoice in invoices:
            if invoice.move_type == 'out_invoice':
                total += invoice.amount_untaxed_signed
            else:
                total -= abs(invoice.amount_untaxed_signed)
        
        return total

    def action_assign_targets(self):
        """Asigna las metas a los vendedores."""
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError('No hay vendedores para asignar metas.')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []
        
        for line in self.line_ids:
            # Validar que la línea tenga vendedor
            if not line.salesperson_id:
                errors.append(f"Línea sin vendedor")
                continue

            # Validar que tenga al menos una categoría
            if not line.category_line_ids:
                errors.append(f"{line.salesperson_id.name}: Sin categorías")
                skipped_count += 1
                continue
            
            # Preparar líneas de categoría
            target_line_vals = []
            for cat_line in line.category_line_ids:
                if cat_line.category_id and cat_line.target_amount > 0:
                    target_line_vals.append((0, 0, {
                        'category_id': cat_line.category_id.id,
                        'target_amount': cat_line.target_amount,
                    }))
            
            if not target_line_vals:
                errors.append(f"{line.salesperson_id.name}: Todas las categorías con monto 0")
                skipped_count += 1
                continue
            
            try:
                # Buscar si existe una meta para este vendedor y periodo
                existing_target = line.existing_target_id or self.env['sales.target'].search([
                    ('salesperson_id', '=', line.salesperson_id.id),
                    ('year', '=', self.year),
                    ('month', '=', self.month),
                    ('company_id', '=', self.company_id.id),
                ], limit=1)
                
                if existing_target:
                    # Actualizar meta existente - Eliminar líneas antiguas y crear nuevas
                    existing_target.target_line_ids.unlink()
                    existing_target.write({
                        'target_line_ids': target_line_vals,
                        'state': 'active',
                    })
                    updated_count += 1
                else:
                    # Crear nueva meta
                    self.env['sales.target'].create({
                        'salesperson_id': line.salesperson_id.id,
                        'year': self.year,
                        'month': self.month,
                        'company_id': self.company_id.id,
                        'state': 'active',
                        'target_line_ids': target_line_vals,
                    })
                    created_count += 1
            except Exception as e:
                errors.append(f"{line.salesperson_id.name}: {str(e)}")
        
        # Mensaje de resultado
        message = f"Asignación completada:\n"
        if created_count > 0:
            message += f"- {created_count} meta(s) creada(s)\n"
        if updated_count > 0:
            message += f"- {updated_count} meta(s) actualizada(s)\n"
        if skipped_count > 0:
            message += f"- {skipped_count} vendedor(es) omitido(s)\n"
        if errors:
            message += f"\nDetalles:\n" + "\n".join(errors[:5])  # Mostrar primeros 5 errores
        
        msg_type = 'success' if (created_count > 0 or updated_count > 0) else 'warning'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Metas Asignadas',
                'message': message,
                'type': msg_type,
                'sticky': True,  # Dejar el mensaje visible
                'next': {
                    'type': 'ir.actions.act_window_close',
                },
            }
        }


class SalesTargetMassAssignWizardLine(models.TransientModel):
    _name = 'sales.target.mass.assign.wizard.line'
    _description = 'Línea de Asignación Masiva de Metas'
    _order = 'salesperson_id'

    wizard_id = fields.Many2one(
        'sales.target.mass.assign.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    
    salesperson_id = fields.Many2one(
        'res.users',
        string='Vendedor',
        required=True,
    )
    
    target_amount = fields.Monetary(
        string='Monto Total',
        compute='_compute_target_amount',
        store=True,
        currency_field='currency_id',
        help='Suma de todas las categorías',
    )
    
    category_line_ids = fields.One2many(
        'sales.target.mass.assign.wizard.category.line',
        'wizard_line_id',
        string='Metas por Categoría',
    )
    
    previous_month_sales = fields.Monetary(
        string='Ventas Mes Anterior',
        readonly=True,
        currency_field='currency_id',
    )
    
    existing_target_id = fields.Many2one(
        'sales.target',
        string='Meta Existente',
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='wizard_id.currency_id',
        readonly=True,
    )
    
    has_existing_target = fields.Boolean(
        string='Tiene Meta',
        compute='_compute_has_existing_target',
        store=True,
    )

    # Indica si ya existe una meta para este vendedor.
    @api.depends('existing_target_id')
    def _compute_has_existing_target(self):
        for record in self:
            record.has_existing_target = bool(record.existing_target_id)

    # Calcula el total sumando todas las categorías.
    @api.depends('category_line_ids.target_amount')
    def _compute_target_amount(self):
        for record in self:
            record.target_amount = sum(record.category_line_ids.mapped('target_amount'))


class SalesTargetMassAssignWizardCategoryLine(models.TransientModel):
    _name = 'sales.target.mass.assign.wizard.category.line'
    _description = 'Línea de Categoría en Asignación Masiva'
    _order = 'category_id'

    wizard_line_id = fields.Many2one(
        'sales.target.mass.assign.wizard.line',
        string='Línea Wizard',
        required=True,
        ondelete='cascade',
    )
    
    category_id = fields.Many2one(
        'product.category',
        string='Categoría',
        required=False,
        readonly=True,
    )
    
    target_amount = fields.Monetary(
        string='Monto Objetivo',
        currency_field='currency_id',
        default=0.0,
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='wizard_line_id.currency_id',
        readonly=True,
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Validar que no se creen líneas sin categoría."""
        # Filtrar líneas sin category_id
        vals_list = [vals for vals in vals_list if vals.get('category_id')]
        if not vals_list:
            return self.browse()
        return super().create(vals_list)

