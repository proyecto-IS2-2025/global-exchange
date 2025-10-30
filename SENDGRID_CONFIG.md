# Configuración de SendGrid para Global Exchange

## 🎯 Problema Actual
El error `TimeoutError: timed out` ocurre porque Render no puede conectarse al servidor SMTP de SendGrid debido a que falta la API Key en las variables de entorno.

## 📋 Solución Paso a Paso

### 1. Obtener API Key de SendGrid

1. Ve a [SendGrid](https://app.sendgrid.com/)
2. Inicia sesión o crea una cuenta gratuita
3. Ve a **Settings** → **API Keys**
4. Haz clic en **Create API Key**
5. Dale un nombre descriptivo (ej: `global-exchange-production`)
6. Selecciona **Full Access** o al menos **Mail Send** permissions
7. Haz clic en **Create & View**
8. **⚠️ IMPORTANTE**: Copia la API Key inmediatamente (solo se muestra una vez)

### 2. Verificar Sender Identity en SendGrid

SendGrid requiere que verifiques el email desde el cual enviarás mensajes:

#### Opción A: Single Sender Verification (Más rápido)
1. Ve a **Settings** → **Sender Authentication**
2. Haz clic en **Verify a Single Sender**
3. Completa el formulario con:
   - **From Name**: Global Exchange
   - **From Email Address**: glex.globalexchange.respaldo@gmail.com
   - **Reply To**: glex.globalexchange.respaldo@gmail.com
   - Completa los demás campos
4. Haz clic en **Create**
5. Revisa tu email y haz clic en el link de verificación

#### Opción B: Domain Authentication (Recomendado para producción)
1. Ve a **Settings** → **Sender Authentication**
2. Haz clic en **Authenticate Your Domain**
3. Sigue las instrucciones para agregar registros DNS

### 3. Configurar Variables de Entorno en Render

1. Ve a tu dashboard de Render: https://dashboard.render.com/
2. Selecciona tu servicio **global-exchange**
3. Ve a la pestaña **Environment**
4. Agrega las siguientes variables:

```
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=glex.globalexchange.respaldo@gmail.com
DEBUG=False
```

5. Haz clic en **Save Changes**

### 4. Re-desplegar en Render

Render re-desplegará automáticamente tu aplicación cuando guardes los cambios en las variables de entorno.

## 🔍 Verificar Configuración

### Verificar que las variables están configuradas:
Puedes verificar en los logs de Render que las variables se cargaron correctamente.

### Probar el envío de email:
1. Intenta hacer login en tu aplicación en Render
2. El sistema debería enviar el código OTP sin errores
3. Si hay problemas, revisa los logs de Render

### Ver estadísticas en SendGrid:
1. Ve a **Activity** en tu dashboard de SendGrid
2. Verás todos los emails enviados, abiertos, clicks, etc.

## 📊 Configuración Actual en settings.py

```python
if DEBUG:
    # ✅ DESARROLLO LOCAL: Gmail SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'glex.globalexchange.respaldo@gmail.com')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'itlf keib ybar gyds')
    DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER', 'glex.globalexchange.respaldo@gmail.com')
else:
    # ✅ PRODUCCIÓN: SendGrid
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_TIMEOUT = 10
    EMAIL_HOST_USER = 'apikey'  # ← Literalmente la palabra "apikey"
    EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'glex.globalexchange.respaldo@gmail.com')
```

## 🎓 Límites del Plan Gratuito de SendGrid

- **100 emails/día** de forma gratuita
- Para más volumen, necesitarás un plan de pago
- Monitorea tu uso en el dashboard

## 🆘 Troubleshooting

### Error: "The from email does not match a verified Sender Identity"
**Solución**: Verifica tu email en SendGrid (paso 2)

### Error: "Forbidden"
**Solución**: Verifica que la API Key tenga permisos de "Mail Send"

### Error: "Unauthorized"
**Solución**: La API Key es incorrecta, genera una nueva

### Error: Timeout
**Solución**: 
- Verifica que `SENDGRID_API_KEY` esté en las variables de entorno de Render
- Verifica que `DEBUG=False` en producción

## 📝 Checklist Final

- [ ] Cuenta de SendGrid creada
- [ ] API Key generada y copiada
- [ ] Sender Identity verificado
- [ ] Variable `SENDGRID_API_KEY` agregada en Render
- [ ] Variable `DEFAULT_FROM_EMAIL` agregada en Render
- [ ] Variable `DEBUG=False` configurada en Render
- [ ] Aplicación re-desplegada
- [ ] Prueba de login exitosa
- [ ] Email OTP recibido

## 🔗 Enlaces Útiles

- [SendGrid Dashboard](https://app.sendgrid.com/)
- [SendGrid API Keys](https://app.sendgrid.com/settings/api_keys)
- [SendGrid Sender Authentication](https://app.sendgrid.com/settings/sender_auth)
- [Render Dashboard](https://dashboard.render.com/)
- [Documentación SendGrid Django](https://docs.sendgrid.com/for-developers/sending-email/django)
