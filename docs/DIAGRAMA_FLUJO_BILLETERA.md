# 🔄 Diagrama de Flujo - Pago con Billetera Digital

## 📊 Flujo General de Compra de Divisas

```
┌─────────────────────────────────────────────────────────────────┐
│                    INICIO: Cliente Compra Divisa                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Cliente Ingresa:                                                │
│  - Divisa a comprar (ej: USD)                                   │
│  - Monto (ej: 100 USD)                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Sistema Calcula:                                                │
│  - Tasa de cambio aplicada                                      │
│  - Monto en guaraníes (ej: ₲750,000)                           │
│  - Comisiones                                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Cliente Confirma Operación                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Selección de Medio de Pago                                      │
│  (Cliente elige de sus medios configurados)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Sistema Crea Transacción (Estado: Pendiente)                   │
│  - Tipo: compra                                                  │
│  - Divisa origen: PYG                                            │
│  - Divisa destino: USD                                           │
│  - Monto origen: ₲750,000                                        │
│  - Monto destino: USD 100                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
           ┌─────────────┴─────────────┐
           │  Detectar Tipo de Medio   │
           └─────────────┬─────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌──────────────┐          ┌──────────────┐
    │  ¿Billetera  │          │     Otro     │
    │ Electrónica? │          │  (Banco,     │
    │              │          │  Stripe,     │
    │              │          │  etc.)       │
    └──────┬───────┘          └──────┬───────┘
           │                         │
         SÍ│                         │NO
           │                         │
           ▼                         ▼
    ┌──────────────────┐     ┌─────────────────┐
    │ realizar_pago_   │     │  Flujo Normal   │
    │ billetera()      │     │  (Bancario,     │
    │                  │     │  Stripe, etc.)  │
    └──────┬───────────┘     └─────────┬───────┘
           │                           │
           │                           │
           └─────────┬─────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Actualizar Estado Transacción                                   │
│  - Si OK: Estado = "pagada"                                      │
│  - Si Error: Estado = "pendiente" (con mensaje de error)        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Mostrar Resultado al Usuario                                    │
│  - Comprobante de pago                                           │
│  - Detalle de la transacción                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                    ┌────────┐
                    │  FIN   │
                    └────────┘
```

## 🔄 Detalle: Función `realizar_pago_billetera()`

