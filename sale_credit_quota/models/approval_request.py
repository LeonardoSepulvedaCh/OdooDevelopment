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
            old_status = old_statuses.get(record.id)
            record._sync_credit_quota_state(old_status, record.request_status)
        
        return res
    
    def _sync_credit_quota_state(self, old_status, new_status):
        """Sincroniza el estado con la solicitud de cupo de crédito asociada"""
        # Verificar si hay solicitud de cupo vinculada
        if not (self.id and self.credit_quota_application_id):
            return
        
        # Verificar si hubo cambio de estado
        if not old_status or old_status == new_status:
            return
        
        # Sincronizar según el nuevo estado
        try:
            if new_status == 'approved' and old_status != 'approved':
                self.credit_quota_application_id.with_context(from_approval=True)._approval_approved()
            elif new_status == 'refused' and old_status != 'refused':
                self.credit_quota_application_id.with_context(from_approval=True)._approval_refused()
        except Exception as e:
            _logger.error(
                'Error al sincronizar estado de la solicitud de cupo %s: %s',
                self.credit_quota_application_id.name, str(e)
            )

