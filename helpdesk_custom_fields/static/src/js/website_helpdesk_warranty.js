import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

// Interacción para cargar dinámicamente facturas y productos en formularios de garantía
export class HelpdeskWarrantyFormLoader extends Interaction {
  static selector = "#helpdesk_warranty_ticket_form";

  dynamicContent = {
    "#warranty_invoice": {
      "t-on-change": this.onInvoiceChange,
    },
    "#warranty_product": {
      "t-on-change": this.onProductChange,
    },
    "#warranty_product_qty": {
      "t-on-input": this.onQuantityChange,
    },
  };

  // Inicializar la interacción
  setup() {
    this.selectedProduct = null;
    this.productMaxQuantities = {};
    this.loadInvoices();
  }

  // Cargar las facturas del usuario autenticado mediante JSON-RPC
  async loadInvoices() {
    const invoiceSelect = this.el.querySelector("#warranty_invoice");

    if (!invoiceSelect) {
      return;
    }

    invoiceSelect.innerHTML = '<option value="">Cargando facturas...</option>';
    invoiceSelect.disabled = true;

    try {
      const result = await rpc("/helpdesk/warranty/get_partner_invoices", {});

      if (result.error) {
        console.error("Error al cargar facturas:", result.error);
        invoiceSelect.innerHTML =
          '<option value="">Error al cargar facturas</option>';
        return;
      }

      invoiceSelect.innerHTML =
        '<option value="">Seleccione una factura</option>';

      if (result.invoices && result.invoices.length > 0) {
        result.invoices.forEach((invoice) => {
          const option = document.createElement("option");
          option.value = invoice.id;
          option.textContent = invoice.display_name;
          invoiceSelect.appendChild(option);
        });
        invoiceSelect.disabled = false;
      } else {
        invoiceSelect.innerHTML =
          '<option value="">No hay facturas disponibles</option>';
      }
    } catch (error) {
      console.error("Error en la llamada JSON-RPC:", error);
      invoiceSelect.innerHTML =
        '<option value="">Error al cargar facturas</option>';
    }
  }

  // Manejar el cambio de factura seleccionada
  onInvoiceChange(ev) {
    const invoiceId = ev.currentTarget.value;

    if (!invoiceId) {
      this.hideProducts();
      return;
    }

    this.loadProducts(invoiceId);
  }

  // Cargar los productos de una factura específica
  async loadProducts(invoiceId) {
    const productSelect = this.el.querySelector("#warranty_product");
    const productField = this.el.querySelector("#warranty_product_field");
    const qtyField = this.el.querySelector("#warranty_product_qty_field");

    if (!productSelect || !productField || !qtyField) {
      return;
    }

    productSelect.innerHTML = '<option value="">Cargando productos...</option>';
    productSelect.disabled = true;
    productField.style.display = "block";

    this.selectedProduct = null;
    this.productMaxQuantities = {};
    this.hideQuantityField();

    try {
      const result = await rpc("/helpdesk/warranty/get_invoice_products", {
        invoice_id: invoiceId,
      });

      if (result.error) {
        console.error("Error al cargar productos:", result.error);
        productSelect.innerHTML =
          '<option value="">Error al cargar productos</option>';
        return;
      }

      if (result.products && result.products.length > 0) {
        this.renderProducts(result.products);
        productSelect.disabled = false;
      } else {
        productSelect.innerHTML =
          '<option value="">Esta factura no tiene productos</option>';
      }
    } catch (error) {
      console.error("Error en la llamada JSON-RPC:", error);
      productSelect.innerHTML =
        '<option value="">Error al cargar productos</option>';
    }
  }

  // Renderizar los productos como opciones de select
  renderProducts(products) {
    const productSelect = this.el.querySelector("#warranty_product");

    if (!productSelect) {
      return;
    }

    productSelect.innerHTML =
      '<option value="">Seleccione un producto</option>';

    products.forEach((product) => {
      this.productMaxQuantities[product.id] = product.quantity;

      const option = document.createElement("option");
      option.value = product.id;

      const productCode = product.default_code
        ? ` (${product.default_code})`
        : "";

      option.textContent = `${product.name}${productCode} - Disponible: ${product.quantity}`;

      productSelect.appendChild(option);
    });
  }

