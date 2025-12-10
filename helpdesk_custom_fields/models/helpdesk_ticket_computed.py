from odoo import api, fields, models
import pytz


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Calcular el número de adjuntos
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for ticket in self:
            ticket.attachment_count = len(ticket.attachment_ids)
    
    # Calcular productos disponibles de la factura
    @api.depends('invoice_id', 'invoice_id.invoice_line_ids', 'invoice_id.invoice_line_ids.product_id')
    def _compute_available_products(self):
        for ticket in self:
            if ticket.invoice_id and ticket.invoice_id.invoice_line_ids:
                products = ticket.invoice_id.invoice_line_ids.mapped('product_id')
                ticket.available_product_ids = [(6, 0, products.ids)]
            else:
                ticket.available_product_ids = [(5, 0, 0)]
    
    # Calcular todos los tiempos de resolución (total y laboral). Calcula: Tiempo total (segundos, horas, días) y Tiempo laboral (segundos considerando calendario de trabajo y festivos). Usa el calendario del empleado asociado al usuario asignado al ticket. Si no hay usuario asignado, usa el calendario de la compañía. Excluye fines de semana y festivos definidos en resource.calendar.leaves.
    @api.depends('create_date', 'date_closed')
    def _compute_resolution_time(self):
        for record in self:
            record._initialize_resolution_time_fields()
            
            if not record.create_date or not record.date_closed:
                continue
            
            total_seconds = record._calculate_total_time()
            calendar = record._get_user_calendar()
            record._calculate_working_time(calendar, total_seconds)
    
    # Inicializar todos los campos de tiempo de resolución en 0
    def _initialize_resolution_time_fields(self):
        self.resolution_time_seconds = 0
        self.resolution_time_hours = 0.0
        self.resolution_time_days = 0.0
        self.resolution_time_working_seconds = 0
    
    # Calcular el tiempo total de resolución en segundos, horas y días
    def _calculate_total_time(self):
        time_diff = self.date_closed - self.create_date
        total_seconds = time_diff.total_seconds()
        
        self.resolution_time_seconds = int(total_seconds)
        self.resolution_time_hours = total_seconds / 3600
        self.resolution_time_days = total_seconds / 86400
        
        return total_seconds
    
    # Obtener el calendario del usuario asignado o el calendario de la compañía. Prioridad: 1. Calendario del empleado (del usuario actual) 2. Calendario por defecto de la compañía
    def _get_user_calendar(self):
        employee = self._get_assigned_employee()
        user_calendar = employee.resource_calendar_id if employee else None
        return user_calendar or self.company_id.resource_calendar_id
    
    # Obtener el empleado asociado al usuario asignado a este ticket
    def _get_assigned_employee(self):
        if not self.user_id:
            return None
        
        return self.env["hr.employee"].sudo().search(
            [("user_id", "=", self.user_id.id)], 
            limit=1
        )
    
    # Calcular el tiempo de trabajo efectivo usando el calendario de recursos. Excluye: Horas no laborables (fuera del horario de atención), Días no laborables (fines de semana según el horario), Festivos (resource.calendar.leaves)
    def _calculate_working_time(self, calendar, total_seconds):
        if not calendar:
            self.resolution_time_working_seconds = int(total_seconds)
            return
        
        start_date_tz = self._convert_to_calendar_timezone(self.create_date, calendar)
        end_date_tz = self._convert_to_calendar_timezone(self.date_closed, calendar)
        
        working_intervals = calendar._work_intervals_batch(start_date_tz, end_date_tz)[False]
        
        total_working_seconds = sum(
            (stop - start).total_seconds()
            for start, stop, meta in working_intervals
        )
        
        self.resolution_time_working_seconds = int(total_working_seconds)
    
    # Convertir una fecha UTC a la zona horaria del calendario. Odoo almacena los campos datetime en UTC, necesitamos convertirlos a la zona horaria del calendario.
    def _convert_to_calendar_timezone(self, datetime_utc, calendar):
        tz = pytz.timezone(calendar.tz or "UTC")
        
        if datetime_utc.tzinfo is None:
            return pytz.UTC.localize(datetime_utc).astimezone(tz)
        
        return datetime_utc.astimezone(tz)

