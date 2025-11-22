from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# Constantes
UNDEFINED_DATE_LABEL = 'No definida'
APPROVAL_REQUEST_MODEL = 'approval.request'

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

    def action_send_to_approval(self):
        """Envía la solicitud de cupo a la app de Aprobaciones"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise ValidationError(_('Solo se pueden enviar a aprobación las solicitudes en estado borrador.'))
        
        if self.approval_request_id:
            raise ValidationError(_('Esta solicitud ya tiene una solicitud de aprobación asociada.'))
        
        # Validar que el cliente no tenga otra solicitud aprobada activa
        if self.customer_id:
            existing_approved = self.search([
                ('customer_id', '=', self.customer_id.id),
                ('state', '=', 'approved'),
                ('id', '!=', self.id),
            ], limit=1)
            
            if existing_approved:
                raise ValidationError(
                    _('No se puede enviar a aprobación.\n\n'
                      'El cliente "%s" ya tiene una solicitud aprobada activa: %s\n\n'
                      'Un cliente solo puede tener una solicitud de cupo de crédito aprobada a la vez. '
                      'Debe finalizar la solicitud existente (código: %s, fecha de fin: %s) antes de aprobar una nueva.') % 
                    (self.customer_id.name, 
                     existing_approved.name,
                     existing_approved.name,
                     existing_approved.credit_quota_end_date or UNDEFINED_DATE_LABEL)
                )
        
        # Validar requisitos mínimos antes de enviar
        self._validate_required_fields_for_approval()
        
        # Obtener la categoría de aprobación
        approval_category = self.env.ref('sale_credit_quota.approval_category_credit_quota', raise_if_not_found=False)
        if not approval_category:
            raise ValidationError(_('No se encontró la categoría de aprobación para solicitudes de cupo de crédito.'))
        
        # Preparar los valores para la solicitud de aprobación
        approval_vals = {
            'name': f'Solicitud de Cupo - {self.name}',
            'category_id': approval_category.id,
            'request_owner_id': self.user_id.id or self.env.user.id,
            'partner_id': self.customer_id.id,
            'reference': self.name,
            'amount': self.final_normal_credit_quota,
            'reason': self._get_approval_reason_html(),
            'date_confirmed': False,
        }
        
        # Agregar fechas del periodo (fecha inicio y fin del cupo)
        if self.credit_quota_start_date:
            # Convertir date a datetime (inicio del día)
            approval_vals['date_start'] = fields.Datetime.to_datetime(self.credit_quota_start_date)
        
        if self.credit_quota_end_date:
            # Convertir date a datetime (final del día)
            approval_vals['date_end'] = fields.Datetime.to_datetime(self.credit_quota_end_date).replace(hour=23, minute=59, second=59)
        
        # Crear la solicitud de aprobación
        approval_request = self.env[APPROVAL_REQUEST_MODEL].create(approval_vals)
        
        # Vincular bidireccionalmente
        self.write({'approval_request_id': approval_request.id})
        approval_request.write({'credit_quota_application_id': self.id})
        
        # Enviar automáticamente la solicitud (confirmar)
        approval_request.action_confirm()
        
        # Mensaje en la solicitud de cupo
        self.message_post(
            body=_('Solicitud enviada a aprobación: %s') % approval_request.name,
            message_type='notification'
        )
        
        # Retornar acción para abrir la solicitud de aprobación
        return {
            'type': 'ir.actions.act_window',
            'res_model': APPROVAL_REQUEST_MODEL,
            'res_id': approval_request.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _get_approval_reason_html(self):
        """Genera el HTML con la información de la solicitud para la app de Aprobaciones"""
        self.ensure_one()
        
        reason = f"""
        <div>
            <h3>Información de la Solicitud</h3>
            <ul>
                <li><strong>Cliente:</strong> {self.customer_id.name or ''}</li>
                <li><strong>NIT/Cédula:</strong> {self.customer_vat or ''}</li>
                <li><strong>Asunto:</strong> {dict(self._fields['subject'].selection).get(self.subject, '')}</li>
                <li><strong>Sucursal:</strong> {dict(self._fields['branch_office'].selection).get(self.branch_office, '')}</li>
                <li><strong>Asesor:</strong> {self.user_id.name or ''}</li>
            </ul>
            
            <h3>Cupos Propuestos</h3>
            <ul>
                <li><strong>Cupo Normal:</strong> ${self.final_normal_credit_quota:,.2f}</li>
                <li><strong>Cupo Dorado:</strong> ${self.final_golden_credit_quota:,.2f}</li>
                <li><strong>Plazo de Pago:</strong> {self.property_payment_term_id.name if self.property_payment_term_id else 'N/A'}</li>
                <li><strong>Vigencia:</strong> {self.credit_quota_start_date or 'N/A'} hasta {self.credit_quota_end_date or 'N/A'}</li>
            </ul>
            
            <h3>Información del Negocio</h3>
            <ul>
                <li><strong>Nombre:</strong> {self.business_name or ''}</li>
                <li><strong>Ciudad:</strong> {self.business_city or ''}</li>
                <li><strong>Años de Actividad:</strong> {self.business_years_of_activity or 0}</li>
            </ul>
            
            <h3>Análisis del Asesor</h3>
            <p><strong>Lo Bueno:</strong><br/>{self.good_points or ''}</p>
            <p><strong>Lo Malo:</strong><br/>{self.bad_points or ''}</p>
            <p><strong>Novedades:</strong><br/>{self.new_points or ''}</p>
        </div>
        """
        
        return reason
    
    def action_view_approval_request(self):
        """Abre la solicitud de aprobación relacionada"""
        self.ensure_one()
        
        if not self.approval_request_id:
            raise ValidationError(_('Esta solicitud no tiene una solicitud de aprobación asociada.'))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': APPROVAL_REQUEST_MODEL,
            'res_id': self.approval_request_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _approval_approved(self):
        """Método llamado cuando la solicitud de aprobación es aprobada"""
        self.ensure_one()
        
        # Verificar que no esté ya aprobado para evitar ejecutar la lógica múltiples veces
        if self.state == 'approved':
            return True
        
        values = {
            'state': 'approved',
            'approved_date': fields.Date.context_today(self),
        }
        
        # Obtener el usuario que aprobó (último aprobador)
        if self.approval_request_id and self.approval_request_id.approver_ids:
            approved_by_users = self.approval_request_id.approver_ids.filtered(
                lambda a: a.status == 'approved'
            ).mapped('user_id')
            if approved_by_users:
                values['approved_by'] = approved_by_users[-1].id
        
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
        
        approver_name = self.approved_by.name if self.approved_by else 'Sistema'
        
        self.message_post(
            body=_('Solicitud aprobada por %s el %s (vía App de Aprobaciones)') % (approver_name, fields.Date.context_today(self)),
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
    
    def _approval_refused(self):
        """Método llamado cuando la solicitud de aprobación es rechazada"""
        self.ensure_one()
        
        self.write({
            'state': 'rejected',
            'rejected_date': fields.Date.context_today(self),
        })
        
        self.message_post(
            body=_('Solicitud rechazada el %s (vía App de Aprobaciones)') % fields.Date.context_today(self),
            message_type='notification'
        )
        
        # Enviar notificación al canal de discusiones
        try:
            self._send_rejection_notification()
        except Exception as e:
            _logger.warning(
                'No se pudo enviar la notificación al canal para la solicitud rechazada %s: %s', 
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
        
        if self.approval_request_id and self.approval_request_id.request_status not in ('cancel', 'refused'):
            self.approval_request_id.action_cancel()
            self.approval_request_id.message_post(
                body=_('Solicitud de aprobación cancelada automáticamente porque la solicitud de cupo %s fue finalizada.') % self.name,
                message_type='notification'
            )
        
        if self.customer_id:
            self.customer_id.write({
                'normal_credit_quota': 0.0,
                'golden_credit_quota': 0.0,
                'credit_limit': 0.0,
            })
            
            self.customer_id.message_post(
                body=_('Cupos de crédito finalizados y restablecidos a 0 desde la solicitud %s (fecha fin: %s)') % (self.name, self.credit_quota_end_date or UNDEFINED_DATE_LABEL),
                message_type='notification'
            )
        
        self.message_post(
            body=_('Solicitud finalizada - Cupos de crédito restablecidos a 0 (fecha fin del cupo: %s)') % (self.credit_quota_end_date or UNDEFINED_DATE_LABEL),
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
        
        if not self.customer_vat or not self.customer_vat.strip():
            missing_fields.append('Cédula del Cliente')
        
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
        
        # Validar que si es persona jurídica, debe tener un representante legal y al menos otro codeudor
        if self.is_legal_entity:
            has_legal_representative = any(
                codeudor.relationship == 'legal_representative' 
                for codeudor in self.codeudor_ids
            )
            if not has_legal_representative:
                missing_fields.append('Para una Persona Jurídica, debe tener al menos un Codeudor con parentesco "Representante Legal"')
            
            if len(self.codeudor_ids) < 2:
                missing_fields.append('Para una Persona Jurídica, debe tener al menos 2 Codeudores (uno como Representante Legal y otro adicional)')
        
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
        
        # Documentos requeridos para el cliente
        customer_required_tags = ['CTL', 'RUT', 'Cedula de Ciudadanía', 'Pagare', 'Fotos del Negocio', 'CIFIN']
        self._validate_required_documents(self.customer_id, 'Cliente', customer_required_tags, missing_fields)
        
        # Documentos requeridos para los codeudores
        codeudor_required_tags = ['CTL', 'RUT', 'Cedula de Ciudadanía']
        for codeudor in self.codeudor_ids:
            if codeudor.partner_id:
                self._validate_required_documents(
                    codeudor.partner_id, 
                    f'Codeudor {codeudor.name or codeudor.partner_id.name}', 
                    codeudor_required_tags, 
                    missing_fields
                )

        if missing_fields:
            raise ValidationError(
                _('Los siguientes campos son obligatorios para aprobar la solicitud:\n• %s') % 
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

