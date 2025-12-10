# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Migración post-instalación para asignar régimen tributario por defecto
    a todos los contactos existentes que no tengan uno asignado.
    """
    # Buscar el régimen "Régimen Común" (RC) como valor por defecto
    cr.execute("""
        SELECT id FROM l10n_co_tax_regime 
        WHERE code = 'RC' 
        LIMIT 1
    """)
    result = cr.fetchone()
    
    if result:
        default_regime_id = result[0]
        
        # Actualizar todos los contactos sin régimen tributario
        cr.execute("""
            UPDATE res_partner 
            SET l10n_co_tax_regime_id = %s 
            WHERE l10n_co_tax_regime_id IS NULL
        """, (default_regime_id,))
        
        print(f"✅ Migración completada: {cr.rowcount} contactos actualizados con régimen RC por defecto")
    else:
        print("⚠️  No se encontró el régimen RC. Asegúrate de que los datos estén cargados.")

