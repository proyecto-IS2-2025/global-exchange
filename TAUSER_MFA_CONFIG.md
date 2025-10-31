# Configuración de MFA para Sistema TAUSER

## 📋 Descripción

El sistema TAUSER incluye autenticación de dos factores (MFA) por correo electrónico para mayor seguridad al acceder a las transacciones mediante código TAUSER.

## 🔒 Estado del MFA

Por defecto, **MFA está HABILITADO** para máxima seguridad en producción.

## ⚙️ Cómo Habilitar/Deshabilitar MFA

### Acceso a Configuración MFA

1. Iniciar sesión como **administrador**
2. Ir al menú de **Configuración MFA**
3. Verás tres opciones de configuración:
   - **MFA en Inicio de Sesión**: Para el login de usuarios
   - **MFA en Confirmación de Compra**: Para confirmar transacciones de compra
   - **MFA en Tausers**: Para acceder a transacciones en terminales TAUSER 🆕

### Cambiar Estado de MFA en Tausers

En la pantalla de Configuración MFA:

1. Localizar la sección **"MFA en Tausers"**
2. Ver el estado actual (badge verde "ACTIVO" o gris "INACTIVO")
3. Hacer clic en el botón correspondiente:
   - **"Desactivar"** (rojo): Si está activo y deseas deshabilitarlo
   - **"Activar"** (verde): Si está inactivo y deseas habilitarlo
4. El cambio se aplicará inmediatamente
5. Verás un mensaje de confirmación: "MFA en Tausers activado/desactivado exitosamente"

### Indicador Visual en Terminales

Los administradores verán en `/tauser/` un badge indicando el estado:

- 🟢 **Badge Verde**: "MFA Habilitado" ✅
- 🟡 **Badge Amarillo**: "MFA Deshabilitado (Modo Desarrollo)" ⚠️

## 🔄 Flujo con MFA Habilitado

1. Cliente ingresa código TAUSER de 8 dígitos
2. Sistema envía código OTP de 6 dígitos al email del cliente
3. Cliente ingresa código OTP en pantalla de verificación
4. Acceso concedido a detalles de la transacción

## ⚡ Flujo con MFA Deshabilitado

1. Cliente ingresa código TAUSER de 8 dígitos
2. Sistema muestra mensaje: "✓ Código TAUSER verificado correctamente"
3. Acceso directo a detalles de la transacción (sin OTP)

## 🎯 Casos de Uso

### ✅ Habilitar MFA (Recomendado):
- **Producción**: Máxima seguridad para transacciones reales
- **Ambientes con datos sensibles**
- **Cumplimiento de normativas de seguridad**
- **Protección contra acceso no autorizado a terminales**

### ⚠️ Deshabilitar MFA (Solo Desarrollo):
- **Desarrollo local**: Para pruebas rápidas sin configurar email
- **Testing automatizado**: Para simplificar tests de integración
- **Demos**: Para demostrar funcionalidad sin delays
- **Ambientes de capacitación**: Para simplificar el proceso de aprendizaje

## 🗄️ Persistencia de Configuración

- La configuración se guarda en la base de datos (modelo `MFAConfig`)
- Es un **singleton**: Solo existe un registro de configuración
- Persiste entre reinicios del servidor
- Se registra quién hizo el último cambio y cuándo
- No requiere modificar código ni archivos de configuración

## ⚠️ Advertencias de Seguridad

- ⛔ **NO deshabilitar MFA en producción** sin justificación válida
- 🔒 Deshabilitar MFA reduce la seguridad de las transacciones
- 📧 Asegurarse de tener configuración de email correcta si MFA está habilitado
- 🔐 Considerar implementar otros métodos de autenticación si se deshabilita MFA

## 📝 Logs y Monitoreo

Cuando MFA está deshabilitado, el sistema:
- ✓ Salta el paso de envío de OTP
- ✓ Marca automáticamente la sesión como verificada
- ✓ Redirige directamente a la vista de detalles
- ✓ Muestra mensaje: "✓ Código TAUSER verificado correctamente"

## 🔍 Verificación de Estado Actual

Para verificar el estado actual del MFA en Tausers:

1. **Desde la interfaz web**:
   - Ir a la página de Configuración MFA
   - Ver el badge junto a "MFA en Tausers"

2. **Desde la base de datos**:
   ```sql
   SELECT mfa_tauser_enabled FROM mfa_mfaconfig WHERE id = 1;
   ```

3. **Desde el código Python**:
   ```python
   from mfa.models import MFAConfig
   config = MFAConfig.get_config()
   print(f"MFA en Tausers: {'Habilitado' if config.mfa_tauser_enabled else 'Deshabilitado'}")
   ```

## 🧪 Testing

Para tests automatizados, puedes modificar temporalmente la configuración:

```python
from mfa.models import MFAConfig

def test_tauser_sin_mfa():
    config = MFAConfig.get_config()
    config.mfa_tauser_enabled = False
    config.save()
    
    # Tu test aquí
    
    # Restaurar al finalizar
    config.mfa_tauser_enabled = True
    config.save()
```

O usar `setUp` y `tearDown` en tests:

```python
class TauserTestCase(TestCase):
    def setUp(self):
        self.config = MFAConfig.get_config()
        self.original_state = self.config.mfa_tauser_enabled
        self.config.mfa_tauser_enabled = False
        self.config.save()
    
    def tearDown(self):
        self.config.mfa_tauser_enabled = self.original_state
        self.config.save()
    
    def test_acceso_sin_mfa(self):
        # Tu test aquí
        pass
```

## 🔐 Auditoría

El sistema registra automáticamente:
- ✓ Quién cambió la configuración (`updated_by`)
- ✓ Cuándo se hizo el cambio (`updated_at`)
- ✓ Estado anterior y nuevo (en los mensajes de éxito)

Esta información está visible en la parte inferior de la pantalla de Configuración MFA.

## 📞 Soporte

Para preguntas o problemas con la configuración de MFA, contactar al equipo de desarrollo.

---

**Última actualización**: 30 de Octubre, 2025
**Versión**: 1.0
