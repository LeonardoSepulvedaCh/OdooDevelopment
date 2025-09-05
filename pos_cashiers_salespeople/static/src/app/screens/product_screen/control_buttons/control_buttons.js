import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { SelectSalespersonButton } from "./select_salesperson_button/select_salesperson_button";

// Extender los componentes estáticos
ControlButtons.components = {
    ...ControlButtons.components,
    SelectSalespersonButton,
};

// Extender el prototipo
patch(ControlButtons.prototype, {
    get currentSalesperson() {
        return this.pos.getOrder()?.getSalesperson();
    }
});