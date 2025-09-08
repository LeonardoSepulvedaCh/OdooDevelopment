# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from collections import defaultdict
import json
import re


class PosSession(models.Model):
    _inherit = 'pos.session'

    cash_denominations_data = fields.Text(
        string="Datos de Denominaciones",
        help="Datos estructurados de las denominaciones de efectivo en formato JSON"
    )

    def update_closing_control_state_session(self, notes):
        # Procesar las denominaciones antes de guardar las notas
        denominations_data = self._extract_denominations_from_notes(notes)
    
        # Llamar al método original
        result = super(PosSession, self).update_closing_control_state_session(notes)
        
        # Guardar los datos estructurados de denominaciones si no existen ya
        if denominations_data and not self.cash_denominations_data:
            self.write({'cash_denominations_data': json.dumps(denominations_data)})
        
        return result

    def post_closing_cash_details(self, counted_cash, denominations_data=None):
        # Llamar al método original
        result = super(PosSession, self).post_closing_cash_details(counted_cash)
        
        # Si se proporcionaron denominaciones, guardarlas
        if denominations_data:
            self.write({'cash_denominations_data': json.dumps(denominations_data)})
        
        return result

    def action_pos_session_closing_control(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        result = super(PosSession, self).action_pos_session_closing_control(
            balancing_account, amount_to_balance, bank_payment_method_diffs
        )
        
        if self.state == 'closing_control' and not isinstance(result, dict):
            # Crear un mensaje de notificación con enlace al reporte
            self.message_post(
                body=_("Sesión cerrada exitosamente. <a href='/report/pdf/pos_cash_report.report_cash_closing/%s' target='_blank'>Generar Reporte de Cierre</a>") % self.id,
                message_type='notification'
            )
        
        return result

    def _generate_cash_report(self):
        return self.env.ref('pos_cash_report.action_cash_report').report_action(self)

    @api.model
    def _get_cash_report_data(self, session_ids):
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
        orders = session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced'])
        return sum(orders.mapped('amount_total'))

    def _get_total_expenses(self, session):
        # Buscar movimientos de caja negativos (salidas)
        cash_statements = session.statement_line_ids.filtered(
            lambda l: l.amount < 0
        )
        return abs(sum(cash_statements.mapped('amount')))

    def _extract_denominations_from_notes(self, notes):
        if not notes:
            return []
        
        denominations = []
        lines = notes.split('\n')
        
        for line in lines:
            # Buscar líneas que contengan el formato "X x $Y.YY" o "X x Y.YY"
            # También buscar líneas que empiecen con tab o espacios
            has_tab_or_space = '\t' in line or line.startswith(' ')
            has_x = 'x' in line
            
            if has_tab_or_space and has_x:
                try:
                    # Remover tabs y espacios iniciales
                    clean_line = line.replace('\t', '').strip()
                    
                    # Dividir por 'x' para separar cantidad y valor
                    parts = clean_line.split('x')
                    if len(parts) == 2:
                        count_str = parts[0].strip()
                        value_str = parts[1].strip()
                        
                        # Extraer el valor numérico del string de valor
                        # Maneja formatos como: $100,00, $1.000,00, etc.
                        # Primero limpiar caracteres especiales y espacios
                        clean_value = value_str.replace('$', '').replace('\xa0', '').strip()
                        
                        # Buscar números con comas como separador decimal y puntos como separador de miles
                        # Patrón para números como: 100,00 o 1.000,00
                        value_match = re.search(r'[\d.]+,\d{2}', clean_value)
                        if value_match:
                            # Convertir formato europeo (1.000,00) a formato estándar (1000.00)
                            value_str_clean = value_match.group().replace('.', '').replace(',', '.')
                            count = int(count_str)
                            value = float(value_str_clean)
                            
                            denominations.append({
                                'value': value,
                                'count': count,
                                'total': count * value,
                                'formatted_value': value_str.strip()
                            })
                except (ValueError, IndexError):
                    continue
        
        # Ordenar por valor descendente
        denominations.sort(key=lambda x: x['value'], reverse=True)
        
        return denominations

    def _get_cash_denominations(self, session):
        denominations = []
        
        # Primero intentar obtener desde los datos estructurados
        if session.cash_denominations_data:
            try:
                denominations = json.loads(session.cash_denominations_data)
                return self._separate_bills_and_coins(denominations)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Si no hay datos estructurados, parsear desde las notas
        if session.config_id.cash_control and session.closing_notes:
            denominations = self._extract_denominations_from_notes(session.closing_notes)
            return self._separate_bills_and_coins(denominations)
        
        return {'bills': [], 'coins': []}

    def _separate_bills_and_coins(self, denominations):
        bills = []
        coins = []
        
        # Definir el límite entre monedas y billetes (1000 es el límite)
        for denom in denominations:
            if denom['value'] > 1000:
                bills.append(denom)
            else:
                coins.append(denom)
        
        return {
            'bills': bills,
            'coins': coins
        }

    def _parse_denominations_from_notes(self, notes):
        return self._parse_denominations_from_notes_static(notes)

    @api.model
    def _parse_denominations_from_notes_static(self, notes):
        # Crear una instancia temporal para usar el método de instancia
        temp_session = self.env['pos.session'].new()
        return temp_session._extract_denominations_from_notes(notes)

    def _get_payment_methods_summary(self, session):
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
        return self.env.ref('pos_cash_report.action_cash_report').report_action(self)
