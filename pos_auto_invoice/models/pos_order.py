from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Extender los campos de la orden para incluir auto_invoice
    @api.model
    def _order_fields(self, ui_order):
        fields = super()._order_fields(ui_order)
        
        # Si está configurada la facturación automática en el POS config
        if ui_order.get('pos_session_id'):
            session = self.env['pos.session'].browse(ui_order['pos_session_id'])
            if session.config_id.auto_invoice:
                fields['to_invoice'] = True
        
        return fields

    # Preparar valores para la factura cuando se activa auto_invoice
    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        
        # Si está configurada la facturación automática, asegurar que se facture
        if self.config_id.auto_invoice:
            vals['move_type'] = 'out_invoice'
        
        return vals