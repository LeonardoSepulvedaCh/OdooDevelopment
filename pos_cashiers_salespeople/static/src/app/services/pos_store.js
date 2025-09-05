import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    
    async selectSalesperson() {
        try {
            let salespersonUsers = [];
            
            try {
                const configResult = await this.env.services.orm.read('pos.config', [this.config.id], ['salesperson_user_ids']);
                
                if (configResult && configResult.length > 0) {
                    const salespersonIds = configResult[0].salesperson_user_ids || [];
                    
                    if (salespersonIds.length === 0) {
                        this.env.services.notification.add(_t('No hay vendedores configurados para este POS'), {
                            type: 'warning'
                        });
                        return;
                    }
                    
                    salespersonUsers = await this.env.services.orm.read('res.users', salespersonIds, ['id', 'name', 'active']);
                    
                    salespersonUsers = salespersonUsers.filter(user => user.active);
                } else {
                    throw new Error('No se pudo cargar la configuración del POS');
                }
            } catch (loadError) {
                console.error('Error cargando vendedores:', loadError);
                this.env.services.notification.add(_t('Error cargando la lista de vendedores'), {
                    type: 'danger'
                });
                return;
            }

            if (salespersonUsers.length === 0) {
                this.env.services.notification.add(_t('No hay vendedores activos configurados para este POS'), {
                    type: 'warning'
                });
                return;
            }
            
            const selectionList = [];
            
            selectionList.push({
                id: null,
                label: _t("Sin vendedor"),
                isSelected: !this.getOrder()?.salesperson_id,
                item: null,
            });
            
            for (const salesperson of salespersonUsers) {
                selectionList.push({
                    id: salesperson.id,
                    label: salesperson.name,
                    isSelected: this.getOrder()?.salesperson_id?.id === salesperson.id,
                    item: salesperson,
                });
            }
            
            const selectedSalesperson = await makeAwaitable(this.env.services.dialog, SelectionPopup, {
                title: _t("Seleccionar Vendedor"),
                list: selectionList,
            });
            
            if (selectedSalesperson !== undefined) {
                const currentOrder = this.getOrder();
                if (currentOrder) {
                    currentOrder.salesperson_id = selectedSalesperson;
                }
            }
            
        } catch (error) {
            console.error('Error seleccionando vendedor:', error);
            this.env.services.notification.add(_t('Error al seleccionar vendedor: ' + error.message), {
                type: 'danger'
            });
        }
    }
});
