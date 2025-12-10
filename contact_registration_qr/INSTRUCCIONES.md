# Módulo: Registro de Contactos mediante QR

## 📋 Descripción
Módulo para Odoo 19 que permite registrar contactos (clientes) mediante el escaneo de un código QR. Los usuarios son dirigidos a un formulario web público donde completan su información.

## 🔧 Requisitos Previos

### Dependencias de Python
El módulo requiere la librería `qrcode` para generar los códigos QR:

```bash
pip install qrcode[pil]
```

### Módulos de Odoo
- `base` (contactos)
- `l10n_co` (localización colombiana)

## 📦 Instalación

1. **Copiar el módulo** a tu directorio de addons de Odoo:
   ```bash
   cp -r contact_registration_qr /ruta/a/odoo/addons/
   ```

2. **Reiniciar el servidor de Odoo**:
   ```bash
   ./odoo-bin -c /ruta/a/odoo.conf
   ```

3. **Actualizar lista de aplicaciones**:
   - Ir a Aplicaciones
   - Hacer clic en "Actualizar lista de aplicaciones"

4. **Instalar el módulo**:
   - Buscar "Registro de Contactos mediante QR"
   - Hacer clic en "Instalar"

## 🚀 Uso

### 1. Crear un Código QR

1. Ve al menú **"Registro QR" > "Códigos QR"**
2. Haz clic en **"Crear"**
3. Asigna un nombre descriptivo (ej. "Campaña Navidad 2025", "Evento Expo 2025")
4. El sistema generará automáticamente:
   - Un token único
   - Una URL de registro
   - Un código QR

### 2. Descargar y Compartir el QR

1. En la vista del registro, verás el código QR generado
2. **Descarga la imagen** del QR haciendo clic derecho y "Guardar imagen"
3. **Imprime o comparte** el código en:
   - Material publicitario
   - Stands de eventos
   - Redes sociales
   - Folletos
   - Pantallas digitales

### 3. Usuarios Registrándose

1. Los usuarios **escanean el QR** con su teléfono
2. Son dirigidos a un **formulario web público**
3. Completan los campos:
   - ✅ Nombre completo (obligatorio)
   - ✅ Tipo de documento (obligatorio)
   - ✅ Número de identificación (obligatorio)
   - ✅ Correo electrónico (obligatorio)
   - 📍 Dirección
   - 📍 Ciudad
   - 📍 País
   - 📍 Código postal
   - 📋 Obligaciones fiscales
4. Envían el formulario
5. **El contacto se crea automáticamente** en Odoo

### 4. Visualizar Registros

Desde el registro QR:
- Haz clic en el botón **"Contactos"** (esquina superior derecha)
- Verás todos los contactos que se registraron usando ese QR específico

En el listado de contactos:
- Cada contacto mostrará el campo "Registrado desde QR"
- Puedes filtrar contactos por origen de registro

## 🌐 URLs Disponibles

### URL con Token Específico
Cada registro QR tiene su propia URL única:
```
https://tu-dominio.com/contact/register/TOKEN_UNICO
```

### URL Genérica
También puedes usar una URL genérica sin tracking:
```
https://tu-dominio.com/contact/register/generic
```

Esta URL genérica también puede ser convertida en QR para usos donde no necesitas rastrear el origen.

## 🎯 Casos de Uso

- **Eventos y ferias**: Genera un QR por evento para trackear leads
- **Campañas de marketing**: Un QR diferente por campaña
- **Puntos de venta**: QR en el mostrador para registro rápido
- **Material impreso**: Incluye el QR en folletos, tarjetas, carteles
- **Restaurantes/Tiendas**: Registro de clientes para programas de fidelización
- **Formularios de contacto**: Alternativa moderna al formulario en papel

## 🔒 Seguridad

- El formulario es **público** (no requiere login)
- Los datos se validan antes de crear el contacto
- Solo usuarios con permisos pueden:
  - Ver los registros QR (usuarios internos)
  - Crear/editar registros QR (ventas)
  - Eliminar registros QR (administradores)

## 📊 Permisos

| Grupo | Leer | Escribir | Crear | Eliminar |
|-------|------|----------|-------|----------|
| Usuarios internos | ✅ | ❌ | ❌ | ❌ |
| Ventas | ✅ | ✅ | ✅ | ❌ |
| Administradores | ✅ | ✅ | ✅ | ✅ |

## ⚙️ Configuración Avanzada

### Personalizar el Formulario
Edita `views/registration_form_template.xml` para:
- Agregar o quitar campos
- Cambiar estilos CSS
- Modificar mensajes

### Personalizar el Controlador
Edita `controllers/main.py` para:
- Agregar validaciones personalizadas
- Enviar emails de confirmación
- Integrar con otros sistemas
- Agregar lógica de negocio adicional

## 🐛 Solución de Problemas

### Error: "Module not found: qrcode"
```bash
pip install qrcode[pil]
```

### El QR no se genera
Verifica que:
- La librería `qrcode` esté instalada
- El parámetro `web.base.url` esté configurado correctamente
- El módulo esté correctamente instalado

### Los contactos no se crean
Revisa:
- Permisos del usuario público en `res.partner`
- Logs de Odoo para ver errores específicos
- Configuración de CSRF

### El formulario no se muestra correctamente
- Limpia la caché del navegador
- Verifica que el módulo `web` esté actualizado
- Revisa que Bootstrap esté cargado (incluido en `web.layout`)

## 📝 Notas

- Los tokens son generados automáticamente usando `secrets.token_urlsafe()` (seguro)
- Los QR se regeneran automáticamente si cambia la URL base
- Los contactos duplicados deben manejarse a nivel de Odoo (reglas de duplicados)
- El campo de obligaciones fiscales es específico para Colombia

## 🆘 Soporte

Para problemas o consultas:
1. Revisa los logs de Odoo
2. Verifica la configuración del módulo
3. Consulta la documentación oficial de Odoo 19

## 📄 Licencia

LGPL-3

