# Fixture TAUSER - Documentación

## 📋 Resumen

Se ha creado el fixture `tauser/fixtures/tausers_data.json` que inicializa **5 terminales TAUSER** (Terminales de Autoservicio de Usuario) con inventario completo de divisas y denominaciones.

## 🏪 Terminales Creadas

### 1. **TAUSER Central** (TC-001)
- **Ubicación:** Shopping del Sol - Planta Baja
- **Responsable:** admin (usuario ID 2)
- **Inventario:**
  - 3 divisas (USD, EUR, GBP)
  - 14 líneas de denominaciones
  - Stock total: ~$15,000 USD, €12,000 EUR, £8,000 GBP

### 2. **TAUSER Aeropuerto** (TA-001)
- **Ubicación:** Aeropuerto Silvio Pettirossi - Terminal Internacional
- **Responsable:** operador (usuario ID 3)
- **Inventario:**
  - 2 divisas (USD, EUR)
  - 10 líneas de denominaciones
  - Stock total: ~$25,000 USD, €18,000 EUR
  - **Terminal con mayor capacidad** (aeropuerto)

### 3. **TAUSER Multiplaza** (TM-001)
- **Ubicación:** Multiplaza - Sector Norte
- **Responsable:** operador (usuario ID 3)
- **Inventario:**
  - 2 divisas (USD, CAD)
  - 7 líneas de denominaciones
  - Stock total: ~$20,000 USD, C$10,000 CAD

### 4. **TAUSER Paseo La Galería** (TG-001)
- **Ubicación:** Paseo La Galería - Entrada Principal
- **Responsable:** admin (usuario ID 2)
- **Inventario:**
  - 2 divisas (USD, EUR)
  - 8 líneas de denominaciones
  - Stock total: ~$18,000 USD, €14,000 EUR

### 5. **TAUSER Mariscal López** (TML-001)
- **Ubicación:** Av. Mariscal López - Oficina Central
- **Responsable:** admin (usuario ID 2)
- **Inventario:**
  - 3 divisas (USD, EUR, GBP)
  - 14 líneas de denominaciones
  - Stock total: ~$30,000 USD, €22,000 EUR, £15,000 GBP
  - **Terminal principal con mayor stock**

## 📊 Resumen de Datos

| Modelo | Cantidad |
|--------|----------|
| **Terminal** | 5 |
| **InventarioDivisaTerminal** | 12 registros |
| **InventarioDenominacionTerminal** | 53 líneas |

## 💵 Denominaciones Incluidas

Cada terminal tiene stock de las siguientes denominaciones según la divisa:

### USD (Dólar)
- $100, $50, $20, $10, $5, $1

### EUR (Euro)
- €500, €200, €100, €50, €20, €10, €5

### GBP (Libra Esterlina)
- £50, £20, £10, £5

### CAD (Dólar Canadiense)
- C$100, C$50, C$20, C$10, C$5

## 🔧 Configuración

### Cantidades Mínimas
Cada línea de inventario tiene una **cantidad mínima** configurada que genera alertas cuando el stock está bajo:
- Billetes grandes (€500, $100): mínimo 5-20 unidades
- Billetes medianos ($50, €50): mínimo 30-50 unidades
- Billetes pequeños ($1, €5): mínimo 100-200 unidades

### Última Reposición
Todas las terminales tienen fecha de última reposición: **2025-10-31 08:00:00 UTC**

## 🚀 Uso

### Cargar el fixture manualmente:
```bash
python manage.py loaddata tauser/fixtures/tausers_data.json
```

### Cargar todo el sistema (incluye TAUSER):
```bash
python setup_system.py
```

## ✅ Verificación

Para verificar que las terminales se cargaron correctamente:

```bash
python manage.py shell -c "from tauser.models import Terminal; print(f'Terminales: {Terminal.objects.count()}')"
```

Para ver el inventario de una terminal:

```bash
python manage.py shell -c "from tauser.models import Terminal; t = Terminal.objects.get(codigo='TC-001'); print(f'Divisas: {t.inventario.count()}, Denominaciones: {t.inventario_denominaciones.count()}')"
```

## 📝 Notas Importantes

1. **Dependencias:** Este fixture requiere que estén cargados previamente:
   - `users/fixtures/users_data.json` (usuarios responsables)
   - `divisas/fixtures/divisas_data.json` (divisas)
   - `divisas/fixtures/denominaciones_data.json` (denominaciones)

2. **Orden de carga:** El fixture se carga al FINAL en `setup_system.py` para garantizar que todas las dependencias existan.

3. **Inventario realista:** Las cantidades están diseñadas para simular operaciones reales:
   - Terminales de alto tráfico (aeropuerto, oficina central) tienen mayor stock
   - Terminales de shoppings tienen stock medio-bajo
   - Cada terminal tiene niveles mínimos configurados para alertas

4. **IDs utilizados:**
   - Terminales: PK 1-5
   - InventarioDivisaTerminal: PK 1-12
   - InventarioDenominacionTerminal: PK 1-53

## 🔄 Integración con setup_system.py

El fixture se agregó al final de la lista `FIXTURES_ORDER` en `setup_system.py`:

```python
# 5. TAUSER (Terminales de autoservicio con inventario)
('TAUSER (Terminales)', 'tauser/fixtures/tausers_data.json'),
```

El resumen del sistema ahora incluye información de TAUSER:
- Cantidad de terminales
- Cantidad de líneas de inventario

---

**Fecha de creación:** 31 de octubre de 2025  
**Última actualización:** 31 de octubre de 2025
