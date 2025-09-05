import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { patch } from "@web/core/utils/patch";

patch(Navbar.prototype, {
    onClickPendingOrders() {
        this.pos.navigate('PendingOrdersScreen');
    },
    
    get mainButton() {
        const currentScreen = this.pos.router.state.current;
        
        if (currentScreen === 'PendingOrdersScreen') {
            return 'pending_orders';
        }
        
        const screens = ["ProductScreen", "PaymentScreen", "ReceiptScreen", "TipScreen"];
        return screens.includes(currentScreen) ? "register" : "order";
    },
});