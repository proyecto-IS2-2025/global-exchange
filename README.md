# 🔐 Sistema de Permisos - Guía de Uso

## 📋 Tabla de Contenidos

1. [Arquitectura](#arquitectura)
2. [Instalación Inicial](#instalación-inicial)
3. [Usuarios de Prueba](#usuarios-de-prueba)
4. [Comandos Disponibles](#comandos-disponibles)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## 🏗️ Arquitectura

El sistema de permisos utiliza una **arquitectura híbrida**:

```
┌─────────────────────────────────────────────────────────┐
│  FIXTURES JSON (usuarios y roles básicos)               │
│  - users/fixtures/users_data.json                       │
│  - roles/fixtures/roles_data.json                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  PERMISOS PERSONALIZADOS (definidos en código)          │
│  - roles/management/commands/permissions_defs/          │
│  - Sincronizados con: python manage.py sync_permissions │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ASIGNACIÓN DINÁMICA (script de management)             │
│  - roles/management/commands/setup_test_roles.py        │
│  - Asigna permisos a roles por codename                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Instalación Inicial

### Opción A: Script Automático (Recomendado)

**Windows:**
```bash
setup_system.bat
```

**Linux/Mac:**
```bash
chmod +x setup_system.sh
./setup_system.sh
```

### Opción B: Manual

```bash
# 1. Aplicar migraciones
python manage.py migrate

# 2. Sincronizar permisos personalizados
python manage.py sync_permissions

# 3. Cargar roles
python manage.py loaddata roles/fixtures/roles_data.json

# 4. Cargar usuarios
python manage.py loaddata users/fixtures/users_data.json

# 5. Asignar permisos a roles
python manage.py setup_test_roles

# 6. Verificar configuración
python manage.py show_permission_matrix
```

---

## 👥 Usuarios de Prueba

| Usuario | Email | Contraseña | Rol | Permisos |
|---------|-------|------------|-----|----------|
| `test_admin` | test_admin@test.com | admin123 | Admin | ✅ Acceso total |
| `test_operador` | test_operador@test.com | admin123 | Operador | ⚠️ Limitado a clientes asignados |
| `test_cliente` | test_cliente@test.com | admin123 | Cliente | ℹ️ Solo operaciones propias |

---

## 🛠️ Comandos Disponibles

### `sync_permissions`
Sincroniza permisos personalizados definidos en `permissions_defs/`

```bash
python manage.py sync_permissions
```

**Cuándo usar:**
- Después de agregar nuevos permisos en `permissions_defs/`
- Después de modificar descripciones de permisos existentes
- En cada deploy a producción

---

### `setup_test_roles`
Asigna permisos a los roles del sistema

```bash
# Asignar permisos (modo silencioso)
python manage.py setup_test_roles

# Asignar permisos (modo verbose)
python manage.py setup_test_roles --verbose
```

**Cuándo usar:**
- Después de crear nuevos roles
- Después de `sync_permissions`
- Para resetear permisos de roles existentes

---

### `show_permission_matrix`
Muestra la matriz de permisos asignados

```bash
# Ver matriz completa
python manage.py show_permission_matrix

# Ver permisos de un rol específico
python manage.py show_permission_matrix --role admin

# Exportar a CSV
python manage.py show_permission_matrix --export
```

---

## 🧪 Testing

### Checklist de Pruebas Manuales

#### Test 1: Usuario Admin
```
☐ Login con test_admin@test.com
☐ Ver dashboard completo con TODAS las opciones
☐ Acceder a "Ver Clientes" → Debe mostrar lista completa
☐ Acceder a "Roles y Permisos" → Debe permitir editar
☐ Acceder a "Divisas" → Debe permitir configurar tasas
☐ Intentar crear límite diario → Debe funcionar
```

#### Test 2: Usuario Operador
```
☐ Login con test_operador@test.com
☐ Ver dashboard LIMITADO (sin botón "Roles y Permisos")
☐ NO ver botón "Asignar Cliente"
☐ Puede ver "Ver Clientes" pero solo asignados
☐ Acceder a /roles/groups/ → Debe redirigir a 403
☐ Intentar crear límite → Debe denegar acceso
```

#### Test 3: Usuario Cliente
```
☐ Login con test_cliente@test.com
☐ Ver SOLO menu_cliente.html (botón "Realizar Operación")
☐ Puede realizar operaciones de compra/venta
☐ NO ver opciones de staff en menú
☐ Acceder a /clientes/lista/ → Debe redirigir a 403
☐ Acceder a /roles/groups/ → Debe redirigir a 403
```

### Pruebas Automatizadas

```bash
# Ejecutar tests de permisos
python manage.py test roles.tests_permisos

# Ejecutar todos los tests
python manage.py test
```

---

## 🔧 Troubleshooting

### Problema: "Permission not found"

**Síntoma:**
```
⚠ Permiso no encontrado: view_all_clientes
```

**Solución:**
```bash
python manage.py sync_permissions
python manage.py setup_test_roles
```

---

### Problema: "Grupo no encontrado"

**Síntoma:**
```
✗ Grupo "admin" no encontrado
```

**Solución:**
```bash
python manage.py loaddata roles/fixtures/roles_data.json
python manage.py setup_test_roles
```

---

### Problema: Usuario puede acceder a URL prohibida

**Síntoma:**
Usuario operador accede a `/roles/groups/` sin problema

**Causas posibles:**
1. Vista NO tiene decorador `@require_permission`
2. Template muestra botón sin verificar `{% if perms.xxx %}`

**Solución:**
```python
# En la vista
from clientes.decorators import require_permission

@login_required
@require_permission("roles.manage_groups", check_client_assignment=False)
def group_list(request):
    # ...
```

```django
{# En el template #}
{% if perms.roles.manage_groups %}
  <a href="{% url 'group_list' %}">Gestionar Roles</a>
{% endif %}
```

---

### Problema: Matriz de permisos vacía

**Síntoma:**
`show_permission_matrix` no muestra permisos

**Solución:**
```bash
# Verificar que los permisos existen
python manage.py shell
>>> from django.contrib.auth.models import Permission
>>> Permission.objects.filter(codename='view_all_clientes').exists()

# Si retorna False:
python manage.py sync_permissions
python manage.py setup_test_roles
```

---

## 📚 Referencias

- [Documentación oficial de permisos Django](https://docs.djangoproject.com/en/stable/topics/auth/default/#permissions-and-authorization)
- Informe técnico: `permisos.txt`
- Tests: `roles/tests_permisos.py`

---

## 📞 Soporte

Para reportar problemas o sugerir mejoras:
1. Ejecutar `python manage.py show_permission_matrix --export`
2. Adjuntar el archivo CSV generado
3. Describir el comportamiento esperado vs. el observado