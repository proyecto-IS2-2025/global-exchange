# 📋 TODO: Implementar CRUD de Segmentos de Cliente

## 🎯 Objetivo
Implementar sistema completo de gestión de segmentos de cliente (VIP, Gold, Standard, etc.)

## 📦 Tareas Pendientes

### 1. Backend
- [ ] Crear vistas CRUD en `clientes/views/segmentos.py`
- [ ] Crear formularios en `clientes/forms.py`
- [ ] Agregar URLs en `clientes/urls.py`
- [ ] Crear tests en `clientes/tests/test_segmentos.py`

### 2. Frontend
- [ ] Crear template `segmentos_list.html`
- [ ] Crear template `segmento_form.html`
- [ ] Crear template `segmento_confirm_delete.html`
- [ ] Agregar estilos CSS específicos

### 3. Permisos
- [ ] Descomentar definiciones en `roles/management/commands/permissions_defs/clientes.py`
  - `manage_segmentos_cliente`
  - `view_segmentos_cliente`
- [ ] Agregar permisos a rol `admin` en `setup_test_roles.py`
- [ ] Ejecutar `python manage.py sync_permissions`
- [ ] Ejecutar `python manage.py setup_test_roles`

### 4. Validaciones
- [ ] Validar que no se eliminen segmentos con clientes asignados
- [ ] Validar nombres únicos de segmentos
- [ ] Validar rangos de descuentos (0-100%)

### 5. Auditoría
- [ ] Registrar creación de segmentos
- [ ] Registrar modificaciones de segmentos
- [ ] Registrar eliminaciones de segmentos

## 🔗 Archivos Relacionados
- `clientes/models.py` (modelo `SegmentoCliente` ya existe)
- `roles/management/commands/permissions_defs/clientes.py` (líneas 280-310)
- `roles/management/commands/setup_test_roles.py` (líneas 85-89, 190-195)

## 📅 Estado
**Pendiente** - No implementado aún

## 📌 Notas
- El modelo `SegmentoCliente` ya está definido en la base de datos
- Los permisos nativos de Django (`add_segmentocliente`, etc.) existen pero no se usan
- Cuando se implemente, seguir el patrón de `clientes/views/limite.py`