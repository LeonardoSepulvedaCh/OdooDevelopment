from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleCreditQuotaDocumentWizard(models.TransientModel):
    _name = 'sale.credit.quota.document.wizard'
    _description = 'Asistente para Agregar Documentos a la Solicitud'

    application_id = fields.Many2one(
        'sale.credit.quota.application',
        string='Solicitud',
        required=True,
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Contacto',
        required=True,
        help='Seleccione el contacto al que desea asociar los documentos'
    )
    partner_ids = fields.Many2many(
        'res.partner',
        string='Contactos Disponibles',
        compute='_compute_partner_ids',
        help='Lista de contactos relacionados con la solicitud (cliente y codeudores)'
    )

    # Calcula los partners disponibles (cliente + codeudores)
    @api.depends('application_id')
    def _compute_partner_ids(self):
        for wizard in self:
            partner_ids = []
            if wizard.application_id:
                if wizard.application_id.customer_id:
                    partner_ids.append(wizard.application_id.customer_id.id)
                if wizard.application_id.codeudor_ids:
                    partner_ids.extend(wizard.application_id.codeudor_ids.mapped('partner_id').ids)
            wizard.partner_ids = [(6, 0, partner_ids)]

    # Abre la interfaz de documentos con el partner seleccionado
    def action_open_documents(self):
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_('Debe seleccionar un contacto antes de continuar.'))
        
        # Recopilar todos los partners relacionados para el filtro
        partner_ids = []
        if self.application_id.customer_id:
            partner_ids.append(self.application_id.customer_id.id)
        if self.application_id.codeudor_ids:
            partner_ids.extend(self.application_id.codeudor_ids.mapped('partner_id').ids)
        
        # Construir el dominio para filtrar por partners relacionados
        if partner_ids:
            domain = [
                ('partner_id', 'in', partner_ids),
                ('type', '!=', 'folder')
            ]
        else:
            domain = [('id', '=', False)]
        
        # Usar la acción de cliente que proporciona la interfaz completa de documentos
        action = self.env['ir.actions.actions']._for_xml_id('documents.document_action_preference')
        
        # Contexto para pre-llenar el partner_id seleccionado
        context = {
            'searchpanel_default_user_folder_id': False,
            'default_type': 'binary',
            'default_partner_id': self.partner_id.id,
            'search_default_partner_id': self.partner_id.id,
        }
        
        return action | {
            'name': _('Documentos de %s - Solicitud %s') % (self.partner_id.name, self.application_id.name),
            'domain': domain,
            'context': context,
        }

