"""
Template de correo electrónico para el pacto de reposición.
Separado en un archivo independiente para mejor mantenibilidad.

"""

import html


# Generar el HTML del correo electrónico para la carta de liquidación.
def get_email_template_html(ticket, valor_formateado, porcentaje_aprobacion, header_url, footer_url):

    nombre_cliente = html.escape(ticket.partner_id.name if ticket.partner_id else 'cliente')
    ticket_name = html.escape(ticket.name)
    descripcion_producto = html.escape(ticket.pacto_descripcion_bicicleta or 'Bicicleta')
    
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
            padding: 0;
            text-align: center;
        }}
        .header img {{
            max-width: 100%;
            width: 100%;
            height: auto;
            display: block;
        }}
        .content {{
            padding: 35px 30px;
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
        .content-contact {{
            text-align: center;
            margin-top: 10px;
        }}
        .contact-section h3 {{
            color: #0056b3;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 16px;
        }}
        .contact-item {{
            color: #333;
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
            padding: 0;
            text-align: center;
        }}
        .footer img {{
            max-width: 100%;
            width: 100%;
            height: auto;
            display: block;
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
        }}
        .disclaimer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 11px;
            color: #6c757d;
            line-height: 1.5;
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
        <!-- Header -->
        <div class="header">
            <img src="{header_url}" alt="Header Bicicletas Milán" />
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
                <h3 style="text-align: center; font-size: 18px; font-weight: 600;">¿Necesita ayuda?</h3>
                <p style="margin-bottom: 15px; text-align: center;">
                    Nuestro equipo está disponible para atenderle:
                </p>
                <div class="content-contact" style="text-align: center; margin-top: 10px;">
                    <div class="contact-item" style="display: inline-block; margin: 0 15px;">
                        <span><strong>Celular:</strong> <a href="tel:+573102424848">+57 310 2424848</a></span>
                    </div>
                    <div class="contact-item" style="display: inline-block; margin: 0 15px;">
                        <span><strong>Email:</strong> <a href="mailto:servicioalcliente@bicicletasmilan.com">servicioalcliente@bicicletasmilan.com</a></span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <img src="{footer_url}" alt="Footer Bicicletas Milán" />
        </div>
        
        <!-- Disclaimer -->
        <div class="disclaimer">
            <p style="margin: 0 0 10px 0; font-size: 12px; color: #495057;">
                <strong>Este correo ha sido generado automáticamente.</strong><br/>
                Si tiene alguna pregunta sobre su liquidación, no dude en contactarnos.
            </p>
            <p style="margin: 10px 0 0 0; font-size: 11px; color: #6c757d;">
                Este mensaje es confidencial y está dirigido exclusivamente al destinatario indicado. 
                Si usted no es el destinatario, le informamos que cualquier divulgación, copia, distribución o 
                uso de este mensaje está prohibido. Si ha recibido este mensaje por error, por favor notifíquenos 
                inmediatamente y elimínelo de su sistema.
            </p>
        </div>
    </div>
</body>
</html>
"""


