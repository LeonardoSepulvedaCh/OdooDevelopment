from odoo import models, api, fields
from datetime import datetime, date

class SaleCreditQuotaApplication(models.Model):
    _inherit = 'sale.credit.quota.application'

    @api.depends('customer_id')
    def _compute_customer_child_ids(self):
        for record in self:
            if record.customer_id:
                child_partners = self.env['res.partner'].search([
                    ('parent_id', '=', record.customer_id.id)
                ])
                record.customer_child_ids = [(6, 0, child_partners.ids)]
            else:
                record.customer_child_ids = [(6, 0, [])]

    @api.depends('customer_child_ids')
    def _compute_customer_child_count(self):
        for record in self:
            record.customer_child_count = len(record.customer_child_ids)

    @api.depends('customer_id', 'codeudor_ids.partner_id')
    def _compute_related_partner_ids(self):
        for record in self:
            partner_ids = []
            
            if record.customer_id:
                partner_ids.append(record.customer_id.id)
            
            if record.codeudor_ids:
                partner_ids.extend(record.codeudor_ids.mapped('partner_id').ids)
            
            record.related_partner_ids = [(6, 0, partner_ids)]

    @api.depends('related_partner_ids')
    def _compute_document_ids(self):
        for record in self:
            if record.related_partner_ids:
                documents = self.env['documents.document'].search([
                    ('partner_id', 'in', record.related_partner_ids.ids),
                    ('type', '!=', 'folder')
                ])
                record.document_ids = [(6, 0, documents.ids)]
            else:
                record.document_ids = [(6, 0, [])]

    def _calculate_total_purchased_for_period(self, customer_id, start_date, end_date):
        """Método auxiliar para calcular el total de compras en un período específico"""
        if not customer_id:
            return 0.0
        
        domain = [
            ('partner_id', '=', customer_id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
        ]
        
        result = self.env['account.move']._read_group(
            domain,
            ['move_type'],
            ['amount_total_signed:sum']
        )
        
        total = 0.0
        for move_type, amount_sum in result:
            if move_type == 'out_invoice':
                total += amount_sum
            elif move_type == 'out_refund':
                total -= amount_sum
        
        return total

    @api.depends('customer_id')
    def _compute_total_purchased_this_year(self):
        for record in self:
            current_year = date.today().year
            start_date = date(current_year, 1, 1)
            end_date = date(current_year, 12, 31)
            
            record.total_purchased_this_year = record._calculate_total_purchased_for_period(
                record.customer_id.id if record.customer_id else None,
                start_date,
                end_date
            )

    @api.depends('customer_id')
    def _compute_total_purchased_last_year(self):
        for record in self:
            last_year = date.today().year - 1
            start_date = date(last_year, 1, 1)
            end_date = date(last_year, 12, 31)
            
            record.total_purchased_last_year = record._calculate_total_purchased_for_period(
                record.customer_id.id if record.customer_id else None,
                start_date,
                end_date
            )

    @api.depends('customer_id')
    def _compute_total_purchased_last_two_years(self):
        for record in self:
            current_year = date.today().year
            start_date = date(current_year - 2, 1, 1)
            end_date = date(current_year - 1, 12, 31)
            
            record.total_purchased_last_two_years = record._calculate_total_purchased_for_period(
                record.customer_id.id if record.customer_id else None,
                start_date,
                end_date
            )

    @api.depends('customer_id')
    def _compute_total_purchased_last_three_years(self):
        for record in self:
            current_year = date.today().year
            start_date = date(current_year - 3, 1, 1)
            end_date = date(current_year - 1, 12, 31)
            
            record.total_purchased_last_three_years = record._calculate_total_purchased_for_period(
                record.customer_id.id if record.customer_id else None,
                start_date,
                end_date
            )

    @api.depends('customer_id')
    def _compute_all_purchase_totals(self):
        """Calcula todos los totales de compras en una sola operación"""
        for record in self:
            if not record.customer_id:
                record.total_purchased_this_year = 0.0
                record.total_purchased_last_year = 0.0
                record.total_purchased_last_two_years = 0.0
                record.total_purchased_last_three_years = 0.0
                continue
            
            current_year = date.today().year
            
            # Definir todos los períodos
            periods = {
                'this_year': (date(current_year, 1, 1), date(current_year, 12, 31)),
                'last_year': (date(current_year - 1, 1, 1), date(current_year - 1, 12, 31)),
                'last_two_years': (date(current_year - 2, 1, 1), date(current_year - 1, 12, 31)),
                'last_three_years': (date(current_year - 3, 1, 1), date(current_year - 1, 12, 31)),
            }
            
            # Calcular todos los totales
            for period_name, (start_date, end_date) in periods.items():
                total = record._calculate_total_purchased_for_period(
                    record.customer_id.id, start_date, end_date
                )
                
                if period_name == 'this_year':
                    record.total_purchased_this_year = total
                elif period_name == 'last_year':
                    record.total_purchased_last_year = total
                elif period_name == 'last_two_years':
                    record.total_purchased_last_two_years = total
                elif period_name == 'last_three_years':
                    record.total_purchased_last_three_years = total