# 📋 Integración de Facturación Electrónica con Sistema de Roles y Permisos

## ✅ Sistema Implementado (SIN Django Admin)

El módulo de facturación electrónica está **completamente integrado** con el sistema de roles y permisos personalizado de Global Exchange.

---

## 🔐 Permisos Creados

### **Para Clientes:**
- `view_facturas_propias` - Ver sus propias facturas
- `download_kude_pdf` - Descargar PDFs de sus facturas

### **Para Operadores de Cuenta:**
- `view_facturas_asignadas` - Ver facturas de clientes asignados
- `generar_factura` - Generar facturas para transacciones completadas

### **Para Supervisores/Gerentes:**
- `view_todas_facturas` - Ver todas las facturas del sistema
- `view_reporte_facturacion` - Ver reportes consolidados
- `export_reporte_facturacion` - Exportar reportes
- `sync_sifen` - Sincronizar estados con SIFEN

### **Para Administradores (Crítico):**
- `generar_factura_manual` - Crear facturas sin transacción
- `cancelar_factura` - Anular facturas aprobadas
- `inutilizar_numero` - Inutilizar números de timbrado
- `manage_config_facturacion` - Administrar configuración del sistema
- `download_kude_xml` - Descargar XMLs

---

## 🌐 URLs Disponibles

### **Para Clientes:**
```
/facturacion/mis-facturas/           # Ver mis facturas
/facturacion/<id>/                   # Ver detalle de factura propia
/facturacion/<id>/pdf/               # Descargar PDF
```

### **Para Staff con Permisos:**
```
/facturacion/                        # Lista todas las facturas
/facturacion/generar/<transaccion>/  # Generar factura
/facturacion/<id>/actualizar-estado/ # Sincronizar con SIFEN
/facturacion/<id>/cancelar/          # Anular factura
/facturacion/<id>/xml/               # Descargar XML
/facturacion/reporte/                # Ver reportes
```

---

## 📝 Cómo Asignar Permisos a Roles

### 1. Sincronizar permisos (ya hecho)
```bash
poetry run python manage.py sync_permissions
```

### 2. Ver todos los permisos disponibles
```bash
poetry run python manage.py show_all_perm
```

### 3. Asignar permisos a un rol

Puedes usar el panel de gestión de roles (sin Django Admin) o hacerlo por código:

```python
from django.contrib.auth.models import Group, Permission

# Ejemplo: Asignar permisos al rol "Operador de Cuenta"
operador = Group.objects.get(name='Operador de Cuenta')

permisos_operador = [
    'facturacion_electronica.view_facturas_asignadas',
    'facturacion_electronica.generar_factura',
    'facturacion_electronica.download_kude_pdf',
]

for codename in permisos_operador:
    app, perm = codename.split('.')
    permiso = Permission.objects.get(
        content_type__app_label=app,
        codename=perm
    )
    operador.permissions.add(permiso)
```

---

## 🎯 Flujo de Trabajo Completo

### **Escenario 1: Cliente ve sus facturas**
1. Cliente inicia sesión
2. Va a `/facturacion/mis-facturas/`
3. Ve solo SUS facturas (filtradas automáticamente)
4. Puede descargar PDFs

### **Escenario 2: Operador genera factura**
1. Operador con permiso `generar_factura` inicia sesión
2. Cliente completa una transacción
3. Operador va a la transacción y genera factura
4. Sistema automáticamente:
   - Conecta al SQL Proxy
   - Inserta datos en tablas `de`, `gActEco`, `gCamItem`, `gPaConEIni`
   - SQL Proxy procesa y envía a SIFEN
   - Factura queda disponible con PDF/XML

### **Escenario 3: Supervisor revisa todo**
1. Supervisor con permiso `view_todas_facturas` inicia sesión
2. Va a `/facturacion/` y ve TODAS las facturas
3. Puede filtrar, buscar, sincronizar estados
4. Accede a reportes consolidados

---

## 🚀 Comandos Útiles

### Ver matriz de permisos
```bash
poetry run python manage.py show_permission_matrix
```

