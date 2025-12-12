import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

patch(PosStore.prototype, {
  async _getSaleOrder(id) {
    const result = await this.data.callRelated(
      "sale.order",
      "load_sale_order_from_pos",
      [id, this.config.id]
    );

    // Si hay datos de usuarios en el resultado, cargarlos en los modelos del POS
    if (result["res.users"]?.length > 0) {
      for (const userData of result["res.users"]) {
        const existingUser = this.models["res.users"].get(userData.id);
        if (!existingUser) {
          this.models["res.users"].create(userData);
        }
      }
    }

    return result["sale.order"][0];
  },

  async onClickSaleOrder(clickedOrderId) {
    const sale_order = await this._getSaleOrder(clickedOrderId);

    // Verificar si la orden actual tiene líneas
    const currentOrder = this.getOrder();
    const currentOrderHasLines = currentOrder?.lines?.length > 0;

    // Si hay una orden activa con líneas, crear una nueva orden independiente
    if (currentOrderHasLines) {
      this.addNewOrder({
        partner_id: sale_order.partner_id,
      });
      this.notification.add(
        "Una nueva orden ha sido creada para la orden de venta."
      );
    }

    // Si no hay líneas en la orden actual, usarla directamente
    if (sale_order.partner_id) {
      this.getOrder().setPartner(sale_order.partner_id);
    }

    // Asignar el vendedor de la orden de venta a la orden del POS
    if (sale_order.user_id) {
      const salesperson = this.models["res.users"].get(sale_order.user_id.id);
      if (
        salesperson &&
        typeof this.getOrder()?.setSalesperson === "function"
      ) {
        this.getOrder().setSalesperson(salesperson);
      }
    }

    // La posición fiscal debe establecerse después del partner
    // para asegurar que se calcule correctamente basándose en la orden de venta
    const orderFiscalPos = sale_order.fiscal_position_id;
    this.getOrder().update({
      fiscal_position_id: orderFiscalPos,
    });

    // Agregar un pago anticipado para transacciones que ya se hicieron online
    if (sale_order.amount_paid > 0) {
      this.addDownPaymentProductOrderlineToOrder(
        sale_order,
        -sale_order.amount_paid,
        false
      );
    }

    const selectedOption = await makeAwaitable(this.dialog, SelectionPopup, {
      title: "¿Qué quieres hacer?",
      list: [
        { id: "0", label: "Liquidar la orden", item: "settle" },
        {
          id: "1",
          label: "Aplicar un pago anticipado (porcentaje)",
          item: "dpPercentage",
        },
        {
          id: "2",
          label: "Aplicar un pago anticipado (importe fijo)",
          item: "dpAmount",
        },
      ],
    });

    if (!selectedOption) {
      return;
    }

    selectedOption == "settle"
      ? await this.settleSO(sale_order, orderFiscalPos)
      : await this.downPaymentSO(sale_order, selectedOption == "dpPercentage");

    this.selectOrderLine(this.getOrder(), this.getOrder()?.lines?.at(-1));
  },
});
