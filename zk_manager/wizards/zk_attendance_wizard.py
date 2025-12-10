from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ZKAttendanceWizard(models.TransientModel):
    _name = 'zk.attendance.wizard'
    _description = 'Wizard para obtener registros de asistencia'

    device_id = fields.Many2one('zk.devices', string='Dispositivo', required=True)
    state = fields.Selection([
        ('draft', 'Listo'),
        ('loading', 'Procesando...'),
        ('done', 'Completado')
    ], default='draft', string='Estado')
    records_count = fields.Integer(string='Registros nuevos', readonly=True)
    message = fields.Text(string='Mensaje', readonly=True)

    # Obtiene los registros de asistencia del dispositivo
    def action_get_attendance(self):
        self.ensure_one()
        
        try:
            # Cambiar estado a procesando
            self.write({
                'state': 'loading',
                'message': 'Conectando al dispositivo y obteniendo registros...'
            })
            self.env.cr.commit()
            
            # Obtener registros
            records_count = self.device_id.get_attendance_info(self.device_id)
            
            # Actualizar estado
            self.write({
                'state': 'done',
                'records_count': records_count,
                'message': f'Se han importado {records_count} registros nuevos de asistencia.'
            })
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'zk.attendance.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
            
        except Exception as e:
            self.write({
                'state': 'draft',
                'message': f'Error: {str(e)}'
            })
            raise UserError(_('Error al obtener registros: %s') % str(e))

