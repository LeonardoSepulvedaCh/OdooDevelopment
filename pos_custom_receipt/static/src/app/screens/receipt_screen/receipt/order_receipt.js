import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { _t } from "@web/core/l10n/translation";

export class CustomOrderReceipt extends OrderReceipt {
    static template = "point_of_sale.OrderReceipt";
    
    // Verifica si el recibo personalizado está habilitado
    get useCustomReceipt() {
        return this.order.config.use_custom_receipt;
    }

    // Override del método vatText para personalizar el texto del RUT/NIT
    get vatText() {
        if (this.useCustomReceipt && this.order.company.country_id?.code === 'CO') {
            return _t("NIT: %(vatId)s", { vatId: this.order.company.vat });
        }
        return super.vatText;
    }

    // Verificar si hay información de facturación electrónica
    hasElectronicInvoiceData() {
        return this.useCustomReceipt && 
               this.order.account_move && 
               this.order.account_move.l10n_co_edi_cufe_cude_ref &&
               this.order.company.country_id?.code === 'CO';
    }

}