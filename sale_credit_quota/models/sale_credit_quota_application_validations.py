from odoo import models, api, _
from odoo.exceptions import ValidationError

class SaleCreditQuotaApplication(models.Model):
    _inherit = 'sale.credit.quota.application'

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
