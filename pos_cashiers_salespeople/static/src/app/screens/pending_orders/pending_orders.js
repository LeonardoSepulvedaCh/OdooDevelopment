import { registry } from "@web/core/registry";
import {
  Component,
  useState,
  onWillStart,
  onMounted,
  onWillUnmount,
} from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { useUserRoleService } from "@pos_cashiers_salespeople/app/services/user_role_service";

export class PendingOrdersScreen extends Component {
  static template = "pos_cashiers_salespeople.PendingOrdersScreen";
  static storeOnOrder = false;
  static props = {};

  setup() {
    this.pos = usePos();
    this.ui = useService("ui");
    this.orm = useService("orm");
    this.dialog = useService("dialog");
    this.userRoleService = useUserRoleService();
    this.state = useState({
      pendingOrders: [],
      selectedOrder: null,
      loading: true,
      isUserCashier: false,
      showMobileDetail: false,
    });

    onWillStart(async () => {
      // Verificar si el usuario actual es cajero
      this.state.isUserCashier = await this.userRoleService.isUserCashier(
        this.pos
      );
      await this.loadPendingOrders();
    });

    onMounted(() => {
      // Listener para manejar cambios de tamaño de ventana
      this.resizeHandler = this.handleResize.bind(this);
      window.addEventListener("resize", this.resizeHandler);
      // Verificar el tamaño inicial
      this.handleResize();
    });

    onWillUnmount(() => {
      // Limpiar el listener al desmontar el componente
      if (this.resizeHandler) {
        window.removeEventListener("resize", this.resizeHandler);
      }
    });
  }

  handleResize() {
    // Si la pantalla es mayor a 768px (no es móvil), resetear el estado
    // para mostrar ambos paneles simultáneamente
    const isMobile = window.innerWidth <= 768;
    if (!isMobile && this.state.showMobileDetail) {
      this.state.showMobileDetail = false;
    }
  }

  async loadPendingOrders() {
    try {
      this.state.loading = true;
      // Cargar solo las órdenes pendientes del punto de venta actual
      const orders = await this.orm.searchRead(
        "pos.order.pending",
        [
          ["status", "=", "pending"],
          ["pos_config_id", "=", this.pos.config.id],
        ],
        [
          "name",
          "pos_reference",
          "salesperson_id",
          "partner_id",
          "date_order",
          "amount_total",
          "amount_untaxed",
          "amount_tax",
          "order_lines",
          "note",
        ],
        { order: "date_order desc" }
      );

      // Procesar las órdenes para incluir los datos de las líneas
      this.state.pendingOrders = orders.map((order) => ({
        ...order,
        orderLinesData: this.parseOrderLines(order.order_lines),
        salesperson_name: order.salesperson_id
          ? order.salesperson_id[1]
          : "Sin vendedor",
        partner_name: order.partner_id
          ? order.partner_id[1]
          : "Cliente genérico",
        formatted_date: this.formatDate(order.date_order),
      }));
    } catch (error) {
      console.error("Error cargando órdenes pendientes:", error);
      this.state.pendingOrders = [];
    } finally {
      this.state.loading = false;
    }
  }

  parseOrderLines(orderLinesJson) {
    try {
      return orderLinesJson ? JSON.parse(orderLinesJson) : [];
    } catch (error) {
      console.error("Error parsing order lines:", error);
      return [];
    }
  }

