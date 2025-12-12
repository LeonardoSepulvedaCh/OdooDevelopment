import { OpeningControlPopup } from "@point_of_sale/app/components/popups/opening_control_popup/opening_control_popup";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(OpeningControlPopup.prototype, {
    /**
     * Override del método confirm para validar que se use el botón de denominaciones
     */
    async confirm() {
        // Si está habilitado el forzar uso de denominaciones y hay control de efectivo
        if (this.pos.config.force_cash_denomination_usage && this.cashMethodCount) {
            // Verificar que se haya usado el botón de denominaciones
            if (!this.moneyDetails) {
                this.dialog.add(AlertDialog, {
                    title: _t("Denominaciones requeridas"),
                    body: _t("Debe usar el botón de denominaciones para registrar el monto de apertura de caja."),
                });
                return;
            }
        }
        
        // Si todo está bien, llamar al método original
        await super.confirm();
    },

    /**
     * Override del método handleInputChange para prevenir entrada manual
     */
    handleInputChange() {
        if (this.pos.config.force_cash_denomination_usage && this.cashMethodCount) {
            // No permitir edición manual si está forzado el uso de denominaciones
            // No limpiar las notas ni hacer nada
            return;
        }
        // Si no está forzado, comportamiento normal
        super.handleInputChange();
    }
});


