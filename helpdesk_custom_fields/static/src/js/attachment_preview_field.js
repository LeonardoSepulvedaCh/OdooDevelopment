/** @odoo-module **/

import { Component, onWillDestroy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { FileViewer } from "@web/core/file_viewer/file_viewer";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FileInput } from "@web/core/file_input/file_input";
import { useX2ManyCrud } from "@web/views/fields/relational_utils";
import { _t } from "@web/core/l10n/translation";

export class AttachmentPreviewField extends Component {
    static template = "helpdesk_custom_fields.AttachmentPreviewField";
    static components = {
        FileInput,
    };
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.operations = useX2ManyCrud(() => this.props.record.data[this.props.name], true);
        
        // ID único para el FileViewer
        this.fileViewerId = `attachment_preview_${Math.random().toString(36).substring(7)}`;
        
        // Información del modelo y registro actual para FileInput
        this.resModel = this.props.record.resModel;
        this.resId = this.props.record.resId || false;
        
        // Asegurar que se cierre el visor cuando el componente se destruya
        onWillDestroy(() => {
            this.closeFileViewer();
        });
    }
    
    closeFileViewer() {
        if (registry.category("main_components").contains(this.fileViewerId)) {
            registry.category("main_components").remove(this.fileViewerId);
        }
    }

    get uploadText() {
        return this.props.record.fields[this.props.name].string;
    }

    get files() {
        return this.props.record.data[this.props.name].records.map((record) => {
            const data = record.data;
            const mimetype = data.mimetype || '';
            const fileName = data.name || 'Sin nombre';
            
            return {
                id: record.resId,
                name: fileName,
                mimetype: mimetype,
                create_date: data.create_date,
                create_uid: data.create_uid,
                // Propiedades para el FileViewer
                isViewable: this.isFileViewable(mimetype),
                isPdf: this.isPdf(mimetype),
                isImage: this.isImage(mimetype),
                isText: this.isText(mimetype),
                isVideo: this.isVideo(mimetype),
                downloadUrl: `/web/content/${record.resId}?download=true`,
                defaultSource: this.getFileSource(record.resId, mimetype),
            };
        });
    }

    getFileSource(id, mimetype) {
        return this.isImage(mimetype) ? `/web/image/${id}` : `/web/content/${id}`;
    }

    isImage(mimetype) {
        return mimetype && mimetype.startsWith('image/');
    }

    isText(mimetype) {
        return mimetype && mimetype.startsWith('text/');
    }

    isVideo(mimetype) {
        return mimetype && mimetype.startsWith('video/');
    }

    isPdf(mimetype) {
        return mimetype === 'application/pdf';
    }

    isFileViewable(mimetype) {
        return this.isImage(mimetype) || this.isPdf(mimetype) || this.isText(mimetype) || this.isVideo(mimetype);
    }

    getExtension(file) {
        return file.name ? file.name.split('.').pop().toUpperCase() : '';
    }
    
    getNameWithoutExtension(file) {
        if (!file.name) return '';
        const lastDotIndex = file.name.lastIndexOf('.');
        return lastDotIndex > 0 ? file.name.substring(0, lastDotIndex) : file.name;
    }
    
    getUserName(file) {
        if (!file.create_uid) {
            return '';
        }
        
        // Formato array [id, nombre] - el más común en Odoo
        if (Array.isArray(file.create_uid) && file.create_uid.length > 1) {
            return file.create_uid[1];
        }
        
        // Formato objeto {id: X, display_name: 'nombre'}
        if (typeof file.create_uid === 'object' && file.create_uid.display_name) {
            return file.create_uid.display_name;
        }
        
        // Formato número (solo ID)
        if (typeof file.create_uid === 'number') {
            return `Usuario #${file.create_uid}`;
        }
        
        return '';
    }
    
    getFormattedDate(file) {
        // Formatear la fecha de creación de forma amigable
        if (!file.create_date) return '';
        
        try {
            const date = new Date(file.create_date);
            const now = new Date();
            const diffTime = Math.abs(now - date);
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) {
                return _t("Hoy");
            } else if (diffDays === 1) {
                return _t("Ayer");
            } else if (diffDays < 7) {
                return _t("Hace ") + diffDays + _t(" días");
            } else {
                // Formato: DD/MM/YYYY
                const day = date.getDate().toString().padStart(2, '0');
                const month = (date.getMonth() + 1).toString().padStart(2, '0');
                const year = date.getFullYear();
                return `${day}/${month}/${year}`;
            }
        } catch (error) {
            return '';
        }
    }

    getFileIcon(mimetype) {
        if (!mimetype) return 'fa-file-o';
        
        if (this.isImage(mimetype)) return 'fa-file-image-o';
        if (this.isPdf(mimetype)) return 'fa-file-pdf-o';
        if (this.isText(mimetype)) return 'fa-file-text-o';
        if (this.isVideo(mimetype)) return 'fa-file-video-o';
        if (mimetype.includes('word')) return 'fa-file-word-o';
        if (mimetype.includes('excel') || mimetype.includes('spreadsheet')) return 'fa-file-excel-o';
        
        return 'fa-file-o';
    }

    async onFileUploaded(files) {
        // Validar que el registro esté guardado
        if (!this.resId) {
            this.notification.add(_t("Por favor, guarda el registro antes de subir archivos."), {
                title: _t("Advertencia"),
                type: "warning",
            });
            return;
        }
        
        for (const file of files) {
            if (file.error) {
                this.notification.add(file.error, {
                    title: _t("Error al subir"),
                    type: "danger",
                });
                return;
            }
            
            try {
                // Agregar el attachment al campo many2many
                await this.operations.saveRecord([file.id]);
            } catch (error) {
                console.error("Error al guardar el archivo:", error);
                this.notification.add(_t("Error al agregar el archivo al registro"), {
                    title: _t("Error"),
                    type: "danger",
                });
            }
        }
        
        // Mostrar mensaje de éxito
        this.notification.add(_t("Archivo(s) subido(s) exitosamente"), {
            type: "success",
        });
    }

    async onFileRemove(deleteId) {
        const record = this.props.record.data[this.props.name].records.find(
            (record) => record.resId === deleteId
        );
        this.operations.removeRecord(record);
    }
    
    async onFileRename(fileId, currentName) {
        const lastDotIndex = currentName.lastIndexOf('.');
        const nameWithoutExt = lastDotIndex > 0 ? currentName.substring(0, lastDotIndex) : currentName;
        const extension = lastDotIndex > 0 ? currentName.substring(lastDotIndex) : '';
        
        const newName = window.prompt(_t("Nuevo nombre del archivo:"), nameWithoutExt);
        
        if (!newName || newName.trim() === '' || newName.trim() === nameWithoutExt) {
            return;
        }
        
        const finalName = newName.trim() + extension;
        
        try {
            await this.orm.write('ir.attachment', [fileId], { name: finalName });
            
            const record = this.props.record.data[this.props.name].records.find(
                (record) => record.resId === fileId
            );
            
            if (record) {
                await record.update({ name: finalName });
            }
            
            this.notification.add(_t("Nombre actualizado a: ") + finalName, {
                type: "success",
            });
        } catch (error) {
            this.notification.add(_t("Error al actualizar el nombre del archivo"), {
                title: _t("Error"),
                type: "danger",
            });
        }
    }

    onFileClick(file) {
        if (!file.isViewable) {
            window.location.href = file.downloadUrl;
            return;
        }
        
        this.closeFileViewer();
        
        const viewableFiles = this.files.filter(f => f.isViewable);
        const startIndex = viewableFiles.findIndex(f => f.id === file.id);
        
        if (startIndex === -1) return;
        
        registry.category("main_components").add(this.fileViewerId, {
            Component: FileViewer,
            props: {
                files: viewableFiles,
                startIndex: startIndex,
                close: () => this.closeFileViewer(),
            },
        });
    }
}

export const attachmentPreviewField = {
    component: AttachmentPreviewField,
    supportedTypes: ["many2many"],
    relatedFields: [
        { name: "name", type: "char" },
        { name: "mimetype", type: "char" },
        { name: "create_date", type: "datetime" },
        { name: "create_uid", type: "many2one", relation: "res.users" },
    ],
};

registry.category("fields").add("attachment_preview", attachmentPreviewField);

