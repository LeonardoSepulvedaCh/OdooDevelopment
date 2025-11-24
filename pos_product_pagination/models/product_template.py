from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pos_total_qty_sold = fields.Float(
        string='Cantidad Vendida en POS',
        compute='_compute_pos_total_qty_sold',
        store=False,
        help='Cantidad total vendida de este producto en el POS'
    )

    @api.depends_context('company')
    def _compute_pos_total_qty_sold(self):
        """
        Calcula la cantidad total vendida de cada producto template en el POS.
        Se usa para ordenar los productos por más vendidos.
        Utiliza read_group para agregación eficiente a nivel de base de datos.
        """
        # Inicializar todos los productos en 0
        for product in self:
            product.pos_total_qty_sold = 0.0

        if not self.ids:
            return

        # Obtener las variantes de productos de los templates actuales
        product_variants = self.env['product.product'].search([
            ('product_tmpl_id', 'in', self.ids)
        ])
        
        if not product_variants:
            return
        
        # Usar read_group para agregar cantidades a nivel de base de datos
        # Esto es mucho más eficiente que cargar todas las líneas en memoria
        grouped_data = self.env['pos.order.line']._read_group(
            domain=[
                ('product_id', 'in', product_variants.ids),
                ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
                ('order_id.company_id', '=', self.env.company.id)
            ],
            groupby=['product_id'],
            aggregates=['qty:sum']
        )
        
        # Mapear cantidades por template
        qty_by_template = {}
        for product_variant, qty_sum in grouped_data:
            if product_variant:
                template_id = product_variant.product_tmpl_id.id
                qty_by_template[template_id] = qty_by_template.get(template_id, 0.0) + qty_sum
        
        # Asignar las cantidades calculadas
        for product in self:
            product.pos_total_qty_sold = qty_by_template.get(product.id, 0.0)

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Extiende los campos cargados en el POS para incluir pos_total_qty_sold.
        """
        fields = super()._load_pos_data_fields(config_id)
        fields.append('pos_total_qty_sold')
        return fields

