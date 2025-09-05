import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    
    async selectSalesperson() {
        try {
            
            const salespersonIds = this.config.salesperson_user_ids || [];
            
            console.log('=== SELECT SALESPERSON DEBUG ===');
            console.log('this.config.salesperson_user_ids:', this.config.salesperson_user_ids);
            console.log('salespersonIds array:', salespersonIds);
            console.log('salespersonIds length:', salespersonIds.length);

            /* imprimer el nombre y id de los vendedores configurados */
            salespersonIds.forEach((salesperson, index) => {
                console.log(`salesperson[${index}]:`, salesperson.id, salesperson.name, salesperson);
            });

            if (salespersonIds.length === 0) {
                this.env.services.notification.add(_t('No hay vendedores configurados para este POS'), {
                    type: 'warning'
                });
                return;
            }
            
            // Preparar la lista de selección
            const selectionList = [];
            
            // Opción para no seleccionar vendedor
            selectionList.push({
                id: null,
                label: _t("Sin vendedor"),
                isSelected: !this.getOrder()?.salesperson_id,
                item: null,
            });
            
            // Agregar vendedores configurados en salespersonIds
            for (const salesperson of salespersonIds) {
                selectionList.push({
                    id: salesperson.id,
                    label: salesperson.name,
                    isSelected: this.getOrder()?.salesperson_id?.id === salesperson.id,
                    item: salesperson,
                });
            }

            selectionList.forEach(selection => {
                console.log('Vendedor: ', selection.id, selection.label, selection.isSelected, selection.item);
            });
            
            // Mostrar popup de selección
            const selectedSalesperson = await makeAwaitable(this.env.services.dialog, SelectionPopup, {
                title: _t("Seleccionar Vendedor"),
                list: selectionList,
            });
            
            if (selectedSalesperson !== undefined) {
                // Establecer el vendedor en la orden actual
                const currentOrder = this.getOrder();
                if (currentOrder) {
                    currentOrder.salesperson_id = selectedSalesperson;
                    console.log('Vendedor seleccionado:', selectedSalesperson);
                }
            }
            
        } catch (error) {
            console.error('Error seleccionando vendedor:', error);
            this.env.services.notification.add(_t('Error al seleccionar vendedor'), {
                type: 'danger'
            });
        }
    }
});
