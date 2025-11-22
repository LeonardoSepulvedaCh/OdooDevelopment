from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import html_escape


class AccountInvoiceDueDateExtension(models.Model):
    """
    Modelo para registrar prórrogas en fechas de vencimiento de facturas.
    
    Cada registro representa una prórroga autorizada para una factura específica.
    """
    _name = 'account.invoice.due.date.extension'
    _description = 'Prórroga de Fecha de Vencimiento de Factura'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc, create_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Número de Prórroga',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: 'Nuevo',
        help="Número consecutivo de la prórroga"
    )
    
    state = fields.Selection(
        string='Estado',
        selection=[
            ('draft', 'Borrador'),
            ('approved', 'Aprobado'),
            ('rejected', 'Rechazado'),
            ('cancelled', 'Cancelado')
        ],
        required=True,
        default='draft',
        index=True,
        tracking=True,
        help="Estado de la prórroga"
    )
    
    keep_discount = fields.Boolean(
        string='Mantener Descuento',
        default=False,
        tracking=True,
        help="Indica si el descuento de pago anticipado continúa aplicando con la prórroga"
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
        domain="[('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted'), ('payment_state', '!=', 'paid')]",
        ondelete='cascade',
        index=True,
        help="Factura a la que se aplicará la prórroga"
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='invoice_id.partner_id',
        store=True,
        readonly=True
    )
    
    invoice_date = fields.Date(
        string='Fecha de Factura',
        related='invoice_id.invoice_date',
        store=True,
        readonly=True
    )
    
    original_due_date = fields.Date(
        string='Fecha de Vencimiento Original',
        related='invoice_id.invoice_date_due',
        store=True,
        readonly=True
    )
    
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Término de Pago',
        related='invoice_id.invoice_payment_term_id',
        store=True,
        readonly=True,
        help="Término de pago acordado en la factura"
    )
    
    extended_due_date = fields.Date(
        string='Nueva Fecha de Vencimiento',
        required=True,
        tracking=True,
        help="Nueva fecha de vencimiento acordada con el cliente"
    )
    
    reason = fields.Text(
        string='Motivo de la Prórroga',
        tracking=True,
        help="Razón por la cual se otorga la prórroga"
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Autorizado por',
        default=lambda self: self.env.user,
        readonly=True,
        help="Usuario que autorizó la prórroga"
    )
    
    create_date = fields.Datetime(
        string='Fecha de Creación',
        readonly=True
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        tracking=True,
        help="Si está inactivo, esta prórroga no se considerará"
    )
    
    amount_total = fields.Monetary(
        string='Total de la Factura',
        related='invoice_id.amount_total',
        currency_field='currency_id',
        readonly=True
    )
    
    amount_residual = fields.Monetary(
        string='Saldo Pendiente',
        related='invoice_id.amount_residual',
        currency_field='currency_id',
        readonly=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='invoice_id.currency_id',
        readonly=True
    )
    
    payment_state = fields.Selection(
        related='invoice_id.payment_state',
        readonly=True,
        store=True
    )
    
    # Campo de integración con la app de Aprobaciones
    approval_request_id = fields.Many2one(
        'approval.request',
        string='Solicitud de Aprobación',
        readonly=True,
        copy=False,
        tracking=True,
        ondelete='set null',
        help="Solicitud de aprobación asociada a esta prórroga"
    )
    
    approved_date = fields.Date(
        string='Fecha de Aprobación',
        readonly=True,
        copy=False,
        tracking=True
    )
    
    rejected_date = fields.Date(
        string='Fecha de Rechazo',
        readonly=True,
        copy=False
    )
    
    approved_by = fields.Many2one(
        'res.users',
        string='Aprobado por',
        copy=False,
        tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Genera el número consecutivo al crear una prórroga.
        """
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('account.invoice.due.date.extension') or 'Nuevo'
        return super().create(vals_list)

    @api.constrains('invoice_id', 'active', 'state')
    def _check_unique_approved_extension(self):
        """
        Valida que solo exista una prórroga aprobada y activa por factura.
        Permite múltiples prórrogas en estado borrador, rechazado o cancelado.
        """
        for record in self:
            # Solo validar unicidad para prórrogas aprobadas
            if record.active and record.invoice_id and record.state == 'approved':
                # Buscar otras prórrogas aprobadas y activas para la misma factura
                other_approved = self.search([
                    ('invoice_id', '=', record.invoice_id.id),
                    ('active', '=', True),
                    ('state', '=', 'approved'),
                    ('id', '!=', record.id)
                ])
                if other_approved:
                    raise ValidationError(
                        f"Ya existe una prórroga aprobada ({other_approved[0].name}) para la factura {record.invoice_id.name}.\n"
                        "Solo puede existir una prórroga aprobada por factura. Debe cancelar la prórroga existente antes de aprobar una nueva."
                    )

    @api.constrains('extended_due_date', 'original_due_date')
    def _check_extended_due_date(self):
        """
        Valida que la fecha de prórroga sea posterior a la fecha original.
        """
        for record in self:
            if record.original_due_date and record.extended_due_date:
                if record.extended_due_date < record.original_due_date:
                    raise ValidationError(
                        f"La nueva fecha de vencimiento ({record.extended_due_date}) debe ser igual o posterior "
                        f"a la fecha de vencimiento original ({record.original_due_date})."
                    )

    @api.constrains('invoice_id')
    def _check_invoice_not_paid(self):
        """
        Valida que la factura no esté completamente pagada.
        """
        for record in self:
            if record.invoice_id.payment_state == 'paid':
                raise ValidationError(
                    "No se puede crear una prórroga para una factura que ya está pagada completamente."
                )
    
    def action_send_to_approval(self):
        """Envía la prórroga a la app de Aprobaciones"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise ValidationError('Solo se pueden enviar a aprobación las prórrogas en estado borrador.')
        
        if self.approval_request_id:
            raise ValidationError('Esta prórroga ya tiene una solicitud de aprobación asociada.')
        
        # Validar que no existan otras prórrogas aprobadas para esta factura
        other_approved_extensions = self.search([
            ('invoice_id', '=', self.invoice_id.id),
            ('active', '=', True),
            ('state', '=', 'approved'),
            ('id', '!=', self.id)
        ])
        if other_approved_extensions:
            raise ValidationError(
                f"No se puede enviar a aprobación porque ya existe una prórroga aprobada ({other_approved_extensions[0].name}) "
                f"para la factura {self.invoice_id.name}.\n"
                "Solo puede existir una prórroga aprobada por factura. Debe cancelar la prórroga existente antes de enviar una nueva."
            )
        
        # Obtener la categoría de aprobación
        approval_category = self.env.ref(
            'account_invoice_due_date_extension.approval_category_invoice_extension',
            raise_if_not_found=False
        )
        if not approval_category:
            raise ValidationError('No se encontró la categoría de aprobación para prórrogas de facturas.')
        
        # Preparar los valores para la solicitud de aprobación
        approval_vals = {
            'name': f'Prórroga - {self.name}',
            'category_id': approval_category.id,
            'request_owner_id': self.user_id.id or self.env.user.id,
            'partner_id': self.partner_id.id,
            'reference': self.name,
            'amount': self.amount_residual,
            'reason': self._get_approval_reason_html(),
            'date': fields.Datetime.to_datetime(self.extended_due_date) if self.extended_due_date else False,
            'date_confirmed': False,
        }
        
        # Crear la solicitud de aprobación
        approval_request = self.env['approval.request'].create(approval_vals)
        
        # Vincular bidireccionalmente
        self.write({'approval_request_id': approval_request.id})
        approval_request.write({'invoice_extension_id': self.id})
        
        # Enviar automáticamente la solicitud (confirmar)
        approval_request.action_confirm()
        
        # Mensaje en la prórroga
        self.message_post(
            body=f'Solicitud enviada a aprobación: {approval_request.name}',
            message_type='notification'
        )
        
        # Retornar acción para abrir la solicitud de aprobación
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'res_id': approval_request.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _get_approval_reason_html(self):
        """Genera el HTML con la información de la prórroga para la app de Aprobaciones"""
        self.ensure_one()
        
        keep_discount_text = 'Sí' if self.keep_discount else 'No'
        
        # Escapar todos los valores para prevenir XSS
        invoice_name = html_escape(self.invoice_id.name or '')
        partner_name = html_escape(self.partner_id.name or '')
        invoice_date = html_escape(str(self.invoice_date or ''))
        original_due_date = html_escape(str(self.original_due_date or ''))
        extended_due_date = html_escape(str(self.extended_due_date or ''))
        payment_state_label = html_escape(dict(self.invoice_id._fields['payment_state'].selection).get(self.payment_state, ''))
        reason_text = html_escape(self.reason or 'Sin motivo especificado')
        user_name = html_escape(self.user_id.name or '')
        
        reason = f"""
        <div>
            <h3>Información de la Prórroga</h3>
            <ul>
                <li><strong>Factura:</strong> {invoice_name}</li>
                <li><strong>Cliente:</strong> {partner_name}</li>
                <li><strong>Fecha de Factura:</strong> {invoice_date}</li>
                <li><strong>Fecha de Vencimiento Original:</strong> {original_due_date}</li>
                <li><strong>Nueva Fecha de Vencimiento:</strong> {extended_due_date}</li>
            </ul>
            
            <h3>Información Financiera</h3>
            <ul>
                <li><strong>Total de la Factura:</strong> ${self.amount_total:,.2f}</li>
                <li><strong>Saldo Pendiente:</strong> ${self.amount_residual:,.2f}</li>
                <li><strong>Estado de Pago:</strong> {payment_state_label}</li>
                <li><strong>Mantener Descuento:</strong> {keep_discount_text}</li>
            </ul>
            
            <h3>Justificación</h3>
            <p>{reason_text}</p>
            
            <h3>Solicitado por</h3>
            <p>{user_name}</p>
        </div>
        """
        
        return reason
    
    def action_view_approval_request(self):
        """Abre la solicitud de aprobación relacionada"""
        self.ensure_one()
        
        if not self.approval_request_id:
            raise ValidationError('Esta prórroga no tiene una solicitud de aprobación asociada.')
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'res_id': self.approval_request_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _approval_approved(self):
        """Método llamado cuando la solicitud de aprobación es aprobada"""
        self.ensure_one()
        
        # Verificar que no esté ya aprobado para evitar ejecutar la lógica múltiples veces
        if self.state == 'approved':
            return
        
        values = {
            'state': 'approved',
            'approved_date': fields.Date.context_today(self),
        }
        
        # Obtener el usuario que aprobó (último aprobador)
        if self.approval_request_id and self.approval_request_id.approver_ids:
            approved_by_users = self.approval_request_id.approver_ids.filtered(
                lambda a: a.status == 'approved'
            ).mapped('user_id')
            if approved_by_users:
                values['approved_by'] = approved_by_users[-1].id
        
        self.write(values)
        
        approver_name = self.approved_by.name if self.approved_by else 'Sistema'
        
        self.message_post(
            body=f'Prórroga aprobada por {approver_name} el {fields.Date.context_today(self)} (vía App de Aprobaciones)',
            message_type='notification'
        )
    
    def _approval_refused(self):
        """Método llamado cuando la solicitud de aprobación es rechazada"""
        self.ensure_one()
        
        self.write({
            'state': 'rejected',
            'rejected_date': fields.Date.context_today(self),
        })
        
        self.message_post(
            body=f'Prórroga rechazada el {fields.Date.context_today(self)} (vía App de Aprobaciones)',
            message_type='notification'
        )
    
    def _approval_cancelled(self):
        """Método llamado cuando la solicitud de aprobación es cancelada"""
        self.ensure_one()
        
        # Si la prórroga ya está cancelada, no hacer nada
        if self.state == 'cancelled':
            return
        
        self.write({'state': 'cancelled'})
        
        self.message_post(
            body=f'Prórroga cancelada automáticamente el {fields.Date.context_today(self)} porque la solicitud de aprobación fue cancelada',
            message_type='notification'
        )
    
    def action_cancel(self):
        """Cancela la prórroga"""
        self.ensure_one()
        
        if self.state == 'cancelled':
            raise ValidationError('Esta prórroga ya está cancelada.')
        
        self.write({'state': 'cancelled'})
        
        # Si tiene solicitud de aprobación asociada, cancelarla también
        # Solo si no viene desde la app de aprobaciones (para evitar loops)
        if not self.env.context.get('from_approval') and self.approval_request_id:
            if self.approval_request_id.request_status not in ('cancel', 'refused'):
                self.approval_request_id.action_cancel()
                self.approval_request_id.message_post(
                    body=f'Solicitud de aprobación cancelada automáticamente porque la prórroga {self.name} fue cancelada.',
                    message_type='notification'
                )
        
        self.message_post(
            body='Prórroga cancelada',
            message_type='notification'
        )
    
    def action_reset_to_draft(self):
        """Restablece la prórroga a estado borrador"""
        self.ensure_one()
        
        if self.state == 'draft':
            raise ValidationError('Esta prórroga ya está en estado borrador.')
        
        if self.state == 'approved':
            raise ValidationError('No se puede regresar a borrador una prórroga aprobada.')
        
        # Limpiar campos relacionados con la aprobación para permitir reenvío
        self.write({
            'state': 'draft',
            'approval_request_id': False,
            'approved_by': False,
            'approved_date': False,
            'rejected_date': False,
        })
        
        self.message_post(
            body='Prórroga restablecida a borrador',
            message_type='notification'
        )

