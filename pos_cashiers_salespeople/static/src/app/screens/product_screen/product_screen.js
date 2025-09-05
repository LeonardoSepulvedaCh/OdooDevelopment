import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    
    async setup() {
        super.setup(...arguments);
        await this._loadCashierSalespersonData();
    },

    async _loadCashierSalespersonData() {
        try {
            const result = await this.env.services.orm.read('pos.config', [this.pos.config.id], ['cashier_user_ids', 'salesperson_user_ids']);
            if (result && result.length > 0) {
                this.pos.config.cashier_user_ids = result[0].cashier_user_ids || [];
                this.pos.config.salesperson_user_ids = result[0].salesperson_user_ids || [];
            }
        } catch (error) {
            console.error('Error loading cashier/salesperson data:', error);
            this.pos.config.cashier_user_ids = [];
            this.pos.config.salesperson_user_ids = [];
        }
    },
    
    /**
     * Verificar si el usuario actual es cajero en este POS
     * @returns {boolean}
     */
    isCurrentUserCashier() {
        if (!this.pos.user || !this.pos.config) {
            return false;
        }
        const currentUserId = this.pos.user.id;
        const cashierIds = this.pos.config.cashier_user_ids || [];
        
        // Extraer IDs reales de los objetos user
        let cashierUserIds = [];
        if (Array.isArray(cashierIds)) {
            cashierUserIds = cashierIds.map(user => user.id || user);
        } else if (cashierIds && typeof cashierIds === 'object') {
            // Si es un Proxy object, extraer IDs de los users
            for (let key in cashierIds) {
                const user = cashierIds[key];
                if (user && user.id) {
                    cashierUserIds.push(user.id);
                } else if (typeof user === 'number') {
                    cashierUserIds.push(user);
                }
            }
        }
        return cashierUserIds.includes(currentUserId);
    },

    /**
     * Verificar si el usuario actual es vendedor en este POS
     * @returns {boolean}
     */
    isCurrentUserSalesperson() {
        if (!this.pos.user || !this.pos.config) {
            return false;
        }
        const currentUserId = this.pos.user.id;
        const salespersonIds = this.pos.config.salesperson_user_ids || [];
        
        // Extraer IDs reales de los objetos user
        let salespersonUserIds = [];
        if (Array.isArray(salespersonIds)) {
            salespersonUserIds = salespersonIds.map(user => user.id || user);
        } else if (salespersonIds && typeof salespersonIds === 'object') {
            // Si es un Proxy object, extraer IDs de los users
            for (let key in salespersonIds) {
                const user = salespersonIds[key];
                if (user && user.id) {
                    salespersonUserIds.push(user.id);
                } else if (typeof user === 'number') {
                    salespersonUserIds.push(user);
                }
            }
        }
        return salespersonUserIds.includes(currentUserId);
    },

    /**
     * Generar un nombre para el pedido con las dos primeras letras del nombre del vendedor, el numero del dia y un consecutivo de las ordenes creadas por el vendedor
     * @returns {string}
     */
    async generateOrderName() {
        try {
            // Obtener las dos primeras letras del nombre del vendedor
            const salespersonName = this.pos.user.name || 'US';
            const salesperson = salespersonName.split(' ')[0].toUpperCase().slice(0, 2);
            
            // Obtener el día del mes
            const date = new Date().getDate().toString().padStart(2, '0');
            
            // Contar órdenes pendientes del vendedor actual
            const existingOrders = await this.env.services.orm.searchRead(
                'pos.order.pending',
                [
                    ['salesperson_id', '=', this.pos.user.id],
                    ['status', '=', 'pending']
                ],
                ['id'],
                { limit: 1 }
            );
            
            const consecutive = existingOrders.length + 1;
            return `${salesperson} - ${date} - ${consecutive}`;
        } catch (error) {
            console.error('Error generando nombre de orden:', error);
            // Fallback si hay error
            const timestamp = new Date().getTime();
            return `PEDIDO - ${timestamp}`;
        }
    },

    /**
     * Crear un pedido (order) en lugar de ir al pago
     * Esta función guarda el pedido en la base de datos y limpia la vista actual
     */
    async createOrder() {
        const currentOrder = this.pos.getOrder();
        if (!currentOrder) {
            console.warn("No hay orden activa.");
            return;
        }

        // Verificar que la orden no esté vacía
        if (currentOrder.isEmpty()) {
            console.warn("No se puede crear un pedido vacío.");
            return;
        }
        
        try {
            const orderlines = currentOrder.getOrderlines();
            const orderLinesData = orderlines.map(line => ({
                product_id: line.product_id.id,
                product_name: line.product_id.display_name || line.product_id.name,
                quantity: line.quantity || line.qty,
                price_unit: line.price_unit,
                discount: line.discount || 0,
                subtotal: line.getPriceWithTax ? line.getPriceWithTax() : (line.price_unit * line.quantity),
                tax_amount: line.getTax ? line.getTax() : 0
            }));

            // Preparar los datos del pedido para guardar 
            const orderData = {
                name: await this.generateOrderName(),
                pos_reference: currentOrder.pos_reference || '',
                salesperson_id: this.pos.user.id,
                partner_id: currentOrder.partner_id ? currentOrder.partner_id.id : false,
                date_order: this.formatDateForOdoo(new Date()),
                amount_total: currentOrder.getTotalWithTax(),
                amount_untaxed: currentOrder.getTotalWithoutTax(),
                amount_tax: currentOrder.getTotalTax(),
                order_lines: JSON.stringify(orderLinesData),
                pos_config_id: this.pos.config.id,
                status: 'pending'
            };

            // Guardar el pedido en la base de datos
            const result = await this.env.services.orm.create('pos.order.pending', [orderData]);
            
            if (result && result.length > 0) {
                this.env.services.notification.add('Pedido creado exitosamente', {
                    type: 'success',
                    sticky: false,
                });

                this.pos.removeOrder(currentOrder);
                this.pos.addNewOrder();
                
            } else {
                throw new Error('No se pudo guardar el pedido');
            }

        } catch (error) {
            console.error('Error al crear el pedido:', error);
            this.env.services.notification.add('Error al crear el pedido: ' + error.message, {
                type: 'danger',
                sticky: true,
            });
        }
    },

    /**
     * Formatear fecha para Odoo en formato YYYY-MM-DD HH:MM:SS
     * @param {Date} date - Fecha a formatear
     * @returns {string} - Fecha formateada para Odoo
     */
    formatDateForOdoo(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    },

});
