from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

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
        
        self._validate_required_fields_for_approval()
        
        values = {
            'state': 'approved',
            'approved_date': fields.Date.context_today(self),
        }
        
        if not self.approved_by:
            values['approved_by'] = self.env.user.id
        
        self.write(values)
        
        if self.customer_id:
            customer_values = {}
            
            customer_values['normal_credit_quota'] = self.final_normal_credit_quota
            customer_values['golden_credit_quota'] = self.final_golden_credit_quota
            
            if self.final_normal_credit_quota:
                customer_values['credit_limit'] = self.final_normal_credit_quota
                
            if self.property_payment_term_id:
                customer_values['property_payment_term_id'] = self.property_payment_term_id.id
            
            self.customer_id.write(customer_values)
            
            self.customer_id.message_post(
                body=(_('Cupos de crédito actualizados desde la solicitud %s') % self.name),
                message_type='notification'
            )
        
        approver_name = self.approved_by.name if self.approved_by else self.env.user.name
        
        self.message_post(
            body=_('Solicitud aprobada por %s el %s') % (approver_name, fields.Date.context_today(self)),
            message_type='notification'
        )
        
        # Enviar notificación al canal de discusiones
        try:
            self._send_approval_notification()
        except Exception as e:
            _logger.warning(
                'No se pudo enviar la notificación al canal para la solicitud %s: %s', 
                self.name, str(e)
            )
        
        return True

    def action_finish(self):
        self.ensure_one()
        
        if self.state != 'approved':
            raise ValidationError(_('Solo se pueden finalizar solicitudes aprobadas.'))
        
        return self._finish_application()

    def _finish_application(self):
        self.ensure_one()
        
        self.write({
            'state': 'finished',
        })
        
        if self.customer_id:
            self.customer_id.write({
                'normal_credit_quota': 0.0,
                'golden_credit_quota': 0.0,
                'credit_limit': 0.0,
            })
            
            self.customer_id.message_post(
                body=_('Cupos de crédito finalizados y restablecidos a 0 desde la solicitud %s (fecha fin: %s)') % (self.name, self.credit_quota_end_date or 'No definida'),
                message_type='notification'
            )
        
        self.message_post(
            body=_('Solicitud finalizada - Cupos de crédito restablecidos a 0 (fecha fin del cupo: %s)') % (self.credit_quota_end_date or 'No definida'),
            message_type='notification'
        )
        
        return True

    @api.model
    def _cron_finish_expired_applications(self):
        today = fields.Date.today()
        
        expired_applications = self.search([
            ('state', '=', 'approved'),
            ('credit_quota_end_date', '<=', today),
            ('credit_quota_end_date', '!=', False),
        ])
        
        for application in expired_applications:
            try:
                application._finish_application()
            except Exception as e:
                _logger.error(
                    'Error al finalizar automáticamente la solicitud %s: %s', 
                    application.name, str(e)
                )
        
        if expired_applications:
            _logger.info(
                'Finalizadas automáticamente %d solicitudes de cupo de crédito', 
                len(expired_applications)
            )

    def _validate_required_fields_for_approval(self):
        missing_fields = []
        
        if self.final_normal_credit_quota <= 0:
            missing_fields.append('Cupo Normal Final (debe ser mayor a 0)')
        
        if self.final_golden_credit_quota < 0:
            missing_fields.append('Cupo Dorado Final (no puede ser negativo)')
        
        if not self.credit_quota_start_date:
            missing_fields.append('Fecha de Inicio del Cupo')
        
        if not self.credit_quota_end_date:
            missing_fields.append('Fecha de Fin del Cupo')
        
        if not self.property_payment_term_id:
            missing_fields.append('Condiciones de Pago')
        
        if self.suggestion_normal_credit_quota <= 0:
            missing_fields.append('Cupo Normal Sugerido por el Asesor (debe ser mayor a 0)')
        
        if self.suggestion_golden_credit_quota < 0:
            missing_fields.append('Cupo Dorado Sugerido por el Asesor (no puede ser negativo)')
        
        if not self.good_points or not self.good_points.strip():
            missing_fields.append('Observaciones del Asesor - Lo Bueno')
        
        if not self.bad_points or not self.bad_points.strip():
            missing_fields.append('Observaciones del Asesor - Lo Malo')
        
        if not self.new_points or not self.new_points.strip():
            missing_fields.append('Observaciones del Asesor - Novedades')
        
        if not self.codeudor_ids:
            missing_fields.append('Debe tener al menos un Codeudor')
        
        business_fields = [
            ('business_name', 'Nombre del Negocio'),
            ('business_city', 'Ciudad del Negocio'),
        ]
        
        for field_name, field_label in business_fields:
            field_value = getattr(self, field_name)
            if not field_value or not field_value.strip():
                missing_fields.append(f'Información del Negocio - {field_label}')
        
        if self.business_years_of_activity < 0:
            missing_fields.append('Años de Actividad del Negocio (no puede ser negativo)')
        
        
        if self.review_auditoria_state != 'approved':
            missing_fields.append('Revisión por Auditoría debe estar aprobada')
        
        required_tags = ['Cedula de Ciudadanía', 'CTL', 'RUT', 'Fotos del Negocio']
        self._validate_required_documents(self.customer_id, 'Cliente', required_tags, missing_fields)
        
        for codeudor in self.codeudor_ids:
            if codeudor.partner_id:
                self._validate_required_documents(
                    codeudor.partner_id, 
                    f'Codeudor {codeudor.name or codeudor.partner_id.name}', 
                    required_tags, 
                    missing_fields
                )

        if missing_fields:
            raise ValidationError(
                _('Los siguientes campos son obligatorios para aprobar la solicitud %s') % 
                '\n• '.join(missing_fields)
            )
    
    def _validate_required_documents(self, partner, partner_label, required_tags, missing_fields):
        if not partner:
            missing_fields.append(f'{partner_label} - No está definido')
            return
        
        documents = self.env['documents.document'].search([
            ('partner_id', '=', partner.id),
            ('type', '!=', 'folder')
        ])
        
        if not documents:
            missing_fields.append(f'{partner_label} - No tiene documentos anexos')
            return
        
        document_tags = documents.mapped('tag_ids.name')
        
        for required_tag in required_tags:
            if required_tag not in document_tags:
                missing_fields.append(f'{partner_label} - Falta documento con etiqueta "{required_tag}"')

    def action_reject(self):
        self.ensure_one()
        
        if self.state != 'draft':
            raise ValidationError(_('Solo se pueden rechazar solicitudes en estado borrador.'))
        
        self.write({
            'state': 'rejected',
            'rejected_date': fields.Date.context_today(self),
        })
        
        self.message_post(
            body=_('Solicitud rechazada por %s el %s') % (self.env.user.name, fields.Date.context_today(self)),
            message_type='notification'
        )

        return True
