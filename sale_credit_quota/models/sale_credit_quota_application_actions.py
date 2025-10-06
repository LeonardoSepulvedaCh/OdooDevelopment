from odoo import models, _

class SaleCreditQuotaApplication(models.Model):
    _inherit = 'sale.credit.quota.application'

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