  formatDate(dateString) {
    try {
      const date = new Date(dateString);
      return date.toLocaleString("es-ES", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (error) {
      return dateString;
    }
  }

  get pendingOrders() {
    return this.state.pendingOrders;
  }

  get selectedOrder() {
    return this.state.selectedOrder;
  }

  get isCurrentUserCashier() {
    return this.state.isUserCashier;
  }

  selectOrder(order) {
    this.state.selectedOrder = order;
    this.state.showMobileDetail = true; // En móvil, mostrar el detalle
  }

  backToList() {
    this.state.showMobileDetail = false; // Volver a la lista en móvil
  }

  async refreshOrders() {
    await this.loadPendingOrders();
    this.state.showMobileDetail = false; // Volver a la lista después de actualizar
  }

  async loadOrderToPos(order) {
    try {
      const newOrder = this.pos.addNewOrder();

      if (order.partner_id && order.partner_id[0]) {
        try {
          const partnerId = order.partner_id[0];
          const partner = this.pos.models["res.partner"].getBy("id", partnerId);
          if (partner) {
            this.pos.setPartnerToCurrentOrder(partner);
          } else {
            console.warn("Cliente no encontrado en la base de datos del POS");
          }
        } catch (partnerError) {
          console.warn("Error al buscar cliente:", partnerError);
        }
      }

      // Establecer el vendedor si existe
      if (order.salesperson_id && order.salesperson_id[0]) {
        try {
          const salesperson = {
            id: order.salesperson_id[0],
            name: order.salesperson_id[1],
          };

          newOrder.salesperson_id = salesperson;

          newOrder.user_id = salesperson.id;

          console.log("Vendedor establecido:", salesperson.name);
          console.log("user_id establecido:", salesperson.id);
        } catch (salespersonError) {
          console.warn("Error al establecer vendedor:", salespersonError);
        }
      }

      const orderLines = this.parseOrderLines(order.order_lines);

      for (const line of orderLines) {
        try {
          const product = this.pos.models["product.product"].getBy(
            "id",
            line.product_id
          );
          if (product) {
            const vals = {
              product_id: product,
              product_tmpl_id: product.product_tmpl_id,
              price_unit: line.price_unit,
              discount: line.discount || 0,
            };

            const orderLine = await this.pos.addLineToCurrentOrder(
              vals,
              {},
              false
            );

            if (orderLine) {
              orderLine.setQuantity(line.quantity);
            }
          } else {
            console.warn(
              `Producto con ID ${line.product_id} no encontrado en la base de datos del POS`
            );
          }
        } catch (productError) {
          console.error(
            `Error al cargar producto ${line.product_id}:`,
            productError
          );
        }
      }

      await this.orm.write("pos.order.pending", [order.id], {
        status: "completed",
      });

      await this.loadPendingOrders();

      this.state.showMobileDetail = false; // Volver a la lista en móvil

      this.pos.navigateToOrderScreen(newOrder);

      this.env.services.notification.add(
        "Orden cargada exitosamente en el POS",
        {
          type: "success",
        }
      );
    } catch (error) {
      console.error("Error cargando orden al POS:", error);
      this.env.services.notification.add(
        "Error al cargar la orden: " + error.message,
        {
          type: "danger",
        }
      );
    }
  }

  async deleteOrder(order) {
    try {
      this.dialog.add(ConfirmationDialog, {
        title: _t("¿Está seguro?"),
        body: _t("¿Está seguro de eliminar el pedido '%s'?", order.name),
        confirm: async () => {
          try {
            await this.orm.unlink("pos.order.pending", [order.id]);
            await this.loadPendingOrders();
            if (
              this.state.selectedOrder &&
              this.state.selectedOrder.id === order.id
            ) {
              this.state.selectedOrder = null;
            }
            this.state.showMobileDetail = false; // Volver a la lista en móvil
            this.env.services.notification.add(
              _t("Pedido eliminado exitosamente"),
              {
                type: "success",
                sticky: false,
              }
            );
          } catch (deleteError) {
            console.error("Error eliminando pedido:", deleteError);
            this.env.services.notification.add(
              _t("Error al eliminar el pedido: %s", deleteError.message),
              {
                type: "danger",
                sticky: true,
              }
            );
          }
        },
        cancel: () => {},
      });
    } catch (error) {
      console.error("Error mostrando diálogo:", error);
      this.env.services.notification.add(
        _t("Error al mostrar diálogo de confirmación"),
        {
          type: "danger",
          sticky: true,
        }
      );
    }
  }
}

registry.category("pos_pages").add("PendingOrdersScreen", {
  name: "PendingOrdersScreen",
  component: PendingOrdersScreen,
  route: `/pos/ui/${odoo.pos_config_id}/pending_orders`,
  params: {},
});
