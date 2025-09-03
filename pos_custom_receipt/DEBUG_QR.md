# Guía de Depuración - Código QR en Recibo POS

## Pasos para Probar la Funcionalidad

### 1. Actualizar el Módulo
```bash
cd /home/leosecha/OdooProject
python3 odoo-bin -u pos_custom_receipt --stop-after-init
```

### 2. Verificar Configuración POS
1. Ir a **Punto de Venta > Configuración > Punto de Venta**
2. Editar la configuración del POS
3. Verificar que esté marcado: **"Usar recibo personalizado"**

### 3. Crear una Venta de Prueba
1. Abrir el POS
2. Crear una venta con productos
3. **IMPORTANTE**: Seleccionar un cliente (no usar Cliente Genérico)
4. Procesar el pago
5. Generar la factura (debe aparecer en Facturación)

### 4. Procesar Facturación Electrónica
1. Ir a **Facturación > Facturas de Cliente**
2. Buscar la factura generada desde el POS
3. **Enviar a DIAN** (debe tener estado "Aceptado")
4. Verificar que tenga CUFE/CUDE

### 5. Ver el Recibo con QR
1. Volver al POS
2. Ir a **Pedidos** y buscar la venta
3. Hacer clic en **"Reimprimir"**
4. El QR debe aparecer en la sección de facturación electrónica

## Logs de Depuración

Abrir **Herramientas de Desarrollador (F12)** > **Consola** para ver los logs:

### Logs Esperados (Éxito):
```
=== DEBUG QR: Iniciando generación de QR ===
shouldShowQRCode: true
useCustomReceipt: true  
hasElectronicInvoiceData: true
order.account_move: {id: 123, l10n_co_edi_cufe_cude_ref: "abc123...", ...}
qrContainer encontrado: true
=== DEBUG QR: Obteniendo datos del QR ===
qrData obtenido: {qr_text: "NumFac: SETP001...", qr_code_url: "https://...", ...}
=== DEBUG QR: Generando URL del QR ===
qrURL generada: /report/barcode/?barcode_type=QR&value=...
=== DEBUG QR: Imagen QR cargada correctamente ===
=== DEBUG QR: QR generado exitosamente ===
```

### Posibles Problemas y Soluciones:

#### 1. "No se debe mostrar QR"
**Causa**: No se cumplen las condiciones
**Verificar**:
- Recibo personalizado activado
- Factura asociada existe
- Empresa es colombiana (CO)
- Estado DIAN = 'invoice_accepted'

#### 2. "No se encontró contenedor QR"  
**Causa**: Template no se renderiza
**Verificar**:
- Template XML actualizado
- Módulo actualizado correctamente

#### 3. "Error al obtener datos del código QR"
**Causa**: Error en llamada RPC
**Verificar**:
- Método `get_pos_qr_code_data` existe en backend
- Factura tiene adjunto de DIAN
- XML de DIAN es válido

#### 4. "No hay datos de QR disponibles"
**Causa**: Backend retorna None
**Verificar**:
- Factura tiene `l10n_co_dian_attachment_id`
- XML contiene datos requeridos
- No hay errores en parsing XML

#### 5. "Error cargando imagen QR"
**Causa**: URL del QR inválida
**Verificar**:
- Servicio `/report/barcode/` disponible
- Datos del QR válidos
- URL correctamente formateada

## Verificación Manual del Backend

### Probar método directamente en shell:
```python
# Conectar a shell de Odoo
move_id = 123  # ID de tu factura
move = env['account.move'].browse(move_id)
qr_data = env['account.move'].get_pos_qr_code_data(move_id)
print(qr_data)
```

### Verificar datos de factura:
```python
move = env['account.move'].browse(move_id)
print(f"DIAN habilitado: {move.l10n_co_dian_is_enabled}")
print(f"CUFE: {move.l10n_co_edi_cufe_cude_ref}")
print(f"Estado DIAN: {move.l10n_co_dian_state}")
print(f"Adjunto DIAN: {bool(move.l10n_co_dian_attachment_id)}")
```

## Estructura del QR Esperada

El QR debe contener datos como:
```
NumFac: SETP001
FecFac: 2025-01-21
HorFac: 10:30:00-05:00
NitFac: 900123456
DocAdq: 123456789
ValFac: 100000.00
ValIva: 19000.00
ValOtroIm: 0.00
ValTolFac: 119000.00
CUFE: 1234567890abcdef...
QRCode: https://catalogo-vpfe.dian.gov.co/...
```

## Notas Importantes

1. **La factura DEBE estar aceptada por DIAN** para generar QR
2. **Debe existir el adjunto XML** de la DIAN
3. **El cliente no puede ser "Genérico"** para facturación electrónica
4. **La empresa debe tener configuración DIAN** completa
5. **Los logs en consola** son tu mejor herramienta de debug
