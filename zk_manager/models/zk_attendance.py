from odoo import models, fields, api, _

class ZKAttendance(models.Model):
    _name = 'zk.attendance'
    _description = 'Registros de Asistencia ZKTECO'
    _order = 'timestamp desc'

    name = fields.Char(string='Nombre del usuario', required=True)
    user_id = fields.Char(string='ID de usuario', required=True)
    device_id = fields.Many2one(string='Dispositivo', comodel_name='zk.devices', required=True, ondelete='cascade')
    timestamp = fields.Datetime(string='Fecha y hora (Odoo)', required=True)
    timestamp_device = fields.Char(string='Fecha y hora (Dispositivo)', help='Hora exacta registrada en el dispositivo sin conversiones')
    status = fields.Integer(string='Estado')
    punch = fields.Integer(string='Tipo de marcación')
    uid = fields.Integer(string='UID del dispositivo')
    
    # Campos para filtros
    date = fields.Date(string='Fecha', compute='_compute_date', store=True)
    hour = fields.Float(string='Hora', compute='_compute_hour', store=True)
    
    # Campos para mostrar formato 12 horas (desde dispositivo)
    time_12h_device = fields.Char(string='Hora (12h) Dispositivo', compute='_compute_time_12h_device', store=True)
    datetime_formatted_device = fields.Char(string='Fecha y Hora Dispositivo', compute='_compute_datetime_formatted_device', store=True)
    
    active = fields.Boolean(string='Activo', default=True)
    create_date = fields.Datetime(string='Fecha de creación', readonly=True)
    write_date = fields.Datetime(string='Última modificación', readonly=True)

    @api.depends('timestamp')
    def _compute_date(self):
        for record in self:
            if record.timestamp:
                record.date = fields.Date.to_date(record.timestamp)
            else:
                record.date = False

    @api.depends('timestamp')
    def _compute_hour(self):
        for record in self:
            if record.timestamp:
                # Convertir a la zona horaria del usuario antes de extraer la hora
                timestamp_tz = fields.Datetime.context_timestamp(record, record.timestamp)
                record.hour = timestamp_tz.hour + timestamp_tz.minute / 60.0
            else:
                record.hour = 0.0

    # Calcular la hora en formato 12h desde el timestamp del dispositivo
    @api.depends('timestamp_device')
    def _compute_time_12h_device(self):
        for record in self:
            if record.timestamp_device:
                try:
                    dt = fields.Datetime.from_string(record.timestamp_device)
                    record.time_12h_device = dt.strftime('%I:%M %p')
                except (ValueError, TypeError):
                    record.time_12h_device = record.timestamp_device
            else:
                record.time_12h_device = ''

    # Calcular la fecha y hora completa en formato 12h desde el timestamp del dispositivo
    @api.depends('timestamp_device')
    def _compute_datetime_formatted_device(self):
        for record in self:
            if record.timestamp_device:
                try:
                    dt = fields.Datetime.from_string(record.timestamp_device)
                    record.datetime_formatted_device = dt.strftime('%Y-%m-%d %I:%M:%S %p')
                except (ValueError, TypeError):
                    record.datetime_formatted_device = record.timestamp_device
            else:
                record.datetime_formatted_device = '' 