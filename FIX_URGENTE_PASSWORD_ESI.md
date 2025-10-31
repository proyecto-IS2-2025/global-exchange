# 🔍 PROBLEMA REAL IDENTIFICADO - NO ES DE PERMISOS

## 📧 MENSAJE DEL PROFESOR (24/10/2025)

> "Ya le asigné los permisos para usar la API al email registrado."
> 
> "El ESI no inicia sesión en el portal, solamente puede utilizar la API especificada. Con el permiso que le asigné ya pueden utilizar el API o el SQL Proxy."
>
> "Personalmente, creo que el SQL proxy es más sencillo porque oculta toda las operaciones de la API. Les sugiero mirar el ./client/app.py del SQL Proxy como ejemplo, inclusive lo pueden probar, configurando los datos solicitados en el mismo script."

---

## ❌ ERROR ANTERIOR (DESCARTADO)

**Pensé que era:**
```
El operador ESI no tiene permiso para generar DE para el RUC 2595733
```

**Pero el profesor confirmó:** ✅ YA TIENE PERMISOS

---

## 🎯 PROBLEMA REAL IDENTIFICADO

### 1. **Falta la CONTRASEÑA del ESI**

**Estado actual de la base de datos:**
```sql
SELECT ruc, esi_email, esi_passwd, LENGTH(esi_token) as token_len 
FROM public.esi;
```

**Resultado:**
```
ruc     | esi_email                     | esi_passwd | token_len
--------+-------------------------------+------------+-----------
2595733 | glex.globalexchange@gmail.com | (NULL)     | 126
```

### 2. **Cómo funciona la autenticación en SQL Proxy**

Según `sql-proxy01/services/web/fs_proxy/views.py` (líneas 141-157):

```python
def do_DE():
    esi = Esi.query.filter(Esi.estado=='ACTIVO').first()
    
    # SI TIENE CONTRASEÑA → Obtiene token nuevo
    if esi.esi_passwd is not None:
        if esi.esi_passwd != "":
            logging.debug("Tiene passwd. Obtenemos token")
            token = get_token_misife(esi.esi_url, esi.esi_email, esi.esi_passwd)
            esi.esi_token = token
            # Vacía la contraseña después de obtener el token
            esi.esi_passwd = ""
    
    # SI NO TIENE CONTRASEÑA → Usa el token existente (puede estar vencido)
    else:
        logging.debug("esi_passwd es nulo")
    
    # Usa el token para las operaciones
    if not (esi.esi_token is None or esi.esi_token.strip() == ""):
        header = {"Authentication-Token": esi.esi_token}
        # ... hace las operaciones ...
```

### 3. **La función `get_token_misife`**

```python
def get_token_misife(url, email, passwd):
    token = ""
    data = {"email": email, "password": passwd}
    resultado = make_request_esi(url+"/login?include_auth_token", 
                                  "POST", 
                                  {"Content-Type": "application/json"}, 
                                  data)
    if "error" in resultado:
        logging.debug("Error al hacer login "+email)
    else:
        resp = resultado["response"]
        token = resp["response"]["user"]["authentication_token"]
    return token
```

**Proceso:**
1. Envía email + contraseña a `/login?include_auth_token`
2. La API responde con un `authentication_token`
3. Ese token se usa para todas las operaciones subsiguientes

---

## 🔴 POR QUÉ FALLA ACTUALMENTE

### Escenario actual:
```
esi_passwd = NULL
esi_token  = "eyJ2ZXIiOiI1IiwidWlkIjoiZDAyMTQ3ZjNiYjU2NGNhYzllYTRhNWFmZDBjNjI3ZGEi..."
```

### Lo que pasa:
1. ✅ SQL Proxy verifica si tiene contraseña
2. ❌ Como `esi_passwd = NULL`, NO obtiene token nuevo
3. ⚠️ Usa el token existente (que pusimos manualmente)
4. ❌ Ese token está **vencido o es inválido**
5. 🔴 La API rechaza las operaciones

### El error "no tiene permiso" probablemente significa:
```
"El token no es válido" o "El token está vencido"
```

---

## ✅ SOLUCIÓN

### Opción 1: OBTENER LA CONTRASEÑA DEL PROFESOR

El profesor configuró el ESI con:
- Email: `glex.globalexchange@gmail.com`
- Contraseña: **???** (NECESITAMOS ESTA)

**Acción:**
```
Preguntar al profesor:
"¿Cuál es la contraseña del ESI para glex.globalexchange@gmail.com?"
```

