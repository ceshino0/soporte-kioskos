# Matriz de prioridad y SLA — kioskos de autoservicio

La prioridad **la calcula el servidor MCP** (`kioskos_mcp/rules.py`). Este documento sirve
para elegir bien las dos entradas: **impacto** y **urgencia**, usando los datos que devuelve
`buscar_kiosko`.

## Impacto — ¿cuánta venta se pierde?

| Nivel | Criterio | Señales en `buscar_kiosko` / similares |
|---|---|---|
| **alto** | El local se queda **sin autoservicio**, o el fallo afecta a **varios locales** a la vez, o no se puede cobrar con tarjeta en ningún kiosko del local | `kioskos_online_en_local = 0`; `kioskos_en_local = 1` y ese falla; incidencia masiva con `locales_afectados` ≥ 2 |
| **medio** | Falla **parte** de los kioskos del local, o una función clave en uno (pago, impresión del ticket de pedido, envío a cocina), o hay **cobros a clientes sin pedido** | Quedan kioskos online; masiva limitada a un solo local |
| **bajo** | Molestia con alternativa clara: un producto mal en la carta, pantalla con brillo bajo, impresora que atasca a veces | Kiosko online y funcionando en lo esencial |

## Urgencia — ¿cuándo duele?

| Nivel | Criterio | Señales |
|---|---|---|
| **alta** | El local **está en servicio ahora** (o abre en < 1 h), o hay una **apertura** de local en ≤ 2 días | `en_horario_servicio: true`; `apertura_prevista` próxima |
| **media** | Local fuera de servicio pero abre hoy; fallo intermitente | `en_horario_servicio: false` y abre en unas horas |
| **baja** | Puede esperar al siguiente día laborable | Local cerrado, fallo cosmético |

## Matriz

| Impacto \ Urgencia | alta | media | baja |
|---|---|---|---|
| **alto** | P1 | P2 | P3 |
| **medio** | P2 | P3 | P4 |
| **bajo** | P3 | P4 | P4 |

## Reglas que el servidor aplica después de la matriz

1. **Suelo P2 para pagos (`pago_tpv`)**: afecta al cobro (ventas perdidas o cargos a clientes finales).
2. **Suelo P2 para `seguridad`**: posible manipulación del pinpad o incidente PCI-DSS.
3. **Contrato gold**: sube un nivel (P4→P3, P3→P2). Nunca a P1: P1 solo sale de la matriz.
4. **Kiosko o local `en_despliegue`**: el grupo pasa a **Proyectos y Despliegues** (la
   prioridad no cambia).

Por eso conviene pasar siempre `kiosko_id` (o `local_id`): sin él no se aplican 3 y 4.

## SLA (horas naturales desde la creación)

| Prioridad | Primera respuesta | Resolución |
|---|---|---|
| P1 | 15 min | 4 h |
| P2 | 30 min | 8 h |
| P3 | 4 h | 24 h |
| P4 | 8 h | 72 h |

## Errores típicos

- Poner urgencia `alta` porque el encargado escribe "URGENTE" a las 17:30 con el local
  cerrado hasta las 19:00: usa `en_horario_servicio`, no el tono.
- Poner impacto `alto` a un kiosko caído cuando el local tiene otros dos online: es `medio`.
- Olvidar que un **cobro sin pedido** es `medio` como mínimo aunque solo haya pasado una vez:
  hay dinero de un cliente final de por medio.
