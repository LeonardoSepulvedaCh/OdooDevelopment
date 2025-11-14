# Ventas - Comisiones por Asesor

## Descripción

Módulo que extiende la funcionalidad de comisiones de ventas permitiendo definir montos objetivos que deben alcanzarse para obtener el porcentaje de comisión establecido por categoría de producto.

## ¿Por qué SQL Directo en lugar del ORM?

### Razones Arquitecturales

Este módulo hereda de `sale.commission.achievement.report`, que es un **modelo sin tabla física** (`_auto = False`) que utiliza **vistas SQL dinámicas** para calcular comisiones en tiempo real.

El módulo padre construye consultas SQL complejas mediante el método `_table_query()`:

```python
@property
def _table_query(self):
    query = self._query()  # Construye SQL dinámico
    return SQL(query)
```

Nuestro módulo sobrescribe `_rate_to_case()`, que **debe retornar SQL crudo como string** para ser insertado en la definición de la vista materializada.

### Razones de Rendimiento

**Usando ORM (LENTO):**
```python
for sale in self.env['sale.order'].search([...]):
    for line in sale.order_line:
        if line.product_id.public_categ_ids.filtered(lambda c: c.id == category_id):
            total += line.price_subtotal
```
- ❌ Miles de consultas SQL individuales
- ❌ Alto consumo de memoria
- ❌ Tiempo de ejecución: segundos o minutos

**Usando SQL con CTEs (RÁPIDO):**
```python
WITH commission_lines AS (SELECT ...),
     rules AS (SELECT ...),
     calculations AS (SELECT ...)
SELECT * FROM calculations
```
- ✅ Una sola consulta optimizada
- ✅ PostgreSQL optimiza todo el proceso
- ✅ Tiempo de ejecución: milisegundos

**Diferencia:** 100-1000x más rápido con SQL directo.

## Seguridad SQL

Aunque usamos SQL directo, implementamos **medidas de seguridad estrictas**:

### 1. Validación Triple de Valores
```python
# Validación 1: En lectura de parámetros
cleaned_id = str(mandatory_category_id_str).strip()
if cleaned_id.isdigit() and int(cleaned_id) > 0:
    mandatory_category_id_int = int(cleaned_id)

# Validación 2: Verificación en BD
category_exists = self.env['product.public.category'].search_count([('id', '=', id)])

# Validación 3: Antes de usar en SQL
validated_id = str(int(mandatory_category_id_int))
```

### 2. Sin Entrada de Usuario Directa
Los valores provienen de:
- ✅ Parámetros de configuración del sistema (`ir.config_parameter`)
- ✅ IDs de registros de Odoo validados
- ❌ NUNCA de entrada de usuario sin validar

### 3. Logging de Errores
```python
if not category_exists:
    _logger.warning("Categoría con ID %s no existe", category_id)
    return None  # Valor seguro por defecto
```

## Limitación vs Alternativa

### ¿Por qué no usar ORM puro?

Para usar ORM completamente, sería necesario:

1. **Reescribir el módulo padre** `sale.commission.achievement.report`
2. **Eliminar vistas SQL materializadas**
3. **Implementar toda la lógica con `@api.depends` y campos computados**

**Consecuencias:**
- ⚠️ Pérdida de rendimiento significativa (100x más lento)
- ⚠️ Romper compatibilidad con otros módulos de Odoo
- ⚠️ Cambio arquitectural mayor fuera del alcance

### Nuestra Solución: Máxima Seguridad Posible

Dado que **debemos** usar SQL por diseño del módulo padre, implementamos:

✅ Validación estricta de todos los valores
✅ Verificación de existencia en base de datos  
✅ Conversión explícita de tipos (`int()`, `float()`)
✅ Logging completo de errores
✅ Uso de savepoints con nombres estáticos
✅ Código bien documentado y modular

## Características

- Definición de montos objetivo por categoría de producto
- Validación automática de cumplimiento de objetivos
- Cálculo en tiempo real de montos alcanzados
- Soporte para categorías obligatorias con porcentajes mínimos
- Lógica de prioridad de categorías
- **Cálculo jerárquico de categorías de eCommerce**: Incluye automáticamente todas las subcategorías

### Cálculo Jerárquico de Categorías

El módulo implementa un cálculo jerárquico inteligente de categorías de eCommerce:

#### Funcionamiento

Cuando se selecciona una categoría de producto, el sistema incluye automáticamente todas sus subcategorías en el cálculo del "Monto Alcanzado":

- **Categoría Padre (OPTIMUS)**: Incluye TODAS las ventas de OPTIMUS y todas sus subcategorías
  - OPTIMUS/BICICLETAS
  - OPTIMUS/BICICLETAS/MTB/BICICLETA_1
  - OPTIMUS/REPUESTOS/RINES
  - etc.

- **Subcategoría Intermedia (OPTIMUS/BICICLETAS)**: Incluye solo BICICLETAS y sus hijas
  - OPTIMUS/BICICLETAS/MTB
  - OPTIMUS/BICICLETAS/MTB/BICICLETA_1
  - (excluye OPTIMUS/REPUESTOS)

- **Subcategoría Específica (OPTIMUS/REPUESTOS/RINES)**: Incluye solo esa categoría
  - OPTIMUS/REPUESTOS/RINES (sin subcategorías)

#### Implementación Técnica

La lógica de navegación jerárquica está **centralizada en el modelo `product.public.category`**, donde está disponible para toda la aplicación:

```python
# En product.public.category
@api.model
def get_category_with_children_ids(self, category_id):
    """Obtiene una categoría y todas sus hijas recursivamente."""
    if not category_id:
        return []
    categories = self.search([('id', 'child_of', category_id)])
    return categories.ids

# Uso desde cualquier modelo
category_ids = self.env['product.public.category'].get_category_with_children_ids(category_id)
```

**Ventajas de esta arquitectura:**

- ✅ **Centralización**: Lógica en un solo lugar, evitando duplicación
- ✅ **Reutilización**: Disponible para cualquier módulo o personalización
- ✅ **Mantenibilidad**: Cambios en un solo punto afectan toda la aplicación
- ✅ **Estándar Odoo**: Usa el operador `child_of` optimizado internamente
- ✅ **Rendimiento**: Consultas recursivas eficientes + caché del ORM
- ✅ **Flexibilidad**: Fácil de extender o modificar según necesidades futuras

Esto garantiza:
- ✅ Rendimiento óptimo incluso con jerarquías profundas
- ✅ Inclusión automática de nuevas subcategorías
- ✅ Flexibilidad en la configuración de metas por nivel jerárquico
- ✅ Código más limpio y mantenible siguiendo las mejores prácticas de Odoo

## Dependencias

- `sale_commission`
- `sale_commission_margin`

## Autor

@LeonardoSepulvedaCh

## Licencia

OEEL-1

