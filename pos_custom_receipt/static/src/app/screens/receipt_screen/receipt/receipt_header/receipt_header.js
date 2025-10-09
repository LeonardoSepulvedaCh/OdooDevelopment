import { Component } from "@odoo/owl";
import { ReceiptHeader } from "@point_of_sale/app/screens/receipt_screen/receipt/receipt_header/receipt_header";
import { _t } from "@web/core/l10n/translation";

export class CustomReceiptHeader extends ReceiptHeader {
    static template = "point_of_sale.ReceiptHeader";
    
    // Verifica si el recibo personalizado está habilitado
    get useCustomReceiptHeader() {
        return this.order.config.use_custom_receipt;
    }
    
    // Override del método partnerAddress para personalización
    get partnerAddress() {
        if (!this.useCustomReceiptHeader) {
            return super.partnerAddress;
        }
        
        const address = this.order.partner_id.pos_contact_address
            .split("\n")
            .filter((line) => line.trim() !== "")
            .join(" - "); // Cambiar separador
            
        return address;
    }
    
}