  // Manejar el cambio en el select de productos
  onProductChange(ev) {
    const productId = ev.currentTarget.value;
    const qtyField = this.el.querySelector("#warranty_product_qty_field");
    const qtyInput = this.el.querySelector("#warranty_product_qty");
    const qtyHelp = this.el.querySelector("#warranty_product_qty_help");

    if (!productId) {
      this.hideQuantityField();
      return;
    }

    this.selectedProduct = productId;

    if (qtyField) {
      qtyField.style.display = "block";
    }

    // Establecer la cantidad máxima y actualizar el input
    const maxQty = this.productMaxQuantities[productId] || 1;
    if (qtyInput) {
      qtyInput.max = maxQty;
      qtyInput.value = Math.min(1, maxQty);
    }

    if (qtyHelp) {
      qtyHelp.textContent = `Disponible: ${maxQty}`;
    }
  }

  // Validar la cantidad ingresada
  onQuantityChange(ev) {
    const qtyInput = ev.currentTarget;
    const qtyHelp = this.el.querySelector("#warranty_product_qty_help");
    const productId = this.selectedProduct;

    if (!productId) {
      return;
    }

    const maxQty = this.productMaxQuantities[productId] || 1;
    const enteredQty = Number.parseFloat(qtyInput.value) || 0;

    if (enteredQty > maxQty) {
      qtyInput.value = maxQty;
      if (qtyHelp) {
        qtyHelp.textContent = `Disponible: ${maxQty} - ¡Cantidad ajustada al máximo!`;
        qtyHelp.classList.add("text-warning");
      }
    } else if (enteredQty <= 0) {
      qtyInput.value = 0.01;
      if (qtyHelp) {
        qtyHelp.textContent = `Disponible: ${maxQty} - La cantidad debe ser mayor a 0`;
        qtyHelp.classList.add("text-warning");
      }
    } else if (qtyHelp) {
      qtyHelp.textContent = `Disponible: ${maxQty}`;
      qtyHelp.classList.remove("text-warning");
    }
  }

  // Ocultar el campo de cantidad
  hideQuantityField() {
    const qtyField = this.el.querySelector("#warranty_product_qty_field");
    const qtyInput = this.el.querySelector("#warranty_product_qty");
    const qtyHelp = this.el.querySelector("#warranty_product_qty_help");

    if (qtyField) {
      qtyField.style.display = "none";
    }

    if (qtyInput) {
      qtyInput.value = 1;
    }

    if (qtyHelp) {
      qtyHelp.textContent = "Disponible: -";
      qtyHelp.classList.remove("text-warning");
    }
  }

  // Ocultar el campo de productos
  hideProducts() {
    const productField = this.el.querySelector("#warranty_product_field");
    const productSelect = this.el.querySelector("#warranty_product");

    if (productField) {
      productField.style.display = "none";
    }

    if (productSelect) {
      productSelect.innerHTML =
        '<option value="">Seleccione una factura primero</option>';
      productSelect.value = "";
    }

    this.selectedProduct = null;
    this.productMaxQuantities = {};
    this.hideQuantityField();
  }
}

// Interacción de validación para desactivar formularios de garantía
export class HelpdeskWarrantyFormValidation extends Interaction {
  static selector = "#helpdesk_ticket_form";

  dynamicContent = {
    _root: {
      "t-on-submit.prevent": (ev) => {
        if (this.isFormDisabled) {
          ev.stopPropagation();
          return false;
        }
      },
    },
  };

  setup() {
    this.isFormDisabled = this.el.classList.contains(
      "o_warranty_form_disabled"
    );

    if (this.isFormDisabled) {
      this.disableForm();
    }
  }

  disableForm() {
    const formElements = this.el.querySelectorAll(
      "input, textarea, select, button"
    );
    formElements.forEach((element) => {
      element.disabled = true;
    });
  }
}

// Registrar las interacciones en el registro de Odoo
registry
  .category("public.interactions")
  .add(
    "helpdesk_custom_fields.warranty_form_loader",
    HelpdeskWarrantyFormLoader
  );

registry
  .category("public.interactions")
  .add(
    "helpdesk_custom_fields.warranty_form_validation",
    HelpdeskWarrantyFormValidation
  );

export default {
  HelpdeskWarrantyFormLoader,
  HelpdeskWarrantyFormValidation,
};
