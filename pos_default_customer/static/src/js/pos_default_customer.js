import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {

    createNewOrder(data = {}, onGetNextOrderRefs = () => {}) {
        const order = super.createNewOrder(data, onGetNextOrderRefs);
        
        this._setDefaultCustomerToOrder(order);
        
        return order;
    },

    _setDefaultCustomerToOrder(order) {
        try {
            
            if (this.config && this.config.pos_default_customer_id && !order.getPartner()) {
                let defaultCustomerId;
                let defaultCustomer;
                
                if (Array.isArray(this.config.pos_default_customer_id)) {
                    defaultCustomerId = this.config.pos_default_customer_id[0];
                } else if (typeof this.config.pos_default_customer_id === 'object' && this.config.pos_default_customer_id.id) {
                    defaultCustomerId = this.config.pos_default_customer_id.id;
                } else if (typeof this.config.pos_default_customer_id === 'number') {
                    defaultCustomerId = this.config.pos_default_customer_id;
                } else {
                    defaultCustomer = this.config.pos_default_customer_id;
                    defaultCustomerId = defaultCustomer.id;
                }
                
                
                if (!defaultCustomer) {
                    defaultCustomer = this.models["res.partner"].get(defaultCustomerId);
                }
                
                if (defaultCustomer) {
                    order.setPartner(defaultCustomer);
                } else {
                    console.warn('POS Default Customer: Cliente predeterminado no encontrado con ID:', defaultCustomerId);
                }
            } else {
                console.log('POS Default Customer: No se cumplieron las condiciones para establecer cliente predeterminado');
            }
        } catch (error) {
            console.error('POS Default Customer: Error al establecer cliente predeterminado:', error);
        }
    }
});
