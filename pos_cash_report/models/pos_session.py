# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from collections import defaultdict


class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_pos_session_closing_control(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        """Sobrescribe el método de cierre para generar el reporte automáticamente"""
        result = super(PosSession, self).action_pos_session_closing_control(
            balancing_account, amount_to_balance, bank_payment_method_diffs
        )
        
        # Si el resultado es exitoso y la sesión está en estado de cierre, 
        # agregar la opción de generar el reporte
        if self.state == 'closing_control' and not isinstance(result, dict):
            # Crear un mensaje de notificación con enlace al reporte
            self.message_post(
                body=_("Sesión cerrada exitosamente. <a href='/report/pdf/pos_cash_report.report_cash_closing/%s' target='_blank'>Generar Reporte de Cierre</a>") % self.id,
                message_type='notification'
            )
        
        return result

    def _generate_cash_report(self):
        """Genera el reporte de cierre de caja en PDF"""
        return self.env.ref('pos_cash_report.action_cash_report').report_action(self)

    @api.model
    def _get_cash_report_data(self, session_ids):
        """Obtiene los datos para el reporte de cierre de caja"""
        sessions = self.browse(session_ids)
        result = []
        
        for session in sessions:
            data = {
                'session': session,
                'company': session.config_id.company_id,
                'config': session.config_id,
                'currency': session.currency_id,
                'total_sales': self._get_total_sales(session),
                'total_expenses': self._get_total_expenses(session),
                'cash_denominations': self._get_cash_denominations(session),
                'payment_methods': self._get_payment_methods_summary(session),
                'cash_box_start': session.cash_register_balance_start,
                'cash_box_end': session.cash_register_balance_end_real,
                'theoretical_cash': session.cash_register_total_entry_encoding,
                'difference': session.cash_register_difference,
            }
            result.append(data)
        
        return result

    def _get_total_sales(self, session):
        """Calcula el total de ventas de la sesión"""
        orders = session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced'])
        return sum(orders.mapped('amount_total'))

    def _get_total_expenses(self, session):
        """Calcula el total de gastos (salidas de dinero) de la sesión"""
        # Buscar movimientos de caja negativos (salidas)
        cash_statements = session.statement_line_ids.filtered(
            lambda l: l.amount < 0
        )
        return abs(sum(cash_statements.mapped('amount')))

    def _get_cash_denominations(self, session):
        """Obtiene el desglose por denominaciones si está configurado"""
        denominations = []
        
        # Si el POS tiene control de efectivo y denominaciones configuradas
        if session.config_id.cash_control:
            # Buscar movimientos de efectivo positivos (entradas)
            cash_statements = session.statement_line_ids.filtered(
                lambda l: l.amount > 0
            )
            
            # Agrupar por denominación si están en el nombre
            denomination_dict = defaultdict(lambda: {'count': 0, 'total': 0.0})
            
            for line in cash_statements:
                # Extraer información de denominación del nombre/referencia
                if line.payment_ref or line.name:
                    ref_text = line.payment_ref or line.name or ''
                    # Intentar parsear el formato "X monedas/billetes de Y"
                    parts = ref_text.split()
                    if len(parts) >= 4 and 'de' in parts:
                        try:
                            count = int(parts[0])
                            value_idx = parts.index('de') + 1
                            if value_idx < len(parts):
                                value = float(parts[value_idx])
                                denomination_dict[value]['count'] += count
                                denomination_dict[value]['total'] += line.amount
                        except (ValueError, IndexError):
                            pass
            
            # Convertir a lista ordenada
            for value in sorted(denomination_dict.keys(), reverse=True):
                denominations.append({
                    'value': value,
                    'count': denomination_dict[value]['count'],
                    'total': denomination_dict[value]['total'],
                })
        
        return denominations

    def _get_payment_methods_summary(self, session):
        """Obtiene resumen de métodos de pago utilizados"""
        payment_methods = []
        
        # Obtener todos los pagos de las órdenes de la sesión
        orders = session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced'])
        payments = orders.mapped('payment_ids')
        
        # Agrupar por método de pago
        method_totals = defaultdict(lambda: {'count': 0, 'total': 0.0})
        
        for payment in payments:
            method_name = payment.payment_method_id.name
            method_totals[method_name]['count'] += 1
            method_totals[method_name]['total'] += payment.amount
        
        # Convertir a lista
        for method_name, data in method_totals.items():
            payment_methods.append({
                'name': method_name,
                'count': data['count'],
                'total': data['total'],
            })
        
        # Ordenar por total descendente
        payment_methods.sort(key=lambda x: x['total'], reverse=True)
        
        return payment_methods

    def generate_cash_report_manual(self):
        """Acción manual para generar el reporte desde la vista de sesión"""
        return self.env.ref('pos_cash_report.action_cash_report').report_action(self)
