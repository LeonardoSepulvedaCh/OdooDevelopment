# -*- coding: utf-8 -*-
"""
Template de correo electrónico para el pacto de reposición.
Separado en un archivo independiente para mejor mantenibilidad.
"""

# Generar el HTML del correo electrónico para la carta de liquidación.
def get_email_template_html(ticket, logo_url, valor_formateado, porcentaje_aprobacion):
    nombre_cliente = ticket.partner_id.name if ticket.partner_id else 'cliente'
    ticket_name = ticket.name
    descripcion_producto = ticket.pacto_descripcion_bicicleta or 'Bicicleta'
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333333;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}
        .email-container {{
            max-width: 650px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            padding: 30px 20px;
            text-align: center;
        }}
        .header img {{
            max-width: 280px;
            height: auto;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .greeting {{
            font-size: 18px;
            color: #2c3e50;
            margin-bottom: 20px;
            font-weight: 600;
        }}
        .info-box {{
            background-color: #f8f9fa;
            padding: 20px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        .info-box h3 {{
            margin-top: 0;
            color: #e74c3c;
            font-size: 16px;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .highlight strong {{
            color: #856404;
            font-size: 20px;
        }}
        .contact-section {{
            background-color: #e8f4f8;
            padding: 25px;
            border-radius: 6px;
            margin: 25px 0;
        }}
        .contact-section h3 {{
            color: #0056b3;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 16px;
        }}
        .contact-item {{
            display: flex;
            align-items: center;
            margin: 10px 0;
            color: #333;
        }}
        .contact-item svg {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            fill: #0056b3;
        }}
        .contact-item a {{
            color: #0056b3;
            text-decoration: none;
            font-weight: 500;
        }}
        .contact-item a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            background-color: #2c3e50;
            color: #ffffff;
            padding: 30px;
            text-align: center;
        }}
        .footer-company {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .footer-department {{
            font-size: 14px;
            color: #bdc3c7;
            margin-bottom: 20px;
        }}
        .social-links {{
            margin: 20px 0;
        }}
        .social-links a {{
            display: inline-block;
            margin: 0 10px;
            text-decoration: none;
        }}
        .social-icon {{
            width: 32px;
            height: 32px;
            background-color: #ffffff;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.3s ease;
        }}
        .social-icon:hover {{
            transform: scale(1.1);
        }}
        .footer-note {{
            font-size: 12px;
            color: #95a5a6;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #34495e;
        }}
        @media only screen and (max-width: 600px) {{
            .content {{
                padding: 25px 20px;
            }}
            .email-container {{
                margin: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Header con logo -->
        <div class="header">
            <img src="{logo_url}" alt="Bicicletas Milán" />
        </div>
        
        <!-- Contenido principal -->
        <div class="content">
            <div class="greeting">
                Estimado(a) <strong>{nombre_cliente}</strong>,
            </div>
            
            <p style="margin-bottom: 20px; line-height: 1.8;">
                Nos complace informarle que hemos completado la evaluación de su solicitud de 
                <strong>Pacto de Reposición Optimus</strong> correspondiente al ticket 
                <strong>{ticket_name}</strong>.
            </p>
            
            <!-- Información destacada -->
            <div class="info-box">
                <h3>Resumen de la Liquidación</h3>
                <p style="margin: 10px 0;">
                    <strong>Producto:</strong> {descripcion_producto}<br/>
                    <strong>Porcentaje autorizado:</strong> {porcentaje_aprobacion}% del precio de compra
                </p>
            </div>
            
            <!-- Valor a consignar -->
            <div class="highlight">
                <p style="margin: 0; text-align: center;">
                    <strong>Valor a consignar:</strong><br/>
                    <span style="font-size: 28px; color: #856404; font-weight: bold;">
                        ${valor_formateado} COP
                    </span>
                </p>
            </div>
            
            <p style="margin: 20px 0; line-height: 1.8;">
                Por favor, revise el documento adjunto donde encontrará todos los detalles de esta liquidación, 
                incluyendo los <strong>datos bancarios</strong> para realizar la consignación y los 
                <strong>plazos establecidos</strong>.
            </p>
            
            <!-- Sección de contacto -->
            <div class="contact-section">
                <h3>¿Necesita ayuda?</h3>
                <p style="margin-bottom: 15px;">
                    Nuestro equipo está disponible para atenderle:
                </p>
                <div class="contact-item">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56a.977.977 0 00-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z"/>
                    </svg>
                    <span><strong>Celular:</strong> <a href="tel:+573102424848">310 2424848</a></span>
                </div>
                <div class="contact-item">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                    </svg>
                    <span><strong>Email:</strong> <a href="mailto:servicioalcliente@bicicletasmilan.com">servicioalcliente@bicicletasmilan.com</a></span>
                </div>
            </div>
            
            <p style="margin-top: 30px; color: #7f8c8d; font-size: 14px;">
                Este correo ha sido generado automáticamente. Si tiene alguna pregunta sobre su liquidación, 
                no dude en contactarnos.
            </p>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div class="footer-company">INDUSTRIAS BICICLETAS MILÁN S.A.S</div>
            <div class="footer-department">Departamento de Garantías</div>
            
            <div class="footer-note">
                © 2025 INDUSTRIAS BICICLETAS MILÁN S.A.S. Todos los derechos reservados.<br/>
                Este correo electrónico y cualquier archivo transmitido con él son confidenciales y están destinados 
                únicamente para el uso del individuo o entidad a la que están dirigidos.
            </div>
        </div>
    </div>
</body>
</html>
"""


