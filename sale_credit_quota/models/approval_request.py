from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'
    
    credit_quota_application_id = fields.Many2one(
        'sale.credit.quota.application', 
        string='Solicitud de Cupo de Crédito',
        readonly=True,
        copy=False,
        help='Solicitud de cupo de crédito asociada a esta aprobación'
    )
    
    def _compute_request_status(self):
        """Override para interceptar el cambio de estado y sincronizar con solicitud de cupo"""
        # Guardar estados anteriores antes de que se recalculen
        old_statuses = {rec.id: rec.request_status for rec in self if rec.id}
        
        # Ejecutar el compute original
        res = super(ApprovalRequest, self)._compute_request_status()
        
        # Después del compute, verificar cambios y sincronizar
        for record in self:
            if record.id and record.credit_quota_application_id:
                old_status = old_statuses.get(record.id)
                new_status = record.request_status
                
                # Detectar cambio de estado
                if old_status and old_status != new_status:
                    try:
                        if new_status == 'approved' and old_status != 'approved':
                            record.credit_quota_application_id.with_context(from_approval=True)._approval_approved()
                        elif new_status == 'refused' and old_status != 'refused':
                            record.credit_quota_application_id.with_context(from_approval=True)._approval_refused()
                    except Exception as e:
                        _logger.error(
                            'Error al sincronizar estado de la solicitud de cupo %s: %s',
                            record.credit_quota_application_id.name, str(e)
                        )
        
        return res
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create para vincular bidireccionalmente con la solicitud de cupo"""
        records = super(ApprovalRequest, self).create(vals_list)
        
        for record in records:
            # Si ya viene el campo credit_quota_application_id en vals, ya está vinculado
            # Si no, intentar buscar por referencia
            if not record.credit_quota_application_id and record.reference:
                credit_quota_app = self.env['sale.credit.quota.application'].search([
                    ('name', '=', record.reference)
                ], limit=1)
                
                if credit_quota_app and credit_quota_app.approval_request_id == record:
                    record.credit_quota_application_id = credit_quota_app.id
        
        return records

