import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class UserRoleService {
    constructor(env) {
        this.env = env;
        this._cache = new Map(); // Cache para evitar consultas repetidas
    }

    get orm() {
        return this.env.services.orm;
    }

    /**
     * Verifica si el usuario actual es cajero en el POS actual
     * @param {Object} pos - Instancia del POS
     * @param {number} userId - ID del usuario (opcional, usa el usuario actual por defecto)
     * @returns {Promise<boolean>}
     */
    async isUserCashier(pos, userId = null) {
        const targetUserId = userId || pos.user.id;
        const cacheKey = `cashier_${pos.config.id}_${targetUserId}`;

        // Verificar cache primero
        if (this._cache.has(cacheKey)) {
            return this._cache.get(cacheKey);
        }

        try {
            // Verificar que el ORM esté disponible
            if (!this.orm) {
                console.warn('Servicio ORM no disponible aún, reintentando...');
                return false;
            }

            // Leer la configuración del POS para obtener los cajeros
            const posConfig = await this.orm.read(
                'pos.config',
                [pos.config.id],
                ['cashier_user_ids']
            );
            
            let isCashier = false;
            if (posConfig && posConfig.length > 0) {
                const cashierIds = posConfig[0].cashier_user_ids || [];
                isCashier = cashierIds.includes(targetUserId);
            }

            // Guardar en cache
            this._cache.set(cacheKey, isCashier);
            return isCashier;

        } catch (error) {
            console.error('Error verificando si el usuario es cajero:', error);
            // En caso de error, asumir que no es cajero y no guardar en cache
            return false;
        }
    }

    /**
     * Verifica si el usuario actual es vendedor en el POS actual
     * @param {Object} pos - Instancia del POS
     * @param {number} userId - ID del usuario (opcional, usa el usuario actual por defecto)
     * @returns {Promise<boolean>}
     */
    async isUserSalesperson(pos, userId = null) {
        const targetUserId = userId || pos.user.id;
        const cacheKey = `salesperson_${pos.config.id}_${targetUserId}`;

        // Verificar cache primero
        if (this._cache.has(cacheKey)) {
            return this._cache.get(cacheKey);
        }

        try {
            // Verificar que el ORM esté disponible
            if (!this.orm) {
                console.warn('Servicio ORM no disponible aún, reintentando...');
                return false;
            }

            // Leer la configuración del POS para obtener los vendedores
            const posConfig = await this.orm.read(
                'pos.config',
                [pos.config.id],
                ['salesperson_user_ids']
            );
            
            let isSalesperson = false;
            if (posConfig && posConfig.length > 0) {
                const salespersonIds = posConfig[0].salesperson_user_ids || [];
                isSalesperson = salespersonIds.includes(targetUserId);
            }

            // Guardar en cache
            this._cache.set(cacheKey, isSalesperson);
            return isSalesperson;

        } catch (error) {
            console.error('Error verificando si el usuario es vendedor:', error);
            // En caso de error, asumir que no es vendedor y no guardar en cache
            return false;
        }
    }

    /**
     * Obtiene los roles del usuario actual en el POS
     * @param {Object} pos - Instancia del POS
     * @param {number} userId - ID del usuario (opcional, usa el usuario actual por defecto)
     * @returns {Promise<Object>} - Objeto con propiedades isCashier y isSalesperson
     */
    async getUserRoles(pos, userId = null) {
        const [isCashier, isSalesperson] = await Promise.all([
            this.isUserCashier(pos, userId),
            this.isUserSalesperson(pos, userId)
        ]);

        return {
            isCashier,
            isSalesperson
        };
    }

    /**
     * Limpia el cache de roles (útil cuando se cambian configuraciones)
     */
    clearCache() {
        this._cache.clear();
    }

    /**
     * Limpia el cache para un POS específico
     * @param {number} posConfigId - ID de la configuración del POS
     */
    clearPosCache(posConfigId) {
        for (const [key] of this._cache.entries()) {
            if (key.includes(`_${posConfigId}_`)) {
                this._cache.delete(key);
            }
        }
    }
}

// Registrar el servicio
registry.category("services").add("userRole", {
    start(env) {
        return new UserRoleService(env);
    },
});

// Hook para usar el servicio fácilmente
export function useUserRoleService() {
    return useService("userRole");
}
