from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
import calendar


class ResPartner(models.Model):
    _inherit = 'res.partner'

    birth_date = fields.Date(string="Fecha de Nacimiento", help="Fecha de nacimiento del contacto")
    
    # Relación con los contactos adicionales
    related_contact_ids = fields.One2many('related.contact', 'partner_id', string='Contactos Adicionales')

    # Función para obtener los contactos con cumpleaños en una fecha específica
    @api.model
    def _partners_with_bday_on(self, check_date):
        print("==== Se ejecuto la función de checkear cumpleaños ====")
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
        print("==== Se ejecuto la función del cron job ===")
        today_str = fields.Date.context_today(self) 
        today = fields.Date.to_date(today_str)
        tomorrow = today + relativedelta(days=1)

        partners_today = self._partners_with_bday_on(today)
        partners_tomorrow = self._partners_with_bday_on(tomorrow)

        # Manejar cumpleaños del 29 de febrero en años no bisiestos
        if today.month == 2 and today.day == 28 and not calendar.isleap(today.year):
            self.env.cr.execute(
                "SELECT id FROM res_partner WHERE birth_date IS NOT NULL AND to_char(birth_date, 'MM-DD') = %s",
                ('02-29',)
            )
            ids = [r[0] for r in self.env.cr.fetchall()]
            partners_today |= self.browse(ids)

        # Si no hay nada que notificar, salir
        if not partners_today and not partners_tomorrow:
            return True

        # Preparar el mensaje
        body_today = ""
        if partners_today:
            names = ", ".join(partners_today.mapped("name"))
            body_today = _("Hoy cumplen años: %s") % names

        body_tom = ""
        if partners_tomorrow:
            names = ", ".join(partners_tomorrow.mapped("name"))
            body_tom = _("Mañana cumplen años: %s") % names

        full_body = "\n".join([b for b in (body_today, body_tom) if b])

        # Enviar por chat con OdooBot al usuario configurado (por defecto: env.user)
        try:
            odoobot_user = self.env.ref('base.user_root') 
            odoobot_partner = odoobot_user.partner_id
        except Exception:
            odoobot_partner = self.env.user.partner_id

        target_user = self.env.user
        if not target_user.partner_id:
            return True

        # conseguir/crear el canal privado entre OdooBot y el usuario
        channel_get = self.env['mail.channel'].channel_get([target_user.partner_id.id])
        channel = self.env['mail.channel'].browse(channel_get.get('id'))

        # postear como OdooBot 
        channel.message_post(
            body=full_body,
            author_id=odoobot_partner.id,
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )

        return True