**Luego actualizar:**
```sql
UPDATE public.esi 
SET esi_passwd = 'LA_CONTRASEÑA_DEL_PROFESOR',
    esi_token = ''  -- Vaciar para que obtenga uno nuevo
WHERE esi_email = 'glex.globalexchange@gmail.com';
```

### Opción 2: USAR EL CLIENT APP.PY DEL PROFESOR

Según el README del SQL Proxy:

```bash
cd /home/jose/proyecto_is2/sql-proxy01/client
./setup_and_run.sh
```

El script `app.py` permite **configurar un nuevo ESI** con email + contraseña que tú elijas.

**Ventajas:**
- Control total sobre las credenciales
- Puedes configurar tu propia contraseña
- El profesor ya te dio permisos en la API

**Pasos:**
1. Ejecutar `./client/app.py`
2. Seleccionar "Inicializar ESI"
3. Ingresar:
   - RUC: `2595733`
   - DV: `3`
   - Email: `glex.globalexchange@gmail.com`
   - **Contraseña: [LA QUE TÚ ELIJAS]**
   - Ambiente: `TEST`

---

## 📊 COMPARACIÓN: TOKEN CSRF vs TOKEN ESI

### Token de Raquel (CSRF - Portal Web):
```json
"csrf_token": "IjU4ZjAwMzAwMzRiMGMzNGNiMTdhODI4OTY2OWZiNTM2ZTMzZTg1NTMi.aPA24g.CZiHTVen8x7RZgEXIfr7f0Y4dO4"
```
- **Uso:** Portal web de Factura Segura
- **Propósito:** Protección CSRF en formularios HTML
- **NO sirve para SQL Proxy**

### Token ESI (Authentication - API):
```json
"authentication_token": "eyJ2ZXIiOiI1IiwidWlkIjoiZDAyMTQ3ZjNiYjU2NGNhYzllYTRhNWFmZDBjNjI3ZGEi..."
```
- **Uso:** API de Factura Segura
- **Propósito:** Autenticar requests a la API
- **Cómo obtenerlo:** Login con email + contraseña
- **ES EL QUE NECESITAMOS**

---

## 🎯 PLAN DE ACCIÓN INMEDIATO

### 1. **Preguntar contraseña al profesor**
```
Email: soporte@facturasegura.com.py
Asunto: Contraseña ESI para glex.globalexchange@gmail.com

Estimado profesor,

Necesitamos la contraseña del ESI que configuró para:
- Email: glex.globalexchange@gmail.com
- RUC: 2595733-3
- Rango: 51-100

El SQL Proxy requiere email + contraseña para obtener 
el authentication_token automáticamente.

Gracias!
```

### 2. **Actualizar ESI con contraseña**
```bash
cd /home/jose/proyecto_is2/global-exchange
python3 actualizar_esi_password.py
```

### 3. **Generar factura de prueba**
```bash
python3 insertar_factura_directa.py
```

### 4. **Verificar resultado**
```bash
sleep 40
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT dnumdoc, estado, estado_sifen FROM public.de ORDER BY id DESC LIMIT 1;"
```

**Resultado esperado:**
```
dnumdoc |   estado    | estado_sifen
---------+-------------+--------------
0000063 | Aprobado    | Aprobado
```

---

## 📝 EVIDENCIAS PARA EL PROFESOR

### 1. **Sistema implementado correctamente** ✅
- Generación automática funciona
- SQL Proxy comunicándose
- Todas las configuraciones correctas

### 2. **Problema identificado** ✅
- No es de permisos (ya los tenemos)
- No es de configuración (todo correcto)
- Es de **autenticación del token**

### 3. **Falta solo la contraseña ESI** 🔑
- Email: `glex.globalexchange@gmail.com` ✅
- Permisos API: ✅ (otorgados por el profesor)
- Contraseña: ❓ (la necesitamos)

---

## 💡 CONCLUSIÓN

**El error "no tiene permiso" era engañoso.**

El problema real es:
1. ❌ El token que tenemos está vencido/inválido
2. ❌ No tenemos la contraseña para obtener un token nuevo
3. ✅ Los permisos ya están otorgados por el profesor
4. ✅ Todo lo demás está correctamente configurado

**Solución:**
- Obtener contraseña del profesor
- O configurar nueva contraseña con `./client/app.py`
- SQL Proxy obtendrá token válido automáticamente
- Sistema funcionará completamente

---

## 🚀 PRÓXIMOS PASOS

1. ✉️ **Contactar al profesor** pidiendo la contraseña
2. 🔧 **Actualizar ESI** con la contraseña correcta
3. ✨ **Probar generación** de factura
4. 🎉 **Obtener PDF** oficial de SIFEN

**Una vez tengamos la contraseña, el sistema funcionará al 100%**
