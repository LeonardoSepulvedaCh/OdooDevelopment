# Colombia - Medios Magnéticos

## Descripción

Módulo para la gestión de **Medios Magnéticos** e **Informes de Exógenas** según normativa DIAN de Colombia para Odoo v19.

Este módulo extiende la funcionalidad de contactos (`res.partner`) para organizar y gestionar la información tributaria requerida en los reportes de exógenas colombianos.

## Características

### ✅ Versión 1.0.0 - Reorganización de Vista

- **Pestaña "Medios Magnéticos"**: Nueva pestaña como primera posición en el formulario de contactos
- **Campos de Nombres y Apellidos**: Integración con el módulo `contacts_name_split`
  - Primer Nombre (obligatorio)
  - Segundo Nombre
  - Primer Apellido (obligatorio)
  - Segundo Apellido
- **Estructura preparada**: Grupos y secciones listas para agregar campos tributarios progresivamente

### 🔄 Próximas Versiones

- Campos tributarios colombianos (Régimen tributario, Actividad económica, etc.)
- Modelos de soporte para datos maestros
- Generador de reportes de exógenas
- Exportación en formatos DIAN

## Dependencias

- `base`: Módulo base de Odoo
- `contacts`: Gestión de contactos
- `account`: Contabilidad
- `l10n_co`: Localización colombiana base
- `l10n_latam_base`: Base de localización LATAM
- `contacts_name_split`: Gestión de nombres y apellidos separados

## Instalación

1. Copiar el módulo en la carpeta `custom_addons/universal_addons/`
2. Actualizar la lista de módulos
3. Instalar el módulo `Colombia - Medios Magnéticos`

## Uso

1. Ir a **Contactos**
2. Abrir o crear un contacto
3. La pestaña **"Medios Magnéticos"** aparecerá como primera pestaña del formulario
4. Completar los campos de nombres y apellidos (obligatorios)

## Compatibilidad

- Odoo v19.0
- Multicompañía
- Compatible con localización colombiana

## Autor

**Rutavity**  
https://www.rutavity.com

## Licencia

OPL-1 (Odoo Proprietary License v1.0)

## Changelog

### [1.0.0] - 2025-01-07

#### ✨ Características Iniciales
- Creación del módulo base
- Reorganización de vista de contactos
- Pestaña "Medios Magnéticos" como primera pestaña
- Integración con campos de nombres y apellidos
- Estructura preparada para expansión futura

---

**Nota**: Este módulo está en desarrollo activo. Los campos tributarios y funcionalidades de reportes se agregarán progresivamente.

