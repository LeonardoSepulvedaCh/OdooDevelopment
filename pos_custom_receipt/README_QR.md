# Funcionalidad de Código QR para Facturación Electrónica

## Descripción

Esta funcionalidad implementa la generación y visualización de códigos QR en los recibos del POS para facturas con facturación electrónica colombiana (DIAN) activa.

## Características

- **Generación automática de QR**: El código QR se genera automáticamente cuando existe una factura asociada con estado 'invoice_accepted' en el DIAN.
- **Datos del QR**: El QR contiene los mismos datos que se utilizan en las facturas electrónicas oficiales según la normativa colombiana.
- **Visualización dinámica**: El QR se genera dinámicamente en el frontend usando JavaScript.
- **Estilos personalizados**: Incluye estilos CSS específicos para la visualización del QR en el recibo.

## Componentes Implementados

### 1. Backend (`models/account_move.py`)

#### Método `_get_pos_qr_code_data()`
Extrae los datos del XML de la DIAN y genera la información necesaria para el código QR:

```python
def _get_pos_qr_code_data(self):
    """
    Genera los datos del código QR para el recibo del POS
    basado en la lógica de facturación electrónica colombiana
    """
```

**Datos incluidos en el QR:**
- NumFac: Número de factura
- FecFac: Fecha de factura
- HorFac: Hora de factura
- NitFac: NIT del facturador
- DocAdq: Documento del adquiriente
- ValFac: Valor de la factura
- ValIva: Valor del IVA
- ValOtroIm: Otros impuestos
- ValTolFac: Valor total
- CUFE: Código único de factura electrónica
- QRCode: URL del QR de la DIAN

### 2. Frontend (`static/src/app/screens/receipt_screen/receipt/order_receipt.js`)

#### Métodos implementados:

- `getQRCodeData()`: Obtiene los datos del QR desde el backend
- `getQRCodeURL()`: Genera la URL del código QR usando el servicio de reportes
- `shouldShowQRCode()`: Determina si debe mostrar el código QR
- `generateQRCode()`: Genera dinámicamente el código QR en el DOM

### 3. Template (`static/src/app/screens/receipt_screen/receipt/order_receipt.xml`)

Agrega una sección específica para el código QR:

```xml
<div class="qr-code-section text-center mb-3">
    <div class="fw-bold mb-2">Representación Gráfica</div>
    <div class="qr-code-container" t-att-data-invoice-id="order.account_move.id">
        <div class="qr-loading">Generando código QR...</div>
    </div>
</div>
```

### 4. Estilos (`static/src/app/screens/receipt_screen/receipt/order_receipt.scss`)

Incluye estilos específicos para:
- Contenedor del código QR
- Imagen del QR con bordes y sombras
- Estados de carga
- Información adicional
- Estilos para impresión

## Condiciones de Activación

El código QR se muestra únicamente cuando se cumplen todas estas condiciones:

1. ✅ El recibo personalizado está habilitado (`order.config.use_custom_receipt`)
2. ✅ Existe una factura asociada (`order.account_move`)
3. ✅ La factura tiene CUFE/CUDE (`order.account_move.l10n_co_edi_cufe_cude_ref`)
4. ✅ La empresa es colombiana (`order.company.country_id.code == 'CO'`)
5. ✅ El estado de la factura es 'invoice_accepted' (`order.account_move.l10n_co_dian_state`)
6. ✅ Existe adjunto de la DIAN (`order.account_move.l10n_co_dian_attachment_id`)

## Flujo de Funcionamiento

1. **Verificación inicial**: Se verifica si se cumplen las condiciones para mostrar el QR
2. **Montaje del componente**: Al montar el componente, se ejecuta `generateQRCode()`
3. **Llamada al backend**: Se obtienen los datos del QR desde el método `_get_pos_qr_code_data()`
4. **Procesamiento de datos**: Se extrae la información del XML de la DIAN
5. **Generación del QR**: Se crea la URL del código QR usando el servicio de reportes
6. **Visualización**: Se inserta dinámicamente la imagen del QR en el DOM

## Manejo de Errores

- Si no se pueden obtener los datos del QR, el contenedor se oculta
- Si hay errores en la generación, se muestra un mensaje alternativo
- Los errores se registran en la consola para debugging

## Compatibilidad

- ✅ Compatible con Odoo 18
- ✅ Funciona con el módulo `l10n_co_dian`
- ✅ Integrado con el sistema de reportes de Odoo
- ✅ Optimizado para impresión

## Notas Técnicas

- El QR se genera usando el endpoint `/report/barcode/` de Odoo
- Los datos se extraen del XML UBL almacenado en el adjunto de la DIAN
- Se utiliza la misma lógica que en `enterprise/l10n_co_dian/models/account_move.py`
- El componente es asíncrono para no bloquear la UI durante la generación
