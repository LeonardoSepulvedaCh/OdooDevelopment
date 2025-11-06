from odoo import models, _
from odoo.exceptions import ValidationError
import base64
from .helpdesk_pacto_email_template import get_email_template_html


class HelpdeskPactoWizardActions(models.TransientModel):
    _inherit = 'helpdesk.pacto.wizard'

    # Guardar los datos del liquidador en el ticket.
    def action_save_liquidador(self):
        self.ensure_one()
        
        if not self.ticket_id:
            raise ValidationError(_('No se encontró el ticket asociado.'))
        
        valores = self._get_datos_wizard_to_ticket()
        self.ticket_id.write(valores)
        
        return {'type': 'ir.actions.act_window_close'}

    # Reestablecer todos los campos del wizard abriendo uno nuevo con valores por defecto.
    def action_restablecer_valores(self):
        self.ensure_one()
        
        return {
            'name': _('Liquidador Pacto de Reposición Optimus'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.pacto.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.ticket_id.id,
                'active_id': self.ticket_id.id,
                'force_default_values': True,
            },
        }

    # Imprimir la carta de liquidación del pacto de reposición.
    def action_imprimir_carta(self):
        self.ensure_one()
        
        if not self._check_datos_completos_liquidador():
            raise ValidationError(_('Debe completar todos los datos del liquidador antes de imprimir la carta.'))
        
        if not self.pacto_beneficio_aplica:
            raise ValidationError(_(
                'El beneficio de pacto de reposición NO aplica para este ticket.\n\n'
                'Las siguientes condiciones deben estar en SI:\n'
                '- ¿Registra su equipo Optimus en la página web dentro de los 30 días posteriores a la compra?\n'
                '- ¿Presenta la factura legal de compra?\n'
                '- ¿Presenta documento de identidad?\n'
                '- ¿Firma el pacto vigente como señal de conocimiento?\n'
                '- ¿Presenta denuncio ante la entidad competente?'
            ))
        
        self.action_save_liquidador()
        
        return self.env.ref('helpdesk_pacto_reposicion.action_report_pacto_carta').report_action(self.ticket_id)

    # Enviar la carta de liquidación por email al cliente.
    def action_enviar_email(self):
        self.ensure_one()
        
        if not self._check_datos_completos_liquidador():
            raise ValidationError(_('Debe completar todos los datos del liquidador antes de enviar el email.'))
        
        if not self.pacto_beneficio_aplica:
            raise ValidationError(_(
                'El beneficio de pacto de reposición NO aplica para este ticket.\n\n'
                'Las siguientes condiciones deben estar en SI:\n'
                '- ¿Registra su equipo Optimus en la página web dentro de los 30 días posteriores a la compra?\n'
                '- ¿Presenta la factura legal de compra?\n'
                '- ¿Presenta documento de identidad?\n'
                '- ¿Firma el pacto vigente como señal de conocimiento?\n'
                '- ¿Presenta denuncio ante la entidad competente?'
            ))
        
        if not self.ticket_id.partner_id:
            raise ValidationError(_('El ticket no tiene un cliente asociado.'))
        
        if not self.ticket_id.partner_id.email:
            raise ValidationError(_('El cliente no tiene un correo electrónico configurado.'))
        
        valores = self._get_datos_wizard_to_ticket()
        self.ticket_id.write(valores)
        
        pdf_content, pdf_format = self.env['ir.actions.report']._render_qweb_pdf(
            'helpdesk_pacto_reposicion.action_report_pacto_carta',
            res_ids=self.ticket_id.ids
        )
        
        pdf_base64 = base64.b64encode(pdf_content)
        
        nombre_archivo = f'Carta_Pacto_Reposicion_{self.ticket_id.name}.pdf'
        adjunto = self.env['ir.attachment'].create({
            'name': nombre_archivo,
            'type': 'binary',
            'datas': pdf_base64,
            'res_model': 'helpdesk.ticket',
            'res_id': self.ticket_id.id,
            'mimetype': 'application/pdf'
        })
        
        # Preparar variables para el template
        valor_consignar = self._get_valor_a_consignar()
        valor_formateado = '{:,.0f}'.format(valor_consignar).replace(',', '.')
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        logo_url = f"{base_url}/helpdesk_pacto_reposicion/static/src/img/logo_milan.png"
        porcentaje_aprobacion = f'{self.pacto_porcentaje_aprobacion:.0f}'
        
        # Generar el HTML del correo
        cuerpo_email = get_email_template_html(
            self.ticket_id,
            logo_url,
            valor_formateado,
            porcentaje_aprobacion
        )
        
        # Crear y enviar el correo
        mail_values = {
            'subject': f'Solicitud de Pacto de Reposición - {self.ticket_id.partner_id.name}',
            'body_html': cuerpo_email,
            'email_to': self.ticket_id.partner_id.email,
            'email_from': self.env.user.email or self.env.company.email or 'servicioalcliente@bicicletasmilan.com',
            'attachment_ids': [(6, 0, [adjunto.id])],
        }
        
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

        self.ticket_id.message_post(
            body=f'Se ha enviado la carta de liquidación del pacto de reposición al correo {self.ticket_id.partner_id.email}',
            subject='Email Enviado - Carta de Liquidación',
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Email Enviado'),
                'message': _('La carta de liquidación ha sido enviada exitosamente a %s') % self.ticket_id.partner_id.email,
                'type': 'success',
                'sticky': False,
            }
        }

