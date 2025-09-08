{
    'name': 'POS - Reporte de cierre de caja',
    'version': '18.5.0.0.1',
    'category': 'Milan/POS',
    'summary': 'Genera un informe PDF al cerrar la caja en el POS',
    'description': """
Este módulo permite generar un informe detallado en PDF al cerrar la caja en el Punto de Venta (POS).
Incluye:
- Monto total de cierre
- gastos
- Desglose por denominación de billetes y monedas
- Cantidad de pagos por transferencia o Bouchers (Recibos)
""",
    'author': 'Leonardo Sepúlveda',
    'license': 'OPL-1',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_cash_report_template.xml',
        'views/pos_cash_report_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'pos_cash_report/static/src/css/cash_report.css',
        ],
    },
    'installable': True,
    'application': False,
}
