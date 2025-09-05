import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";

export class SelectSalespersonButton extends Component {
    static template = "pos_cashiers_salespeople.SelectSalespersonButton";
    static props = ["salesperson?"];
    
    setup() {
        this.pos = usePos();
        this.ui = useService("ui");
    }
    
    get currentSalesperson() {
        const currentOrder = this.pos.getOrder();
        return currentOrder?.salesperson_id || null;
    }
    
    async onClickSelectSalesperson() {
        await this.pos.selectSalesperson();
    }
}
