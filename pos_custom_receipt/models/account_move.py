# -*- coding: utf-8 -*-

from odoo import models


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
            ])
        else:
            # Asegurar que siempre se cargue el nombre de la factura
            if 'name' not in fields:
                fields.append('name')
        
        return fields
