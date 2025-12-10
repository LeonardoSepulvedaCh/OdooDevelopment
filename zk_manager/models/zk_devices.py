from odoo import models, fields, api, _
from zk import ZK, const
from odoo.exceptions import UserError

class ZKDevices(models.Model):
    _name = 'zk.devices'
    _description = 'Dispositivos ZKTECO'
    
    _ZK_USERS_MODEL = 'zk.users'
    _ZK_ATTENDANCE_MODEL = 'zk.attendance'
    _ERROR_CONNECTION = 'Error al conectar al dispositivo'
    _ERROR_CONNECTION_DETAIL = 'Error al conectar al dispositivo: %s'
    _ERROR_GET_USERS = 'Error al obtener usuarios del dispositivo: %s'
    _ERROR_GET_ATTENDANCE = 'Error al obtener registros de asistencia del dispositivo: %s'
    _ERROR_CLEAR_ATTENDANCE = 'Error al eliminar registros de asistencia del dispositivo: %s'

    name = fields.Char(string='Nombre del dispositivo', required=True)
    device_model = fields.Char(string='Modelo del dispositivo')
    ip = fields.Char(string='Dirección IP', required=True)
    port = fields.Integer(string='Puerto', default=4370)
    password = fields.Char(string='Contraseña', help='Dejar vacío si el dispositivo no tiene contraseña')
    status = fields.Selection(string='Estado', selection=[('connected', 'Conectado'), ('disconnected', 'Desconectado')], default='disconnected')
    users = fields.One2many(string='Usuarios', comodel_name=_ZK_USERS_MODEL, inverse_name='device_id')
    attendance_records = fields.One2many(string='Registros de Asistencia', comodel_name=_ZK_ATTENDANCE_MODEL, inverse_name='device_id')

    # Conectar al dispositivo ZK
    def action_connect(self):
        password = 0 if not self.password else self.password
        
        zk_device = ZK(self.ip, self.port, timeout=5, password=password, force_udp=False, ommit_ping=True)
        connection = None
        try:
            connection = zk_device.connect()
            if not connection:
                raise UserError(_('No se pudo conectar al dispositivo'))
            self.status = 'connected'
            self.device_model = connection.get_device_name()
            return connection
        except Exception as e:
            self.status = 'disconnected'
            raise UserError(_(self._ERROR_CONNECTION_DETAIL % str(e)))
        finally:
            if connection:
                connection.disconnect()

    def action_disconnect(self):
        self.status = 'disconnected'
        return True

    # Obtener los usuarios del dispositivo ZK
    def get_users(self):
        password = 0 if not self.password else self.password
        
        zk_device = ZK(self.ip, self.port, timeout=5, password=password, force_udp=False, ommit_ping=True)
        connection = None
        try:
            connection = zk_device.connect()
            if not connection:
                raise UserError(_(self._ERROR_CONNECTION))
          
            device_users = connection.get_users()
            
            new_users_count = 0
            updated_users_count = 0
            
            for user in device_users:
                privilege = 'user'
                if user.privilege == const.USER_ADMIN:
                    privilege = 'admin'
                
                # Buscar si el usuario ya existe basándose en user_id y device_id
                existing_user = self.env[self._ZK_USERS_MODEL].search([
                    ('user_id', '=', user.user_id),
                    ('device_id', '=', self.id)
                ], limit=1)
                
                if existing_user:
                    # Actualizar usuario existente
                    existing_user.write({
                        'name': user.name,
                        'privilege': privilege,
                    })
                    updated_users_count += 1
                else:
                    # Crear nuevo usuario
                    self.env[self._ZK_USERS_MODEL].create({
                        'name': user.name,
                        'privilege': privilege,
                        'device_id': self.id,
                        'user_id': user.user_id
                    })
                    new_users_count += 1
            
            self.status = 'connected'
            
            message = f'Sincronización completada: {new_users_count} usuarios nuevos, {updated_users_count} usuarios actualizados'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Usuarios sincronizados'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            self.status = 'disconnected'
            raise UserError(_(self._ERROR_GET_USERS % str(e)))
        finally:
            if connection:
                connection.disconnect()

    # Construir conjunto de claves existentes para deduplicación
    def _build_existing_keys(self, device_id):
        existing_records = self.env[self._ZK_ATTENDANCE_MODEL].search([
            ('device_id', '=', device_id)
        ])
        
        existing_keys = set()
        for existing in existing_records:
            # Clave compuesta: (device_id, user_id, timestamp)
            if existing.timestamp:
                key = (existing.device_id.id, existing.user_id, existing.timestamp)
                existing_keys.add(key)
            # También mantener el UID como respaldo
            if existing.uid:
                existing_keys.add(('uid', existing.uid))
        
        return existing_keys
    
    # Verificar si un registro ya existe
    def _is_duplicate_record(self, record, device_id, existing_keys):
        composite_key = (device_id, str(record.user_id), record.timestamp)
        uid_key = ('uid', record.uid)
        return composite_key in existing_keys or uid_key in existing_keys
    
    # Preparar datos de un registro de asistencia para crear
    def _prepare_attendance_record(self, record, device_id, user_dict):
        user_name = user_dict.get(str(record.user_id), f"Usuario {record.user_id}")
        timestamp_device_str = record.timestamp.strftime('%Y-%m-%d %H:%M:%S') if record.timestamp else ''
        
        return {
            'name': user_name,
            'user_id': str(record.user_id),
            'device_id': device_id,
            'timestamp': record.timestamp,
            'timestamp_device': timestamp_device_str,
            'status': record.status,
            'punch': record.punch,
            'uid': record.uid
        }
    
    # Obtener los registros de asistencia del dispositivo ZK
    def get_attendance_info(self, device_id):
        password = 0 if not device_id.password else device_id.password

        zk_device = ZK(device_id.ip, device_id.port, password=password, force_udp=False, ommit_ping=True)
        connection = None
        try:
            connection = zk_device.connect()
            if not connection:
                raise UserError(_(self._ERROR_CONNECTION))
            
            attendance_records = connection.get_attendance()
            
            if not attendance_records:
                return 0
            
            device_users = self.env[self._ZK_USERS_MODEL].search([('device_id', '=', device_id.id)])
            user_dict = {str(user.user_id): user.name for user in device_users}
            
            # Obtener claves de registros existentes para deduplicación
            existing_keys = self._build_existing_keys(device_id.id)
            
            # Procesar registros de asistencia del dispositivo
            records_to_create = []
            for record in attendance_records:
                if self._is_duplicate_record(record, device_id.id, existing_keys):
                    continue
                
                record_data = self._prepare_attendance_record(record, device_id.id, user_dict)
                records_to_create.append(record_data)
            
            if records_to_create:
                self.env[self._ZK_ATTENDANCE_MODEL].create(records_to_create)
            
            return len(records_to_create)
            
        except Exception as e:
            raise UserError(_(self._ERROR_GET_ATTENDANCE % str(e)))
        finally:
            if connection:
                connection.disconnect()

    # Acción para obtener asistencia desde la vista del dispositivo
    def action_get_attendance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Obtener Registros de Asistencia'),
            'res_model': 'zk.attendance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_device_id': self.id,
            }
        }

    # Eliminar los registros de asistencia del dispositivo biométrico
    def action_clear_attendance(self):
        password = 0 if not self.password else self.password
        
        zk_device = ZK(self.ip, self.port, timeout=5, password=password, force_udp=False, ommit_ping=True)
        connection = None
        try:
            connection = zk_device.connect()
            if not connection:
                raise UserError(_(self._ERROR_CONNECTION))
            
            connection.clear_attendance()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Registros eliminados'),
                    'message': _('Los registros de asistencia han sido eliminados del dispositivo biométrico'),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            raise UserError(_(self._ERROR_CLEAR_ATTENDANCE % str(e)))
        finally:
            if connection:
                connection.disconnect()
