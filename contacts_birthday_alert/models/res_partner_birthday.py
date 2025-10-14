from datetime import timedelta
import calendar
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Retorna los partners que cumplen años en una fecha específica.
    @api.model
    def _partners_with_bday_on(self, check_date): 
        if not check_date:
            return self.browse()
        
        partners = self.search([('birth_date', '!=', False)])
        
        result = self.browse()
        target_month = check_date.month
        target_day = check_date.day
        
        for partner in partners:
            if partner.birth_date.month == target_month and partner.birth_date.day == target_day:
                result |= partner
        
        return result

    # Método principal para enviar notificaciones de cumpleaños.
    @api.model
    def send_birthday_notifications(self):
        try:
            target_user = self.env.ref('base.user_admin')
        except Exception:
            target_user = self.env.user

        if not target_user or not target_user.partner_id:
            _logger.warning("send_birthday_notifications: no hay target_user válido, abortando.")
            return True

        record_for_tz = self.with_user(target_user.id)
        today_str = fields.Date.context_today(record_for_tz)
        today = fields.Date.to_date(today_str)
        tomorrow = today + timedelta(days=1)

        partners_today = self._partners_with_bday_on(today)
        partners_tomorrow = self._partners_with_bday_on(tomorrow)

        # Manejo especial para 29 de febrero en años no bisiestos
        if today.month == 2 and today.day == 28 and not calendar.isleap(today.year):
            partners = self.search([('birth_date', '!=', False)])
            for partner in partners:
                if partner.birth_date.month == 2 and partner.birth_date.day == 29:
                    partners_today |= partner

        if not partners_today and not partners_tomorrow:
            _logger.debug("send_birthday_notifications: no hay cumpleaños hoy ni mañana.")
            return True

        try:
            odoobot_user = self.env.ref('base.user_root')
            odoobot_partner = odoobot_user.partner_id
        except Exception:
            odoobot_partner = self.env.user.partner_id

        channel = self._get_or_create_birthday_channel()

        if channel:
            self._post_birthday_messages(
                channel, 
                partners_today, 
                partners_tomorrow, 
                odoobot_partner
            )

        return True

    # Busca o crea el canal de cumpleaños.
    def _get_or_create_birthday_channel(self):
        channel_name = "Cumpleaños Clientes"
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
                    "send_birthday_notifications: canal creado '%s' (id=%s).", 
                    channel_name, 
                    channel.id
                )
            except Exception as e:
                _logger.exception(
                    "send_birthday_notifications: no se pudo crear el canal '%s': %s", 
                    channel_name, 
                    e
                )
                channel = None

        return channel

    # Publica los mensajes de cumpleaños en el canal.
    def _post_birthday_messages(self, channel, partners_today, partners_tomorrow, odoobot_partner):

        try:
            notify_all_members = False

            if partners_today:
                today_body = _("""
                <h5><b>🎂🥳HOY CUMPLEN AÑOS LOS SIGUIENTES CLIENTES🥳🎂</b></h5>
                <ul>
                %s
                </ul>
                """ % "\n".join(["<li>%s</li>" % name for name in partners_today.mapped('name')]))
                
                message_today = channel.sudo().message_post(
                    body=today_body,
                    body_is_html=True,
                    author_id=odoobot_partner.id if odoobot_partner else False,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )

                if notify_all_members:
                    self._notify_channel_members(channel, message_today)

            if partners_tomorrow:
                tomorrow_body = _("""
                <b>📆🎂Mañana cumplen años los siguientes clientes🎂📆</b>
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
                    self._notify_channel_members(channel, message_tomorrow)

        except Exception as e:
            _logger.exception(
                "send_birthday_notifications: fallo al postear en canal: %s", 
                e
            )

    # Crea notificaciones para todos los miembros del canal.
    def _notify_channel_members(self, channel, message):
        partner_ids = channel.sudo().channel_partner_ids.mapped('id')
        if partner_ids:
            notif_model = self.env['mail.notification'].sudo()
            notif_vals = []
            for pid in partner_ids:
                notif_vals.append({
                    'mail_message_id': message.id,
                    'res_partner_id': pid,
                    'notification_type': 'inbox',
                })
            try:
                notif_model.create(notif_vals)
            except Exception as e:
                _logger.exception(
                    "send_birthday_notifications: fallo al crear notificaciones: %s", 
                    e
                )

