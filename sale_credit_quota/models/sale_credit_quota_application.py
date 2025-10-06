from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import re

class SaleCreditQuotaApplication(models.Model):
    _name = 'sale.credit.quota.application'
    _description = 'Solicitud de Cupo de Crédito'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'application_date desc, name'
    
    # Datos de la solicitud
    name = fields.Char(string='Nombre', required=True, index=True, copy=False, readonly=True, default='Nueva Solicitud', help='Código único de la solicitud generado automáticamente')

    state = fields.Selection(
        string='Estado', 
        selection=[
            ('draft', 'Borrador'), 
            ('in_progress', 'En Proceso'), 
            ('approved', 'Aprobado'), 
            ('rejected', 'Rechazado')
        ], 
        required=True, 
        default='draft',
        index=True,
        tracking=1
    )
    branch_office = fields.Selection(
        string='Sucursal',
        selection=[
            ('bucaramanga', 'Bucaramanga'),
            ('bogota', 'Bogotá'),
            ('medellin', 'Medellín'),
            ('cali', 'Cali'),
            ('barranquilla', 'Barranquilla'),
            ('cucuta', 'Cúcuta'),
            ('coorporativo', 'Coorporativo'),
        ],
        required=True
    )
    subject = fields.Selection(
        string='Asunto',
        selection=[
            ('opening', 'Apertura de Cupo'),
            ('increase', 'Incremento de Cupo'),
            ('decrease', 'Decremento de Cupo'),
            ('maintain', 'Mentener Cupo'),
            ('comercial_condition', 'Condiciones Comerciales'),
            ('other', 'Otro'),
            ('penalty', 'Multa'),
            ('dac_sponsor', 'DAC Padrino'),
        ],
        required=True,
        default='opening'
    )

    application_date = fields.Date(string='Fecha de Solicitud', required=True, default=fields.Date.context_today, index=True, copy=False)
    approved_date = fields.Date(string='Fecha de Aprobación', readonly=True, copy=False)
    rejected_date = fields.Date(string='Fecha de Rechazo', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Aprobado por', readonly=True, copy=False, tracking=1)
    rejected_by = fields.Many2one('res.users', string='Rechazado por', readonly=True, copy=False)

    final_normal_credit_quota = fields.Float(string='Cupo Normal Final', digits=(16, 2), default=0.0)
    final_golden_credit_quota = fields.Float(string='Cupo Dorado Final', digits=(16, 2), default=0.0)
    credit_quota_start_date = fields.Date(string='Fecha de Inicio del Cupo')
    credit_quota_end_date = fields.Date(string='Fecha de Fin del Cupo')
    credit_quota_payment_terms_milan = fields.Many2one('account.payment.term', string='Condiciones de Pago Milan')
    credit_quota_payment_terms_optimus = fields.Many2one('account.payment.term', string='Condiciones de Pago Optimus')

    # Datos del cliente
    customer_id = fields.Many2one('res.partner', string='Cliente', required=True, index=True, tracking=2)
    customer_vat = fields.Char(string='Cédula del Cliente', related='customer_id.vat', store=True, readonly=False)
    customer_phone = fields.Char(string='Teléfono del Cliente', related='customer_id.phone', store=True, readonly=False)
    customer_mobile = fields.Char(string='Teléfono Móvil del Cliente', related='customer_id.mobile', store=True, readonly=False)
    customer_email = fields.Char(string='Correo del Cliente', related='customer_id.email', store=True, readonly=False)
    customer_birth_date = fields.Date(string='Fecha de Nacimiento del Cliente', related='customer_id.birth_date')
    customer_address = fields.Char(string='Dirección del Cliente', related='customer_id.street')
    customer_city = fields.Char(string='Ciudad del Cliente', related='customer_id.city')
    customer_state = fields.Char(string='Estado del Cliente')
    customer_years_of_activity = fields.Integer(string='Años de Actividad del Cliente', default=0)
    customer_child_ids = fields.Many2many('res.partner', compute='_compute_customer_child_ids', string='Clientes Hijos', help='Clientes hijos del cliente principal', store=True)
    customer_child_count = fields.Integer(string='Cantidad de Clientes Hijos', compute='_compute_customer_child_count', store=True)

    # Datos de los codeudores
    codeudor_ids = fields.One2many('sale.credit.codeudor', 'application_id', string='Codeudores', copy=True)
    
    # Datos del negocio
    business_name = fields.Char(string='Nombre del Negocio')
    business_address = fields.Char(string='Dirección del Negocio')
    business_city = fields.Char(string='Ciudad del Negocio', help='Ciudad donde se encuentra el negocio del cliente')
    business_years_of_activity = fields.Integer(string='Años de Actividad del Negocio', default=0)

    # Datos del asesor asignado
    user_id = fields.Many2one('res.users', string='Asesor Asignado', required=True, index=True, default=lambda self: self.env.user, tracking=3, domain=[('active', '=', True)], help='Asesor responsable de la solicitud')

    # Datos de la propuesta del asesor
    suggestion_normal_credit_quota = fields.Float(string='Cupo Normal Sugerido', digits=(16, 2), default=0.0)
    suggestion_golden_credit_quota = fields.Float(string='Cupo Dorado Sugerido', digits=(16, 2), default=0.0)
    good_points = fields.Text(string='Lo Bueno', help='Puntos a favor de la solicitud')
    bad_points = fields.Text(string='Lo Malo', help='Puntos en contra de la solicitud')
    new_points = fields.Text(string='Novedades', help='Novedades de la solicitud')

    # Datos de cartera
    total_purchased_this_year = fields.Float(string='Total Comprado Este Año', digits=(16, 2), default=0.0)
    total_purchased_last_year = fields.Float(string='Total Comprado Último Año', digits=(16, 2), default=0.0)
    total_purchased_last_two_years = fields.Float(string='Total Comprado Últimos 2 Años', digits=(16, 2), default=0.0)
    total_purchased_last_three_years = fields.Float(string='Total Comprado Últimos 3 Años', digits=(16, 2), default=0.0)
    taked_discount = fields.Boolean(string='¿Tomó Descuentos?', default=False)
    normal_amount_debt = fields.Float(string='Monto de Deuda Normal (0-30 días)', digits=(16, 2), default=0.0)
    arrears_amount_debt = fields.Float(string='Monto de Deuda en Atraso (+30 días)', digits=(16, 2), default=0.0)
    cartera_observations = fields.Text(string='Observaciones del area de Cartera')

    # Documentos relacionados
    related_partner_ids = fields.Many2many('res.partner', compute='_compute_related_partner_ids', string='Partners Relacionados', help='Cliente y codeudores de esta solicitud')
    document_ids = fields.Many2many('documents.document', compute='_compute_document_ids', string='Documentos', help='Documentos relacionados con el cliente y codeudores')

    # Valida que la fecha de fin del cupo sea posterior a la fecha de inicio
    @api.constrains('credit_quota_start_date', 'credit_quota_end_date')
    def _check_credit_quota_dates(self):
        for record in self:
            if record.credit_quota_start_date and record.credit_quota_end_date:
                if record.credit_quota_end_date < record.credit_quota_start_date:
                    raise ValidationError(
                        _('La fecha de fin del cupo debe ser posterior a la fecha de inicio.')
                    )

    # Valida que los cupos no sean negativos
    @api.constrains('final_normal_credit_quota', 'final_golden_credit_quota')
    def _check_credit_quotas(self):
        for record in self:
            if record.final_normal_credit_quota < 0:
                raise ValidationError(
                    _('El cupo normal final no puede ser negativo.')
                )
            if record.final_golden_credit_quota < 0:
                raise ValidationError(
                    _('El cupo dorado final no puede ser negativo.')
                )

    # Valida que los cupos sugeridos no sean negativos
    @api.constrains('suggestion_normal_credit_quota', 'suggestion_golden_credit_quota')
    def _check_suggestion_quotas(self):
        for record in self:
            if record.suggestion_normal_credit_quota < 0:
                raise ValidationError(
                    _('El cupo normal sugerido no puede ser negativo.')
                )
            if record.suggestion_golden_credit_quota < 0:
                raise ValidationError(
                    _('El cupo dorado sugerido no puede ser negativo.')
                )

    # Valida que los años de actividad no sean negativos
    @api.constrains('customer_years_of_activity', 'business_years_of_activity')
    def _check_years_of_activity(self):
        for record in self:
            if record.customer_years_of_activity < 0:
                raise ValidationError(
                    _('Los años de actividad del cliente no pueden ser negativos.')
                )
            if record.business_years_of_activity < 0:
                raise ValidationError(
                    _('Los años de actividad del negocio no pueden ser negativos.')
                )

    # Onchange methods
    # Prellenar datos del cliente cuando se selecciona
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            if not self.business_name:
                self.business_name = self.customer_id.l10n_co_edi_commercial_name
            
            if not self.business_city and self.customer_id.city:
                self.business_city = self.customer_id.city

            if not self.business_address and self.customer_id.street:
                self.business_address = self.customer_id.street
            
            # Solo si el asesor actual es el usuario por defecto o está vacío
            if (hasattr(self.customer_id, 'user_id') and 
                self.customer_id.user_id and 
                (not self.user_id or self.user_id == self.env.user)):
                self.user_id = self.customer_id.user_id

    # Sugerir prellenar los cupos finales con los sugeridos
    @api.onchange('suggestion_normal_credit_quota', 'suggestion_golden_credit_quota')
    def _onchange_suggestion_quotas(self):
        if self.suggestion_normal_credit_quota and not self.final_normal_credit_quota:
            self.final_normal_credit_quota = self.suggestion_normal_credit_quota
        if self.suggestion_golden_credit_quota and not self.final_golden_credit_quota:
            self.final_golden_credit_quota = self.suggestion_golden_credit_quota

    # Generar automáticamente el nombre de la solicitud antes de crear el registro
    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        for vals in vals_list:
            if vals.get('name', 'Nueva Solicitud') == 'Nueva Solicitud':
                vals['name'] = self._generate_application_name()
        
        return super(SaleCreditQuotaApplication, self).create(vals_list)

    # Generar el nombre consecutivo de la solicitud en formato SC-YYYYMM-#####
    def _generate_application_name(self):
        now = fields.Datetime.now()
        year_month = now.strftime('%Y%m')
        
        prefix = f"SC-{year_month}-"
        
        last_application = self.search([
            ('name', 'like', prefix),
            ('name', 'not in', ['Nueva Solicitud', 'Nuevo'])
        ], limit=1, order='name desc')
        
        if last_application and last_application.name.startswith(prefix):
            last_number_str = last_application.name.replace(prefix, '')
            if last_number_str.isdigit():
                last_number = int(last_number_str)
                next_number = last_number + 1
            else:
                next_number = 1
        else:
            next_number = 1
        
        sequence = f"{next_number:05d}"
        return f"{prefix}{sequence}"

    # Obtener los clientes hijos del cliente principal
    @api.depends('customer_id')
    def _compute_customer_child_ids(self):
        for record in self:
            if record.customer_id:
                child_partners = self.env['res.partner'].search([
                    ('parent_id', '=', record.customer_id.id)
                ])
                record.customer_child_ids = [(6, 0, child_partners.ids)]
            else:
                record.customer_child_ids = [(6, 0, [])]

    # Contar los clientes hijos
    @api.depends('customer_child_ids')
    def _compute_customer_child_count(self):
        for record in self:
            record.customer_child_count = len(record.customer_child_ids)

    # Obtener los contactos relacionados (cliente + codeudores)
    @api.depends('customer_id', 'codeudor_ids.partner_id')
    def _compute_related_partner_ids(self):
        for record in self:
            partner_ids = []
            
            if record.customer_id:
                partner_ids.append(record.customer_id.id)
            
            if record.codeudor_ids:
                partner_ids.extend(record.codeudor_ids.mapped('partner_id').ids)
            
            record.related_partner_ids = [(6, 0, partner_ids)]

    # Obtener los documentos relacionados con los partners
    @api.depends('related_partner_ids')
    def _compute_document_ids(self):
        for record in self:
            if record.related_partner_ids:
                documents = self.env['documents.document'].search([
                    ('partner_id', 'in', record.related_partner_ids.ids),
                    ('type', '!=', 'folder')
                ])
                record.document_ids = [(6, 0, documents.ids)]
            else:
                record.document_ids = [(6, 0, [])]
    
    # Acción para abrir la vista de clientes hijos
    def action_view_customer_children(self):
        self.ensure_one()

        if self.customer_id:
            direct_children = self.env['res.partner'].search([
                ('parent_id', '=', self.customer_id.id)
            ])
            
            if not direct_children:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sin clientes hijos'),
                        'message': _('El cliente %s no tiene contactos hijos asociados.') % self.customer_id.name,
                        'type': 'warning',
                    }
                }
            
            return {
                'name': _('Clientes Hijos de %s (%d)') % (self.customer_id.name, len(direct_children)),
                'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'view_mode': 'list,form',
                'domain': [('id', 'in', direct_children.ids)],
                'context': {
                    'default_parent_id': self.customer_id.id,
                    'default_is_company': False,
                },
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No hay cliente seleccionado.'),
                    'type': 'danger',
                }
            }
    
    # Abrir un wizard para seleccionar el contacto antes de cargar documentos
    def action_open_documents(self):
        self.ensure_one()
        
        wizard = self.env['sale.credit.quota.document.wizard'].create({
            'application_id': self.id,
            'partner_id': self.customer_id.id if self.customer_id else False,
        })
        
        return {
            'name': _('Seleccionar Contacto para Asociar Documentos'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.credit.quota.document.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    