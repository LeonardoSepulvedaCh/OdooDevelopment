import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
  async setup() {
    super.setup(...arguments);
    await this._loadCashierSalespersonData();
  },

  async _loadCashierSalespersonData() {
    try {
      const result = await this.env.services.orm.read(
        "pos.config",
        [this.pos.config.id],
        ["cashier_user_ids", "salesperson_user_ids"]
      );
      if (result?.length > 0) {
        this.pos.config.cashier_user_ids = result[0].cashier_user_ids || [];
        this.pos.config.salesperson_user_ids =
          result[0].salesperson_user_ids || [];
      }
    } catch (error) {
      console.error("Error loading cashier/salesperson data:", error);
      this.pos.config.cashier_user_ids = [];
      this.pos.config.salesperson_user_ids = [];
    }
  },

  isCurrentUserCashier() {
    if (!this.pos.user || !this.pos.config) {
      return false;
    }
    const currentUserId = this.pos.user.id;
    const cashierIds = this.pos.config.cashier_user_ids || [];

    // Extraer IDs reales de los objetos user
    let cashierUserIds = [];
    if (Array.isArray(cashierIds)) {
      cashierUserIds = cashierIds.map((user) => user.id || user);
    } else if (cashierIds && typeof cashierIds === "object") {
      // Si es un Proxy object, extraer IDs de los users
      for (let key in cashierIds) {
        const user = cashierIds[key];
        if (user?.id) {
          cashierUserIds.push(user.id);
        } else if (typeof user === "number") {
          cashierUserIds.push(user);
        }
      }
    }
    return cashierUserIds.includes(currentUserId);
  },

  isCurrentUserSalesperson() {
    if (!this.pos.user || !this.pos.config) {
      return false;
    }
    const currentUserId = this.pos.user.id;
    const salespersonIds = this.pos.config.salesperson_user_ids || [];

    // Extraer IDs reales de los objetos user
    let salespersonUserIds = [];
    if (Array.isArray(salespersonIds)) {
      salespersonUserIds = salespersonIds.map((user) => user.id || user);
    } else if (salespersonIds && typeof salespersonIds === "object") {
      // Si es un Proxy object, extraer IDs de los users
      for (let key in salespersonIds) {
        const user = salespersonIds[key];
        if (user?.id) {
          salespersonUserIds.push(user.id);
        } else if (typeof user === "number") {
          salespersonUserIds.push(user);
        }
      }
    }
    return salespersonUserIds.includes(currentUserId);
  },

  /**
   * Transforma una línea de pedido en datos serializables
   */
  _mapOrderLineToData(line) {
    const priceWithTax = line.priceIncl || 0;
    const priceWithoutTax = line.priceExcl || 0;
    const quantity = line.quantity || line.qty || 0;
    const priceUnit = line.price_unit || 0;
    const discount = line.discount || 0;
    const priceAfterDiscount = priceUnit * (1 - discount / 100);
    const subtotal = priceWithTax || priceAfterDiscount * quantity;
    const taxAmount = priceWithTax - priceWithoutTax || 0;

    return {
      product_id: line.product_id.id,
      product_name: line.product_id.display_name || line.product_id.name,
      quantity,
      price_unit: priceUnit,
      discount,
      subtotal,
      tax_amount: taxAmount,
    };
  },

  /**
   * Verifica si un error es de duplicado
   */
  _isDuplicateError(error) {
    return (
      error?.message?.includes("unique") ||
      error?.message?.includes("duplicate") ||
      error?.message?.includes("Ya existe un pedido con este nombre")
    );
  },

  /**
   * Prepara los datos del pedido para guardar
   */
  async _prepareOrderData(currentOrder, salespersonId) {
    const orderLinesData = currentOrder
      .getOrderlines()
      .map((line) => this._mapOrderLineToData(line));
    const orderName = await this.generateOrderName(salespersonId);
    const orderTotalWithTax = currentOrder.priceIncl || 0;
    const orderTotalWithoutTax = currentOrder.priceExcl || 0;
    const orderTaxAmount =
      currentOrder.amountTaxes || orderTotalWithTax - orderTotalWithoutTax;

    return {
      name: orderName,
      pos_reference: currentOrder.pos_reference || "",
      salesperson_id: salespersonId,
      partner_id: currentOrder.partner_id?.id || false,
      date_order: this.formatDateForOdoo(new Date()),
      amount_total: orderTotalWithTax,
      amount_untaxed: orderTotalWithoutTax,
      amount_tax: orderTaxAmount,
      order_lines: JSON.stringify(orderLinesData),
      pos_config_id: this.pos.config.id,
      status: "pending",
    };
  },

  /**
   * Maneja el éxito al crear el pedido
   */
  _handleOrderSuccess(currentOrder) {
    this.env.services.notification.add("Pedido creado exitosamente", {
      type: "success",
      sticky: false,
    });
    this.pos.removeOrder(currentOrder);
    this.pos.addNewOrder();
  },

  /**
   * Maneja los errores al crear el pedido
   */
  _handleOrderError(error) {
    this.env.services.notification.add(
      "Error al crear el pedido: " + error.message,
      {
        type: "danger",
        sticky: true,
      }
    );
  },

  async generateOrderName(salespersonId = null) {
    try {
      const currentOrder = this.pos.getOrder();

      // Determinar el vendedor - usar el parámetro, el de la orden actual, o el usuario actual
      let targetSalespersonId = salespersonId;
      if (!targetSalespersonId && currentOrder?.getSalesperson()) {
        targetSalespersonId = currentOrder.getSalesperson().id;
      }
      if (!targetSalespersonId) {
        targetSalespersonId = this.pos.user.id;
      }

      // Obtener información del vendedor
      let salespersonName = "US";
      if (targetSalespersonId === this.pos.user.id) {
        salespersonName = this.pos.user.name || "US";
      } else if (currentOrder?.getSalesperson()?.id === targetSalespersonId) {
        salespersonName = currentOrder.getSalesperson().name || "US";
      } else {
        // Obtener el nombre del vendedor desde la base de datos
        try {
          const salespersonData = await this.env.services.orm.read(
            "res.users",
            [targetSalespersonId],
            ["name"]
          );
          if (salespersonData?.length > 0) {
            salespersonName = salespersonData[0].name || "US";
          }
        } catch (userError) {
          console.warn("No se pudo obtener el nombre del vendedor:", userError);
        }
      }

      const salesperson = salespersonName
        .split(" ")[0]
        .toUpperCase()
        .slice(0, 2);

      const today = new Date();
      const date = today.getDate().toString().padStart(2, "0");
      const startOfDay = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate()
      );
      const endOfDay = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate() + 1
      );

      // Contar TODOS los pedidos del día (pendientes y completados) para evitar
      // reutilizar números consecutivos y mantener un registro secuencial correcto
      const orderCount = await this.env.services.orm.searchCount(
        "pos.order.pending",
        [
          ["salesperson_id", "=", targetSalespersonId],
          ["date_order", ">=", this.formatDateForOdoo(startOfDay)],
          ["date_order", "<", this.formatDateForOdoo(endOfDay)],
          // No filtrar por estado para contar todos los pedidos del día
        ]
      );

      // El consecutivo es el conteo + 1
      // Nota: Esto maneja implícitamente la concurrencia ya que la base de datos
      // garantiza el conteo atómico al momento de la consulta
      const consecutive = orderCount + 1;
      return `${salesperson} - ${date} - ${consecutive
        .toString()
        .padStart(2, "0")}`;
    } catch (error) {
      console.error("Error generando nombre de orden:", error);
      const timestamp = Date.now().toString().slice(-6);
      return `PEDIDO - ${timestamp}`;
    }
  },

  async createOrder() {
    const currentOrder = this.pos.getOrder();
    if (!currentOrder) {
      console.warn("No hay orden activa.");
      return;
    }

    if (currentOrder.isEmpty()) {
      console.warn("No se puede crear un pedido vacío.");
      return;
    }

    const maxRetries = 3;
    const salespersonId = currentOrder.getSalesperson()?.id || this.pos.user.id;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const orderData = await this._prepareOrderData(
          currentOrder,
          salespersonId
        );
        const result = await this.env.services.orm.create("pos.order.pending", [
          orderData,
        ]);

        if (result?.length > 0) {
          this._handleOrderSuccess(currentOrder);
          return;
        }
        throw new Error("No se pudo guardar el pedido");
      } catch (error) {
        console.error(
          `Error al crear el pedido (intento ${attempt + 1}/${maxRetries}):`,
          error
        );

        const shouldRetry =
          this._isDuplicateError(error) && attempt + 1 < maxRetries;

        if (shouldRetry) {
          console.log("Colisión de nombre detectada, reintentando...");
          await new Promise((resolve) =>
            setTimeout(resolve, 100 * (attempt + 1))
          );
          continue;
        }

        this._handleOrderError(error);
        break;
      }
    }
  },

  formatDateForOdoo(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  },
});
