# Portal Invoice Partner Grouping

Módulo de Odoo 19.0 que agrupa las facturas del portal del cliente por contacto de empresa (escenario B2B), manteniendo toda la funcionalidad nativa y proporcionando una experiencia de usuario optimizada tanto para escritorio como para dispositivos móviles.

## 📋 Características Principales

### 🎯 Agrupación por Contacto
- Agrupa automáticamente las facturas por partner/contacto de empresa
- Muestra el nombre, email y total pendiente de cada contacto
- Preserva el orden original de las facturas (respeta ordenamiento y filtros nativos)
- Mantiene compatibilidad con vista única (sin agrupación) cuando hay un solo contacto

### 💰 Descuento por Pronto Pago (EPD)
- Muestra el precio original tachado y el precio con descuento destacado en verde
- Compatible con la funcionalidad de Early Payment Discount de Odoo
- Cálculo automático del monto con descuento vigente

### 🎨 Diseño Responsive
- **Desktop (≥768px)**: Vista de tabla tradicional con todas las columnas
- **Mobile (<768px)**: Vista de tarjetas elegantes y compactas
- Animaciones suaves y efectos visuales modernos
- Interfaz adaptada a cada tamaño de pantalla

### 📱 Vista Mobile (Tarjetas)
Cada factura se muestra como una tarjeta con:
- Checkbox para selección múltiple
- Número de factura como hipervínculo
- Icono de estado con tooltip
- Fecha de vencimiento destacada
- Badge de días vencidos (si aplica)
- Monto pendiente destacado
- Botones: Descargar PDF y Pagar ahora

### 🔍 Filtros Mejorados
- **Facturas Pendientes** (por defecto): Muestra solo facturas pendientes de pago
- **Facturas de clientes**: Vista completa (facturas + notas de crédito)
- **Notas de crédito**: Filtro específico para refunds
- Integración completa con filtros nativos de Odoo

### ✅ Funcionalidades de Selección
- Checkbox maestro para seleccionar todas las facturas de la página
- Checkbox de grupo para seleccionar todas las facturas de un contacto
- Checkboxes individuales por factura
- Estados intermedios (indeterminate) para selección parcial
- Integración con `payment_rutavity` para pagos múltiples
- Barra de resumen con total seleccionado

### 🎭 Estados Visuales
- **Pagada**: ✓ Icono verde (check-circle)
- **Pendiente**: 🕐 Icono azul (clock-o)
- **Vencida**: ⚠️ Icono rojo (exclamation-circle)
- **Cancelada**: 🚫 Icono amarillo (ban)
- Tooltips en todos los iconos

### 🔘 Acciones Rápidas
- **Botón Pagar**: Redirige a `/my/invoices/overdue?invoice_ids={id}` (solo facturas pendientes)
- **Hipervínculo**: Click en número de factura para ver detalles
- **Descargar PDF**: Descarga directa del PDF de la factura


### URL por Defecto
El acceso desde el menú del portal usa el filtro de facturas pendientes:
```
/my/invoices?filterby=pending_invoices&sortby=most_overdue
```

## 🚀 Uso

1. **Acceder al portal**: Los clientes inician sesión en el portal de Odoo
2. **Ver facturas**: Navegar a "Mis Facturas" desde el menú
3. **Facturas agrupadas**: Si el cliente tiene múltiples contactos de empresa, verá las facturas agrupadas
4. **Selección múltiple**: Marcar checkboxes para pagar múltiples facturas
5. **Pago individual**: Click en "Pagar" para procesar un pago único

## 📊 Columnas de la Tabla (Desktop)

| Columna | Descripción |
|---------|-------------|
| Checkbox | Selección para pago múltiple |
| Invoice # | Número de factura (hipervínculo) |
| Invoice Date | Fecha de emisión |
| Due Date | Fecha de vencimiento (rojo si vencida) |
| Amount Due | Monto pendiente (con descuento EPD si aplica) |
| Status | Estado de la factura (icono con tooltip) |
| Actions | Botón de pagar |

## 📱 Campos de la Tarjeta (Mobile)

- Checkbox de selección
- Número de factura (hipervínculo)
- Estado (icono)
- Fecha de vencimiento
- Días vencidos (badge rojo, solo si aplica)
- Saldo pendiente (grande y destacado)
- Botones: Descargar PDF | Pagar ahora

## 🎯 Características Técnicas

- **Compatibilidad**: Odoo 19.0
- **Framework**: Bootstrap 5
- **Arquitectura**: Herencia de controladores y templates
- **Performance**: Agrupación en memoria (sin queries adicionales)
- **Responsive**: Mobile-first design
- **Testing**: Suite de tests automatizados incluida


Ejecutar tests:
```bash
./odoo-bin -d test_db --test-enable --stop-after-init -i portal_invoice_partner_grouping
```

## 🔄 Integración con payment_rutavity

El módulo se integra automáticamente con `payment_rutavity` si está instalado:
- Barra de resumen de pago múltiple
- Checkboxes sincronizados
- Navegación a página de pago con facturas seleccionadas

## 🎨 Personalización

### Estilos
Los estilos se encuentran en `static/src/scss/portal_styles.scss` y pueden personalizarse según necesidades.

### Filtros
Para modificar los filtros por defecto, editar el método `_get_account_searchbar_filters` en `controllers/portal.py`.


## 👥 Autor

**Rutavity**
- Website: https://www.rutavity.com
- Categoría: Rutavity/Accounting


---
