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
    
    # Calcular todos los tiempos de resolución (total y laboral)
    @api.depends('create_date', 'date_closed')
    def _compute_resolution_time(self):
        """
        Calculate resolution time in all formats: total and working hours.
        
        Calculates:
        - Total time: seconds, hours, days
        - Working time: seconds (considering work calendar and holidays)
        
        Uses the resource calendar of the employee associated with the user assigned to the ticket.
        If no user is assigned, falls back to company calendar.
        Excludes weekends and holidays defined in resource.calendar.leaves.
        """
        for record in self:
            # Get the employee associated with the user assigned to this ticket
            employee = None
            if record.user_id:
                employee = (
                    self.env["hr.employee"]
                    .sudo()
                    .search([("user_id", "=", record.user_id.id)], limit=1)
                )
            
            # Get the calendar from the employee, or fallback to company calendar
            user_calendar = employee.resource_calendar_id if employee else None
            # Initialize all fields
            record.resolution_time_seconds = 0
            record.resolution_time_hours = 0.0
            record.resolution_time_days = 0.0
            record.resolution_time_working_seconds = 0
            
            if not record.create_date or not record.date_closed:
                continue
            
            # ===== CALCULATE TOTAL TIME =====
            time_diff = record.date_closed - record.create_date
            total_seconds = time_diff.total_seconds()
            
            record.resolution_time_seconds = int(total_seconds)
            record.resolution_time_hours = total_seconds / 3600
            record.resolution_time_days = total_seconds / 86400
            
            # ===== CALCULATE WORKING TIME =====
            # Use calendar in this order of priority:
            # 1. Employee's calendar (from current user)
            # 2. Company's default calendar
            calendar = user_calendar or record.company_id.resource_calendar_id
            
            if not calendar:
                # If no calendar available, use total time as working time
                record.resolution_time_working_seconds = int(total_seconds)
                continue
            
            # Ensure dates have timezone information (required by resource calendar)
            tz = pytz.timezone(calendar.tz or "UTC")
            
            # Odoo stores datetime fields in UTC, we need to convert them to the calendar's timezone
            # First, ensure they have UTC timezone, then convert to calendar timezone
            if record.create_date.tzinfo is None:
                # If naive, localize to UTC first, then convert to calendar timezone
                start_date_tz = pytz.UTC.localize(record.create_date).astimezone(tz)
            else:
                # If already aware, convert to calendar timezone
                start_date_tz = record.create_date.astimezone(tz)
            
            if record.date_closed.tzinfo is None:
                # If naive, localize to UTC first, then convert to calendar timezone
                end_date_tz = pytz.UTC.localize(record.date_closed).astimezone(tz)
            else:
                # If already aware, convert to calendar timezone
                end_date_tz = record.date_closed.astimezone(tz)
            
            # Calculate working hours between dates using resource calendar
            # This method automatically excludes:
            # - Non-working hours (outside attendance schedule)
            # - Non-working days (weekends based on attendance)
            # - Holidays (resource.calendar.leaves)
            working_intervals = calendar._work_intervals_batch(
                start_date_tz, end_date_tz
            )[False]
            
            # Sum up all working intervals to get total working seconds
            total_working_seconds = sum(
                (stop - start).total_seconds()
                for start, stop, meta in working_intervals
            )
            
            record.resolution_time_working_seconds = int(total_working_seconds)

