# ⚡ SETUP EN 1 COMANDO

## Para los Integrantes del Equipo

Ejecuta esto y tendrás todo configurado automáticamente:

```bash
cd global-exchange
poetry run python configurar_rango_automatico.py
```

**Resultado:**
```
🎉 CONFIGURACIÓN COMPLETADA

✅ Tu rango de facturas:
   Número inicial: 0000083
   Número final: 0000132
   Total disponible: 50 facturas

✅ ¡Todo listo! Puedes generar facturas sin conflictos.
```

---

## ¿Qué hace este comando?

1. ✅ Ve el último número usado (actualmente: **82**)
2. ✅ Te asigna automáticamente los próximos **50 números**
3. ✅ Actualiza tu `.env` con la configuración
4. ✅ Verifica que todo esté correcto

---

## ¿Y si varios lo ejecutamos?

**No problem.** Cada uno obtiene un rango diferente:

- **Primero** → 83-132
- **Segundo** → 133-182
- **Tercero** → 183-232

---

## Reiniciar el servidor

Después de configurar, reinicia Django:

```bash
pkill -f runserver
poetry run python manage.py runserver
```

---

## ¡Listo!

Ahora cuando generes facturas, el sistema automáticamente:
- ✅ Usa el próximo número de TU rango
- ✅ No colisiona con tus compañeros
- ✅ Te avisa si te quedas sin números

---

**Más info:** Consulta `PARA_EQUIPO.md` para detalles completos.
