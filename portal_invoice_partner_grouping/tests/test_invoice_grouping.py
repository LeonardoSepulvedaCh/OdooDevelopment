# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Command
from odoo.tests.common import tagged, HttpCase
from odoo.addons.account.tests.common import AccountTestInvoicingHttpCommon


@tagged('post_install', '-at_install')
class TestPortalInvoiceGrouping(AccountTestInvoicingHttpCommon):
    """
    Tests para validar la agrupación de facturas por partner en el portal.
    
    Casos de prueba:
    1. Agrupación correcta con múltiples partners
    2. Vista sin agrupación con un solo partner
    3. Vista vacía sin facturas
    4. Compatibilidad con filtros y ordenamiento
    5. Cálculo correcto de totales por partner
    6. Manejo de facturas rectificativas (refunds)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Crear usuario portal de prueba
        cls.user_portal = cls._create_new_portal_user()
        cls.portal_partner = cls.user_portal.partner_id
        
        # Crear partners de prueba para B2B
        cls.partner_company_a = cls.env['res.partner'].create({
            'name': 'Company A',
            'company_type': 'company',
            'city': 'Madrid',
            'country_id': cls.env.ref('base.es').id,
        })
        
        cls.partner_company_b = cls.env['res.partner'].create({
            'name': 'Company B',
            'company_type': 'company',
            'city': 'Barcelona',
            'country_id': cls.env.ref('base.es').id,
        })
        
        cls.partner_company_c = cls.env['res.partner'].create({
            'name': 'Company C',
            'company_type': 'company',
            'city': 'Valencia',
            'country_id': cls.env.ref('base.es').id,
        })

    def _create_test_invoice(self, partner, amount, post=True, move_type='out_invoice'):
        """Helper para crear facturas de prueba."""
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'Test Product',
                'price_unit': amount,
                'quantity': 1,
            })]
        })
        if post:
            invoice.action_post()
        return invoice

    def test_01_grouping_multiple_partners(self):
        """Test: Agrupación correcta cuando hay múltiples partners."""
        # Crear facturas para diferentes partners
        invoice_a1 = self._create_test_invoice(self.partner_company_a, 1000.0)
        invoice_a2 = self._create_test_invoice(self.partner_company_a, 500.0)
        invoice_b1 = self._create_test_invoice(self.partner_company_b, 750.0)
        invoice_c1 = self._create_test_invoice(self.partner_company_c, 250.0)
        
        # Simular datos de facturas como los devuelve el controlador
        invoices_data = [
            {'invoice': invoice_a1},
            {'invoice': invoice_a2},
            {'invoice': invoice_b1},
            {'invoice': invoice_c1},
        ]
        
        # Importar controlador
        from odoo.addons.portal_invoice_partner_grouping.controllers.portal import PortalAccountInherit
        controller = PortalAccountInherit()
        
        # Ejecutar agrupación
        grouped = controller._group_invoices_by_partner(invoices_data)
        
        # Validaciones
        self.assertEqual(len(grouped), 3, "Debe haber 3 grupos (uno por partner)")
        
        # Validar Company A (2 facturas)
        group_a = grouped[self.partner_company_a.id]
        self.assertEqual(group_a['count'], 2, "Company A debe tener 2 facturas")
        self.assertEqual(group_a['partner'], self.partner_company_a)
        self.assertAlmostEqual(group_a['total_due'], 1500.0, places=2)
        
        # Validar Company B (1 factura)
        group_b = grouped[self.partner_company_b.id]
        self.assertEqual(group_b['count'], 1, "Company B debe tener 1 factura")
        self.assertAlmostEqual(group_b['total_due'], 750.0, places=2)
        
        # Validar Company C (1 factura)
        group_c = grouped[self.partner_company_c.id]
        self.assertEqual(group_c['count'], 1, "Company C debe tener 1 factura")
        self.assertAlmostEqual(group_c['total_due'], 250.0, places=2)

    def test_02_grouping_single_partner(self):
        """Test: Vista sin agrupación cuando hay un solo partner."""
        # Crear facturas para un solo partner
        invoice1 = self._create_test_invoice(self.partner_company_a, 1000.0)
        invoice2 = self._create_test_invoice(self.partner_company_a, 500.0)
        
        invoices_data = [
            {'invoice': invoice1},
            {'invoice': invoice2},
        ]
        
        from odoo.addons.portal_invoice_partner_grouping.controllers.portal import PortalAccountInherit
        controller = PortalAccountInherit()
        
        grouped = controller._group_invoices_by_partner(invoices_data)
        
        # Debe haber solo 1 grupo
        self.assertEqual(len(grouped), 1, "Debe haber solo 1 grupo")
        
        # Validar que contiene ambas facturas
        group = grouped[self.partner_company_a.id]
        self.assertEqual(group['count'], 2, "El grupo debe tener 2 facturas")

    def test_03_empty_invoices(self):
        """Test: Vista vacía cuando no hay facturas."""
        from odoo.addons.portal_invoice_partner_grouping.controllers.portal import PortalAccountInherit
        controller = PortalAccountInherit()
        
        # Probar con lista vacía
        grouped = controller._group_invoices_by_partner([])
        self.assertEqual(len(grouped), 0, "Lista vacía debe retornar dict vacío")
        
        # Probar con None
        grouped = controller._group_invoices_by_partner(None)
        self.assertEqual(len(grouped), 0, "None debe retornar dict vacío")

    def test_04_refund_handling(self):
        """Test: Manejo correcto de facturas rectificativas (refunds)."""
        # Crear factura y rectificativa
        invoice = self._create_test_invoice(self.partner_company_a, 1000.0)
        refund = self._create_test_invoice(self.partner_company_a, 300.0, move_type='out_refund')
        
        invoices_data = [
            {'invoice': invoice},
            {'invoice': refund},
        ]
        
        from odoo.addons.portal_invoice_partner_grouping.controllers.portal import PortalAccountInherit
        controller = PortalAccountInherit()
        
        grouped = controller._group_invoices_by_partner(invoices_data)
        
        # Validar que el total considera la rectificativa con signo negativo
        group = grouped[self.partner_company_a.id]
        self.assertEqual(group['count'], 2, "Debe haber 2 documentos")
        # Total = 1000 - 300 = 700 (la rectificativa se resta)
        expected_total = invoice.amount_residual - refund.amount_residual
        self.assertAlmostEqual(group['total_due'], expected_total, places=2)

    def test_05_invoices_without_partner(self):
        """Test: Manejo de facturas sin partner asignado."""
        # Crear factura sin partner (caso edge)
        invoice_no_partner = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': False,  # Sin partner
            'invoice_line_ids': [Command.create({
                'name': 'Test Product',
                'price_unit': 100.0,
                'quantity': 1,
            })]
        })
        
        invoices_data = [{'invoice': invoice_no_partner}]
        
        from odoo.addons.portal_invoice_partner_grouping.controllers.portal import PortalAccountInherit
        controller = PortalAccountInherit()
        
        grouped = controller._group_invoices_by_partner(invoices_data)
        
        # Debe agruparse bajo key=0 (sin partner)
        self.assertIn(0, grouped, "Facturas sin partner deben agruparse bajo key=0")
        self.assertEqual(grouped[0]['count'], 1)
        self.assertFalse(grouped[0]['partner'], "Partner debe ser False")

    def test_06_order_preserved(self):
        """Test: Los grupos mantienen el orden de aparición de las facturas (respeta sortby)."""
        # Crear facturas en orden específico (simula sortby del usuario)
        invoice_c = self._create_test_invoice(self.partner_company_c, 100.0)  # Valencia
        invoice_a = self._create_test_invoice(self.partner_company_a, 100.0)  # Madrid (A)
        invoice_b = self._create_test_invoice(self.partner_company_b, 100.0)  # Barcelona (B)
        
        # Orden de entrada: C, A, B (como si viniera ordenado por fecha u otro campo)
        invoices_data = [
            {'invoice': invoice_c},
            {'invoice': invoice_a},
            {'invoice': invoice_b},
        ]
        
        from odoo.addons.portal_invoice_partner_grouping.controllers.portal import PortalAccountInherit
        controller = PortalAccountInherit()
        
        grouped = controller._group_invoices_by_partner(invoices_data)
        
        # Obtener partner_ids en orden de aparición en el dict
        partner_ids_order = list(grouped.keys())
        
        # Validar que el orden es C, A, B (orden de entrada, NO alfabético)
        expected_order = [
            self.partner_company_c.id,
            self.partner_company_a.id,
            self.partner_company_b.id,
        ]
        
        self.assertEqual(partner_ids_order, expected_order, 
                        "Los grupos deben mantener el orden de aparición de las facturas")

    def test_07_error_handling_malformed_data(self):
        """Test: Manejo robusto de datos malformados."""
        from odoo.addons.portal_invoice_partner_grouping.controllers.portal import PortalAccountInherit
        controller = PortalAccountInherit()
        
        # Datos malformados
        malformed_data = [
            {'invoice': None},  # Invoice None
            {},  # Dict vacío
            {'other_key': 'value'},  # Sin key 'invoice'
        ]
        
        # No debe lanzar excepción
        try:
            grouped = controller._group_invoices_by_partner(malformed_data)
            # Debe retornar dict vacío o manejar gracefully
            self.assertIsInstance(grouped, dict, "Debe retornar un dict")
        except Exception as e:
            self.fail(f"No debe lanzar excepción con datos malformados: {e}")

    def test_08_integration_portal_access(self):
        """Test de integración: Acceso al portal con agrupación."""
        # Crear facturas para múltiples partners
        invoice_a = self._create_test_invoice(self.partner_company_a, 1000.0)
        invoice_b = self._create_test_invoice(self.partner_company_b, 500.0)
        
        # Autenticar como usuario portal
        self.authenticate(self.user_portal.login, self.user_portal.login)
        
        # Acceder a la ruta del portal
        response = self.url_open('/my/invoices')
        
        # Validar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200, 
                        "El portal debe ser accesible")
        
        # Validar que el contenido contiene elementos de agrupación
        content = response.content.decode('utf-8')
        # Debe contener la clase CSS del grupo
        self.assertIn('o_portal_invoice_partner_group', content,
                     "El template debe incluir elementos de agrupación")


@tagged('post_install', '-at_install')
class TestPortalInvoiceGroupingCompatibility(AccountTestInvoicingHttpCommon):
    """
    Tests de compatibilidad con otros módulos.
    
    Valida que el módulo no rompe funcionalidad nativa:
    - Paginación
    - Filtros
    - Ordenamiento
    - Búsqueda por fecha
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_portal = cls._create_new_portal_user()

    def test_01_pagination_preserved(self):
        """Test: La paginación sigue funcionando correctamente."""
        # Crear muchas facturas para forzar paginación
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        
        for i in range(25):  # Más que items_per_page por defecto (20)
            self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_line_ids': [Command.create({
                    'name': f'Product {i}',
                    'price_unit': 100.0,
                })]
            }).action_post()
        
        self.authenticate(self.user_portal.login, self.user_portal.login)
        
        # Acceder a página 1
        response_p1 = self.url_open('/my/invoices/page/1')
        self.assertEqual(response_p1.status_code, 200)
        
        # Acceder a página 2
        response_p2 = self.url_open('/my/invoices/page/2')
        self.assertEqual(response_p2.status_code, 200)
        
        # Validar que hay enlace de paginación
        content = response_p1.content.decode('utf-8')
        self.assertIn('pagination', content.lower(),
                     "Debe existir paginación")

    def test_02_filters_preserved(self):
        """Test: Los filtros nativos y personalizados siguen funcionando."""
        self.authenticate(self.user_portal.login, self.user_portal.login)
        
        # Filtro de facturas
        response = self.url_open('/my/invoices?filterby=invoices')
        self.assertEqual(response.status_code, 200)
        
        # Filtro de compras
        response = self.url_open('/my/invoices?filterby=bills')
        self.assertEqual(response.status_code, 200)

        # Filtro de facturas pendientes
        response = self.url_open('/my/invoices?filterby=pending_invoices')
        self.assertEqual(response.status_code, 200)

        # Filtro de notas de crédito
        response = self.url_open('/my/invoices?filterby=customer_refunds')
        self.assertEqual(response.status_code, 200)

    def test_03_sorting_preserved(self):
        """Test: El ordenamiento sigue funcionando."""
        self.authenticate(self.user_portal.login, self.user_portal.login)
        
        # Ordenar por fecha
        response = self.url_open('/my/invoices?sortby=date')
        self.assertEqual(response.status_code, 200)
        
        # Ordenar por fecha de vencimiento
        response = self.url_open('/my/invoices?sortby=duedate')
        self.assertEqual(response.status_code, 200)
        
        # Ordenar por nombre
        response = self.url_open('/my/invoices?sortby=name')
        self.assertEqual(response.status_code, 200)

    def test_04_pending_filter_and_default(self):
        """Test: El filtro por defecto y 'Facturas pendientes' solo muestran facturas por cobrar."""
        portal_partner = self.user_portal.partner_id

        # Crear factura pendiente
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': portal_partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'Servicio',
                'price_unit': 100.0,
            })]
        })
        invoice.action_post()

        # Crear nota de crédito (no debe aparecer)
        refund = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': portal_partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'Devolución',
                'price_unit': 50.0,
            })]
        })
        refund.action_post()

        self.authenticate(self.user_portal.login, self.user_portal.login)

        # Vista por defecto (sin filtro explícito) debe usar facturas pendientes
        response_default = self.url_open('/my/invoices')
        self.assertEqual(response_default.status_code, 200)
        content_default = response_default.content.decode('utf-8')
        self.assertIn(invoice.name, content_default, "La factura pendiente debe aparecer por defecto")
        self.assertNotIn(refund.name, content_default, "La nota de crédito no debe aparecer por defecto")

        # Filtro explícito de facturas pendientes
        response_pending = self.url_open('/my/invoices?filterby=pending_invoices')
        self.assertEqual(response_pending.status_code, 200)
        content_pending = response_pending.content.decode('utf-8')
        self.assertIn(invoice.name, content_pending, "La factura pendiente debe aparecer en el filtro de pendientes")
        self.assertNotIn(refund.name, content_pending, "La nota de crédito no debe aparecer en el filtro de pendientes")

        # Filtro 'Facturas de clientes' vuelve a incluir notas de crédito
        response_invoices = self.url_open('/my/invoices?filterby=invoices')
        self.assertEqual(response_invoices.status_code, 200)
        content_invoices = response_invoices.content.decode('utf-8')
        self.assertIn(invoice.name, content_invoices, "La factura pendiente debe seguir visible en el filtro general")
        self.assertIn(refund.name, content_invoices, "La nota de crédito debe reaparecer en el filtro general")

    def test_05_customer_refund_filter(self):
        """Test: El nuevo filtro de notas de crédito lista únicamente los reembolsos."""
        portal_partner = self.user_portal.partner_id

        # Crear factura pendiente (no debe aparecer en el filtro de notas de crédito)
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': portal_partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'Servicio',
                'price_unit': 120.0,
            })]
        })
        invoice.action_post()

        # Crear nota de crédito
        refund = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': portal_partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'Devolución',
                'price_unit': 65.0,
            })]
        })
        refund.action_post()

        self.authenticate(self.user_portal.login, self.user_portal.login)

        response = self.url_open('/my/invoices?filterby=customer_refunds')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')
        self.assertIn(refund.name, content, "La nota de crédito debe aparecer en el filtro de notas de crédito")
        self.assertNotIn(invoice.name, content, "La factura estándar no debe aparecer en el filtro de notas de crédito")

    def test_04_portal_menu_uses_pending_filter(self):
        """Test: El enlace del portal para facturas apunta al filtro pending_invoices."""
        self.authenticate(self.user_portal.login, self.user_portal.login)

        response = self.url_open('/my/home')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')
        self.assertIn('filterby=pending_invoices', content,
                      "El enlace del menú debe apuntar al filtro pending_invoices")
        self.assertIn('sortby=most_overdue', content,
                      "El enlace del menú debe mantener el orden 'most_overdue'")

