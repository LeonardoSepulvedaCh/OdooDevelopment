import { Component } from "@odoo/owl";
import { ReceiptHeader } from "@point_of_sale/app/screens/receipt_screen/receipt/receipt_header/receipt_header";
import { _t } from "@web/core/l10n/translation";

export class CustomReceiptHeader extends ReceiptHeader {
    static template = "point_of_sale.ReceiptHeader";
    
    /**
     * Verifica si el recibo personalizado está habilitado
     */
    get useCustomReceiptHeader() {
        return this.order.config.use_custom_receipt;
    }
    
    /**
     * Método personalizado para obtener información adicional de la empresa
     */
    getCustomCompanyInfo() {
        if (!this.useCustomReceiptHeader) {
            return null;
        }
        
        const company = this.order.company;
        return {
            slogan: "Tu empresa de confianza", // Personalizable
            website: company.website || "www.tuempresa.com",
            phone: company.phone || "+57 300 123 4567",
            email: company.email || "info@tuempresa.com",
            address: this.getFormattedCompanyAddress()
        };
    }
    
    /**
     * Método personalizado para formatear la dirección de la empresa
     */
    getFormattedCompanyAddress() {
        const company = this.order.company;
        const addressParts = [];
        
        if (company.street) {
            addressParts.push(company.street);
        }
        if (company.street2) {
            addressParts.push(company.street2);
        }
        if (company.city) {
            addressParts.push(company.city);
        }
        if (company.state_id && company.state_id.name) {
            addressParts.push(company.state_id.name);
        }
        if (company.zip) {
            addressParts.push(company.zip);
        }
        if (company.country_id && company.country_id.name) {
            addressParts.push(company.country_id.name);
        }
        
        return addressParts.join(', ');
    }
    
    /**
     * Método personalizado para obtener el saludo según la hora
     */
    getGreetingByTime() {
        if (!this.useCustomReceiptHeader) {
            return "";
        }
        
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
     * Método personalizado para formatear la fecha en español
     */
    getFormattedDateSpanish() {
        if (!this.useCustomReceiptHeader || !this.order.date_order) {
            return this.order.formatDateOrTime('date_order');
        }
        
        const date = new Date(this.order.date_order);
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
        const time = date.toLocaleTimeString('es-CO', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });
        
        return `${dayName}, ${day} de ${month} de ${year} - ${time}`;
    }
    
    /**
     * Método personalizado para obtener información del cajero formateada
     */
    getFormattedCashierInfo() {
        if (!this.useCustomReceiptHeader) {
            return null;
        }
        
        const cashierName = this.order.getCashierName();
        if (!cashierName) {
            return null;
        }
        
        return {
            name: cashierName,
            greeting: this.getGreetingByTime(),
            message: `Le atendió: ${cashierName}`
        };
    }
    
    /**
     * Método personalizado para obtener el número de ticket formateado
     */
    getFormattedTicketNumber() {
        if (!this.useCustomReceiptHeader) {
            return this.order.pos_reference;
        }
        
        // Agregar prefijo personalizado al número de ticket
        return `TICKET #${this.order.pos_reference}`;
    }
    
    /**
     * Override del método partnerAddress para personalización
     */
    get partnerAddress() {
        if (!this.useCustomReceiptHeader) {
            return super.partnerAddress;
        }
        
        // Personalizar formato de dirección del cliente
        const address = this.order.partner_id.pos_contact_address
            .split("\n")
            .filter((line) => line.trim() !== "")
            .join(" - "); // Cambiar separador
            
        return address;
    }
    
    /**
     * Método personalizado para obtener información del cliente
     */
    getCustomerInfo() {
        if (!this.useCustomReceiptHeader || !this.order.partner_id) {
            return null;
        }
        
        const partner = this.order.partner_id;
        return {
            name: partner.name,
            phone: partner.phone || partner.mobile,
            email: partner.email,
            vat: partner.vat,
            address: this.partnerAddress
        };
    }
    
    /**
     * Método personalizado para determinar si mostrar información extendida
     */
    shouldShowExtendedInfo() {
        return this.useCustomReceiptHeader && this.order.get_total_with_tax() > 0;
    }
}
