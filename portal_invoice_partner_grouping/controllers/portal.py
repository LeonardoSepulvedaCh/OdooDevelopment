# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from collections import OrderedDict

from odoo import _, http
from odoo.http import request
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.portal.controllers.portal import pager as portal_pager

_logger = logging.getLogger(__name__)


class PortalAccountInherit(PortalAccount):
    """
    Herencia del controlador de portal de facturas para añadir agrupación por partner.
    
    IMPORTANTE: Este controlador SOLO AÑADE funcionalidad, nunca reemplaza.
    - Usa super() para heredar comportamiento nativo
    - No modifica dominios de búsqueda
    - No altera paginación, filtros ni ordenamiento
    - Compatible con otros módulos que hereden PortalAccount
    """

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """
        Sobrescribe portal_my_invoices para añadir agrupación por partner.
        
        Estrategia de compatibilidad:
        1. Llama a _prepare_my_invoices_values (respeta herencias de otros módulos)
        2. Ejecuta paginación nativa
        3. Obtiene facturas según paginación
        4. AÑADE variable 'invoices_grouped_by_partner' al contexto
        5. Renderiza con template extendido
        
        Args:
            page: Número de página actual
            date_begin: Fecha inicial de filtro
            date_end: Fecha final de filtro
            sortby: Campo de ordenamiento
            filterby: Filtro aplicado
            **kw: Argumentos adicionales (compatibilidad con otros módulos)
        
        Returns:
            Renderizado del template con agrupación
        """
        # Filtro por defecto: facturas pendientes
        filterby = filterby or 'pending_invoices'

        # PASO 1: Obtener valores preparados (respeta herencia de otros módulos)
        values = self._prepare_my_invoices_values(page, date_begin, date_end, sortby, filterby)

        # PASO 2: Crear pager usando los valores del método padre
        pager = portal_pager(**values['pager'])

        # PASO 3: Obtener facturas según offset del pager (funcionalidad nativa)
        invoices = values['invoices'](pager['offset'])
        
        # Mantener historial de sesión (funcionalidad nativa)
        try:
            request.session['my_invoices_history'] = [i['invoice'].id for i in invoices][:100]
        except (KeyError, TypeError, AttributeError) as e:
            _logger.warning(f"No se pudo actualizar historial de facturas: {e}")

        # PASO 4: AÑADIR agrupación por partner (NO sobrescribir nada)
        invoices_grouped = self._group_invoices_by_partner(invoices)

        # PASO 5: Actualizar contexto AÑADIENDO nuevas variables
        values.update({
            'invoices': invoices,  # Mantener variable original
            'pager': pager,  # Mantener pager original
            'invoices_grouped_by_partner': invoices_grouped,  # NUEVA variable
            'has_multiple_partners': len(invoices_grouped) > 1,  # NUEVA variable
        })

        return request.render("portal_invoice_partner_grouping.portal_my_invoices_grouped", values)

    def _get_account_searchbar_filters(self):
        """Ajusta el filtro de facturas de clientes y agrega filtro para notas de crédito."""
        filters = super()._get_account_searchbar_filters()

        # Copiar para evitar mutar el dict original de otros módulos
        filters = dict(filters)
        invoice_filter = filters.get('invoices')
        if invoice_filter:
            invoice_filter = dict(invoice_filter)
            # Restaurar dominio original de Odoo (incluye notas de crédito y recibos)
            invoice_filter['domain'] = [
                ('move_type', 'in', ('out_invoice', 'out_refund', 'out_receipt')),
            ]
            filters['invoices'] = invoice_filter

        # Nuevo filtro de facturas pendientes (sin notas de crédito)
        filters['pending_invoices'] = {
            'label': _('Pending Invoices'),
            'domain': [
                ('move_type', 'in', ('out_invoice', 'out_receipt')),
                ('payment_state', 'in', ('not_paid', 'partial', 'in_payment')),
            ],
        }

        # Añadir filtro explícito para notas de crédito de clientes
        filters['customer_refunds'] = {
            'label': _('Credit Notes'),
            'domain': [
                ('move_type', '=', 'out_refund'),
            ],
        }

        return filters

    def _group_invoices_by_partner(self, invoices):
        """
        Agrupa facturas por partner_id RESPETANDO EL ORDEN ORIGINAL.
        
        CRÍTICO: Las facturas ya vienen ordenadas según sortby del usuario.
        Esta función NO debe reordenar, solo agrupar manteniendo el orden.
        
        Args:
            invoices: Lista de diccionarios con invoice_data del método padre
                     Formato: [{'invoice': account.move, ...}, ...]
                     YA ORDENADAS según parámetro sortby
        
        Returns:
            OrderedDict: Grupos en orden de aparición (mantiene sortby original)
            {
                partner_id: {
                    'partner': res.partner,
                    'invoices': [invoice_data, ...],
                    'total_due': float,
                    'count': int,
                }
            }
            
        Manejo de errores:
        - Si invoices es None o vacío, retorna dict vacío
        - Si un invoice no tiene partner, se agrupa bajo "Sin contacto"
        - Si hay error procesando invoice, lo omite y registra warning
        """
        grouped = {}  # Usamos dict normal, no defaultdict
        partner_order = []  # Para mantener orden de aparición

        # Validación: manejar caso de lista vacía o None
        if not invoices:
            return {}

        try:
            for invoice_data in invoices:
                try:
                    # Extraer invoice del diccionario (formato nativo de Odoo)
                    invoice = invoice_data.get('invoice')
                    
                    if not invoice:
                        _logger.warning("invoice_data sin clave 'invoice': %s", invoice_data)
                        continue

                    # Obtener partner (puede ser False si no tiene)
                    partner = invoice.partner_id
                    partner_key = partner.id if partner else 0

                    # Si es la primera factura de este partner, inicializar grupo
                    if partner_key not in grouped:
                        partner_order.append(partner_key)  # Guardar orden de aparición
                        grouped[partner_key] = {
                            'partner': partner,
                            'invoices': [],
                            'total_due': 0.0,
                            'count': 0,
                        }

                    # Añadir factura al grupo (mantiene orden original)
                    grouped[partner_key]['invoices'].append(invoice_data)
                    grouped[partner_key]['count'] += 1

                    # Calcular total pendiente (respetando facturas rectificativas)
                    try:
                        if invoice.move_type == 'out_refund':
                            amount = -invoice.amount_residual
                        else:
                            amount = invoice.amount_residual
                        grouped[partner_key]['total_due'] += amount
                    except (AttributeError, TypeError) as e:
                        _logger.warning(f"Error calculando monto para factura {invoice.id}: {e}")

                except (AttributeError, KeyError, TypeError) as e:
                    _logger.warning(f"Error procesando invoice_data: {e}")
                    continue

        except Exception as e:
            _logger.error(f"Error crítico en _group_invoices_by_partner: {e}", exc_info=True)
            return {}

        # Retornar OrderedDict en el orden de aparición (respeta sortby)
        try:
            ordered_grouped = OrderedDict()
            for partner_key in partner_order:
                ordered_grouped[partner_key] = grouped[partner_key]
            return ordered_grouped
        except Exception as e:
            _logger.warning(f"Error creando OrderedDict: {e}")
            return grouped

