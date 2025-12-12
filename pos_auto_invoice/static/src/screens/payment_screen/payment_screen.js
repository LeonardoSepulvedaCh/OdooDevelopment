import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted, onPatched } from "@odoo/owl";

patch(PaymentScreen.prototype, {
  setup() {
    super.setup();
    this._checkAutoInvoice();

    onMounted(() => {
      this._updateInvoiceButton();
    });

    onPatched(() => {
      this._updateInvoiceButton();
    });
  },

  _checkAutoInvoice() {
    // No activar facturación automática para reembolsos (monto negativo)
    const isRefund = this.currentOrder.priceIncl < 0;

    if (this.pos.config.auto_invoice && !isRefund) {
      if (!this.currentOrder.isToInvoice()) {
        this.currentOrder.setToInvoice(true);
      }
    }
  },

  _updateInvoiceButton() {
    const invoiceButton = document.querySelector(".js_invoice");

    if (invoiceButton && this.pos.config.auto_invoice) {
      invoiceButton.disabled = true;
      invoiceButton.classList.add("pos-auto-invoice-disabled");
    } else if (invoiceButton && !this.pos.config.auto_invoice) {
      invoiceButton.disabled = false;
      invoiceButton.classList.remove("pos-auto-invoice-disabled");
    }
  },

  async addNewPaymentLine(paymentMethod) {
    const result = await super.addNewPaymentLine(paymentMethod);

    if (result && this.pos.config.auto_invoice) {
      this._checkAutoInvoice();
      this._updateInvoiceButton();
    }

    return result;
  },

  async validateOrder(isForceValidate = false) {
    // No activar facturación automática para reembolsos (monto negativo)
    const isRefund = this.currentOrder.priceIncl < 0;

    if (this.pos.config.auto_invoice && !isRefund) {
      this.currentOrder.setToInvoice(true);
    }

    return await super.validateOrder(isForceValidate);
  },
});
