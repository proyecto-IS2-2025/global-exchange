# Guía de Solución Rápida

## El problema encontrado:

El formulario **SÍ tiene** la opción "Reporte Periódico" en el código HTML generado, 
pero no aparece en tu navegador.

## Solución:

### Opción 1: Recarga Forzada (Recomendada)
1. En la página de gestión de notificaciones
2. Presiona **Ctrl + Shift + R** (Chrome/Edge) o **Ctrl + F5** (Firefox)
3. Esto limpia el caché y recarga completamente

### Opción 2: Limpiar Caché del Navegador
1. Abre las herramientas de desarrollo (F12)
2. Click derecho en el botón de recargar
3. Selecciona "Vaciar caché y recargar de forma forzada"

### Opción 3: Modo Incógnito
1. Abre una ventana de incógnito (Ctrl + Shift + N)
2. Ve a http://127.0.0.1:8000/notificaciones/
3. Inicia sesión
4. Deberías ver la opción "Reporte Periódico"

## Verificación del HTML

El HTML generado por Django es:
```html
<select name="tipo_alerta" class="form-select" id="id_tipo_alerta">
  <option value="general" selected>Cambio General</option>
  <option value="umbral">Alcanzar Umbral</option>
  <option value="periodica">Reporte Periódico</option>  ← ESTA OPCIÓN EXISTE
</select>
```

## Si aún no aparece:

1. Verifica en la consola del navegador (F12) si hay errores JavaScript
2. Inspecciona el elemento del select y verifica el HTML
3. Asegúrate de estar en la página correcta: /notificaciones/
