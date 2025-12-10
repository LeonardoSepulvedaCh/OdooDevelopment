from odoo import models, fields, api


class AccountMove(models.Model):
    """Extiende account.move para gestionar prórrogas en fechas de vencimiento."""
    _inherit = 'account.move'

    extension_ids = fields.One2many(
        'account.invoice.due.date.extension',
        'invoice_id',
        string='Registros de Prórroga',
        help="Historial de prórrogas aplicadas a esta factura"
    )
    
    extension_count = fields.Integer(
        string='Número de Prórrogas',
        compute='_compute_extension_count',
        help="Total de prórrogas aprobadas registradas"
    )

    extended_due_date = fields.Date(
        string='Fecha de Vencimiento Extendida',
        compute='_compute_extended_due_date',
        store=True,
        help="Fecha de vencimiento con prórroga. Si se define, esta fecha se usará "
             "en lugar de la fecha de vencimiento original para determinar si la "
             "factura está vencida. Se obtiene del registro de prórroga más reciente."
    )

    effective_due_date = fields.Date(
        string='Fecha de Vencimiento Efectiva',
        compute='_compute_effective_due_date',
        store=True,
        index=True,
        help="Fecha de vencimiento efectiva: usa la fecha extendida si está definida, "
             "de lo contrario usa la fecha de vencimiento original."
    )

    is_overdue = fields.Boolean(
        string='¿Está Vencida?',
        compute='_compute_is_overdue',
        store=True,
        help="Indica si la factura está vencida según la fecha de vencimiento efectiva."
    )

    extension_keep_discount = fields.Boolean(
        string='Prórroga Mantiene Descuento',
        compute='_compute_extended_due_date',
        store=True,
        help="Indica si la prórroga aprobada mantiene el descuento por pronto pago activo."
    )

    @api.depends('extension_ids.active', 'extension_ids.state')
    def _compute_extension_count(self):
        """Calcula el número de prórrogas aprobadas."""
        for move in self:
            move.extension_count = 0
        
        if not self.ids:
            return
        
        extension_data = self.env['account.invoice.due.date.extension']._read_group(
            domain=[
                ('invoice_id', 'in', self.ids),
                ('active', '=', True),
                ('state', '=', 'approved')
            ],
            groupby=['invoice_id'],
            aggregates=['__count']
        )
        
        count_map = {invoice.id: count for invoice, count in extension_data}
        
        for move in self:
            move.extension_count = count_map.get(move.id, 0)

    @api.depends('extension_ids.extended_due_date', 'extension_ids.active', 'extension_ids.state', 'extension_ids.keep_discount')
    def _compute_extended_due_date(self):
        """Obtiene la fecha de prórroga más reciente aprobada."""
        for move in self:
            approved_extensions = move.extension_ids.filtered(lambda e: e.active and e.state == 'approved')
            if approved_extensions:
                latest_extension = approved_extensions.sorted(lambda e: e.extended_due_date, reverse=True)[0]
                move.extended_due_date = latest_extension.extended_due_date
                move.extension_keep_discount = latest_extension.keep_discount
            else:
                move.extended_due_date = False
                move.extension_keep_discount = False

    @api.depends('extended_due_date', 'invoice_date_due')
    def _compute_effective_due_date(self):
        """Calcula la fecha efectiva: usa extended_due_date si existe, sino invoice_date_due."""
        for move in self:
            if move.extended_due_date:
                move.effective_due_date = move.extended_due_date
            else:
                move.effective_due_date = move.invoice_date_due

    @api.depends('effective_due_date', 'payment_state', 'state')
    def _compute_is_overdue(self):
        """Determina si la factura está vencida según effective_due_date."""
        today = fields.Date.context_today(self)
        for move in self:
            if move.move_type == 'out_invoice' and move.state == 'posted':
                is_not_paid = move.payment_state in ('not_paid', 'partial')
                has_overdue_date = move.effective_due_date and move.effective_due_date < today
                move.is_overdue = is_not_paid and has_overdue_date
            else:
                move.is_overdue = False

    def _get_invoice_next_payment_values(self, custom_amount=None):
        """Ajusta valores de pago considerando prórroga y descuento por pronto pago (EPD)."""
        result = super()._get_invoice_next_payment_values(custom_amount=custom_amount)
        
        if not result or self.move_type not in ('out_invoice', 'out_refund'):
            return result
        
        if self.extended_due_date:
            self._apply_extension_logic(result)
        else:
            self._apply_overdue_logic(result)
        
        return result
    
    def _apply_extension_logic(self, result):
        """Aplica lógica de prórroga: ajusta fechas y gestiona descuento EPD."""
        today = fields.Date.context_today(self)
        is_paid = self.payment_state == 'paid'
        original_next_due_date = result.get('next_due_date')
        
        result['next_due_date'] = self.extended_due_date
        self._update_installment_state_for_extension(result, today, is_paid)
        
        result['epd_disabled_by_extension'] = not self.extension_keep_discount
        if not self.extension_keep_discount:
            self._disable_early_payment_discount(result)
        
        result.update({
            'has_extension': True,
            'original_due_date': original_next_due_date,
            'extended_due_date': self.extended_due_date,
            'extension_keep_discount': self.extension_keep_discount,
        })
    
    def _update_installment_state_for_extension(self, result, today, is_paid):
        """Actualiza installment_state según la fecha de prórroga."""
        if is_paid:
            return
        
        is_overdue = self.extended_due_date < today
        was_overdue = result.get('installment_state') == 'overdue'
        
        if is_overdue:
            result['installment_state'] = 'overdue'
        elif was_overdue:
            result['installment_state'] = 'next'
    
    def _apply_overdue_logic(self, result):
        """Desactiva EPD si la factura está vencida sin prórroga."""
        result['has_extension'] = False
        result['epd_disabled_by_extension'] = False
        
        is_overdue_without_extension = self._is_invoice_overdue_without_extension()
        has_epd = result.get('installment_state') == 'epd'
        
        if is_overdue_without_extension and has_epd:
            self._disable_early_payment_discount(result)
            result['epd_disabled_by_overdue'] = True
        else:
            result['epd_disabled_by_overdue'] = False
    
    def _is_invoice_overdue_without_extension(self):
        """Verifica si la factura está vencida sin prórroga."""
        if self.payment_state == 'paid':
            return False
        
        if not self.invoice_date_due:
            return False
        
        today = fields.Date.context_today(self)
        return self.invoice_date_due < today
    
    def _disable_early_payment_discount(self, payment_values):
        """Desactiva el descuento por pronto pago (EPD)."""
        if payment_values.get('installment_state') == 'epd':
            payment_values['installment_state'] = 'next'
            payment_values['amount_due'] = self.amount_residual
            payment_values['next_amount_to_pay'] = self.amount_residual
            payment_values['next_payment_reference'] = self.name
        
        payment_values.pop('epd_discount_amount_currency', None)
        payment_values.pop('epd_discount_amount', None)
        payment_values.pop('discount_date', None)
        payment_values.pop('epd_days_left', None)
        payment_values.pop('epd_line', None)
        payment_values.pop('epd_discount_msg', None)

    def action_view_extensions(self):
        """Abre la vista de prórrogas de la factura."""
        self.ensure_one()
        
        action = {
            'name': f'Prórrogas - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice.due.date.extension',
            'view_mode': 'list,form',
            'domain': [('invoice_id', '=', self.id)],
            'context': {
                'default_invoice_id': self.id,
            }
        }
        
        can_create = self.env.user.has_group('account_invoice_due_date_extension.group_invoice_extension_approver')
        if not can_create:
            action['flags'] = {'create': False}
        
        return action

