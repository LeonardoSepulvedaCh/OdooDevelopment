from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    # Constante para el modelo de asistencias ZK
    _ZK_ATTENDANCE_MODEL = 'zk.attendance'
    
    zk_user_ids = fields.One2many(
        string='Usuarios ZK',
        comodel_name='zk.users',
        inverse_name='employee_id',
        help='Usuarios ZK vinculados a este empleado'
    )
    zk_user_count = fields.Integer(
        string='Cantidad de usuarios ZK',
        compute='_compute_zk_user_count',
        store=False
    )
    zk_attendance_ids = fields.Many2many(
        string='Asistencias ZK',
        comodel_name=_ZK_ATTENDANCE_MODEL,
        compute='_compute_zk_attendances',
        store=False,
        help='Registros de asistencia de los usuarios ZK vinculados a este empleado'
    )
    zk_attendance_count = fields.Integer(
        string='Total de asistencias',
        compute='_compute_zk_attendances',
        store=False
    )
    
    # Calcular la cantidad de usuarios ZK vinculados
    @api.depends('zk_user_ids')
    def _compute_zk_user_count(self):
        for record in self:
            record.zk_user_count = len(record.zk_user_ids)
    
    # Obtener los pares (user_id, device_id) de los usuarios ZK vinculados
    def _get_user_device_pairs(self):
        return [(str(zk_user.user_id), zk_user.device_id.id) 
                for zk_user in self.zk_user_ids 
                if zk_user.user_id and zk_user.device_id]
    
    # Construir el dominio para buscar asistencias de múltiples pares user_id/device_id
    def _build_attendance_domain(self, user_device_pairs):
        if not user_device_pairs:
            return []
        
        domain = []
        for _i in range(len(user_device_pairs) - 1):
            domain.append('|')
        
        for user_id, device_id in user_device_pairs:
            domain.extend([
                '&',
                ('user_id', '=', user_id),
                ('device_id', '=', device_id)
            ])
        
        return domain
    
    # Calcular las asistencias de los usuarios ZK vinculados
    @api.depends('zk_user_ids', 'zk_user_ids.user_id', 'zk_user_ids.device_id')
    def _compute_zk_attendances(self):
        for record in self:
            user_device_pairs = record._get_user_device_pairs()
            
            if user_device_pairs:
                domain = record._build_attendance_domain(user_device_pairs)
                attendances = self.env[self._ZK_ATTENDANCE_MODEL].search(domain, order='timestamp desc')
                record.zk_attendance_ids = attendances
                record.zk_attendance_count = len(attendances)
            else:
                record.zk_attendance_ids = False
                record.zk_attendance_count = 0

    # Acción para abrir la vista de asistencias del empleado
    def action_view_zk_attendances(self):
        self.ensure_one()
        
        user_device_pairs = self._get_user_device_pairs()
        domain = self._build_attendance_domain(user_device_pairs)
        
        return {
            'name': _('Asistencias de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': self._ZK_ATTENDANCE_MODEL,
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'create': False}
        }

