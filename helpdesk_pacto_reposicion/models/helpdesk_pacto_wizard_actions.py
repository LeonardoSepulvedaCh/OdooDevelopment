from odoo import models, _
from odoo.exceptions import ValidationError
import base64


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
        
        self.action_save_liquidador()
        
        return self.env.ref('helpdesk_pacto_reposicion.action_report_pacto_carta').report_action(self.ticket_id)

    # Enviar la carta de liquidación por email al cliente.
    def action_enviar_email(self):
        self.ensure_one()
        
        if not self._check_datos_completos_liquidador():
            raise ValidationError(_('Debe completar todos los datos del liquidador antes de enviar el email.'))
        
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
        
        nombre_cliente = self.ticket_id.partner_id.name or 'Estimado cliente'
        valor_consignar = self._get_valor_a_consignar()
        valor_formateado = '{:,.0f}'.format(valor_consignar).replace(',', '.')
        
        cuerpo_email = f"""
            <p>Estimado(a) <strong>{nombre_cliente}</strong>,</p>
            
            <p>Nos permitimos enviarle la carta de liquidación de su pacto de reposición correspondiente al ticket <strong>{self.ticket_id.name}</strong>.</p>
            
            <p>De acuerdo con la evaluación realizada, se ha autorizado el <strong>{self.pacto_porcentaje_aprobacion:.0f}%</strong> 
            del precio de compra para la reposición de su bicicleta <strong>{self.pacto_descripcion_bicicleta}</strong>.</p>
            
            <p>El valor a consignar es de: <strong>${valor_formateado} COP</strong></p>
            
            <p>Por favor, revise el documento adjunto para conocer todos los detalles de esta liquidación, 
            incluyendo los datos bancarios para realizar la consignación y los plazos establecidos.</p>
            
            <p>Si tiene alguna duda o consulta, no dude en contactarnos a través de nuestras líneas de atención:</p>
            <ul>
                <li><strong>Teléfono:</strong> 013000950000</li>
                <li><strong>Celular:</strong> 318 7346271</li>
                <li><strong>Email:</strong> servicioalcliente@bicicletasmilan.com</li>
            </ul>
            
            <p>Atentamente,<br/>
            <strong>Departamento de Garantías</strong><br/>
            INDUSTRIAS BICICLETAS MILÁN S.A.S</p>
        """
        
        mail_values = {
            'subject': f'Carta de Liquidación Pacto de Reposición - Ticket {self.ticket_id.name}',
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

