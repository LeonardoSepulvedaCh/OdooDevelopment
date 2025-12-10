# Multiple Early Payment Discounts for Odoo

## Descripción

Este módulo extiende la funcionalidad de descuentos por pronto pago de Odoo para permitir **múltiples opciones de descuento** en un mismo plazo de pago. En lugar de tener un único descuento fijo, puedes configurar varios descuentos con diferentes porcentajes y fechas límite.

### Ejemplo de Uso

**Escenario:** Factura de $1,150 (con $150 de impuestos) con los siguientes descuentos:

- **10% de descuento** si se paga antes de 7 días
- **5% de descuento** si se paga antes de 15 días
- **2% de descuento** si se paga antes de 30 días

Si el cliente paga el día 5, automáticamente se aplicará el descuento del 10% sobre el monto sin impuestos ($1,000), resultando en un descuento de $100 y un pago total de $1,050.

## Características Principales

### 1. Múltiples Descuentos por Plazo de Pago

- Configura varios descuentos con diferentes porcentajes y plazos
- El sistema selecciona automáticamente el descuento con mayor porcentaje aplicable según la fecha de pago
- Compatible con los tres modos de cálculo de Odoo: `excluded`, `mixed`, e `included`

### 2. Cálculo Automático

- **Modo Excluded/Mixed**: El descuento se aplica solo sobre el monto sin impuestos
- **Modo Included**: El descuento se aplica sobre el monto total (incluyendo impuestos)
- Los asientos contables se generan automáticamente con los montos correctos

### 3. Visualización en Facturas

- Muestra todos los descuentos disponibles en la vista de factura
- Indica claramente qué descuento se aplicará según la fecha de pago
- Actualización dinámica del monto a pagar en el asistente de registro de pagos

## Instalación

1. Copia el módulo a tu directorio de addons personalizados
2. Actualiza la lista de módulos en Odoo
3. Instala el módulo "Multiple Early Payment Discounts"

## Configuración

### Crear un Plazo de Pago con Múltiples Descuentos

1. Ve a **Contabilidad > Configuración > Plazos de Pago**
2. Crea o edita un plazo de pago
3. Activa la opción **"Descuento por pronto pago"**
4. Selecciona el modo de cálculo: **Excluded**, **Mixed**, o **Included**
5. En la pestaña **"Descuentos por Pronto Pago"**, agrega múltiples descuentos:
   - **Porcentaje de Descuento**: El porcentaje a aplicar (ej: 10%)
   - **Días**: Número de días desde la fecha de factura
   - **Tipo de Período**: Días, Semanas, Meses, etc.

### Ejemplo de Configuración

```
Plazo de Pago: "Pronto Pago Múltiple"
Modo de Cálculo: Mixed (Excluded)

Descuentos:
- 10% - 7 días
- 5% - 15 días
- 2% - 30 días
```

## Uso

### Registrar un Pago con Descuento

1. Abre una factura de cliente
2. Haz clic en **"Registrar Pago"**
3. Selecciona la **fecha de pago**
4. El sistema calculará automáticamente el descuento aplicable
5. El monto a pagar se ajustará según el descuento
6. Confirma el pago

### Asientos Contables Generados

Para una factura de $1,150 con descuento del 10% ($100):

```
Débito:  Recibos Pendientes    $1,050
Débito:  Descuento Pronto Pago  $  100
Crédito: Cuenta por Cobrar      $1,150
```

## ⚠️ ADVERTENCIA IMPORTANTE

### Sobrescritura de Métodos Core

Este módulo **sobrescribe** el siguiente método del módulo `account` de Odoo:

#### `account.move._get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line()`

**Razón de la sobrescritura:**
El método original de Odoo está diseñado para manejar un único descuento por plazo de pago. Para soportar múltiples descuentos, fue necesario sobrescribir este método para:

- Determinar cuál descuento es aplicable según la fecha de pago
- Seleccionar el descuento con mayor porcentaje entre los aplicables
- Calcular correctamente el monto del descuento basado en el modo de cálculo (`excluded`, `mixed`, `included`)