```
┌─────────────────────────────────────────────────────────────────┐
│  INICIO: realizar_pago_billetera(medio_datos, monto, ref)      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Importar Modelos                                                │
│  - Billetera, PagoBilletera, UsuarioBilletera                  │
│  - Cuenta, EntidadBancaria                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Extraer datos_campos de medio_datos                            │
│  - Buscar número de teléfono                                    │
│  - Buscar entidad bancaria (opcional)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
           ┌─────────────┴─────────────┐
           │  ¿Hay número de teléfono? │
           └─────────────┬─────────────┘
                         │
              NO ┌───────┴───────┐ SÍ
                 │               │
                 ▼               ▼
         ┌──────────────┐  ┌────────────────────┐
         │ ERROR 12     │  │ Buscar Usuario     │
         │ Datos        │  │ Billetera por      │
         │ incompletos  │  │ número teléfono    │
         └──────┬───────┘  └────────┬───────────┘
                │                   │
                │                   ▼
                │         ┌─────────┴──────────┐
                │         │  ¿Usuario existe?  │
                │         └─────────┬──────────┘
                │                   │
                │        NO ┌───────┴───────┐ SÍ
                │           │               │
                │           ▼               ▼
                │   ┌──────────────┐  ┌────────────────┐
                │   │ ERROR 14     │  │ Obtener        │
                │   │ Billetera no │  │ Billetera      │
                │   │ encontrada   │  │ Activa         │
                │   └──────┬───────┘  └────────┬───────┘
                │          │                   │
                │          │                   ▼
                │          │         ┌─────────┴──────────┐
                │          │         │ ¿Billetera activa? │
                │          │         └─────────┬──────────┘
                │          │                   │
                │          │        NO ┌───────┴───────┐ SÍ
                │          │           │               │
                │          │           ▼               ▼
                │          │   ┌──────────────┐  ┌────────────────┐
                │          │   │ ERROR 14     │  │ Verificar      │
                │          │   │ No activa    │  │ Saldo          │
                │          │   └──────┬───────┘  └────────┬───────┘
                │          │          │                   │
                │          │          │                   ▼
                │          │          │         ┌─────────┴──────────┐
                │          │          │         │ ¿Saldo suficiente? │
                │          │          │         └─────────┬──────────┘
                │          │          │                   │
                │          │          │        NO ┌───────┴───────┐ SÍ
                │          │          │           │               │
                │          │          │           ▼               ▼
                │          │          │   ┌──────────────┐  ┌────────────────┐
                │          │          │   │ ERROR 51     │  │ Obtener Cuenta │
                │          │          │   │ Saldo        │  │ Empresa        │
                │          │          │   │ insuficiente │  │ (Destino)      │
                │          │          │   └──────┬───────┘  └────────┬───────┘
                │          │          │          │                   │
                │          │          │          │                   ▼
                │          │          │          │         ┌─────────┴──────────┐
                │          │          │          │         │ ¿Cuenta encontrada?│
                │          │          │          │         └─────────┬──────────┘
                │          │          │          │                   │
                │          │          │          │        NO ┌───────┴───────┐ SÍ
                │          │          │          │           │               │
                │          │          │          │           ▼               ▼
                │          │          │          │   ┌──────────────┐  ┌────────────────┐
                │          │          │          │   │ ERROR 14     │  │ Crear          │
                │          │          │          │   │ Cuenta no    │  │ PagoBilletera  │
                │          │          │          │   │ encontrada   │  │                │
                │          │          │          │   └──────┬───────┘  │ ┌────────────┐ │
                │          │          │          │          │          │ │ AUTOMÁTICO:│ │
                │          │          │          │          │          │ │- Debita    │ │
                │          │          │          │          │          │ │  billetera │ │
                │          │          │          │          │          │ │- Acredita  │ │
                │          │          │          │          │          │ │  cuenta    │ │
                │          │          │          │          │          │ │- Genera    │ │
                │          │          │          │          │          │ │  movimiento│ │
                │          │          │          │          │          │ │- UUID      │ │
                │          │          │          │          │          │ └────────────┘ │
                │          │          │          │          │          └────────┬───────┘
                │          │          │          │          │                   │
                │          └──────────┴──────────┴──────────┘                   │
                │                     │                                         │
                │                     ▼                                         ▼
                │          ┌──────────────────┐                    ┌────────────────────┐
                │          │  Retornar Error  │                    │  Retornar Éxito    │
                └──────────┤  - ok: false     │                    │  - ok: true        │
                           │  - code: XX      │                    │  - code: 00        │
                           │  - message: ...  │                    │  - message: ...    │
                           └────────┬─────────┘                    │  - comprobante: .. │
                                    │                              └────────┬───────────┘
                                    │                                       │
                                    └───────────┬───────────────────────────┘
                                                │
                                                ▼
                                         ┌────────────┐
                                         │    FIN     │
                                         └────────────┘
```

## 🗂️ Integración en Flujo de Compra

```
crear_transaccion_desde_compra()
         │
         ├─ Crear Transacción (estado: pendiente)
         │
         ├─ Obtener medio_datos
         │
         ├─ tipo_medio = medio_datos.get('tipo')
         │
         ├─ ¿'billetera' in tipo_medio?
         │
         ├─ SÍ ──┐
         │       │
         │       ├─ resultado = realizar_pago_billetera(...)
         │       │
         │       ├─ ¿resultado['ok']?
         │       │
         │       ├─ SÍ ──┐
         │       │       ├─ transaccion.cambiar_estado('pagada')
         │       │       ├─ messages.success("Pago exitoso...")
         │       │       └─ redirect(confirmacion_operacion)
         │       │
         │       └─ NO ──┐
         │               ├─ messages.warning("Error en pago...")
         │               └─ redirect(compra_sumario)
         │
         └─ NO ──┐
                 │
                 ├─ Flujo bancario tradicional
                 │   ├─ _extraer_cuenta_desde_medio(...)
                 │   ├─ realizar_transferencia_bancaria(...)
                 │   └─ Actualizar estado según resultado
                 │
                 └─ redirect(confirmacion_operacion)
```

## 💾 Modelos y Relaciones

