# Módulo Cliente POS

## Descripción
Este módulo agrega un campo adicional al modelo de contactos de Odoo para determinar si un cliente es visible en el Punto de Venta (POS).

## Funcionalidades
- Agrega un campo booleano `pos_customer` al modelo `res.partner`
- Solo los contactos con `pos_customer = True` se muestran en el POS
- El campo aparece en el formulario de contacto después del campo email
- Filtra automáticamente los clientes en el POS usando JavaScript
- Incluye logs de debug para facilitar la solución de problemas

## Instalación
1. Copiar el módulo a la carpeta `custom_addons`
2. Actualizar la lista de módulos en Odoo
3. Instalar el módulo "Cliente POS"
4. Reiniciar el servicio Odoo
5. Limpiar la caché del navegador

## Uso
1. Ir a Contactos > Contactos
2. Editar un contacto
3. Marcar/desmarcar el campo "Cliente POS"
4. Solo los contactos marcados aparecerán en el POS

## Archivos del módulo
- `models/res_partner.py`: Extensión del modelo de contactos con campo pos_customer
- `views/res_partner_view.xml`: Vista del formulario de contacto
- `static/src/js/pos_partner_filter.js`: Filtro JavaScript para el POS (Odoo 18)
- `data/pos_config_data.xml`: Configuración del POS para incluir el campo
- `security/ir.model.access.csv`: Permisos de seguridad
- `test_pos_partner_visibility.py`: Script de prueba del módulo
- `INSTALACION.md`: Instrucciones detalladas de instalación

## Notas técnicas
- Compatible con Odoo 18.0
- Depende de los módulos: point_of_sale, sale, contacts
- El filtro se aplica tanto en la carga inicial como en la búsqueda de clientes
- Utiliza la nueva arquitectura de Odoo 18 con PosGlobalState y patch
- Incluye logs de debug para facilitar la solución de problemas
- El campo pos_customer tiene índice para mejor rendimiento

## Solución de problemas
- Verificar que el JavaScript se cargue en la consola del navegador
- Revisar los logs de debug del módulo
- Limpiar la caché del navegador si es necesario
- Verificar permisos de seguridad

## Verificación
Para verificar que el módulo funciona:
1. Abrir el POS
2. Abrir la consola del navegador (F12)
3. Deberías ver los mensajes de debug del módulo
4. Solo los contactos marcados como "Cliente POS" aparecerán en el POS