### Ver permisos de facturación
```bash
poetry run python manage.py show_all_perm | grep facturacion
```

### Crear usuario de prueba con permisos
```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Crear operador
operador = User.objects.create_user(
    username='operador1',
    password='test1234',
    is_staff=True
)

# Asignar al grupo "Operador de Cuenta"
grupo = Group.objects.get(name='Operador de Cuenta')
operador.groups.add(grupo)
```

---

## 🔧 Integración con Transacciones

Para generar automáticamente facturas cuando una transacción se completa:

```python
# En tu vista de completar transacción
from facturacion_electronica.utils import generar_factura_desde_transaccion

def completar_transaccion(request, transaccion_id):
    transaccion = get_object_or_404(Transaccion, pk=transaccion_id)
    
    # ... tu lógica de completar transacción ...
    
    transaccion.estado = 'completada'
    transaccion.save()
    
    # Generar factura automáticamente
    if request.user.has_perm('facturacion_electronica.generar_factura'):
        try:
            factura = generar_factura_desde_transaccion(transaccion)
            messages.success(
                request, 
                f'Transacción completada. Factura {factura.numero_factura} generada.'
            )
        except Exception as e:
            messages.warning(
                request,
                f'Transacción completada pero no se pudo generar factura: {e}'
            )
```

---

## 📊 Estructura de Permisos por Rol

### **Cliente** (No Staff)
- ✅ Ver sus propias facturas
- ✅ Descargar PDFs de sus facturas
- ❌ No puede generar, cancelar ni ver facturas de otros

### **Operador de Cuenta** (Staff Básico)
- ✅ Ver facturas de clientes asignados
- ✅ Generar facturas para transacciones completadas
- ✅ Descargar PDFs
- ❌ No puede cancelar ni ver todas

### **Supervisor** (Staff Avanzado)
- ✅ Ver TODAS las facturas del sistema
- ✅ Generar facturas
- ✅ Ver reportes consolidados
- ✅ Sincronizar con SIFEN
- ✅ Descargar PDFs y XMLs
- ⚠️ Puede cancelar facturas (con auditoría)

### **Administrador** (Crítico)
- ✅ TODO lo anterior +
- ✅ Generar facturas manuales
- ✅ Inutilizar números de timbrado
- ✅ Administrar configuración del sistema

---

## 🎓 Para Presentar al Profesor

**Destacar:**
1. ✅ **NO usamos Django Admin** - Sistema de permisos propio
2. ✅ **Separación de roles clara** - Cliente vs Staff vs Supervisor vs Admin
3. ✅ **Auditoría completa** - Permisos críticos con `requiere_auditoria=True`
4. ✅ **Integración con SQL Proxy** - No reinventamos la rueda
5. ✅ **Escalable** - Fácil agregar más permisos o roles

**Demostración:**
1. Mostrar cliente viendo solo sus facturas
2. Mostrar operador generando factura
3. Mostrar supervisor con reporte completo
4. Mostrar permisos granulares en el código

---

## 📁 Archivos Clave

```
roles/management/commands/permissions_defs/
  └── facturacion_electronica.py  # 14 permisos definidos

facturacion_electronica/
  ├── views.py          # Vistas protegidas con @require_permission
  ├── urls.py           # URLs con namespace 'facturacion'
  ├── models.py         # Modelo FacturaElectronica
  ├── services.py       # SQLProxyService
  └── templates/
      └── facturacion/
          ├── lista_facturas.html       # Vista staff
          ├── mis_facturas.html         # Vista cliente
          └── detalle_factura.html      # Detalle compartido
```

---

## ✅ Checklist Final

- [x] Permisos definidos en `roles/management/commands/permissions_defs/`
- [x] Permisos sincronizados con `sync_permissions`
- [x] Vistas protegidas con `@require_permission`
- [x] URLs integradas en proyecto principal
- [x] Templates creados con Bootstrap
- [x] Facturación funcionando (factura 0000051 generada)
- [x] Sistema NO usa Django Admin
- [x] Listo para demostración al profesor

---

**¡Tu sistema de facturación electrónica está listo para producción!** 🎉