```
┌─────────────────────┐
│ UsuarioBilletera    │
│ ─────────────────── │
│ + numero_celular    │◄─────────┐
│ + password          │          │ 1:1
│ + nombre            │          │
│ + apellido          │          │
└─────────────────────┘          │
                                 │
                        ┌────────┴────────┐
                        │   Billetera     │
                        │ ─────────────── │
                        │ + usuario       │
                        │ + entidad       │──────┐
                        │ + saldo         │      │ N:1
                        │ + activa        │      │
                        └────────┬────────┘      │
                                 │               │
                          1:N    │               │
                                 ▼               ▼
                        ┌─────────────────┐  ┌──────────────────┐
                        │ PagoBilletera   │  │ EntidadBancaria  │
                        │ ─────────────── │  │ ──────────────── │
                        │ + billetera     │  │ + nombre         │
                        │ + cuenta_destino├──┤ + codigo         │
                        │ + monto         │  │ + color_...      │
                        │ + comprobante   │  └──────────────────┘
                        │ + fecha         │          │
                        │ + exitoso       │          │ 1:N
                        └────────┬────────┘          │
                                 │                   ▼
                          1:N    │          ┌──────────────────┐
                                 ▼          │     Cuenta       │
                        ┌─────────────────┐ │ ──────────────── │
                        │ Movimiento      │ │ + numero_cuenta  │
                        │ Billetera       │ │ + entidad        │
                        │ ─────────────── │ │ + saldo          │
                        │ + tipo: PAGO    │ │ + usuario        │
                        │ + monto         │ └──────────────────┘
                        │ + descripcion   │
                        │ + comprobante   │
                        └─────────────────┘
```

## 🔒 Transacción Atómica

```
with transaction.atomic():
    │
    ├─ 1. Obtener billetera (select_for_update)
    │      - Bloquea registro para evitar race conditions
    │
    ├─ 2. Verificar saldo >= monto
    │      - Si NO: lanzar ValidationError → ROLLBACK
    │
    ├─ 3. Debitar billetera.saldo -= monto
    │      - Actualizar registro
    │
    ├─ 4. Acreditar cuenta_destino.saldo += monto
    │      - Actualizar registro
    │
    ├─ 5. Crear MovimientoBilletera
    │      - tipo: PAGO
    │      - monto, descripción, comprobante
    │
    ├─ 6. Guardar PagoBilletera
    │      - exitoso: True
    │      - comprobante: UUID
    │
    └─ ¿Error en algún paso?
       ├─ SÍ → ROLLBACK (todos los cambios se deshacen)
       └─ NO → COMMIT (todos los cambios se guardan)
```

## 📝 Flujo de Datos

```
ClienteMedioDePago (DB)
         │
         ├─ datos_campos: JSON
         │   {
         │     "Teléfono de billetera": "0981111111",
         │     "Entidad": "Banco Py"
         │   }
         │
         ▼
crear_transaccion_desde_compra()
         │
         ├─ medio_datos = transaccion.get_medio_pago_info()
         │   {
         │     "tipo": "Billetera Electrónica",
         │     "datos_campos": {...},
         │     "nombre": "Billetera Digital",
         │     "comision": "0.00%"
         │   }
         │
         ▼
realizar_pago_billetera(medio_datos, monto, ref)
         │
         ├─ telefono = extraer_de(datos_campos)
         │   → "0981111111"
         │
         ├─ usuario = UsuarioBilletera.get(numero_celular=telefono)
         │   → UsuarioBilletera(id=1, nombre="Juan")
         │
         ├─ billetera = Billetera.get(usuario=usuario, activa=True)
         │   → Billetera(id=1, saldo=1500000)
         │
         ├─ cuenta_emp = Cuenta.get(numero_cuenta='000111222')
         │   → Cuenta(id=X, saldo=Y)
         │
         ├─ pago = PagoBilletera.create(...)
         │   → PagoBilletera(
         │       id=N,
         │       comprobante=UUID,
         │       exitoso=True
         │     )
         │
         └─ return {
              'ok': True,
              'code': '00',
              'message': 'Pago exitoso',
              'comprobante': UUID
            }
```

---

**Nota**: Los diagramas están simplificados para claridad. Consulta el código fuente para implementación completa.
