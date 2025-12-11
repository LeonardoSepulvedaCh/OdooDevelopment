/**
 * Author: Sebastián Rodríguez
 * Description: Extension of ControlButtons to filter sale orders by POS configuration
 */

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";

patch(ControlButtons.prototype, {

    /**
     * Override onClickQuotation to add POS config filter to domain
     * 
     * @override
     */
    onClickQuotation() {
        const context = {};
        if (this.partner) {
            context["search_default_partner_id"] = this.partner.id;
        }

        let domain = [
            ["state", "!=", "cancel"],
            ["invoice_status", "!=", "invoiced"],
            ["currency_id", "=", this.pos.currency.id],
            ["amount_unpaid", ">", 0],
        ];

        // Add partner filter if partner is selected
        if (this.pos.getOrder()?.getPartner()) {
            domain = [
                ...domain,
                ["partner_id", "any", [["id", "child_of", [this.pos.getOrder().getPartner().id]]]],
            ];
        }

        // Add POS config filter - only show orders for current POS
        if (this.pos.config?.id) {
            domain = [
                ...domain,
                ["pos_config_ids", "in", [this.pos.config.id]],
            ];
        }

        this.dialog.add(SelectCreateDialog, {
            resModel: "sale.order",
            noCreate: true,
            multiSelect: false,
            domain,
            context: context,
            onSelected: async (resIds) => {
                await this.pos.onClickSaleOrder(resIds[0]);
            },
        });
    },
});
