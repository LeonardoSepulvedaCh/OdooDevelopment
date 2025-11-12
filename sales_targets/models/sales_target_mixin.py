# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date
from dateutil.relativedelta import relativedelta


class SalesTargetMixin(models.AbstractModel):
    """
    Mixin con lógica compartida para cálculos de metas comerciales.
    Centraliza funciones comunes usadas por sales.target y sales.target.line.
    """
    _name = 'sales.target.mixin'
    _description = 'Mixin de Metas Comerciales'

    # Calcula las fechas de inicio y fin para un periodo (mes/año)
    @staticmethod
    def get_period_dates(year, month):
        month_int = int(month)
        date_from = date(year, month_int, 1)
        
        if month_int == 12:
            date_to = date(year, 12, 31)
        else:
            next_month = date_from + relativedelta(months=1)
            date_to = next_month - relativedelta(days=1)
        
        return date_from, date_to

    # Construye el dominio para buscar facturas en un periodo
    def _get_invoice_domain(self, salesperson_id, date_from, date_to, company_id):
        return [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_user_id', '=', salesperson_id),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', '=', company_id),
        ]

    # Calcula el total de una factura considerando su tipo (sin impuestos)
    @staticmethod
    def calculate_invoice_total(invoice):
        if invoice.move_type == 'out_invoice':
            return invoice.amount_untaxed_signed
        else:
            return -abs(invoice.amount_untaxed_signed)

    # Calcula el total de una línea de factura considerando su tipo
    @staticmethod
    def calculate_line_total(line, invoice_type):
        if invoice_type == 'out_invoice':
            return line.price_subtotal
        else:
            return -abs(line.price_subtotal)

    # Calcula el porcentaje de cumplimiento de una meta
    @staticmethod
    def calculate_achievement_percentage(target_amount, invoiced_amount):
        if target_amount > 0:
            return round((invoiced_amount / target_amount) * 100)
        return 0.0

