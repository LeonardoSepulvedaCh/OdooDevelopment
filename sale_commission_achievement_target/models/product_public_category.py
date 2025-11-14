from odoo import models, api


class ProductPublicCategory(models.Model):
    """
    Extensión del modelo de categorías públicas de eCommerce.
    
    Agrega métodos auxiliares para trabajar con jerarquías de categorías,
    facilitando la obtención de categorías hijas de forma recursiva.
    """
    _inherit = 'product.public.category'

    @api.model
    def get_category_with_children_ids(self, category_id):
        """
        Obtiene todos los IDs de una categoría y sus hijas recursivamente.
        
        Este método centraliza la lógica de navegación jerárquica de categorías,
        utilizando el operador 'child_of' optimizado de Odoo. Es útil para cálculos
        que necesitan incluir no solo una categoría específica, sino también todas
        sus subcategorías en cualquier nivel de profundidad.
        
        Args:
            category_id (int): ID de la categoría raíz desde donde comenzar la búsqueda
            
        Returns:
            list: Lista de IDs de categorías (incluye la categoría raíz y todos sus descendientes)
                  Retorna lista vacía si category_id es None, False o 0
            
        Ejemplos:
            >>> self.env['product.public.category'].get_category_with_children_ids(5)
            [5, 12, 13, 24, 25, 26]
            
            Si la jerarquía es:
            - OPTIMUS (ID: 1)
              - BICICLETAS (ID: 2)
                - MTB (ID: 3)
                  - BICICLETA_1 (ID: 4)
              - REPUESTOS (ID: 5)
                - RINES (ID: 6)
            
            Llamando con category_id=2 (BICICLETAS) retornará: [2, 3, 4]
            Llamando con category_id=1 (OPTIMUS) retornará: [1, 2, 3, 4, 5, 6]
            Llamando con category_id=6 (RINES sin hijas) retornará: [6]
        """
        if not category_id:
            return []
        
        # Usar el operador 'child_of' de Odoo para obtener la categoría y todas sus hijas
        categories = self.search([('id', 'child_of', category_id)])
        return categories.ids

