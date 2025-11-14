# 🧮 Esquema de Comisiones para Asesores

## Tipos de Comisión

Existen **dos tipos principales de comisiones** que puede ganar un asesor:

- **1. Comisión por pago a tiempo**
    
    **Descripción:**
    
    El asesor gana una comisión del **0.7% sobre el total recaudado**, siempre y cuando el cliente pague su deuda dentro del plazo considerado como “pago a tiempo”.
    
    **Definición de Pago a Tiempo:**
    
    - El pago se considera “a tiempo” si se realiza **antes del vencimiento efectivo de la deuda**.
    - El **vencimiento efectivo** se calcula como:
        
        Fecha de vencimiento original + 7 días de gabela + prórrogas aprobadas (si las hay).
        
    
    **Ejemplo:**
    
    - El asesor recauda $1.000.000.
    - Como todo el monto fue pagado a tiempo, gana el **0.7% = $7.000**.
    
    **Resumen:**
    
    - Este beneficio **solo se pierde si el pago es tardío**.
    - Se calcula sobre el **monto total recaudado** con pagos a tiempo.

---

- **2. Comisión por meta de venta**
    
    **Descripción:**
    
    El asesor puede ganar **una comisión adicional sobre el monto recaudado**, calculada **por cada categoría de venta**, siempre y cuando cumpla la **meta asignada a esa categoría**.
    
    Cada categoría tiene **su propio porcentaje de comisión**, el cual se aplica **solo si se cumple la meta de venta correspondiente**.
    
    **Reglas de Aplicación:**
    
    - Las **metas de venta** están definidas por **categorías de eCommerce** (por ejemplo: Patines, Accesorios, Promociones, etc.).
    - Cada categoría tiene asignado su **porcentaje de comisión sobre el recaudo**.
        
        Por ejemplo:
        
        | Categoría | % Comisión sobre recaudo |
        | --- | --- |
        | Patines | 0.3% |
        | Cascos | 0.2% |
        | Promociones | 0.1% |
    - El asesor **solo comisiona en una categoría** si alcanza o supera el **100% de la meta asignada** para esa categoría.
    - La **categoría “Promociones”** también genera comisión (sobre su propio recaudo), pero además tiene una **condición especial**:
        - El asesor **debe cumplir el 100% de la meta de Promociones** para que se valide el pago de las comisiones de las demás categorías.
        - Si **no cumple la meta de Promociones**, **pierde las comisiones adicionales** de todas las demás categorías (aunque las haya cumplido).
        - Si la cumple, se calcula también su comisión del recaudo de “Promociones” con el porcentaje asignado a esa categoría.
    
    **Ejemplo:**
    
    1. **Metas asignadas:**
        
        
        | Categoría | Meta | Vendido | % Comisión | Cumplimiento |
        | --- | --- | --- | --- | --- |
        | Patines | $200.000 | $210.000 | 0.3% | ✅ |
        | Promociones | $20.000 | $20.000 | 0.1% | ✅ (cumple 100%) |
    2. **Recaudo total:** $1.000.000
        - Comisión base (por pago a tiempo): 0.7% = **$7.000**
        - Recaudo por categoría:
            - Patines: $300.000
            - Promociones: $20.000
    3. **Cálculo de comisiones por meta:**
        - Patines: $300.000 × 0.3% = **$900**
        - Promociones: $20.000 × 0.1% = **$20**
    
    **Total Comisión del Mes:**
    
    > Comisión base = $7.000
    > 
    > - Comisión metas = $900 + $20
    >     
    >     **Total = $7.920**
    >     
    
    **Resumen:**
    
    - Cada categoría tiene su propio **porcentaje de comisión** sobre el recaudo.
    - Solo se paga la comisión de una categoría si **cumple o supera su meta.**
    - El cumplimiento de la meta de **Promociones (100%) es obligatorio** para habilitar el pago de las comisiones de las demás categorías.
    - Si no cumple la meta de Promociones, **no se paga ninguna comisión adicional.**
    - Si la cumple, además de habilitar las demás categorías, también **genera su propia comisión** sobre el recaudo de Promociones.