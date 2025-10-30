# Configuración de Email Actualizada

## 📧 Nueva Cuenta de Correo

Se actualizó la configuración de correo electrónico para notificaciones y MFA (Multi-Factor Authentication).

### ✅ Credenciales Actualizadas

**Correo electrónico:** `glex.globalexchange.respaldo@gmail.com`  
**Contraseña de aplicación:** `itlf keib ybar gyds`  
**Proveedor:** Gmail (SMTP)

## 📁 Archivo Modificado

**Archivo:** `casa_de_cambios/settings.py`

### Configuración Anterior:
```python
EMAIL_HOST_USER = 'glex.globalexchange.respaldo@gmail.com'
EMAIL_HOST_PASSWORD = 'itlf keib ybar gyds'
```

### Configuración Actual:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'glex.globalexchange.respaldo@gmail.com'
EMAIL_HOST_PASSWORD = 'itlf keib ybar gyds'
DEFAULT_FROM_EMAIL = 'glex.globalexchange.respaldo@gmail.com'
SERVER_EMAIL = 'glex.globalexchange.respaldo@gmail.com'
```

## 🔧 Nuevas Variables Agregadas

Se agregaron las siguientes variables de configuración para asegurar consistencia:

- **`DEFAULT_FROM_EMAIL`**: Email remitente por defecto para todas las notificaciones
- **`SERVER_EMAIL`**: Email usado para mensajes de error del servidor

## 📨 Funcionalidades Afectadas

Esta configuración se utiliza en:

### 1. **MFA (Multi-Factor Authentication)**
- **Archivo:** `mfa/utils.py`
- **Función:** Envío de códigos de verificación 2FA
- **Uso:** `send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])`

### 2. **Notificaciones de Transacciones**
- **Archivo:** `transacciones/models.py` (línea ~420)
- **Función:** Notificaciones de estado de transacciones
- **Uso:** `from_email=settings.EMAIL_HOST_USER`

### 3. **Autenticación y Recuperación**
- **Archivo:** `autenticacion/utils.py`
- **Función:** Emails de recuperación de contraseña, activación de cuenta, etc.
- **Uso:** `send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [email])`

## 🔐 Seguridad

### Contraseña de Aplicación de Gmail

La contraseña `iceq lnzf rtjl qgxx` es una **contraseña de aplicación** generada por Google, no la contraseña real de la cuenta.

#### ¿Qué es una contraseña de aplicación?
- Token de autenticación específico para aplicaciones
- Más seguro que usar la contraseña real
- Se puede revocar sin afectar el acceso a la cuenta principal
- Requerido cuando se usa verificación en dos pasos en Gmail

### Recomendaciones de Seguridad

1. ⚠️ **No compartir estas credenciales públicamente**
2. ⚠️ **No subir este archivo a repositorios públicos**
3. ✅ **Usar variables de entorno en producción** (recomendado):
   ```python
   import os
   EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'glex.globalexchange.respaldo@gmail.com')
   EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'itlf keib ybar gyds')
   ```
4. ✅ **Agregar `settings.py` al `.gitignore`** si contiene credenciales sensibles
5. ✅ **Rotar contraseñas de aplicación periódicamente**

## 🧪 Verificación de Funcionamiento

Para probar que el correo está funcionando correctamente:

### 1. Desde la consola de Django:
```python
python manage.py shell

from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Prueba de Configuración',
    'Este es un correo de prueba desde Global Exchange.',
    settings.EMAIL_HOST_USER,
    ['tu_email@ejemplo.com'],
    fail_silently=False,
)
```

### 2. Probar MFA:
- Iniciar sesión en el sistema
- Activar MFA en el perfil de usuario
- Verificar que llegue el código al correo

### 3. Probar notificaciones:
- Crear una transacción
- Verificar que lleguen las notificaciones de estado

## 📝 Notas Adicionales

### Límites de Gmail SMTP
- **Límite diario:** ~500 correos por día
- **Límite por hora:** ~100 correos por hora
- **Destinatarios por mensaje:** Máximo 100

Si se necesita enviar más correos, considerar:
- **SendGrid** (hasta 100 correos/día gratis)
- **Amazon SES**
- **Mailgun**
- **Servidor SMTP dedicado**

### Troubleshooting

Si los correos no se envían:

1. **Verificar credenciales:**
   ```bash
   python manage.py shell
   from django.conf import settings
   print(settings.EMAIL_HOST_USER)
   print(settings.EMAIL_HOST_PASSWORD)
   ```

2. **Verificar conexión SMTP:**
   - Puerto 587 debe estar abierto
   - TLS debe estar habilitado
   - Firewall/Antivirus no debe bloquear la conexión

3. **Verificar cuenta de Gmail:**
   - La cuenta debe tener verificación en dos pasos activada
   - La contraseña de aplicación debe ser válida
   - Verificar en Gmail > Seguridad > Contraseñas de aplicación

4. **Ver logs de error:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## ✅ Checklist de Configuración

- [x] Actualizar `EMAIL_HOST_USER`
- [x] Actualizar `EMAIL_HOST_PASSWORD`
- [x] Agregar `DEFAULT_FROM_EMAIL`
- [x] Agregar `SERVER_EMAIL`
- [ ] Probar envío de correo de prueba
- [ ] Probar MFA
- [ ] Probar notificaciones de transacciones
- [ ] Considerar variables de entorno para producción
- [ ] Documentar en el README del proyecto

---

**Fecha de actualización:** 17 de octubre de 2025  
**Rama:** develop  
**Autor:** GitHub Copilot Assistant  
**Motivo:** Cambio de cuenta de correo para notificaciones y MFA
