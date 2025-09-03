import { Component } from "@odoo/owl";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { _t } from "@web/core/l10n/translation";
import { formatCurrency } from "@web/core/currency";

export class CustomOrderReceipt extends OrderReceipt {
    static template = "point_of_sale.OrderReceipt";
    
    /**
     * Verifica si el recibo personalizado está habilitado
     */
    get useCustomReceipt() {
        return this.order.config.use_custom_receipt;
    }
    
    /**
     * Método personalizado para obtener información adicional del recibo
     * Solo se ejecuta si está habilitado el recibo personalizado
     */
    getCustomReceiptInfo() {
        if (!this.useCustomReceipt) {
            return null;
        }
        return {
            businessHours: {
                weekdays: "Lunes a Viernes: 8:00 AM - 6:00 PM",
                saturday: "Sábados: 8:00 AM - 2:00 PM",
                sunday: "Domingos: Cerrado"
            },
            socialMedia: {
                facebook: "@TuEmpresa",
                instagram: "@TuEmpresa",
                whatsapp: "+57 300 123 4567"
            },
            policies: {
                returnPolicy: "Válido para cambios y devoluciones por 30 días",
                warranty: "Garantía según términos del fabricante"
            }
        };
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
     * Método personalizado para obtener el saludo según la hora
     */
    getGreetingMessage() {
        const hour = new Date().getHours();
        if (hour < 12) {
            return "¡Buenos días!";
        } else if (hour < 18) {
            return "¡Buenas tardes!";
        } else {
            return "¡Buenas noches!";
        }
    }

    /**
     * Método personalizado para calcular puntos de fidelidad (ejemplo)
     */
    getLoyaltyPoints() {
        if (!this.useCustomReceipt) {
            return 0;
        }
        const total = this.order.get_total_with_tax();
        // 1 punto por cada $1000 pesos (ajusta según tu moneda)
        return Math.floor(total / 1000);
    }

    /**
     * Método personalizado para determinar si mostrar promociones
     */
    shouldShowPromotions() {
        if (!this.useCustomReceipt) {
            return false;
        }
        return this.order.get_total_with_tax() > 50000; // Mostrar si la compra es mayor a $50,000
    }

    /**
     * Método personalizado para obtener mensaje promocional
     */
    getPromotionalMessage() {
        if (!this.useCustomReceipt) {
            return "";
        }
        const total = this.order.get_total_with_tax();
        if (total > 100000) {
            return "¡Felicidades! Tu próxima compra tiene 10% de descuento";
        } else if (total > 50000) {
            return "¡Compra $50,000 más y obtén 5% de descuento!";
        }
        return "";
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
}
