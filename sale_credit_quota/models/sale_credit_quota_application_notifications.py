from odoo import models, api, fields, _
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class SaleCreditQuotaApplication(models.Model):
    _inherit = 'sale.credit.quota.application'

    # Busca o crea el canal de aprobaciones de cupos de crédito.
    def _get_or_create_credit_approval_channel(self):
        channel_name = "Solicitudes de Cupos de Crédito"
        Channel = self.env['discuss.channel']
        
        channel = Channel.sudo().search([
            ('name', '=', channel_name),
            ('channel_type', '=', 'channel')
        ], limit=1)

        if not channel:
            try:
                channel = Channel.sudo().create({
                    'name': channel_name,
                    'channel_type': 'channel',
                })
                _logger.info(
                    "Canal creado '%s' (id=%s).", 
                    channel_name, 
                    channel.id
                )
            except Exception as e:
                _logger.exception(
                    "No se pudo crear el canal '%s': %s", 
                    channel_name, 
                    e
                )
                channel = None

        return channel

    # Envía una notificación al canal de discusiones cuando se aprueba un cupo de crédito.
    def _send_approval_notification(self):
        self.ensure_one()
        
        channel = self._get_or_create_credit_approval_channel()
        
        if not channel:
            _logger.warning(
                "No se pudo obtener el canal de aprobaciones para la solicitud %s", 
                self.name
            )
            return

        try:
            odoobot_user = self.env.ref('base.user_root')
            odoobot_partner = odoobot_user.partner_id
        except Exception:
            odoobot_partner = self.env.user.partner_id

        try:
            normal_quota = self.final_normal_credit_quota
            golden_quota = self.final_golden_credit_quota
            
            approver_name = self.approved_by.name if self.approved_by else self.env.user.name
            
            solicitud = self.name or 'N/A'
            cliente = self.customer_id.name or 'N/A'
            documento = self.customer_vat or 'N/A'
            sucursal = dict(self._fields['branch_office'].selection).get(self.branch_office, 'N/A')
            asunto = dict(self._fields['subject'].selection).get(self.subject, 'N/A')
            cupo_normal = '{:,.2f}'.format(normal_quota)
            cupo_dorado = '{:,.2f}'.format(golden_quota)
            condiciones_pago = self.property_payment_term_id.name if self.property_payment_term_id else 'N/A'
            fecha_inicio = self.credit_quota_start_date.strftime('%d/%m/%Y') if self.credit_quota_start_date else 'N/A'
            fecha_fin = self.credit_quota_end_date.strftime('%d/%m/%Y') if self.credit_quota_end_date else 'N/A'
            fecha_aprobacion = self.approved_date.strftime('%d/%m/%Y') if self.approved_date else 'N/A'
            
            message_body = """
                <h5><b>✅ CUPO DE CRÉDITO APROBADO</b></h5>
                <ul>
                <li><b>Solicitud:</b> {solicitud}</li>
                <li><b>Cliente:</b> {cliente}</li>
                <li><b>Documento:</b> {documento}</li>
                <li><b>Sucursal:</b> {sucursal}</li>
                <li><b>Asunto:</b> {asunto}</li>
                <li><b>💰 Cupo Normal:</b> $ {cupo_normal}</li>
                <li><b>🌟 Cupo Dorado:</b> $ {cupo_dorado}</li>
                <li><b>Condiciones de Pago:</b> {condiciones_pago}</li>
                <li><b>Vigencia:</b> Desde {fecha_inicio} hasta {fecha_fin}</li>
                <li><b>Aprobado por:</b> {approver_name}</li>
                <li><b>Fecha de Aprobación:</b> {fecha_aprobacion}</li>
                </ul>
            """.format(
                solicitud=solicitud,
                cliente=cliente,
                documento=documento,
                sucursal=sucursal,
                asunto=asunto,
                cupo_normal=cupo_normal,
                cupo_dorado=cupo_dorado,
                condiciones_pago=condiciones_pago,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                approver_name=approver_name,
                fecha_aprobacion=fecha_aprobacion
            )
            
            channel.sudo().message_post(
                body=message_body,
                body_is_html=True,
                author_id=odoobot_partner.id if odoobot_partner else False,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            
            _logger.info(
                "Notificación de aprobación enviada al canal para la solicitud %s", 
                self.name
            )
            
        except Exception as e:
            _logger.exception(
                "Error al enviar notificación de aprobación para la solicitud %s: %s", 
                self.name, 
                e
            )

    # Método del cron para notificar solicitudes por vencer
    @api.model
    def _cron_notify_expiring_applications(self):
        today = fields.Date.today()
        warning_date = today + timedelta(days=8)
        
        expiring_applications = self.search([
            ('state', '=', 'approved'),
            ('credit_quota_end_date', '>=', today),
            ('credit_quota_end_date', '<=', warning_date),
            ('credit_quota_end_date', '!=', False),
        ])
        
        if not expiring_applications:
            _logger.info("No hay solicitudes de cupo de crédito por vencer en los próximos 8 días")
            return
        
        channel = self._get_or_create_credit_approval_channel()
        
        if not channel:
            _logger.warning("No se pudo obtener el canal de notificaciones para solicitudes por vencer")
            return
        
        try:
            odoobot_user = self.env.ref('base.user_root')
            odoobot_partner = odoobot_user.partner_id
        except Exception:
            odoobot_partner = self.env.user.partner_id
        
        # Agrupar solicitudes por días restantes para el mensaje
        applications_by_days = {}
        for application in expiring_applications:
            days_remaining = (application.credit_quota_end_date - today).days
            if days_remaining not in applications_by_days:
                applications_by_days[days_remaining] = []
            applications_by_days[days_remaining].append(application)
        
        try:
            message_parts = [
                "<h5><b>⚠️ SOLICITUDES DE CUPO DE CRÉDITO POR VENCER</b></h5>",
                "<p>Las siguientes solicitudes de cupo de crédito están próximas a vencer:</p>"
            ]
            
            for days_remaining in sorted(applications_by_days.keys()):
                applications = applications_by_days[days_remaining]
                day_text = "día" if days_remaining == 1 else "días"
                
                message_parts.append(f"<h6><b>📅 Vencen en {days_remaining} {day_text}:</b></h6>")
                message_parts.append("<ul>")
                
                for application in applications:
                    cliente = application.customer_id.name or 'N/A'
                    documento = application.customer_vat or 'N/A'
                    sucursal = dict(application._fields['branch_office'].selection).get(application.branch_office, 'N/A')
                    fecha_fin = application.credit_quota_end_date.strftime('%d/%m/%Y') if application.credit_quota_end_date else 'N/A'
                    cupo_normal = '{:,.2f}'.format(application.final_normal_credit_quota)
                    cupo_dorado = '{:,.2f}'.format(application.final_golden_credit_quota)
                    
                    message_parts.append(f"""
                        <li>
                            <b>{application.name}</b> - {cliente} (Doc: {documento})<br/>
                            <small>
                                📍 Sucursal: {sucursal} <br/>
                                💰 Cupo Normal: $ {cupo_normal} | 
                                🌟 Cupo Dorado: $ {cupo_dorado}<br/>
                                📅 Fecha de Vencimiento: {fecha_fin}
                            </small>
                        </li>
                    """)
                
                message_parts.append("</ul>")
            
            message_parts.append("<p><small><i>💡 Recuerde revisar y gestionar estas solicitudes antes de su vencimiento.</i></small></p>")
            
            message_body = "".join(message_parts)
            
            channel.sudo().message_post(
                body=message_body,
                body_is_html=True,
                author_id=odoobot_partner.id if odoobot_partner else False,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            
            _logger.info(
                "Notificación de solicitudes por vencer enviada al canal. "
                "Total de solicitudes notificadas: %d", 
                len(expiring_applications)
            )
            
        except Exception as e:
            _logger.exception(
                "Error al enviar notificación de solicitudes por vencer: %s", 
                e
            )

