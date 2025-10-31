# Análisis del XML del Profesor vs Nuestra Configuración

## 📋 DATOS DEL EMISOR (gEmis)
```xml
<!-- XML del Profesor -->
<dRucEm>2595733</dRucEm>
<dDVEmi>3</dDVEmi>
<iTipCont>1</iTipCont>
<dNomEmi>DE generado en ambiente de prueba - sin valor comercial ni fiscal</dNomEmi>
<dDirEmi>YVAPOVO C/ TOBATI</dDirEmi>
<dNumCas>1543</dNumCas>
<cDepEmi>1</cDepEmi>
<dDesDepEmi>CAPITAL</dDesDepEmi>
<cCiuEmi>1</cCiuEmi>
<dDesCiuEmi>ASUNCION (DISTRITO)</dDesCiuEmi>
<dTelEmi>(0961)988439</dTelEmi>
<dEmailE>ggonzar@gmail.com</dEmailE>
```

**✅ Nuestra configuración:**
- RUC: 2595733-3 ✅
- Tipo contribuyente: 1 ✅
- Email: glex.globalexchange@gmail.com ✅
- Actividades: 62010, 74909 ✅

---

## 📋 DATOS DEL RECEPTOR (gDatRec) - **¡AQUÍ ESTÁ EL PROBLEMA!**

```xml
<!-- XML del Profesor -->
<iNatRec>1</iNatRec>          <!-- Naturaleza: 1 = No contribuyente -->
<iTiOpe>1</iTiOpe>            <!-- Tipo operación: 1 = B2C (con cliente final) -->
<cPaisRec>PRY</cPaisRec>      <!-- País: Paraguay -->
<iTiContRec>2</iTiContRec>    <!-- Tipo contribuyente receptor: 2 = Persona física -->
<dRucRec>80026216</dRucRec>   <!-- RUC del receptor: 80026216 -->
<dDVRec>6</dDVRec>            <!-- DV del receptor: 6 -->
<dNomRec>GUILLERMO GONZALEZ</dNomRec>
<dEmailRec>soporte@facturasegura.com.py</dEmailRec>
```

**❌ Lo que estamos enviando:**
```python
'1', '1', 'PRY', '1',                           # iNatRec, iTiOpe, cPaisRec, iTiContRec
'{datos_factura.get('cliente_ruc', EMISOR_CONFIG['ruc'])}',  # dRucRec
'{datos_factura.get('cliente_dv', EMISOR_CONFIG['dv'])}',    # dDVRec
'1', '', '{datos_factura.get('cliente_documento', '12345678')}',  # iTipIDRec, dDTipIDRec, dNumIDRec
```

### 🔴 ERRORES IDENTIFICADOS:

1. **iTiContRec = '1'** (nosotros) vs **iTiContRec = '2'** (profesor)
   - Valor 1 = Contribuyente (requiere RUC válido registrado en SET)
   - Valor 2 = Persona física (RUC puede ser cualquier número válido)

2. **iTipIDRec = '1'** (nosotros) - Este campo NO debe estar cuando hay RUC
   - Según el XML del profesor, cuando hay `dRucRec`, NO se usan `iTipIDRec` ni `dNumIDRec`
   - Estos campos son para identificación alternativa (cédula, pasaporte, etc.)

---

## 📋 TIMBRADO (gTimb)

```xml
<!-- XML del Profesor -->
<dNumTim>02595733</dNumTim>
<dEst>001</dEst>
<dPunExp>001</dPunExp>
<dNumDoc>0000011</dNumDoc>
<dFeIniT>2025-03-27</dFeIniT>
```

**✅ Nuestra configuración:**
- Timbrado: 02595733 ✅
- Establecimiento: 001 ✅
- Punto: 001 ❌ (Nosotros usamos 003)
- Fecha inicio: 2025-03-27 ✅

---

## 📋 ITEMS (gCamItem)

```xml
<!-- XML del Profesor -->
<dCodInt>1</dCodInt>
<dDesProSer>SERVICIOS DE CONTABILIDAD MARZO 2025</dDesProSer>
<cUniMed>77</cUniMed>
<dDesUniMed>UNI</dDesUniMed>
<dCantProSer>1</dCantProSer>
<dPUniProSer>1500000</dPUniProSer>
<iAfecIVA>1</iAfecIVA>
<dPropIVA>100</dPropIVA>
<dTasaIVA>10</dTasaIVA>
<dBasGravIVA>1363636</dBasGravIVA>
<dLiqIVAItem>136364</dLiqIVAItem>
```

**⚠️ Lo que estamos enviando:**
- Código interno: '1' ✅
- Descripción: variable ✅
- Cantidad: variable ✅
- Precio unitario: variable ✅
- **IVA:** Aquí puede haber un problema con los cálculos

---

## 🎯 CORRECCIONES NECESARIAS

### 1. **iTiContRec debe ser '2' (persona física) en lugar de '1'**
   - Línea en services.py: `'1', '1', 'PRY', '1',`
   - Debe ser: `'1', '1', 'PRY', '2',`

### 2. **Eliminar iTipIDRec, dDTipIDRec, dNumIDRec cuando hay RUC**
   - Actualmente: `'1', '', '{datos_factura.get('cliente_documento', '12345678')}',`
   - Debe ser: campos vacíos o no enviar

### 3. **Punto de expedición**
   - Profesor usa: 001
   - Nosotros usamos: 003
   - Verificar que 003 esté en el rango autorizado

---

## 💡 SOLUCIÓN RÁPIDA PARA MAÑANA

**Opción 1 (Más segura):** Usar los mismos datos del profesor
```python
'1', '1', 'PRY', '2',  # iTiContRec = 2 (persona física)
'80026216',            # dRucRec del profesor
'6',                   # dDVRec del profesor
```

**Opción 2 (Usar RUC genérico válido):**
```python
'1', '1', 'PRY', '2',  # iTiContRec = 2
'80000000',            # RUC genérico
'1',                   # DV genérico
```

**Opción 3 (Sin contribuyente - solo nombre):**
```python
'2', '1', 'PRY', '',   # iNatRec = 2 (extranjero o sin RUC)
'',                    # Sin RUC
'',                    # Sin DV
```

---

## 📊 RESUMEN

| Campo | Profesor | Nosotros | Estado |
|-------|----------|----------|--------|
| dRucEm | 2595733 | 2595733 | ✅ |
| dDVEmi | 3 | 3 | ✅ |
| iTiContRec | **2** | **1** | ❌ |
| dRucRec | 80026216 | 2595733 o 0 | ❌ |
| dDVRec | 6 | 3 o 0 | ❌ |
| iTipIDRec | (vacío) | 1 | ❌ |
| dPunExp | 001 | 003 | ⚠️ |

**CONCLUSIÓN:** El error principal es `iTiContRec = 1` cuando debería ser `2`, y estamos enviando campos de identificación alternativa cuando ya tenemos RUC.
