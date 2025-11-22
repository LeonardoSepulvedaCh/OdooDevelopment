from odoo import models, fields, api


class AccountMove(models.Model):
    """
    Extensión de account.move para añadir gestión de prórrogas en fechas de vencimiento.
    
    Añade un campo de fecha de vencimiento extendida que permite registrar prórrogas
    sin alterar la fecha de vencimiento original ni los asientos contables.
    """
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
        """
        Calcula el número de prórrogas aprobadas y activas para la factura.
        Solo las prórrogas aprobadas se consideran en el conteo.
        Usa lectura agrupada para evitar N+1.
        """
        # Inicializar todos los conteos a 0
        for move in self:
            move.extension_count = 0
        
        if not self.ids:
            return
        
        # Lectura agrupada para obtener conteos en bloque
        extension_data = self.env['account.invoice.due.date.extension'].read_group(
            domain=[
                ('invoice_id', 'in', self.ids),
                ('active', '=', True),
                ('state', '=', 'approved')
            ],
            fields=['invoice_id'],
            groupby=['invoice_id']
        )
        
        # Mapear los conteos a cada factura
        count_map = {data['invoice_id'][0]: data['invoice_id_count'] for data in extension_data}
        
        for move in self:
            move.extension_count = count_map.get(move.id, 0)

    @api.depends('extension_ids.extended_due_date', 'extension_ids.active', 'extension_ids.state', 'extension_ids.keep_discount')
    def _compute_extended_due_date(self):
        """
        Obtiene la fecha de prórroga del registro más reciente, activo y aprobado.
        Solo las prórrogas en estado 'approved' afectan la fecha de vencimiento efectiva.
        También obtiene el valor de keep_discount de esa prórroga.
        """
        for move in self:
            # Filtrar solo prórrogas activas Y aprobadas
            approved_extensions = move.extension_ids.filtered(lambda e: e.active and e.state == 'approved')
            if approved_extensions:
                # Ordenar por fecha de prórroga descendente y tomar la más reciente
                latest_extension = approved_extensions.sorted(lambda e: e.extended_due_date, reverse=True)[0]
                move.extended_due_date = latest_extension.extended_due_date
                move.extension_keep_discount = latest_extension.keep_discount
            else:
                move.extended_due_date = False
                move.extension_keep_discount = False

    @api.depends('extended_due_date', 'invoice_date_due')
    def _compute_effective_due_date(self):
        """
        Calcula la fecha de vencimiento efectiva.
        
        Si extended_due_date está definido, se usa ese valor.
        De lo contrario, se usa invoice_date_due.
        """
        for move in self:
            if move.extended_due_date:
                move.effective_due_date = move.extended_due_date
            else:
                move.effective_due_date = move.invoice_date_due

    @api.depends('effective_due_date', 'payment_state', 'state')
    def _compute_is_overdue(self):
        """
        Determina si la factura está vencida según la fecha efectiva.
        
        Una factura se considera vencida si:
        - Es una factura de cliente (out_invoice)
        - Está publicada (posted)
        - No está pagada completamente
        - La fecha de vencimiento efectiva es anterior a hoy
        """
        today = fields.Date.context_today(self)
        for move in self:
            # Solo aplica a facturas de cliente publicadas
            if move.move_type == 'out_invoice' and move.state == 'posted':
                # Verifica si está pagada
                is_not_paid = move.payment_state in ('not_paid', 'partial')
                # Verifica si tiene fecha de vencimiento efectiva y si ya pasó
                has_overdue_date = move.effective_due_date and move.effective_due_date < today
                move.is_overdue = is_not_paid and has_overdue_date
            else:
                move.is_overdue = False

    def _get_invoice_next_payment_values(self, custom_amount=None):
        """
        Sobrescribe el método para considerar la fecha de vencimiento extendida (prórroga)
        al determinar si una factura está vencida.
        
        Este método es usado por:
        - Portal de pagos de clientes
        - Sistema de pronto pago (early payment discount)
        - Otros módulos que consultan el estado de pago
        
        Cuando existe una prórroga aprobada (extended_due_date), se utiliza esta fecha
        en lugar de la fecha de vencimiento original para determinar si la factura
        está vencida, pero sin afectar la contabilidad.
        
        Además, maneja el descuento por pronto pago según el campo extension_keep_discount:
        - Si extension_keep_discount = True: mantiene el descuento EPD activo
        - Si extension_keep_discount = False: desactiva el descuento EPD durante la prórroga
        
        También desactiva el descuento EPD si la factura está vencida sin prórroga,
        ya que el descuento de "pronto pago" solo aplica si se paga dentro del plazo.
        """
        # Obtener valores originales del método padre
        result = super()._get_invoice_next_payment_values(custom_amount=custom_amount)
        
        # Early return: Si no hay resultado o no es una factura de cliente
        if not result or self.move_type not in ('out_invoice', 'out_refund'):
            return result
        
        # Aplicar lógica de prórroga o factura vencida
        if self.extended_due_date:
            self._apply_extension_logic(result)
        else:
            self._apply_overdue_logic(result)
        
        return result
    
    def _apply_extension_logic(self, result):
        """
        Aplica la lógica de prórroga a los valores de pago.
        Ajusta fechas, estado de vencimiento y gestión del descuento EPD.
        
        Args:
            result (dict): Diccionario con los valores de pago a modificar
        """
        today = fields.Date.context_today(self)
        is_paid = self.payment_state == 'paid'
        original_next_due_date = result.get('next_due_date')
        
        # Reemplazar la fecha de vencimiento con la fecha extendida
        result['next_due_date'] = self.extended_due_date
        
        # Actualizar installment_state según la fecha extendida
        self._update_installment_state_for_extension(result, today, is_paid)
        
        # Gestionar descuento EPD según extension_keep_discount
        result['epd_disabled_by_extension'] = not self.extension_keep_discount
        if not self.extension_keep_discount:
            self._disable_early_payment_discount(result)
        
        # Agregar información de la prórroga
        result.update({
            'has_extension': True,
            'original_due_date': original_next_due_date,
            'extended_due_date': self.extended_due_date,
            'extension_keep_discount': self.extension_keep_discount,
        })
    
    def _update_installment_state_for_extension(self, result, today, is_paid):
        """
        Actualiza el installment_state basándose en la fecha de prórroga.
        
        Args:
            result (dict): Diccionario con los valores de pago
            today (date): Fecha actual
            is_paid (bool): Si la factura está pagada
        """
        if is_paid:
            return
        
        is_overdue = self.extended_due_date < today
        was_overdue = result.get('installment_state') == 'overdue'
        
        if is_overdue:
            result['installment_state'] = 'overdue'
        elif was_overdue:
            # La factura ya no está vencida gracias a la prórroga
            result['installment_state'] = 'next'
    
    def _apply_overdue_logic(self, result):
        """
        Aplica la lógica cuando NO hay prórroga.
        Desactiva el descuento EPD si la factura está vencida.
        
        Args:
            result (dict): Diccionario con los valores de pago a modificar
        """
        result['has_extension'] = False
        result['epd_disabled_by_extension'] = False
        
        # Verificar si debe desactivar EPD por estar vencida
        is_overdue_without_extension = self._is_invoice_overdue_without_extension()
        has_epd = result.get('installment_state') == 'epd'
        
        if is_overdue_without_extension and has_epd:
            self._disable_early_payment_discount(result)
            result['epd_disabled_by_overdue'] = True
        else:
            result['epd_disabled_by_overdue'] = False
    
    def _is_invoice_overdue_without_extension(self):
        """
        Verifica si la factura está vencida sin prórroga.
        
        Returns:
            bool: True si está vencida sin prórroga
        """
        if self.payment_state == 'paid':
            return False
        
        if not self.invoice_date_due:
            return False
        
        today = fields.Date.context_today(self)
        return self.invoice_date_due < today
    
    def _disable_early_payment_discount(self, payment_values):
        """
        Método auxiliar para desactivar el descuento por pronto pago (EPD)
        en el diccionario de valores de pago.
        
        Args:
            payment_values (dict): Diccionario con los valores de pago a modificar
        """
        # Remover información del descuento por pronto pago
        if payment_values.get('installment_state') == 'epd':
            # Cambiar el estado de 'epd' a 'next'
            payment_values['installment_state'] = 'next'
            # El monto a pagar será el monto residual sin descuento
            payment_values['amount_due'] = self.amount_residual
            payment_values['next_amount_to_pay'] = self.amount_residual
            payment_values['next_payment_reference'] = self.name
        
        # Limpiar todos los campos relacionados con EPD
        payment_values.pop('epd_discount_amount_currency', None)
        payment_values.pop('epd_discount_amount', None)
        payment_values.pop('discount_date', None)
        payment_values.pop('epd_days_left', None)
        payment_values.pop('epd_line', None)
        payment_values.pop('epd_discount_msg', None)

    def action_view_extensions(self):
        """
        Acción para abrir la vista de prórrogas de esta factura.
        """
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
        
        # Solo los administradores o gestores pueden crear prórrogas
        can_create = self.env.user.has_group('account_invoice_due_date_extension.group_invoice_extension_approver')
        if not can_create:
            action['flags'] = {'create': False}
        
        return action

