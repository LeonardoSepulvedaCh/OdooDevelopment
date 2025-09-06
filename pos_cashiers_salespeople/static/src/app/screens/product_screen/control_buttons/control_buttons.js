import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { SelectSalespersonButton } from "./select_salesperson_button/select_salesperson_button";
import { useState, onWillStart } from "@odoo/owl";
import { useUserRoleService } from "@pos_cashiers_salespeople/app/services/user_role_service";

// Extender los componentes estáticos
ControlButtons.components = {
    ...ControlButtons.components,
    SelectSalespersonButton,
};

// Extender el prototipo
patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.userRoleService = useUserRoleService();
        this.cashierState = useState({
            isUserCashier: false
        });

        onWillStart(async () => {
            this.cashierState.isUserCashier = await this.userRoleService.isUserCashier(this.pos);
        });
    },

    get currentSalesperson() {
        return this.pos.getOrder()?.getSalesperson();
    },

    get isCurrentUserCashier() {
        return this.cashierState.isUserCashier;
    }
});