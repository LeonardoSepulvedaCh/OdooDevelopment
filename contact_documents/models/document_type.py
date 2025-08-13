from odoo import models, fields

class DocumentType(models.Model):
    _name = 'document.type'
    _description = 'Tipo de Documento'
    _order = 'name'

    name = fields.Char(string='Nombre de la Categoría', required=True)
    active = fields.Boolean(string='Activo', default=True)

    # Restricciones SQL
    _sql_constraints = [
        ('check_name_uniq', 'UNIQUE(name)', 'El nombre de la categoría debe ser único')
    ]

    def toggle_active(self):
        for record in self:
            record.active = not record.active