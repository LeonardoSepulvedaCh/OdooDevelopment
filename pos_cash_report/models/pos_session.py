from odoo import api, fields, models, _
from collections import defaultdict
from markupsafe import Markup
import json
import re


class PosSession(models.Model):
    _inherit = 'pos.session'

    # Constantes para validación de denominaciones - Denominaciones válidas en pesos colombianos (COP)
    VALID_DENOMINATIONS = [
        100000, 50000, 20000, 10000, 5000, 2000, 1000,
        500, 200, 100, 50,
    ]
    BILL_THRESHOLD = 1000
    MAX_COUNT_PER_DENOMINATION = 10000  
    MAX_DENOMINATION_VALUE = 200000  

    cash_denominations_data = fields.Text(
        string="Datos de Denominaciones",
        help="Datos estructurados de las denominaciones de efectivo en formato JSON"
    )
    
    def get_report_data(self):
        """
        Método público para obtener los datos del reporte.
        Utilizado directamente desde la plantilla QWeb.
        """
        self.ensure_one()
        return self._prepare_report_data(self)

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
            # Crear mensaje con Markup para prevenir XSS
            # self.id es un entero, pero usamos int() explícitamente para seguridad
            session_id = int(self.id)
            report_url = f'/report/pdf/pos_cash_report.report_cash_closing/{session_id}'
            
            # Construir mensaje HTML de forma segura con Markup
            message_body = Markup(
                _("Sesión cerrada exitosamente. <a href='%s' target='_blank'>Generar Reporte de Cierre</a>")
            ) % report_url
            
            self.message_post(
                body=message_body,
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
            
            if not (has_tab_or_space and has_x):
                continue
            
            denomination = self._parse_denomination_line(line)
            if denomination:
                denominations.append(denomination)
        
        # Ordenar por valor descendente
        denominations.sort(key=lambda x: x['value'], reverse=True)
        
        return denominations

    # Longitud máxima para valores de denominación (previene ReDoS)
    MAX_VALUE_STRING_LENGTH = 20

    # Parsear una línea individual para extraer información de denominación
    def _parse_denomination_line(self, line):
        try:
            # Remover tabs y espacios iniciales
            clean_line = line.replace('\t', '').strip()
            
            # Dividir por 'x' para separar cantidad y valor
            parts = clean_line.split('x')
            if len(parts) != 2:
                return None
            
            count_str = parts[0].strip()
            value_str = parts[1].strip()
            
            # Extraer el valor numérico del string de valor
            clean_value = value_str.replace('$', '').replace('\xa0', '').strip()
            
            # Limitar longitud para prevenir ataques ReDoS
            if len(clean_value) > self.MAX_VALUE_STRING_LENGTH:
                return None
            
            value_match = re.match(r'^(\d{1,3})(?:\.(\d{3}))*,(\d{2})$', clean_value)
            if not value_match:
                # Intentar formato simple sin separador de miles: 100000,00
                value_match = re.match(r'^(\d+),(\d{2})$', clean_value)
                if not value_match:
                    return None
                # Extraer valor del formato simple
                integer_part = value_match.group(1)
                decimal_part = value_match.group(2)
                value = float(f"{integer_part}.{decimal_part}")
            else:
                # Reconstruir el número desde los grupos capturados
                value_str_clean = clean_value.replace('.', '').replace(',', '.')
                value = float(value_str_clean)
            
            count = int(count_str)
            
            return {
                'value': value,
                'count': count,
                'total': count * value,
                'formatted_value': value_str.strip()
            }
        except (ValueError, IndexError):
            return None

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

    # Valida y sanitiza una denominación individual. Retorna la denominación validada o None si es inválida.
    def _validate_denomination(self, denom):
        if not isinstance(denom, dict):
            return None
        
        # Verificar que existan las claves requeridas
        required_keys = {'value', 'count'}
        if not required_keys.issubset(denom.keys()):
            return None
        
        try:
            value = float(denom.get('value', 0))
            count = int(denom.get('count', 0))
        except (ValueError, TypeError):
            return None
        
        # Validar rangos
        if value <= 0 or value > self.MAX_DENOMINATION_VALUE:
            return None
        if count <= 0 or count > self.MAX_COUNT_PER_DENOMINATION:
            return None
        
        # Recalcular el total (no confiar en el valor proporcionado)
        calculated_total = round(value * count, 2)
        
        # Obtener el valor formateado, si existe, o generarlo
        formatted_value = denom.get('formatted_value', '')
        if not formatted_value or not isinstance(formatted_value, str):
            formatted_value = f"${value:,.2f}"
        
        return {
            'value': value,
            'count': count,
            'total': calculated_total,
            'formatted_value': formatted_value,
        }

    # Separa las denominaciones en billetes y monedas. Valida y sanitiza cada denominación antes de clasificarla.
    def _separate_bills_and_coins(self, denominations):
        bills = []
        coins = []
        
        if not isinstance(denominations, list):
            return {'bills': [], 'coins': []}
        
        for denom in denominations:
            validated = self._validate_denomination(denom)
            if not validated:
                continue
            
            # Clasificar según el umbral definido
            if validated['value'] > self.BILL_THRESHOLD:
                bills.append(validated)
            else:
                coins.append(validated)
        
        # Ordenar por valor descendente
        bills.sort(key=lambda x: x['value'], reverse=True)
        coins.sort(key=lambda x: x['value'], reverse=True)
        
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

    def _get_payment_methods_totals(self, payment_methods):
        """Calcula los totales de métodos de pago"""
        total_count = sum(method['count'] for method in payment_methods)
        total_amount = sum(method['total'] for method in payment_methods)
        return {
            'count': total_count,
            'amount': total_amount
        }

    def _get_denominations_totals(self, denominations_data):
        """Calcula los totales de billetes y monedas"""
        bills = denominations_data.get('bills', [])
        coins = denominations_data.get('coins', [])
        
        bills_count = sum(d['count'] for d in bills)
        bills_total = sum(d['total'] for d in bills)
        
        coins_count = sum(d['count'] for d in coins)
        coins_total = sum(d['total'] for d in coins)
        
        return {
            'bills': {
                'count': bills_count,
                'total': bills_total
            },
            'coins': {
                'count': coins_count,
                'total': coins_total
            },
            'grand_total': bills_total + coins_total
        }

    def _get_cash_movements(self, session):
        """Obtiene y calcula los movimientos de efectivo"""
        cash_lines = session.statement_line_ids.filtered(lambda l: l.amount != 0)
        
        movements = []
        for line in cash_lines:
            movements.append({
                'description': line.payment_ref or line.name or 'Movimiento de efectivo',
                'date': line.date,
                'amount': line.amount,
                'is_negative': line.amount < 0
            })
        
        total_movements = sum(line.amount for line in cash_lines)
        
        return {
            'lines': movements,
            'total': total_movements,
            'has_movements': bool(cash_lines)
        }

    def _get_orders_summary(self, session):
        """Obtiene el resumen de órdenes de la sesión"""
        paid_orders = session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced'])
        cancelled_orders = session.order_ids.filtered(lambda o: o.state == 'cancel')
        
        return {
            'paid_count': len(paid_orders),
            'cancelled_count': len(cancelled_orders),
            'total_count': len(session.order_ids)
        }

    def _prepare_report_data(self, session):
        """
        Prepara todos los datos necesarios para el reporte de cierre de caja.
        Consolida todos los cálculos en un solo lugar para mejor rendimiento y mantenibilidad.
        """
        # Cálculos financieros
        total_sales = self._get_total_sales(session)
        total_expenses = self._get_total_expenses(session)
        
        # Métodos de pago
        payment_methods = self._get_payment_methods_summary(session)
        payment_methods_totals = self._get_payment_methods_totals(payment_methods)
        
        # Denominaciones de efectivo
        denominations_data = self._get_cash_denominations(session)
        denominations_totals = self._get_denominations_totals(denominations_data)
        
        # Movimientos de efectivo
        cash_movements = self._get_cash_movements(session)
        
        # Resumen de órdenes
        orders_summary = self._get_orders_summary(session)
        
        # Extraer solo el número de la sesión del nombre completo
        session_number = session.name.split('/')[-1] if session.name else ''
        
        return {
            # Información de sesión
            'session': session,
            'session_number': session_number,
            'user': session.user_id,
            'config': session.config_id,
            'company': session.config_id.company_id,
            'currency': session.currency_id,
            
            # Fechas
            'start_at': session.start_at,
            'stop_at': session.stop_at,
            'state': session.state,
            'state_display': 'Cerrado' if session.state == 'closed' else session.state,
            
            # Financiero
            'total_sales': total_sales,
            'total_expenses': total_expenses,
            'cash_box_start': session.cash_register_balance_start,
            'cash_box_end_expected': session.cash_register_balance_end,
            'cash_box_end_real': session.cash_register_balance_end_real,
            'difference': session.cash_register_difference,
            'has_difference': session.cash_register_difference != 0,
            
            # Métodos de pago
            'payment_methods': payment_methods,
            'payment_methods_totals': payment_methods_totals,
            'has_payment_methods': bool(payment_methods),
            
            # Denominaciones
            'denominations': denominations_data,
            'denominations_totals': denominations_totals,
            'has_denominations': bool(denominations_data.get('bills') or denominations_data.get('coins')),
            
            # Movimientos
            'cash_movements': cash_movements,
            
            # Órdenes
            'orders': orders_summary,
            
            # Configuración
            'cash_control_enabled': session.config_id.cash_control,
        }

    def generate_cash_report_manual(self):
        return self.env.ref('pos_cash_report.action_cash_report').report_action(self)
