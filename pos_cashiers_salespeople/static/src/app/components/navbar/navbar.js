import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { patch } from "@web/core/utils/patch";

patch(Navbar.prototype, {
    onClickPendingOrders() {
        this.pos.navigate('PendingOrdersScreen');
    },
});