# POS - Cajeros y Vendedores

## Descripción

Este módulo extiende la configuración del Punto de Venta (POS) de Odoo 18 para permitir definir usuarios específicos que pueden actuar como cajeros y vendedores en cada POS individual.

## Características

- **Campos de Cajeros**: Selección múltiple de usuarios que pueden actuar como cajeros
- **Campos de Vendedores**: Selección múltiple de usuarios que pueden actuar como vendedores
- **Validaciones**: Verifica que los usuarios seleccionados estén activos
- **Métodos de utilidad**: Funciones para verificar roles de usuarios
- **Integración completa**: Se integra tanto en la vista del formulario de POS como en la configuración general
- **Comportamiento diferenciado en POS**: 
  - **Cajeros**: Ven el botón "Pago" y pueden procesar pagos normalmente
  - **Vendedores**: Ven el botón "Realizar pedido" que crea el pedido y limpia la vista para continuar vendiendo

## Instalación

1. Copiar el módulo a la carpeta `custom_addons`
2. Actualizar la lista de módulos en Odoo
3. Instalar el módulo "POS - Cajeros y Vendedores"
4. Reiniciar el servicio Odoo si es necesario

## Uso

### Configuración Individual del POS

1. Ir a **Punto de Venta > Configuración > Punto de Venta**
2. Abrir la configuración de un POS específico
3. En la sección de configuración, encontrarás los nuevos campos:
   - **Cajeros**: Seleccionar usuarios que pueden actuar como cajeros
   - **Vendedores**: Seleccionar usuarios que pueden actuar como vendedores

### Configuración General

1. Ir a **Punto de Venta > Configuración > Ajustes**
2. Seleccionar un POS en el campo "Point of Sale"
3. Configurar los campos de cajeros y vendedores para el POS seleccionado

## Estructura del Módulo

```
pos_cashiers_salespeople/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── pos_config.py          # Extensión del modelo pos.config
│   └── res_config_settings.py # Extensión de la configuración general
├── views/
│   └── pos_config_views.xml   # Vistas para mostrar los nuevos campos
├── static/
│   └── src/
│       └── app/
│           ├── services/
│           │   └── pos_store.js # Extensión del servicio POS
│           └── screens/
│               └── product_screen/
│                   ├── product_screen.js  # Extensión de ProductScreen
│                   └── product_screen.xml # Template modificado
└── security/
    └── ir.model.access.csv    # Permisos de acceso
```

## Campos Agregados

### En pos.config

- `cashier_user_ids` (Many2many): Lista de usuarios cajeros
- `salesperson_user_ids` (Many2many): Lista de usuarios vendedores

### En res.config.settings

- `pos_cashier_user_ids` (Many2many): Cajeros del POS seleccionado
- `pos_salesperson_user_ids` (Many2many): Vendedores del POS seleccionado

## Métodos Útiles

El módulo incluye varios métodos de utilidad en el modelo `pos.config`:

- `get_cashier_users()`: Obtiene la lista de cajeros del POS
- `get_salesperson_users()`: Obtiene la lista de vendedores del POS
- `is_user_cashier(user_id)`: Verifica si un usuario es cajero
- `is_user_salesperson(user_id)`: Verifica si un usuario es vendedor

## Validaciones

- Los usuarios seleccionados como cajeros deben estar activos
- Los usuarios seleccionados como vendedores deben estar activos
- Se muestran mensajes de error descriptivos si se seleccionan usuarios inactivos

## Compatibilidad

- **Versión de Odoo**: 18.0
- **Dependencias**: point_of_sale
- **Licencia**: OPL-1

## Notas Técnicas

- Utiliza relaciones Many2many con tablas intermedias personalizadas
- Los campos tienen dominios que filtran solo usuarios activos
- Se integra perfectamente con la interfaz existente del POS
- Incluye validaciones a nivel de modelo para mantener la integridad de los datos
- Los datos de cajeros y vendedores se cargan dinámicamente en el frontend usando el servicio ORM
- Incluye manejo robusto de errores y logs de debug para facilitar el troubleshooting

## Funcionalidades del Frontend

### Comportamiento por Rol

**Para usuarios definidos como Cajeros:**
- Ven el botón "Pago" en la pantalla de productos
- Pueden procesar pagos normalmente
- Tienen acceso completo a las funcionalidades de cobro

**Para usuarios definidos como Vendedores (sin ser cajeros):**
- Ven el botón "Realizar pedido" en lugar de "Pago"
- Al hacer clic, el pedido se envía al sistema como borrador
- La vista se limpia automáticamente para crear un nuevo pedido
- Reciben notificación de confirmación del pedido creado

### Lógica de Roles

1. Si un usuario es **solo cajero**: Ve botón "Pago"
2. Si un usuario es **solo vendedor**: Ve botón "Realizar pedido"  
3. Si un usuario es **cajero Y vendedor**: Ve botón "Pago" (cajero tiene prioridad)
4. Si un usuario **no está definido** en ningún rol: Ve botón "Pago" (comportamiento por defecto)

## Desarrollo Futuro

Este módulo está preparado para futuras extensiones que podrían incluir:
- Restricciones de acceso basadas en roles
- Reportes por cajero/vendedor
- Configuración de comisiones por vendedor
- Notificaciones automáticas a cajeros cuando se crean pedidos
- Dashboard de pedidos pendientes por vendedor

## Soporte

Para soporte técnico o consultas sobre el módulo, contactar al desarrollador:
- **Autor**: @LeonardoSepulvedaCh
- **Repositorio**: https://github.com/LeonardoSepulvedaCh
