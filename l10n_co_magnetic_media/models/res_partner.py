# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    """
    Extensión del modelo res.partner para gestión de Medios Magnéticos.
    
    Este modelo extiende res.partner para agregar campos tributarios
    requeridos en los informes de exógenas de Colombia.
    
    Los campos de nombres y apellidos son heredados del módulo
    contacts_name_split y se reorganizan en la vista.
    """
    _inherit = 'res.partner'
    
    # ===========================
    # CAMPOS TRIBUTARIOS
    # ===========================
    
    l10n_co_tax_regime_id = fields.Many2one(
        comodel_name='l10n_co.tax.regime',
        string='Régimen Tributario',
        index=True,
        tracking=True,
        help='Régimen tributario del contacto según clasificación DIAN'
    )
    
    l10n_co_document_type_id = fields.Many2one(
        comodel_name='l10n_co.document.type',
        string='Tipo de Documento',
        index=True,
        tracking=True,
        help='Tipo de documento de identificación según clasificación DIAN'
    )
    
    l10n_co_economic_activity_id = fields.Many2one(
        comodel_name='l10n_co.economic.activity',
        string='Actividad Económica',
        index=True,
        tracking=True,
        help='Actividad económica del contacto según clasificación CIIU'
    )
    
    l10n_co_entity_type_id = fields.Many2one(
        comodel_name='l10n_co.entity.type',
        string='Tipo Entidad',
        compute='_compute_l10n_co_entity_type_id',
        inverse='_inverse_l10n_co_entity_type_id',
        store=True,
        index=True,
        tracking=True,
        help='Tipo de entidad: Natural (Persona) o Jurídico (Empresa). '
             'Se sincroniza automáticamente con el campo Persona/Empresa.'
    )
    
    l10n_co_nationality_id = fields.Many2one(
        comodel_name='l10n_co.nationality',
        string='Nacionalidad',
        index=True,
        tracking=True,
        help='Nacionalidad del contacto para efectos tributarios'
    )
    
    l10n_co_foreign_type_id = fields.Many2one(
        comodel_name='l10n_co.foreign.type',
        string='Tipo Extranjero',
        index=True,
        tracking=True,
        help='Tipo de extranjero: aplica solo si la nacionalidad es Extranjero'
    )
    
    l10n_co_fiscal_regime_id = fields.Many2one(
        comodel_name='l10n_co.fiscal.regime',
        string='Régimen Fiscal',
        index=True,
        tracking=True,
        default=lambda self: self.env.ref('l10n_co_magnetic_media.l10n_co_fiscal_regime_49', raise_if_not_found=False),
        domain="['|', ('vigencia_hasta', '=', False), ('vigencia_hasta', '>=', context_today())]",
        help='Régimen fiscal del contacto para facturación electrónica. '
             'Por defecto: No responsable de IVA. Solo se muestran regímenes vigentes.'
    )
    
    l10n_co_edi_payment_option_id = fields.Many2one(
        comodel_name='l10n_co_edi.payment.option',
        string='Medio de Pago',
        index=True,
        tracking=True,
        default=lambda self: self.env.ref('l10n_co_edi.payment_option_9', raise_if_not_found=False),
        help='Medio de pago para facturación electrónica y reportes de Medios Magnéticos. '
             'Por defecto: 10 - Efectivo. Este campo utiliza el catálogo nativo de Odoo para Colombia.'
    )
    
    l10n_co_discount_code_id = fields.Many2one(
        comodel_name='l10n_co.discount.code',
        string='Código de Descuento',
        index=True,
        tracking=True,
        help='Código de descuento aplicable al contacto para reportes de Medios Magnéticos. '
             'Clasifica el tipo de descuento según normativa DIAN.'
    )
    
    l10n_co_resident = fields.Selection(
        selection=[('SI', 'Sí'), ('NO', 'No')],
        string='Residente',
        tracking=True,
        help='Indica si el contacto es residente o no residente en Colombia '
             'para efectos de reportes de Medios Magnéticos.'
    )
    
    l10n_co_tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='res_partner_l10n_co_account_tax_rel',
        column1='partner_id',
        column2='tax_id',
        string='Impuestos',
        tracking=True,
        domain="[('active', '=', True), ('type_tax_use', 'in', ['sale', 'purchase'])]",
        help='Impuestos y retenciones que aplican a este contacto para efectos de facturación. '
             'Estos impuestos se utilizarán automáticamente en facturas de venta, compra y legalizaciones.'
    )
    
    # ===========================
    # MÉTODOS COMPUTADOS
    # ===========================
    
    @api.depends('company_type')
    def _compute_l10n_co_entity_type_id(self):
        """
        Sincroniza el Tipo de Entidad con el campo company_type de Odoo.
        - company_type = 'person' → Tipo Entidad = 1 (Natural)
        - company_type = 'company' → Tipo Entidad = 2 (Jurídico)
        """
        entity_type_natural = self.env.ref('l10n_co_magnetic_media.l10n_co_entity_type_1', raise_if_not_found=False)
        entity_type_juridico = self.env.ref('l10n_co_magnetic_media.l10n_co_entity_type_2', raise_if_not_found=False)
        
        for partner in self:
            if partner.company_type == 'company':
                partner.l10n_co_entity_type_id = entity_type_juridico
            else:  # 'person' o cualquier otro valor por defecto
                partner.l10n_co_entity_type_id = entity_type_natural
    
    def _inverse_l10n_co_entity_type_id(self):
        """
        Sincronización inversa: si el usuario cambia el Tipo de Entidad,
        actualiza el campo company_type de Odoo.
        - Tipo Entidad = 1 (Natural) → company_type = 'person'
        - Tipo Entidad = 2 (Jurídico) → company_type = 'company'
        """
        for partner in self:
            if partner.l10n_co_entity_type_id:
                if partner.l10n_co_entity_type_id.code == '2':
                    partner.company_type = 'company'
                else:  # code == '1' o cualquier otro valor
                    partner.company_type = 'person'
    
    @api.onchange('company_type')
    def _onchange_company_type(self):
        """
        Proporciona feedback inmediato en la UI cuando cambia el RadioButton.
        """
        entity_type_natural = self.env.ref('l10n_co_magnetic_media.l10n_co_entity_type_1', raise_if_not_found=False)
        entity_type_juridico = self.env.ref('l10n_co_magnetic_media.l10n_co_entity_type_2', raise_if_not_found=False)
        
        if self.company_type == 'company':
            self.l10n_co_entity_type_id = entity_type_juridico
        else:
            self.l10n_co_entity_type_id = entity_type_natural
    
    @api.onchange('l10n_co_nationality_id')
    def _onchange_l10n_co_nationality_id(self):
        """
        Sincroniza automáticamente el Tipo de Extranjero según la Nacionalidad:
        - Nacional (1) → Tipo Extranjero = No aplica (0)
        - Extranjero (2) → Tipo Extranjero = Sin Clave (2) por defecto
        """
        if self.l10n_co_nationality_id:
            # Si es Nacional, asignar "No aplica"
            if self.l10n_co_nationality_id.code == '1':
                foreign_type_no_aplica = self.env.ref('l10n_co_magnetic_media.l10n_co_foreign_type_0', raise_if_not_found=False)
                self.l10n_co_foreign_type_id = foreign_type_no_aplica
            # Si es Extranjero, asignar "Sin Clave" por defecto (pero el usuario puede cambiar)
            elif self.l10n_co_nationality_id.code == '2':
                # Solo asignar si está vacío
                if not self.l10n_co_foreign_type_id:
                    foreign_type_sin_clave = self.env.ref('l10n_co_magnetic_media.l10n_co_foreign_type_2', raise_if_not_found=False)
                    self.l10n_co_foreign_type_id = foreign_type_sin_clave

