from odoo import models, fields, api, _
from datetime import datetime, date

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
        default='opening',
        tracking=1
    )

    application_date = fields.Date(string='Fecha de Solicitud', required=True, default=fields.Date.context_today, index=True, copy=False)
    approved_date = fields.Date(string='Fecha de Aprobación', readonly=True, copy=False, tracking=1)
    rejected_date = fields.Date(string='Fecha de Rechazo', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Aprobado por', readonly=True, copy=False, tracking=1)

    final_normal_credit_quota = fields.Float(string='Cupo Normal Final', digits=(16, 2), default=0.0)
    final_golden_credit_quota = fields.Float(string='Cupo Dorado Final', digits=(16, 2), default=0.0)
    credit_quota_start_date = fields.Date(string='Fecha de Inicio del Cupo')
    credit_quota_end_date = fields.Date(string='Fecha de Fin del Cupo')
    property_payment_term_id = fields.Many2one('account.payment.term', string='Condiciones de Pago')

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

    average_days_to_pay = fields.Integer(string='Días Promedio de Pago', default=0, compute='_compute_average_days_to_pay', store=True)

    # Datos de los codeudores
    codeudor_ids = fields.One2many('sale.credit.codeudor', 'application_id', string='Codeudores', copy=True, tracking=1)
    
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
    total_purchased_this_year = fields.Float(string='Total Comprado Este Año', digits=(16, 2), default=0.0, compute='_compute_all_purchase_totals')
    total_purchased_last_year = fields.Float(string='Total Comprado Último Año (Año Pasado)', digits=(16, 2), default=0.0, compute='_compute_all_purchase_totals')
    total_purchased_last_two_years = fields.Float(string='Total Comprado Hace 2 Años', digits=(16, 2), default=0.0, compute='_compute_all_purchase_totals')
    total_purchased_last_three_years = fields.Float(string='Total Comprado Hace 3 Años', digits=(16, 2), default=0.0, compute='_compute_all_purchase_totals')
    count_purchased = fields.Integer(string='Cantidad de Compras', default=0, compute='_compute_all_purchase_totals')
    taked_discount = fields.Boolean(string='¿Tomó Descuentos?', default=False)
    normal_amount_debt = fields.Float(string='Monto de Deuda Normal (0-30 días)', digits=(16, 2), default=0.0, compute='_compute_normal_amount_debt')
    arrears_amount_debt = fields.Float(string='Monto de Deuda en Atraso (+30 días)', digits=(16, 2), default=0.0, compute='_compute_arrears_amount_debt')
    cartera_observations = fields.Text(string='Observaciones del area de Cartera')

    # Documentos relacionados
    related_partner_ids = fields.Many2many('res.partner', compute='_compute_related_partner_ids', string='Partners Relacionados', help='Cliente y codeudores de esta solicitud')
    document_ids = fields.Many2many('documents.document', compute='_compute_document_ids', string='Documentos', help='Documentos relacionados con el cliente y codeudores', tracking=1)

    # Campos de auditoría de la solicitud
    audit_cifin_observations = fields.Text(string='Observaciones sobre la CIFIN')
    audit_ctl_observations = fields.Text(string='Observaciones sobre el CTL')
    audit_is_reported_cifin = fields.Boolean(string='¿Fue Reportado en la CIFIN?', default=False)
    audit_debt_cifin = fields.Float(string='Deudas', digits=(16, 2), default=0.0)
    audit_is_late = fields.Boolean(string='¿Tiene deuda en mora?', default=False)
    audit_total_late_payment = fields.Float(string='Total de Mora', digits=(16, 2), default=0.0)

    # Onchange methods - para traer los datos del cliente
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            if not self.business_name:
                self.business_name = self.customer_id.l10n_co_edi_commercial_name
            
            if not self.business_city and self.customer_id.city:
                self.business_city = self.customer_id.city

            if not self.business_address and self.customer_id.street:
                self.business_address = self.customer_id.street
            
            self.property_payment_term_id = self.customer_id.property_payment_term_id
            
            # Solo si el asesor actual es el usuario por defecto o está vacío
            if (hasattr(self.customer_id, 'user_id') and 
                self.customer_id.user_id and 
                (not self.user_id or self.user_id == self.env.user)):
                self.user_id = self.customer_id.user_id

    @api.onchange('suggestion_normal_credit_quota', 'suggestion_golden_credit_quota')
    def _onchange_suggestion_quotas(self):
        if self.suggestion_normal_credit_quota and not self.final_normal_credit_quota:
            self.final_normal_credit_quota = self.suggestion_normal_credit_quota
        if self.suggestion_golden_credit_quota and not self.final_golden_credit_quota:
            self.final_golden_credit_quota = self.suggestion_golden_credit_quota

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        for vals in vals_list:
            if vals.get('name', 'Nueva Solicitud') == 'Nueva Solicitud':
                vals['name'] = self._generate_application_name()
        
        return super(SaleCreditQuotaApplication, self).create(vals_list)

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