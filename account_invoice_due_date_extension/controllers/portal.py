from odoo import fields
from odoo.http import request
from odoo.addons.portal_invoice_partner_grouping.controllers.portal import PortalAccountInherit


class PortalAccountExtension(PortalAccountInherit):
    """Extiende el controlador del portal para considerar prórrogas."""
    
    def _get_overdue_invoices_domain(self, partner_id=None):
        """Retorna dominio de facturas vencidas usando effective_due_date."""
        return [
            ('state', 'not in', ('cancel', 'draft')),
            ('move_type', 'in', ('out_invoice', 'out_receipt')),
            ('payment_state', 'not in', ('in_payment', 'paid', 'reversed', 'blocked', 'invoicing_legacy')),
            ('effective_due_date', '<', fields.Date.today()),
            ('partner_id', '=', partner_id or request.env.user.partner_id.id),
        ]

