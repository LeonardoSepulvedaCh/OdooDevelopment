import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    
    setup() {
        super.setup(...arguments);
        this.salesperson_id = null;
    },
    
    getSalesperson() {
        return this.salesperson_id;
    },
    
    setSalesperson(salesperson) {
        this.salesperson_id = salesperson;
    },
    
    serialize() {
        const result = super.serialize(...arguments);
        result.salesperson_id = this.salesperson_id ? this.salesperson_id.id : null;
        
        if (this.salesperson_id) {
            result.user_id = this.salesperson_id.id;
        }
        
        return result;
    }
});
