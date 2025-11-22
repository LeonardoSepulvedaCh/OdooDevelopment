from odoo import fields
from odoo.http import request
from odoo.addons.portal_invoice_partner_grouping.controllers.portal import PortalAccountInherit


class PortalAccountExtension(PortalAccountInherit):
    """
    Sobrescribe el controlador del portal para considerar las prórrogas
    al determinar qué facturas están vencidas.
    """
    
    def _get_overdue_invoices_domain(self, partner_id=None):
        """
        Sobrescribe el dominio de facturas vencidas para usar effective_due_date
        en lugar de invoice_date_due.
        
        Este método es usado por el portal para determinar qué facturas mostrar
        como vencidas. Al usar effective_due_date, las facturas con prórroga
        aprobada no aparecerán como vencidas hasta que pase la fecha extendida.
        """
        return [
            ('state', 'not in', ('cancel', 'draft')),
            ('move_type', 'in', ('out_invoice', 'out_receipt')),
            ('payment_state', 'not in', ('in_payment', 'paid', 'reversed', 'blocked', 'invoicing_legacy')),
            ('effective_due_date', '<', fields.Date.today()),
            ('partner_id', '=', partner_id or request.env.user.partner_id.id),
        ]

