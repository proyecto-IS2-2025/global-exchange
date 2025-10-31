# 🚀 Inicialización del Sistema - Global Exchange

Este documento explica cómo inicializar completamente el sistema con todos los datos y permisos necesarios.

## 📋 Scripts Disponibles

### 1. `setup_system.py` - Script Completo de Inicialización ⭐

**Este es el script recomendado para usar.** Realiza todo el proceso de inicialización en el orden correcto:

```bash
python setup_system.py
```

**¿Qué hace?**
1. ✅ Verifica la conexión a la base de datos
2. ✅ Carga todos los fixtures en el orden correcto (respetando dependencias)
3. ✅ Sincroniza todos los permisos personalizados
4. ✅ Asigna permisos a los grupos según la matriz de permisos
5. ✅ Verifica que los grupos tengan permisos correctos
6. ✅ Verifica que el usuario dev existe
7. ✅ Muestra un resumen completo del sistema

**Características:**
- 🎨 Salida colorizada para fácil lectura
- ⚠️ Detecta problemas de codificación UTF-16
- 📊 Reporta estadísticas detalladas
- 🛡️ Manejo robusto de errores

### 2. `load_all_fixtures.py` - Solo Carga de Fixtures

Si solo necesitas cargar los fixtures sin sincronizar permisos:

```bash
python load_all_fixtures.py
```

### 3. Sincronización Manual de Permisos

Si ya tienes los datos y necesitas sincronizar/asignar permisos:

```bash
# Sincronizar permisos personalizados
python manage.py sync_permissions

# Asignar permisos a grupos
python manage.py assign_group_permissions --force
```

## 🔑 Permisos por Grupo

Después de ejecutar `setup_system.py`, cada grupo tendrá estos permisos:

| Grupo | Permisos Asignados | Descripción |
|-------|-------------------|-------------|
| **administrador** | 62 permisos | Acceso completo al sistema |
| **operador** | 23 permisos | Gestión de clientes, transacciones y cotizaciones |
| **observador** | 16 permisos | Solo lectura de datos del sistema |
| **cliente** | 12 permisos | Gestión de sus datos + operaciones de compra/venta |
| **usuario_registrado** | 8 permisos | Visualización limitada |
| **usuario_no_registrado** | 3 permisos | Solo cotizaciones públicas |
| **dev** | 0 permisos* | *Superusuario - acceso total sin permisos |

## 👥 Usuarios de Prueba

Después de ejecutar `setup_system.py`, tendrás estos usuarios disponibles:

| Email | Contraseña | Rol | Descripción |
|-------|------------|-----|-------------|
| `dev@test.com` | `12345678` | **Superusuario** | Acceso total al sistema |
| `admin@gmail.com` | `12345678` | Administrador | Gestión completa |
| `operador@test.com` | `12345678` | Operador | Operaciones del día a día |
| `observador@test.com` | `12345678` | Observador | Solo lectura |
| `cliente@test.com` | `12345678` | Cliente | Cliente del sistema |
| `user1@gmail.com` | `12345678` | Cliente | Cliente de prueba 1 |
| `user2@gmail.com` | `12345678` | Cliente | Cliente de prueba 2 |
| `user3@gmail.com` | `12345678` | Cliente | Cliente de prueba 3 |
| `user4@gmail.com` | `12345678` | Usuario Registrado | Usuario registrado |
| `registrado@test.com` | `12345678` | Usuario Registrado | Usuario registrado |

## 📦 Fixtures Incluidos

El sistema carga los siguientes datos:

1. **Usuarios** (`users/fixtures/users_data.json`)
   - 10 usuarios de prueba
   - Incluye dev, admin, operador, observador, clientes

2. **Roles y Grupos** (`roles/fixtures/roles_data.json`)
   - 7 grupos: dev, operador, observador, usuario_no_registrado, cliente, usuario_registrado, administrador
   - Permisos personalizados sincronizados

3. **Divisas** (`divisas/fixtures/divisas_data.json`)
   - 10 divisas (USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, MXN, PYG)

4. **Denominaciones** (`divisas/fixtures/denominaciones_data.json`)
   - Billetes y monedas para cada divisa

5. **Medios de Pago** (`medios_pago/fixtures/medios_data.json`)
   - Banco local
   - Tarjeta de crédito internacional
   - Billetera electrónica

6. **Medios Financieros** (`medios_pago/fixtures/mediosfinancieros_data.json`)
   - 17 configuraciones de campos dinámicos

7. **Clientes** (`clientes/fixtures/clientes_data.json`)
   - 3 clientes con cotizaciones por segmento

8. **Medios Financieros Cliente** (`clientes/fixtures/mediosfinancieroscliente_data.json`)
   - 5 medios de pago configurados para clientes

9. **Bancos** (`banco/fixtures/bancos_data.json`)
   - Datos de bancos

10. **Billeteras** (`billetera/fixtures/billetera_data.json`)
    - Datos de billeteras electrónicas

## 🔧 Solución de Problemas

### Error de Codificación UTF-16

Si ves errores como:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0
```

**Solución:** Los fixtures deben estar en UTF-8. El script `setup_system.py` detecta automáticamente este problema.

Para convertir manualmente:
```bash
python fix_all_fixtures_encoding.py
```

### Error de Dependencias Faltantes

Si ves errores de foreign keys:
```
IntegrityError: la llave (user_id)=(11) no está presente en la tabla
```

**Solución:** Los fixtures deben cargarse en el orden correcto. El script `setup_system.py` ya maneja esto.

### Permisos No Aplicados

Si los usuarios no tienen permisos después de cargar fixtures:

```bash
python manage.py sync_permissions
```

## 🎯 Workflow Recomendado

### Para Desarrollo Local

1. **Primera vez:**
   ```bash
   # Crear y aplicar migraciones
   python manage.py migrate
   
   # Inicializar todo el sistema
   python setup_system.py
   ```

2. **Después de cambios en fixtures:**
   ```bash
   python setup_system.py
   ```

3. **Después de cambios en permisos:**
   ```bash
   python manage.py sync_permissions
   ```

### Para Resetear la Base de Datos

```bash
# 1. Borrar la base de datos (cuidado en producción!)
python manage.py flush --no-input

# 2. Volver a inicializar
python setup_system.py
```

## 📝 Notas Importantes

- ⚠️ **Contraseñas de prueba:** Todos los usuarios usan `12345678`. **Cambiar en producción.**
- ⚠️ **Usuario dev:** Es superusuario, tiene acceso total al sistema.
- ⚠️ **Fixtures en producción:** No ejecutar en producción sin revisar los datos.
- ✅ **Codificación:** Todos los fixtures deben estar en UTF-8 sin BOM.
- ✅ **Orden de carga:** Los scripts respetan automáticamente el orden de dependencias.

## 🔐 Seguridad

Antes de desplegar a producción:

1. ✅ Cambiar todas las contraseñas de usuarios de prueba
2. ✅ Eliminar o desactivar el usuario `dev` si no es necesario
3. ✅ Revisar permisos de cada grupo
4. ✅ Configurar variables de entorno para datos sensibles

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs del script (tienen colores para fácil lectura)
2. Verifica que la base de datos esté corriendo
3. Asegúrate de que las migraciones estén aplicadas
4. Revisa que los fixtures estén en UTF-8

---

**¡El sistema está listo para usar! 🎉**
