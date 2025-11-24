from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Extiende los campos cargados en el POS para incluir description_ecommerce.
        Esto permite usar la descripción del ecommerce como fallback.
        """
        fields = super()._load_pos_data_fields(config_id)
        fields.append('description_ecommerce')
        return fields

    def get_product_info_pos(self, price, quantity, pos_config_id, product_variant_id=False):
        """
        Extiende el método original para incluir la imagen principal y las imágenes adicionales del sitio web.
        """
        # Obtener la información base del método padre
        result = super().get_product_info_pos(price, quantity, pos_config_id, product_variant_id)
        
        # Lista para almacenar todas las imágenes (principal + adicionales)
        product_images = []
        
        # 1. Agregar la imagen principal del producto - Determinar si usar imagen de variante o de template
        if product_variant_id:
            product_variant = self.env['product.product'].browse(product_variant_id)
            main_image_model = 'product.product'
            main_image_id = product_variant.id
            has_main_image = product_variant.image_variant_1920 or product_variant.image_1920
        else:
            main_image_model = 'product.template'
            main_image_id = self.id
            has_main_image = self.image_1920
        
        if has_main_image:
            product_images.append({
                'id': f'main_{main_image_id}',
                'name': 'Imagen Principal',
                'sequence': 0,
                'image_url': f'/web/image/{main_image_model}/{main_image_id}/image_512',
                'image_url_large': f'/web/image/{main_image_model}/{main_image_id}/image_1024',
                'is_main': True,
            })
        
        # 2. Agregar las imágenes adicionales del producto (product.image del módulo website_sale)
        # Usamos image_512 para un balance entre calidad y rendimiento
        if self.product_template_image_ids:
            for image in self.product_template_image_ids:
                # Solo incluir imágenes que tengan contenido
                if image.image_1920:
                    product_images.append({
                        'id': image.id,
                        'name': image.name,
                        'sequence': image.sequence,
                        'image_url': f'/web/image/product.image/{image.id}/image_512',
                        'image_url_large': f'/web/image/product.image/{image.id}/image_1024',
                        'is_main': False,
                    })
        
        product_images.sort(key=lambda x: x['sequence'])
        
        result['product_images'] = product_images
        
        return result

