# Prueba Rápida del QR - POS Custom Receipt

## ✅ Cambios Implementados

1. **Backend simplificado**: Ahora usa directamente los métodos existentes de DIAN
2. **Frontend optimizado**: Usa la URL del barcode que viene del backend
3. **Misma lógica que facturas**: Exactamente igual que el módulo base

## 🚀 Pasos para Probar

### 1. Actualizar Módulo
```bash
cd /home/leosecha/OdooProject
python3 odoo-bin -u pos_custom_receipt --stop-after-init
```

### 2. Probar Backend (Opcional)
```bash
# En shell de Odoo
python3 odoo-bin shell -d tu_database --addons-path=addons,enterprise,custom_addons

# Ejecutar en el shell:
exec(open('custom_addons/pos_custom_receipt/test_qr.py').read())
```

### 3. Probar en POS
1. **Crear venta en POS** con cliente específico
2. **Generar factura** desde el POS
3. **Ir a Facturación** > Buscar la factura
4. **Enviar a DIAN** y esperar estado "Aceptado"
5. **Volver al POS** > Pedidos > Reimprimir
6. **Abrir F12** para ver logs de debugging

## 📋 Logs Esperados

Con los cambios actuales, deberías ver:

```
=== DEBUG QR: Iniciando generación de QR ===
shouldShowQRCode: true
useCustomReceipt: true
hasElectronicInvoiceData: true
order.account_move: {id: 123, l10n_co_edi_cufe_cude_ref: "abc123...", ...}
qrContainer encontrado: true
=== DEBUG QR: Obteniendo datos del QR ===
qrData obtenido: {
  qr_text: "NumFac: SETP001...",
  barcode_src: "/report/barcode/?barcode_type=QR&value=...",
  cufe_cude: "abc123...",
  invoice_name: "SETP001",
  signing_datetime: "2025-01-21 14:35:12"
}
=== DEBUG QR: Generando URL del QR ===
qrURL generada: /report/barcode/?barcode_type=QR&value=...
=== DEBUG QR: Imagen QR cargada correctamente ===
=== DEBUG QR: QR generado exitosamente ===
```

## 🔧 Diferencias Clave

### Antes:
- Método complejo que parseaba XML manualmente
- Generaba URL del QR desde cero
- Podía tener inconsistencias con facturas oficiales

### Ahora:
- Usa métodos existentes del módulo `l10n_co_dian`
- Obtiene URL del barcode ya generada
- **100% consistente con facturas oficiales**

## ❌ Si Sigue Sin Funcionar

### 1. Verificar que la factura tenga QR en PDF
- Ir a la factura en Facturación
- Descargar PDF
- Verificar que tenga QR visible

### 2. Verificar datos en consola
```javascript
// En consola del navegador (F12)
// Cuando esté en el recibo del POS
console.log('Order:', pos.selectedOrder);
console.log('Account Move:', pos.selectedOrder.account_move);
```

### 3. Verificar método backend
```python
# En shell de Odoo
move = env['account.move'].browse(MOVE_ID)  # Reemplazar MOVE_ID
qr_data = env['account.move'].get_pos_qr_code_data(move.id)
print(qr_data)
```

## 📱 Resultado Esperado

El recibo del POS debe mostrar:
- ✅ Sección "Representación Gráfica"  
- ✅ Código QR idéntico al de la factura PDF
- ✅ Información del CUFE
- ✅ Mensaje "Consulte en www.dian.gov.co"

## 🐛 Debugging

Si el QR no aparece, revisar en orden:
1. ¿Está activado el recibo personalizado?
2. ¿La venta tiene factura asociada?
3. ¿La factura está aceptada por DIAN?
4. ¿Los logs muestran datos del QR?
5. ¿La URL del barcode es válida?

**La clave es que ahora usa exactamente la misma lógica que las facturas oficiales** 🎯
