from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'
    
    invoice_extension_id = fields.Many2one(
        'account.invoice.due.date.extension',
        string='Prórroga de Factura',
        readonly=True,
        copy=False,
        help='Prórroga de factura asociada a esta aprobación'
    )
    
    def _compute_request_status(self):
        """Override para interceptar el cambio de estado y sincronizar con la prórroga"""
        # Guardar estados anteriores antes de que se recalculen
        old_statuses = {rec.id: rec.request_status for rec in self if rec.id}
        
        # Ejecutar el compute original
        res = super(ApprovalRequest, self)._compute_request_status()
        
        # Después del compute, verificar cambios y sincronizar
        for record in self:
            old_status = old_statuses.get(record.id)
            record._sync_invoice_extension_state(old_status, record.request_status)
        
        return res
    
    def _sync_invoice_extension_state(self, old_status, new_status):
        """Sincroniza el estado con la prórroga de factura asociada"""
        # Verificar si hay prórroga vinculada
        if not (self.id and self.invoice_extension_id):
            return
        
        # Verificar si hubo cambio de estado
        if not old_status or old_status == new_status:
            return
        
        # Sincronizar según el nuevo estado
        try:
            if new_status == 'approved' and old_status != 'approved':
                self.invoice_extension_id.with_context(from_approval=True)._approval_approved()
            elif new_status == 'refused' and old_status != 'refused':
                self.invoice_extension_id.with_context(from_approval=True)._approval_refused()
            elif new_status == 'cancel' and old_status != 'cancel':
                self.invoice_extension_id.with_context(from_approval=True)._approval_cancelled()
        except Exception as e:
            _logger.error(
                'Error al sincronizar estado de la prórroga %s: %s',
                self.invoice_extension_id.name, str(e)
            )

