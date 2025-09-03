# -*- coding: utf-8 -*-

from odoo import models, api, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _load_pos_data_fields(self, config):
        """
        Extiende los campos de account.move cargados en el POS para incluir
        información de facturación electrónica colombiana
        """
        fields = super()._load_pos_data_fields(config)
        
        # Agregar campos de facturación electrónica colombiana si la empresa es de Colombia
        if config.company_id.country_id and config.company_id.country_id.code == 'CO':
            fields.extend([
                'name',                        # Nombre de la factura
                'l10n_co_edi_cufe_cude_ref',  # CUFE/CUDE/CUDS
                'l10n_co_dian_state',          # Estado de la factura electrónica (si existe)
                'l10n_co_dian_attachment_id',  # Adjunto de la DIAN
                'l10n_co_dian_is_enabled',     # Si DIAN está habilitado
                'l10n_co_edi_is_support_document',  # Si es documento soporte
                'country_code',                # Código del país
                'company_currency_id',         # Moneda de la empresa
                'move_type',                   # Tipo de documento
                'pos_qr_barcode_src',          # URL del código QR para POS
            ])
        else:
            # Asegurar que siempre se cargue el nombre de la factura
            if 'name' not in fields:
                fields.append('name')
        
        return fields

    # Campo calculado para la URL del QR en POS
    pos_qr_barcode_src = fields.Char(
        string="POS QR Barcode URL",
        compute="_compute_pos_qr_barcode_src",
        help="URL del código QR para mostrar en el recibo del POS"
    )

    @api.depends('l10n_co_dian_state', 'l10n_co_dian_attachment_id', 'l10n_co_edi_cufe_cude_ref')
    def _compute_pos_qr_barcode_src(self):
        """
        Calcula la URL del código QR para el recibo del POS
        """
        for move in self:
            if (move.l10n_co_dian_is_enabled and 
                move.l10n_co_edi_cufe_cude_ref and 
                move.l10n_co_dian_state == 'invoice_accepted' and
                move.l10n_co_dian_attachment_id):
                try:
                    # Usar el método existente para obtener la URL del barcode
                    dian_values = move._l10n_co_dian_get_extra_invoice_report_values()
                    move.pos_qr_barcode_src = dian_values.get('barcode_src', False)
                except Exception:
                    move.pos_qr_barcode_src = False
            else:
                move.pos_qr_barcode_src = False

    @api.model
    def get_pos_qr_code_data(self, move_id):
        """
        Genera los datos del código QR para el recibo del POS
        usando exactamente la misma lógica que las facturas oficiales
        """
        move = self.browse(move_id)
        
        # Solo generar QR si es una factura colombiana con DIAN habilitado
        if (not move.l10n_co_dian_is_enabled or 
            not move.l10n_co_edi_cufe_cude_ref or 
            move.l10n_co_dian_state != 'invoice_accepted' or
            not move.l10n_co_dian_attachment_id):
            return None

        try:
            # Usar el método existente del módulo base para obtener el texto del QR
            qr_text = move._l10n_co_dian_get_invoice_report_qr_code_value()
            
            # Usar el método existente para obtener los valores extra del reporte
            dian_values = move._l10n_co_dian_get_extra_invoice_report_values()
            
            return {
                'qr_text': qr_text,
                'barcode_src': dian_values.get('barcode_src'),
                'cufe_cude': dian_values.get('identifier'),
                'invoice_name': move.name,
                'signing_datetime': dian_values.get('signing_datetime'),
            }
            
        except Exception as e:
            # Log del error para debugging
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f"Error generando datos QR para factura {move_id}: {str(e)}")
            return None
