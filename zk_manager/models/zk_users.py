from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from zk import ZK, const

class ZKUsers(models.Model):
    _name = 'zk.users'
    _description = 'Usuarios de dispositivos ZKTECO'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    privilege = fields.Selection(string='Privilegio', selection=[('admin', 'Admin'), ('user', 'Usuario')], default='user')
    device_id = fields.Many2one(string='Dispositivo', comodel_name='zk.devices', required=True, ondelete='cascade')
    user_id = fields.Integer(string='ID de usuario', required=True)
    group_id = fields.Char(string='ID de grupo', help='ID del grupo al que pertenece el usuario')
    password = fields.Integer(string='Contraseña', help='Contraseña numérica del usuario en el dispositivo (solo números)')
    card = fields.Integer(string='Tarjeta', help='Número de tarjeta RFID del usuario')
    
    employee_id = fields.Many2one(string='Empleado', comodel_name='hr.employee', ondelete='restrict', help='Empleado vinculado a este usuario ZK')
    image_1920 = fields.Binary(string='Foto', max_width=1920, max_height=1920)
    
    active = fields.Boolean(string='Activo', default=True)
    create_date = fields.Datetime(string='Fecha de creación', readonly=True)
    write_date = fields.Datetime(string='Última modificación', readonly=True)
    
    # Campos computados de asistencia
    last_attendance_date = fields.Datetime(
        string='Última asistencia',
        compute='_compute_attendance_info',
        store=False,
        help='Fecha y hora del último registro de asistencia'
    )
    total_attendances = fields.Integer(
        string='Total de asistencias',
        compute='_compute_attendance_info',
        store=False,
        help='Número total de registros de asistencia'
    )

    # Validar que no existan usuarios duplicados (user_id) en el mismo dispositivo
    @api.constrains('user_id', 'device_id')
    def _check_unique_user_device(self):
        for record in self:
            if record.user_id and record.device_id:
                duplicates = self.search([
                    ('user_id', '=', record.user_id),
                    ('device_id', '=', record.device_id.id),
                    ('id', '!=', record.id)
                ])
                if duplicates:
                    raise ValidationError(
                        _('El ID de usuario %s ya existe en el dispositivo %s.') % (record.user_id, record.device_id.name)
                    )

    # Calcular la información de asistencias del usuario
    @api.depends('user_id', 'device_id')
    def _compute_attendance_info(self):
        for record in self:
            if record.user_id:
                attendances = self.env['zk.attendance'].search([
                    ('user_id', '=', str(record.user_id)),
                    ('device_id', '=', record.device_id.id)
                ], order='timestamp desc')
                
                record.total_attendances = len(attendances)
                record.last_attendance_date = attendances[0].timestamp if attendances else False
            else:
                record.total_attendances = 0
                record.last_attendance_date = False

    # Copiar la foto del empleado al usuario ZK cuando se vincula un empleado
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.image_1920:
            self.image_1920 = self.employee_id.image_1920

    # Buscar el UID del usuario existente en el dispositivo
    def _find_existing_user_uid(self, connection):
        device_users = connection.get_users()
        for device_user in device_users:
            if str(device_user.user_id) == str(self.user_id):
                return device_user.uid
        return None

    # Preparar los parámetros para sincronizar el usuario al dispositivo
    def _prepare_sync_params(self):
        privilege_value = const.USER_ADMIN if self.privilege == 'admin' else const.USER_DEFAULT
        user_password = str(self.password) if self.password else ''
        group_id_value = str(self.group_id) if self.group_id else ''
        card_value = int(self.card) if self.card else 0
        
        return {
            'privilege': privilege_value,
            'password': user_password,
            'group_id': group_id_value,
            'card': card_value
        }

    # Re-habilita y desconecta el dispositivo de forma segura
    def _cleanup_connection(self, connection):
        try:
            connection.enable_device()
        except Exception:
            pass
        try:
            connection.disconnect()
        except Exception:
            pass
    
    # Sincroniza el usuario al dispositivo ZK
    def action_sync_to_device(self):
        self.ensure_one()
        
        if not self.device_id:
            raise UserError(_('No se ha especificado un dispositivo'))
        
        if not self.user_id:
            raise UserError(_('El ID de usuario es obligatorio para sincronizar'))
        
        device_password = 0 if not self.device_id.password else self.device_id.password
        zk_device = ZK(self.device_id.ip, self.device_id.port, timeout=5, password=device_password, force_udp=False, ommit_ping=True)
        connection = None
        
        try:
            connection = zk_device.connect()
            if not connection:
                raise UserError(_('No se pudo conectar al dispositivo'))
            
            connection.disable_device()
            existing_uid = self._find_existing_user_uid(connection)
            sync_params = self._prepare_sync_params()
            
            connection.set_user(
                uid=existing_uid,
                name=self.name,
                privilege=sync_params['privilege'],
                password=sync_params['password'],
                group_id=sync_params['group_id'],
                user_id=str(self.user_id),
                card=sync_params['card']
            )
            
            connection.enable_device()
            self.device_id.status = 'connected'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Usuario sincronizado'),
                    'message': _('El usuario %s se ha sincronizado exitosamente al dispositivo %s') % (self.name, self.device_id.name),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            if connection:
                self._cleanup_connection(connection)
            raise UserError(_('Error al sincronizar usuario al dispositivo: %s') % str(e))
        
        finally:
            if connection:
                connection.disconnect()
    