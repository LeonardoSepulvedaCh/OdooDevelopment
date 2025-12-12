import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(ClosePosPopup.prototype, {
  /**
   * Override del método confirm para validar que se use el botón de denominaciones
   */
  async confirm() {
    // Si está habilitado el forzar uso de denominaciones y hay control de efectivo
    if (
      this.pos.config.force_cash_denomination_usage &&
      this.pos.config.cash_control
    ) {
      // Verificar que se haya usado el botón de denominaciones
      if (!this.moneyDetails) {
        this.dialog.add(AlertDialog, {
          title: _t("Denominaciones requeridas"),
          body: _t(
            "Debe usar el botón de denominaciones para registrar el monto de cierre de caja."
          ),
        });
        return;
      }
    }

    // Si está bien, llamar al método original
    await super.confirm(...arguments);
  },

  /**
   * Override del método setManualCashInput para prevenir entrada manual
   */
  setManualCashInput(amount) {
    if (
      this.pos.config.force_cash_denomination_usage &&
      this.pos.config.cash_control
    ) {
      // Si está forzado el uso de denominaciones, no permitir entrada manual
      // No hacer nada, mantener el valor que viene del botón de denominaciones
      return;
    }
    // Si no está forzado, comportamiento normal
    super.setManualCashInput(amount);
  },
});
