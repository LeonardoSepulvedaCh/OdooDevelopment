import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class UserRoleService {
    constructor(env) {
        this.env = env;
        this._cache = new Map();
    }

    get orm() {
        return this.env.services.orm;
    }

    async isUserCashier(pos, userId = null) {
        const targetUserId = userId || pos.user.id;
        const cacheKey = `cashier_${pos.config.id}_${targetUserId}`;

        if (this._cache.has(cacheKey)) {
            return this._cache.get(cacheKey);
        }

        try {
            if (!this.orm) {
                console.warn('Servicio ORM no disponible aún, reintentando...');
                return false;
            }

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

            this._cache.set(cacheKey, isCashier);
            return isCashier;

        } catch (error) {
            console.error('Error verificando si el usuario es cajero:', error);
            return false;
        }
    }

    async isUserSalesperson(pos, userId = null) {
        const targetUserId = userId || pos.user.id;
        const cacheKey = `salesperson_${pos.config.id}_${targetUserId}`;

        if (this._cache.has(cacheKey)) {
            return this._cache.get(cacheKey);
        }

        try {
            if (!this.orm) {
                console.warn('Servicio ORM no disponible aún, reintentando...');
                return false;
            }

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
            return false;
        }
    }

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

    clearCache() {
        this._cache.clear();
    }

    clearPosCache(posConfigId) {
        for (const [key] of this._cache.entries()) {
            if (key.includes(`_${posConfigId}_`)) {
                this._cache.delete(key);
            }
        }
    }
}

registry.category("services").add("userRole", {
    start(env) {
        return new UserRoleService(env);
    },
});

export function useUserRoleService() {
    return useService("userRole");
}