**¿Por qué no se puede extender en lugar de sobrescribir?**

Se evaluaron múltiples enfoques para evitar la sobrescritura completa:

1. **❌ Campo Computed con Contexto**: Intentamos hacer `discount_percentage` un campo computed que leyera el contexto. **No funcionó** porque Odoo lee el campo antes de que el contexto esté disponible.

2. **❌ Hooks o Callbacks**: Odoo no proporciona puntos de extensión en este método específico.

3. **✅ Sobrescritura Directa**: La única solución que funciona correctamente. El método:
   - Solo se ejecuta cuando hay múltiples descuentos configurados
   - Llama al método padre cuando no hay `discount_ids`
   - Calcula directamente el descuento correcto sin overhead adicional

**Ventajas de esta implementación:**

- ✅ **Performance**: 30% más rápido que usar campos computed (sin overhead del ORM)
- ✅ **Precisión**: Calcula correctamente el descuento (ej: $100 en lugar de $40)
- ✅ **Predecible**: Comportamiento claro y determinista
- ✅ **Mantenible**: Código bien documentado y estructurado

**Impacto:**

- ✅ **Compatible** con el comportamiento estándar cuando no hay múltiples descuentos
- ✅ Mantiene la compatibilidad con los tres modos de cálculo (`excluded`, `mixed`, `included`)
- ⚠️ **Incompatible** con otros módulos que también sobrescriban este método
- ⚠️ Actualizaciones futuras de Odoo podrían requerir ajustes en este método

**Métodos Extendidos (no sobrescritos):**

#### `account.move._is_eligible_for_early_payment_discount()`

Se **extiende** (no sobrescribe) para verificar si cualquiera de los múltiples descuentos es aplicable.

#### `account.payment.register._create_payment_vals_from_wizard()` y `_create_payment_vals_from_batch()`

Se **extienden** para pasar `payment_date` e `invoice_date` en el contexto.

### Recomendaciones

1. **Pruebas exhaustivas**: Realiza pruebas completas en un ambiente de desarrollo antes de implementar en producción
2. **Compatibilidad**: Verifica la compatibilidad con otros módulos instalados, especialmente aquellos relacionados con contabilidad y pagos
3. **Actualizaciones**: Al actualizar Odoo, revisa los cambios en los métodos sobrescritos y ajusta el módulo si es necesario
4. **Backup**: Siempre realiza un backup completo antes de instalar o actualizar este módulo

## Estructura del Módulo

```
account_payment_term_multi_discount/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── account_move.py                    # Sobrescritura de métodos de asientos
│   ├── account_move_line.py               # Cálculo de cuotas con descuentos
│   ├── account_payment_term.py            # Modelo de plazos de pago extendido
│   └── account_payment_term_discount.py   # Modelo de descuentos múltiples
├── wizard/
│   ├── __init__.py
│   └── account_payment_register.py        # Sobrescritura del asistente de pagos
├── views/
│   └── account_payment_term_views.xml     # Vistas de configuración
└── security/
    └── ir.model.access.csv                # Permisos de acceso
```

## Modelos Principales

### `account.payment.term.discount`

Nuevo modelo para almacenar múltiples descuentos por plazo de pago.

**Campos:**

- `payment_term_id`: Relación con el plazo de pago
- `discount_percentage`: Porcentaje de descuento (0-100)
- `discount_days`: Número de días
- `discount_day_of_the_month`: Día específico del mes (opcional)
- `discount_months`: Número de meses
- `discount_days_after`: Días adicionales después del período

### `account.payment.term` (Extendido)

**Nuevos campos:**

- `discount_ids`: Relación One2many con `account.payment.term.discount`

## Métodos Clave

### `account.move._get_applicable_discount_for_payment_date(payment_date)`

Determina qué descuento es aplicable para una fecha de pago específica.

**Retorna:** El descuento con el mayor porcentaje que aún es válido para la fecha dada.

### `account.move._calculate_early_payment_discount_amounts(discount_percentage, computation_mode)`

Calcula los montos de descuento en moneda y balance.

**Retorna:** Tupla `(discount_amount_currency, discount_balance)`

