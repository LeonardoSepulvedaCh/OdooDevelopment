from datetime import timedelta
from html import escape
import calendar
import logging

from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    birth_date = fields.Date(string="Fecha de Nacimiento", help="Fecha de nacimiento del contacto")
    related_contact_ids = fields.One2many('related.contact', 'partner_id', string='Contactos Adicionales')
    card_code = fields.Char(string="Código de Contacto", help="Código del contacto", compute='_compute_card_code')
    warehouse_id = fields.Many2one('stock.warehouse', string="Bodega asignada", help="Bodega de la cual se despacharán pedidos al cliente", ondelete='set null')

    # Funciones para el cron de cumpleaños
    @api.model
    def _partners_with_bday_on(self, check_date):
        if not check_date:
            return self.browse()
        mmdd = check_date.strftime('%m-%d')
        self.env.cr.execute(
            "SELECT id FROM res_partner WHERE birth_date IS NOT NULL AND to_char(birth_date, 'MM-DD') = %s",
            (mmdd,)
        )
        ids = [r[0] for r in self.env.cr.fetchall()]
        return self.browse(ids)

    @api.model
    def send_birthday_notifications(self):
        try:
            target_user = self.env.ref('base.user_admin')
        except Exception:
            target_user = self.env.user

        if not target_user or not target_user.partner_id:
            _logger.warning("send_birthday_notifications: no hay target_user válido, abortando.")
            return True

        # Fecha según la Zona Horaria del usuario target_user
        record_for_tz = self.with_user(target_user.id)
        today_str = fields.Date.context_today(record_for_tz)
        today = fields.Date.to_date(today_str)
        tomorrow = today + timedelta(days=1)

        # Buscar partners con cumpleaños hoy / mañana
        partners_today = self._partners_with_bday_on(today)
        partners_tomorrow = self._partners_with_bday_on(tomorrow)

        # Manejo 29-feb en años no bisiestos
        if today.month == 2 and today.day == 28 and not calendar.isleap(today.year):
            self.env.cr.execute(
                "SELECT id FROM res_partner WHERE birth_date IS NOT NULL AND to_char(birth_date, 'MM-DD') = %s",
                ('02-29',)
            )
            ids = [r[0] for r in self.env.cr.fetchall()]
            partners_today |= self.browse(ids)

        if not partners_today and not partners_tomorrow:
            _logger.debug("send_birthday_notifications: no hay cumpleaños hoy ni mañana.")
            return True

        # Remitente del mensaje (OdooBot)
        try:
            odoobot_user = self.env.ref('base.user_root')
            odoobot_partner = odoobot_user.partner_id
        except Exception:
            odoobot_partner = self.env.user.partner_id

        # Buscar el canal a enviar el mensaje
        channel_name = "Cumpleaños Clientes"
        Channel = self.env['discuss.channel']
        channel = None

        if not channel:
            channel = Channel.sudo().search([
                ('name', '=', channel_name),
                ('channel_type', '=', 'channel')
            ], limit=1)

        # Si no existe el canal lo crea
        if not channel:
            try:
                channel = Channel.sudo().create({
                    'name': channel_name,
                    'channel_type': 'channel',
                })
                _logger.info("send_birthday_notifications: canal creado '%s' (id=%s).", channel_name, channel.id)
            except Exception as e:
                _logger.exception("send_birthday_notifications: no se pudo crear el canal '%s': %s", channel_name, e)
                channel = None

        # Enviar mensajes por separado
        if channel:
            try:
                notify_all_members = False

                # Mensaje para cumpleaños de hoy
                if partners_today:
                    today_body = _("""
                    <h5><b>🎂🥳HOY CUMPLEN AÑOS LOS SIGUIENTES CLIENTES🥳🎂</b></h5>
                    <ul>
                    %s
                    </ul>
                    """ % "\n".join(["<li>%s</li>" % name for name in partners_today.mapped('name')]))
                    
                    message_today = channel.sudo().message_post(
                        body=today_body,
                        body_is_html =True,
                        author_id=odoobot_partner.id if odoobot_partner else False,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )

                    if notify_all_members:
                        partner_ids = channel.sudo().channel_partner_ids.mapped('id')
                        if partner_ids:
                            notif_model = self.env['mail.notification'].sudo()
                            notif_vals = []
                            for pid in partner_ids:
                                notif_vals.append({
                                    'mail_message_id': message_today.id,
                                    'res_partner_id': pid,
                                    'notification_type': 'inbox',
                                })
                            try:
                                notif_model.create(notif_vals)
                            except Exception as e:
                                _logger.exception("send_birthday_notifications: fallo al crear notificaciones para hoy: %s", e)

                # Mensaje para cumpleaños de mañana
                if partners_tomorrow:
                    tomorrow_body = _("""
                    <b>🎂🥳Mañana cumplen años los siguientes clientes🥳🎂</b>
                    <ul>
                    %s
                    </ul>
                    """ % "\n".join(["<li>%s</li>" % name for name in partners_tomorrow.mapped('name')]))

                    message_tomorrow = channel.sudo().message_post(
                        body=tomorrow_body,
                        body_is_html=True,
                        author_id=odoobot_partner.id if odoobot_partner else False,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )

                    if notify_all_members:
                        partner_ids = channel.sudo().channel_partner_ids.mapped('id')
                        if partner_ids:
                            notif_model = self.env['mail.notification'].sudo()
                            notif_vals = []
                            for pid in partner_ids:
                                notif_vals.append({
                                    'mail_message_id': message_tomorrow.id,
                                    'res_partner_id': pid,
                                    'notification_type': 'inbox',
                                })
                            try:
                                notif_model.create(notif_vals)
                            except Exception as e:
                                _logger.exception("send_birthday_notifications: fallo al crear notificaciones para mañana: %s", e)

                return True
            except Exception as e:
                _logger.exception("send_birthday_notifications: fallo al postear en canal '%s': %s", channel_name, e)

        return True
    
    # Funciones para el campo card_code. Si el cliente no es una empresa, el codigo es CNL-(vat) de lo contrario es PNL-(vat)
    def _compute_card_code(self):
        for partner in self:
            vat_full = partner.vat or ''
            
            # Extraer solo la parte numérica antes del guión (sin dígito verificador)
            if '-' in vat_full:
                vat_code = vat_full.split('-')[0]
            else:
                vat_code = vat_full
            
            if partner.is_company:
                partner.card_code = 'pnl' + vat_code
            else:
                partner.card_code = 'cnl' + vat_code
