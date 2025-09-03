import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { _t } from "@web/core/l10n/translation";

export class CustomOrderReceipt extends OrderReceipt {
    static template = "point_of_sale.OrderReceipt";
    
    /**
     * Verifica si el recibo personalizado está habilitado
     */
    get useCustomReceipt() {
        return this.order.config.use_custom_receipt;
    }

    /**
     * Método personalizado para formatear la fecha en español
     */
    formatDateSpanish(dateString) {
        const date = new Date(dateString);
        const months = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ];
        const days = [
            'Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'
        ];
        
        const dayName = days[date.getDay()];
        const day = date.getDate();
        const month = months[date.getMonth()];
        const year = date.getFullYear();
        
        return `${dayName}, ${day} de ${month} de ${year}`;
    }


    /**
     * Override del método vatText para personalizar el texto del RUT/NIT
     */
    get vatText() {
        if (this.useCustomReceipt && this.order.company.country_id?.code === 'CO') {
            return _t("NIT: %(vatId)s", { vatId: this.order.company.vat });
        }
        return super.vatText;
    }

    /**
     * Método personalizado para obtener información de contacto formateada
     */
    getFormattedContactInfo() {
        if (!this.useCustomReceipt) {
            return [];
        }
        
        const company = this.order.company;
        const contactInfo = [];
        
        if (company.phone) {
            contactInfo.push(`Tel: ${company.phone}`);
        }
        if (company.mobile) {
            contactInfo.push(`Cel: ${company.mobile}`);
        }
        if (company.email) {
            contactInfo.push(`Email: ${company.email}`);
        }
        if (company.website) {
            contactInfo.push(`Web: ${company.website}`);
        }
        
        return contactInfo;
    }

    /**
     * Método auxiliar para verificar si hay información de facturación electrónica
     * (Mantenido para compatibilidad futura, aunque ahora se evalúa directamente en el template)
     */
    hasElectronicInvoiceData() {
        return this.useCustomReceipt && 
               this.order.account_move && 
               this.order.account_move.l10n_co_edi_cufe_cude_ref &&
               this.order.company.country_id?.code === 'CO';
    }

    /**
     * Método para obtener información del CUFE formateada
     */
    getCufeInfo() {
        if (!this.hasElectronicInvoiceData()) {
            return null;
        }
        
        return {
            cufe: this.order.account_move.l10n_co_edi_cufe_cude_ref,
            invoice_name: this.order.account_move.name,
            dian_state: this.order.account_move.l10n_co_dian_state
        };
    }
}