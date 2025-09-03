# POS - Recibo Personalizado

## Descripción

Módulo para Odoo 18 que permite personalizar completamente el recibo de venta del Punto de Venta (POS). Este módulo extiende la funcionalidad estándar del POS agregando elementos personalizados, estilos mejorados y información adicional relevante para el negocio.

## Características

### ✨ Personalización Visual
- **Encabezado personalizado** con gradientes y diseño atractivo
- **Pie de página mejorado** con información de contacto y redes sociales
- **Estilos CSS modernos** con soporte para temas claros y oscuros
- **Optimización para impresión** con estilos específicos para papel

### 📋 Información Adicional
- Horarios de atención del negocio
- Información de redes sociales (Facebook, Instagram, WhatsApp)
- Políticas de devolución y garantía
- Mensajes promocionales dinámicos
- Sistema de puntos de fidelidad (ejemplo)

### 🎨 Elementos Personalizables
- Colores y gradientes del encabezado
- Información de contacto y redes sociales
- Mensajes promocionales
- Políticas de la empresa
- Estilos de los totales y líneas de pago

## Instalación

1. Copia el módulo en la carpeta `custom_addons` de tu instalación de Odoo
2. Actualiza la lista de aplicaciones
3. Instala el módulo "POS - Recibo Personalizado"
4. Ve a **Configuración > Aplicaciones POS > [Tu POS] > Configuración**
5. Activa la opción **"Usar recibo personalizado"**
6. Reinicia el servicio de Odoo para cargar los assets

```bash
# Actualizar módulos
./odoo-bin -u pos_custom_receipt -d tu_base_de_datos

# O instalar desde la interfaz web
# Apps > Update Apps List > Buscar "POS - Recibo Personalizado" > Install
```

## Configuración

### Activar el Recibo Personalizado

1. Ve a **Punto de Venta > Configuración > Configuración del Punto de Venta**
2. Selecciona tu configuración de POS
3. En la sección **"Otras Configuraciones"**, activa **"Usar recibo personalizado"**
4. Guarda los cambios

**Importante:** El recibo personalizado solo se aplicará cuando esta opción esté activada. Si está desactivada, se usará el recibo estándar de Odoo.

### Personalización Básica

Para personalizar los elementos del recibo, edita los siguientes archivos:

#### 1. Contenido y Estructura (`order_receipt.xml`)
```xml
<!-- Cambiar información de redes sociales -->
<div>Facebook: @TuEmpresa | Instagram: @TuEmpresa</div>
<div>WhatsApp: +57 300 123 4567</div>

<!-- Modificar horarios de atención -->
<div>Lunes a Viernes: 8:00 AM - 6:00 PM</div>
<div>Sábados: 8:00 AM - 2:00 PM</div>
```

#### 2. Estilos Visuales (`order_receipt.scss`)
```scss
// Cambiar colores del encabezado
.custom-receipt-header {
    background: linear-gradient(135deg, #tu-color-1 0%, #tu-color-2 100%);
}

// Personalizar colores del total
.pos-receipt-amount.receipt-total {
    background: linear-gradient(135deg, #tu-color-verde 0%, #tu-color-verde-claro 100%);
}
```

#### 3. Lógica Personalizada (`order_receipt.js`)
```javascript
// Modificar cálculo de puntos de fidelidad
getLoyaltyPoints() {
    const total = this.order.get_total_with_tax();
    return Math.floor(total / 5000); // 1 punto cada $5000
}

// Personalizar mensajes promocionales
getPromotionalMessage() {
    const total = this.order.get_total_with_tax();
    if (total > 200000) {
        return "¡Obtén 15% de descuento en tu próxima compra!";
    }
    // ... más condiciones
}
```

## Estructura del Módulo

```
pos_custom_receipt/
├── __init__.py
├── __manifest__.py
├── README.md
└── static/
    └── src/
        └── app/
            └── screens/
                └── receipt_screen/
                    └── receipt/
                        ├── order_receipt.js    # Lógica personalizada
                        ├── order_receipt.xml   # Template HTML
                        └── order_receipt.scss  # Estilos CSS
```

## Personalización Avanzada

### Agregar Nuevos Elementos

1. **En el XML**: Usar XPath para insertar contenido
```xml
<xpath expr="//div[@class='before-footer']" position="inside">
    <div class="mi-elemento-personalizado">
        <!-- Tu contenido aquí -->
    </div>
</xpath>
```

2. **En el JavaScript**: Agregar nuevos métodos
```javascript
// Método personalizado para calcular descuentos
getCustomDiscount() {
    // Tu lógica aquí
    return discount;
}
```

3. **En el SCSS**: Definir estilos para nuevos elementos
```scss
.mi-elemento-personalizado {
    // Tus estilos aquí
}
```

### Modificar Elementos Existentes

Para cambiar elementos del recibo original, usa XPath:

```xml
<!-- Cambiar texto existente -->
<xpath expr="//span[text()='Total']" position="replace">
    <span>Total a Pagar</span>
</xpath>

<!-- Agregar atributos -->
<xpath expr="//div[@class='pos-receipt-amount']" position="attributes">
    <attribute name="style">background-color: #f0f0f0;</attribute>
</xpath>
```

## Solución de Problemas

### El módulo no se carga
1. Verifica que la estructura de carpetas sea correcta
2. Asegúrate de que el archivo `__manifest__.py` tenga la configuración de assets
3. Reinicia el servicio de Odoo

### Error "Element cannot be located in element tree"
Este error ocurre cuando hay problemas con la herencia de templates. Asegúrate de que:
1. Las condiciones `t-if` estén dentro de los elementos `xpath`, no fuera
2. Los selectores xpath sean correctos y existan en el template padre
3. El módulo esté correctamente actualizado

### Los estilos no se aplican
1. Verifica que el archivo SCSS esté incluido en los assets
2. Limpia la caché del navegador
3. Actualiza el módulo con `-u pos_custom_receipt`
4. Asegúrate de que la opción "Usar recibo personalizado" esté activada

### Los cambios no aparecen
1. Actualiza la página del POS (F5)
2. Verifica que la opción "Usar recibo personalizado" esté activada en la configuración del POS
3. Verifica que no haya errores en la consola del navegador
4. Comprueba los logs de Odoo para errores

## Contribuir

Si encuentras bugs o tienes sugerencias de mejora:

1. Crea un issue en el repositorio
2. Envía un pull request con tus cambios
3. Asegúrate de probar tus cambios antes de enviarlos

## Licencia

Este módulo está licenciado bajo OPL-1 (Odoo Proprietary License).

## Autor

**@LeonardoSepulvedaCh**
- GitHub: https://github.com/LeonardoSepulvedaCh

---

¡Disfruta personalizando tus recibos del POS! 🎨✨
