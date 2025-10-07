from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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

    def action_view_customer_purchases(self):
        self.ensure_one()
        
        if not self.customer_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No hay cliente seleccionado.'),
                    'type': 'danger',
                }
            }

        # Buscar todas las facturas del cliente
        domain = [
            ('partner_id', '=', self.customer_id.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
        ]
        
        purchases = self.env['account.move'].search(domain)
        
        if not purchases:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin compras'),
                    'message': _('El cliente %s no tiene compras registradas.') % self.customer_id.name,
                    'type': 'warning',
                }
            }

        return {
            'name': _('Compras de %s (%d)') % (self.customer_id.name, len(purchases)),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_partner_id': self.customer_id.id,
                'default_move_type': 'out_invoice',
                'search_default_partner_id': self.customer_id.id,
                'search_default_posted': 1,
            },
        }

    def action_approve(self):
        self.ensure_one()
        
        if self.state != 'draft':
            raise ValidationError(_('Solo se pueden aprobar solicitudes en estado borrador.'))
        
        missing_fields = []
        
        if not self.property_payment_term_id:
            missing_fields.append('Condiciones de Pago')

        if self.final_normal_credit_quota <= 0:
            missing_fields.append('Cupo Normal Final (debe ser mayor a 0)')
        
        if missing_fields:
            raise ValidationError(
                _('Los siguientes campos son obligatorios para aprobar la solicitud:\n• %s') % 
                '\n• '.join(missing_fields)
            )
        
        self.write({
            'state': 'approved',
            'approved_date': fields.Date.context_today(self),
            'approved_by': self.env.user.id,
        })
        
        if self.customer_id:
            customer_values = {}
            
            customer_values['normal_credit_quota'] = self.final_normal_credit_quota
            customer_values['golden_credit_quota'] = self.final_golden_credit_quota
                
            if self.property_payment_term_id:
                customer_values['property_payment_term_id'] = self.property_payment_term_id.id
            
            self.customer_id.write(customer_values)
            
            cupo_message = _('Cupos de crédito actualizados desde la solicitud %s:') % self.name
            cupo_message += _('\n• Cupo Normal: %s') % self.final_normal_credit_quota
            cupo_message += _('\n• Cupo Dorado: %s') % self.final_golden_credit_quota
            if 'property_payment_term_id' in customer_values:
                cupo_message += _('\n• Condiciones de Pago: %s') % self.property_payment_term_id.name
            
            self.customer_id.message_post(
                body=cupo_message,
                message_type='notification'
            )
        
        self.message_post(
            body=_('Solicitud aprobada por %s') % self.env.user.name,
            message_type='notification'
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Solicitud Aprobada'),
                'message': _('La solicitud %s ha sido aprobada exitosamente.') % self.name,
                'type': 'success',
            }
        }

    def action_reject(self):
        self.ensure_one()
        
        if self.state != 'draft':
            raise ValidationError(_('Solo se pueden rechazar solicitudes en estado borrador.'))
        
        self.write({
            'state': 'rejected',
            'rejected_date': fields.Date.context_today(self),
        })
        
        self.message_post(
            body=_('Solicitud rechazada por %s') % self.env.user.name,
            message_type='notification'
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Solicitud Rechazada'),
                'message': _('La solicitud %s ha sido rechazada.') % self.name,
                'type': 'warning',
            }
        }
