from datetime import date, timedelta
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
            return

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
            return

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

    # Busca o crea el canal de cumpleaños.
    def _get_or_create_birthday_channel(self):
        channel_name = "Cumpleaños Clientes"
        channel_model = self.env['discuss.channel']
        
        channel = channel_model.sudo().search([
            ('name', '=', channel_name),
            ('channel_type', '=', 'channel')
        ], limit=1)

        if not channel:
            try:
                channel = channel_model.sudo().create({
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

    # Calcula la edad que cumplirá un partner en una fecha específica.
    def _calculate_age_on_date(self, partner, reference_date):
        if not partner.birth_date:
            return None
        return reference_date.year - partner.birth_date.year

    # Formatea la lista de partners con sus edades.
    def _format_partner_list_items(self, partners, reference_date):
        items = []
        for partner in partners:
            age = self._calculate_age_on_date(partner, reference_date)
            if age is not None:
                items.append("<li>%s - %d años</li>" % (partner.name, age))
            else:
                items.append("<li>%s</li>" % partner.name)
        return "\n".join(items)

    # Publica un mensaje de cumpleaños en el canal.
    def _post_single_birthday_message(self, channel, partners, title, reference_date, odoobot_partner, notify_all_members=False):
        if not partners:
            return None

        items = self._format_partner_list_items(partners, reference_date)
        body = _("""
        %s
        <ul>
        %s
        </ul>
        """ % (title, items))

        message = channel.sudo().message_post(
            body=body,
            body_is_html=True,
            author_id=odoobot_partner.id if odoobot_partner else False,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        if notify_all_members:
            self._notify_channel_members(channel, message)

        return message

    # Publica los mensajes de cumpleaños en el canal.
    def _post_birthday_messages(self, channel, partners_today, partners_tomorrow, odoobot_partner):
        try:
            notify_all_members = False
            today = date.today()
            tomorrow = today + timedelta(days=1)

            if partners_today:
                title = "<h5><b>🎂🥳HOY CUMPLEN AÑOS LOS SIGUIENTES CLIENTES🥳🎂</b></h5>"
                self._post_single_birthday_message(
                    channel, partners_today, title, today, odoobot_partner, notify_all_members
                )

            if partners_tomorrow:
                title = "<b>📆🎂Mañana cumplen años los siguientes clientes🎂📆</b>"
                self._post_single_birthday_message(
                    channel, partners_tomorrow, title, tomorrow, odoobot_partner, notify_all_members
                )

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

