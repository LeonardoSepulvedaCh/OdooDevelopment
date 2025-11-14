# Manual de Usuario - Módulo Helpdesk Campos Personalizados

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Configuración Inicial](#configuración-inicial)
3. [Crear un Ticket de Garantía](#crear-un-ticket-de-garantía)
4. [Campos del Ticket](#campos-del-ticket)
5. [Gestión de Despacho](#gestión-de-despacho)
6. [Adjuntos y Documentos](#adjuntos-y-documentos)
7. [Etapas del Ticket](#etapas-del-ticket)
8. [Imprimir Acta de Garantía](#imprimir-acta-de-garantía)
9. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

Este módulo extiende el sistema de Helpdesk de Odoo para gestionar tickets de garantía con campos personalizados adaptados al flujo de trabajo de Rutavity. Permite registrar información detallada sobre garantías, gestionar despachos, adjuntar documentos y generar actas de garantía.

### Características Principales

- **Campos personalizados** para identificar clientes y productos
- **Gestión de series y consecutivos** automáticos por ciudad
- **Control de despachos** (retorno y envío)
- **Adjuntos de documentos** con vista previa
- **Reporte de acta de garantía** imprimible
- **Validaciones automáticas** para asegurar datos completos

---

## Configuración Inicial

### Activar Equipo de Garantías

Para que los campos personalizados aparezcan en los tickets, es necesario marcar el equipo como "Equipo de Garantías":

1. Vaya a **Helpdesk > Configuración > Equipos**
2. Seleccione el equipo que manejará garantías
3. Marque la casilla **"Es equipo de garantías"**
4. Guarde los cambios

**Nota:** Solo los tickets asignados a equipos marcados como "Equipo de Garantías" mostrarán los campos personalizados.

---

## Crear un Ticket de Garantía

### Pasos para Crear un Nuevo Ticket

1. Vaya a **Helpdesk > Tickets > Crear**
2. Seleccione el **Equipo** (debe ser un equipo de garantías)
3. Complete los campos obligatorios:
   - **Cliente:** Seleccione el cliente desde el campo de búsqueda
   - **Serie:** Seleccione la serie correspondiente (PQRS, Ticket por ciudad, etc.)
   - **Factura:** Seleccione la factura relacionada con la garantía
4. El sistema asignará automáticamente un **número consecutivo** según la serie seleccionada
5. Complete los demás campos según sea necesario
6. Haga clic en **Guardar**

### Series Disponibles

- **PQRS:** Para peticiones, quejas, reclamos y sugerencias
- **Ticket Cúcuta:** Para tickets de la ciudad de Cúcuta
- **Ticket Medellín:** Para tickets de la ciudad de Medellín
- **Ticket Bogotá:** Para tickets de la ciudad de Bogotá
- **Ticket Bucaramanga:** Para tickets de la ciudad de Bucaramanga
- **Ticket Barranquilla:** Para tickets de la ciudad de Barranquilla
- **Ticket Cali:** Para tickets de la ciudad de Cali
- **Otro:** Para casos que no correspondan a las series anteriores

**Importante:** El número consecutivo se genera automáticamente y no se puede modificar. Cada serie tiene su propia numeración independiente.

---

## Campos del Ticket

### Información del Cliente

#### Código del Cliente (Card_Code)
- Se completa automáticamente al seleccionar el cliente
- Si el cliente tiene un código asignado, se mostrará aquí
- Puede editarse manualmente si es necesario

#### Tipo de Cliente
Seleccione el tipo de cliente:
- **Mayorista**
- **Consumidor Final**
- **Hipermercado**
- **Licitación**
- **Otro**

### Información de la Garantía

#### Factura
- **Campo obligatorio** para equipos de garantías
- Seleccione la factura relacionada con el producto en garantía
- Solo se mostrarán facturas del cliente seleccionado
- Al seleccionar una factura, se habilitará el campo de productos

#### Productos Asociados
- Aparece después de seleccionar una factura
- Muestra solo los productos que están en la factura seleccionada
- Puede seleccionar uno o varios productos usando las etiquetas
- **Validación:** Solo puede seleccionar productos que estén en la factura

#### Sucursal
- Seleccione la sucursal o almacén relacionado con el ticket
- Útil para identificar el origen o destino de los productos

#### Origen
Indique cómo se originó el ticket:
- **Rutavity:** Generado desde la plataforma Rutavity
- **Call Center:** Llamada telefónica
- **Correo:** Solicitud por correo electrónico
- **Asesor:** Gestionado por un asesor de ventas
- **Otro:** Otro origen no especificado

### Etiquetas (Tags)

Las etiquetas ayudan a categorizar el tipo de problema o solicitud. Algunas etiquetas disponibles incluyen:

- **Calidad artículo**
- **Mercancía trocada**
- **Faltantes**
- **Rayones/Golpes**
- **Funcionamiento**
- **Facturación**
- **Demora en despacho**
- **Pieza defectuosa**
- Y muchas más...

Puede seleccionar múltiples etiquetas para un mismo ticket.

---

## Gestión de Despacho

El módulo permite gestionar dos tipos de despacho:

### 1. Retorno del Cliente al Almacén

Cuando el cliente devuelve un producto para evaluación:

1. Vaya a la pestaña **"Gestión de Despacho"** en el ticket
2. Marque la casilla **"¿Hubo retorno?"**
3. Seleccione el **Medio de transporte:**
   - **RETORNO CLIENTE:** El cliente trae el producto
   - **TRANSPORTADORA:** Se usa una empresa transportadora
   - **INDEPENDIENTE:** Transporte independiente
   - **TRANSPORTE PROPIO:** Transporte de la empresa
   - **CONTRA ENTREGA:** Pago contra entrega
   - **NO APLICA:** No hay retorno

4. Si seleccionó **TRANSPORTADORA**, complete:
   - **Transportador:** Seleccione la empresa transportadora
   - **N° Guía Transportador:** Número de guía de envío
   - **Placa Vehículo:** Placa del vehículo
   - **Número Paquetes:** Cantidad de paquetes
   - **Valor Flete:** Costo del transporte
   - **Valor mercancía declarado:** Valor asegurado

**Importante:** Si usa transportadora, debe adjuntar la guía de transporte en la pestaña de Anexos.

### 2. Despacho del Almacén al Cliente

Cuando se envía el producto reparado o reemplazado al cliente:

1. En la misma pestaña **"Gestión de Despacho"**
2. Marque la casilla **"¿Fue despachado?"**
3. Seleccione el **Medio de transporte** (mismas opciones que retorno)
4. Complete los datos de transportadora si aplica (igual que en retorno)

---

## Adjuntos y Documentos

### Subir Anexos

1. Vaya a la pestaña **"Anexos"** en el ticket
2. Haga clic en **"Subir Anexos"**
3. Seleccione los archivos que desea adjuntar:
   - Imágenes (fotos del producto dañado)
   - Documentos PDF (facturas, guías de transporte)
   - Cualquier otro archivo relevante
4. Los archivos se mostrarán con vista previa

### Acta de Garantía

**Importante:** Para finalizar un ticket de garantía, debe adjuntar al menos un documento marcado como **"Acta de Garantía"**.

El sistema validará que exista este documento antes de permitir cerrar el ticket.

---

## Etapas del Ticket

### Flujo de Etapas

Los tickets de garantía siguen este flujo:

1. **Nuevo:** Ticket recién creado
2. **Pendiente de Revisión:** En revisión por el equipo
3. **Por Realizar (Despacho):** Listo para despacho
4. **Resuelto:** Ticket finalizado
5. **Rechazado:** Garantía rechazada

### Permisos de Movimiento

- **Usuarios sin permisos especiales:** Solo pueden mover tickets de "Nuevo" a "Pendiente de Revisión"
- **Usuarios con permisos:** Pueden mover tickets a cualquier etapa

Si necesita mover un ticket a etapas avanzadas, contacte al administrador del sistema para obtener los permisos necesarios.

### Cambios Automáticos

- Al mover un ticket a **"Por Realizar (Despacho)"**, el sistema crea automáticamente actividades para usuarios del almacén
- Al mover a **"Resuelto"**, se registra automáticamente la fecha y hora de finalización
- Al mover a **"Rechazado"**, se envía una notificación al canal configurado

### Tiempo de Resolución

El sistema calcula automáticamente:
- **Tiempo de resolución (horas):** Tiempo desde la creación hasta la finalización
- **Tiempo de resolución (días):** Mismo tiempo expresado en días

Estos campos se actualizan automáticamente cuando se cierra el ticket.

---

## Imprimir Acta de Garantía

### Cómo Imprimir el Acta

1. Abra el ticket de garantía
2. En la parte superior del formulario, haga clic en el botón **"Imprimir Acta"** (icono de impresora)
3. Se abrirá una nueva ventana con el acta de garantía en formato PDF
4. Use el botón de imprimir del navegador para imprimir o guardar el documento

### Información del Acta

El acta incluye:
- Datos del cliente
- Información del ticket (serie y consecutivo)
- Productos asociados
- Fechas de inicio y finalización
- Comentarios del área de garantías
- Y otra información relevante

**Nombre del archivo:** El PDF se genera con el nombre `Acta_Garantia_[SERIE]_[CONSECUTIVO]`

---

## Comentario del Área de Garantías

En la pestaña **"Comentario del área de garantías"** puede agregar observaciones internas sobre el proceso de garantía. Este campo es útil para:
- Documentar el diagnóstico del problema
- Registrar acciones tomadas
- Agregar notas para otros miembros del equipo
- Dejar constancia de acuerdos con el cliente

---

## Preguntas Frecuentes

### ¿Por qué no veo los campos personalizados en mi ticket?

**Respuesta:** Verifique que:
1. El ticket esté asignado a un equipo marcado como "Equipo de Garantías"
2. Si no ve el equipo marcado, contacte al administrador

### ¿Puedo cambiar el número consecutivo de un ticket?

**Respuesta:** No. El número consecutivo se genera automáticamente y no se puede modificar. Si cambia la serie del ticket, se generará un nuevo consecutivo para la nueva serie.

### ¿Qué pasa si cambio la serie de un ticket?

**Respuesta:** El sistema generará un nuevo número consecutivo para la nueva serie. El número anterior de la serie antigua no se reutilizará.

### ¿Por qué no puedo finalizar el ticket?

**Respuesta:** Verifique que:
1. Haya adjuntado al menos un documento marcado como "Acta de Garantía"
2. Todos los campos obligatorios estén completos (Serie, Factura)
3. Tenga los permisos necesarios para finalizar tickets

### ¿Cómo sé qué productos puedo seleccionar?

**Respuesta:** Solo puede seleccionar productos que estén en la factura relacionada. Si no ve el producto que necesita, verifique que esté en la factura seleccionada.

### ¿Qué debo hacer si uso transportadora?

**Respuesta:** 
1. Complete todos los campos de transportadora (guía, placa, paquetes, valores)
2. **Adjunte la guía de transporte** en la pestaña de Anexos
3. El sistema mostrará un aviso recordándole adjuntar la guía

### ¿Puedo reabrir un ticket cerrado?

**Respuesta:** Sí. Si mueve un ticket de "Resuelto" a otra etapa, se limpiará la fecha de finalización y el ticket se considerará reabierto.

### ¿Cómo se calcula el tiempo de resolución?

**Respuesta:** Se calcula automáticamente desde la fecha de creación del ticket hasta la fecha de finalización (cuando se mueve a "Resuelto"). Se muestra tanto en horas como en días.

### ¿Qué son las etiquetas y para qué sirven?

**Respuesta:** Las etiquetas ayudan a categorizar y filtrar tickets. Permiten identificar rápidamente el tipo de problema (calidad, funcionamiento, facturación, etc.) y facilitan la búsqueda y reportes.

---

## Notas Importantes

- Los campos marcados con asterisco (*) son **obligatorios** para tickets de garantías
- El sistema realiza validaciones automáticas para asegurar la integridad de los datos
- Los números consecutivos son únicos e irrecuperables una vez asignados
- Siempre adjunte la guía de transporte cuando use transportadora
- El acta de garantía es obligatoria para finalizar tickets

---

## Soporte

Si tiene dudas o problemas con el módulo, contacte al administrador del sistema o al equipo de soporte técnico.

---

**Versión del Manual:** 1.0  
**Fecha de Actualización:** 2024  
**Módulo:** Helpdesk - Campos Personalizados v1.0.0



