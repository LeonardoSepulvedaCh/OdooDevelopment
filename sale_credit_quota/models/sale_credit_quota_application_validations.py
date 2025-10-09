from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class SaleCreditQuotaApplication(models.Model):
    _inherit = 'sale.credit.quota.application'

    @api.constrains('application_date')
    def _check_application_date(self):
        for record in self:
            if record.application_date:
                if record.application_date > fields.Date.today():
                    raise ValidationError(
                        _('La fecha de solicitud no puede ser futura.')
                    )

    @api.constrains('credit_quota_start_date', 'credit_quota_end_date')
    def _check_credit_quota_dates(self):
        for record in self:
            if record.credit_quota_start_date and record.credit_quota_end_date:
                if record.credit_quota_end_date < record.credit_quota_start_date:
                    raise ValidationError(
                        _('La fecha de fin del cupo debe ser posterior a la fecha de inicio.')
                    )

    @api.constrains('final_normal_credit_quota', 'final_golden_credit_quota')
    def _check_credit_quotas(self):
        for record in self:
            if record.final_normal_credit_quota < 0:
                raise ValidationError(
                    _('El cupo normal final no puede ser negativo.')
                )
            if record.final_golden_credit_quota < 0:
                raise ValidationError(
                    _('El cupo dorado final no puede ser negativo.')
                )

    @api.constrains('suggestion_normal_credit_quota', 'suggestion_golden_credit_quota')
    def _check_suggestion_quotas(self):
        for record in self:
            if record.suggestion_normal_credit_quota < 0:
                raise ValidationError(
                    _('El cupo normal sugerido no puede ser negativo.')
                )
            if record.suggestion_golden_credit_quota < 0:
                raise ValidationError(
                    _('El cupo dorado sugerido no puede ser negativo.')
                )

    @api.constrains('customer_years_of_activity', 'business_years_of_activity')
    def _check_years_of_activity(self):
        for record in self:
            if record.customer_years_of_activity < 0:
                raise ValidationError(
                    _('Los años de actividad del cliente no pueden ser negativos.')
                )
            if record.business_years_of_activity < 0:
                raise ValidationError(
                    _('Los años de actividad del negocio no pueden ser negativos.')
                )

    @api.constrains('customer_id', 'state')
    def _check_single_approved_application_per_customer(self):
        for record in self:
            if record.customer_id and record.state == 'approved':
                existing_approved = self.search([
                    ('customer_id', '=', record.customer_id.id),
                    ('state', '=', 'approved'),
                    ('id', '!=', record.id),
                ])
                
                if existing_approved:
                    existing_names = ', '.join(existing_approved.mapped('name'))
                    raise ValidationError(
                        _('El cliente "%s" ya tiene una solicitud aprobada: %s.\n\n'
                          'Un cliente solo puede tener una solicitud de cupo de crédito aprobada a la vez. '
                          'Debe finalizar la solicitud existente antes de aprobar una nueva.') % 
                        (record.customer_id.name, existing_names)
                    )
