---
name: triage-kioskos
description: >-
  Clasifica y registra incidencias de kioskos de autoservicio en restaurantes clientes (pago
  con tarjeta o datáfono que falla, cobro sin pedido, kiosko que no enciende o está offline,
  ticket de pedido que no se imprime, pedidos que no llegan a cocina/KDS, precios o productos
  mal en el menú, pinpad manipulado) usando el MCP "kioskos". Úsala cuando un encargado,
  cliente o técnico reporte un fallo de un kiosko o local, pegue su correo/WhatsApp, pida
  abrir o priorizar un ticket, pregunte si una caída ya está reportada o quiera vincular
  tickets a una incidencia masiva. NO la uses para: presupuestos, venta o alta de kioskos
  nuevos, planificar una instalación o apertura, cambios de carta programados, formación de
  uso del kiosko sin fallo, facturación del contrato, ni cerrar o borrar tickets en bloque.
allowed-tools: Read, mcp__kioskos__buscar_kiosko, mcp__kioskos__buscar_incidencias_similares, mcp__kioskos__obtener_ticket, mcp__kioskos__proponer_ticket
version: 1.0.0
---

# Triage de incidencias de kioskos de autoservicio

Convierte el aviso de un restaurante ("¡el kiosko no cobra!") en un ticket bien clasificado,
con la prioridad que marcan las reglas del contrato, vinculado a la incidencia masiva si la hay
y sin datos de tarjeta dentro.

**Principio:** tú propones *impacto* y *urgencia* con hechos (telemetría, nº de kioskos del
local, horario de servicio); el servidor MCP calcula prioridad, SLA y grupo resolutor. Nunca
escribas una prioridad o un grupo "a mano".

`crear_ticket` y `actualizar_ticket` tienen efectos secundarios y **no** están en
`allowed-tools` a propósito: Claude Code pedirá permiso antes de ejecutarlas.

## Referencias (léelas cuando las necesites)

| Fichero | Cuándo |
|---|---|
| `reference/matriz-prioridad.md` | Paso 4: decidir impacto y urgencia en un restaurante |
| `reference/categorias.md` | Paso 4: elegir categoría, casos frontera, diagnóstico rápido |
| `reference/plantillas-respuesta.md` | Paso 7: respuesta al encargado del local |

## Flujo

### 1. Extraer los hechos
Del mensaje, anota sin inventar:
- **Quién reporta**: email del contacto (encargado, operaciones del cliente o técnico interno).
- **Qué kiosko**: nº de kiosko en el local ("el 2"), id `KSK-…`, nº de serie o solo el local.
- **Síntoma** literal, con el texto exacto del error si lo hay ("Error de comunicación con TPV").
- **Efecto en el servicio**: ¿se puede pedir en otro kiosko?, ¿cola en caja?, ¿hay cobros
  a clientes sin pedido?
- **Desde cuándo** y qué se ha probado (reiniciar, cambiar rollo de papel…).

Si no sabes **quién reporta** ni **qué local** es, pregunta solo eso antes de seguir.

### 2. Contexto del kiosko → `mcp__kioskos__buscar_kiosko`
Busca por el email de quien reporta (devuelve los kioskos de su local) o por kiosko/local.
Fíjate en:
- `online` / `minutos_sin_conexion`: un kiosko que "no enciende" y lleva 90 min sin
  telemetría confirma el fallo; si está `online`, el problema es de pantalla o de aplicación.
- `kioskos_en_local` y `kioskos_online_en_local`: si **no queda ningún kiosko operativo**,
  el local está sin autoservicio → impacto `alto`.
- `en_horario_servicio`: en servicio → urgencia `alta`; local cerrado → como mucho `media`.
- `estado` / `estado_local` = `en_despliegue` y `apertura_prevista`: es un proyecto en curso;
  el servidor lo enviará a Proyectos y Despliegues. Si la apertura es en ≤ 2 días, urgencia `alta`.
- `nivel_contrato`: no lo uses para subir prioridad tú; el servidor ya lo aplica.
- `incidencias_abiertas` > 0: revisa con `obtener_ticket` antes de crear otro.

### 3. Duplicados e incidencias masivas → `mcp__kioskos__buscar_incidencias_similares`
- Pasa 3-6 palabras clave del síntoma y la `categoria` provisional.
- Si `posible_incidencia_masiva = true`: usa `ticket_padre_sugerido` como `ticket_padre` e
  indica en la descripción `locales_afectados` y `versiones_software_afectadas`. Si todos los
  afectados comparten versión, menciónalo: apunta a un fallo de release (útil para N2).
- Si el **mismo kiosko** ya tiene un ticket abierto con el mismo síntoma, no crees otro:
  informa y ofrece añadir comentario con `actualizar_ticket`.

### 4. Clasificar
Con `reference/categorias.md` y `reference/matriz-prioridad.md` decide `categoria`, `impacto`
y `urgencia`.

Reglas duras:
- **Cobro sin pedido / cargos duplicados** → `pago_tpv`, y dilo explícitamente en el título:
  hay un cliente final afectado económicamente.
- **Pinpad con aspecto manipulado, dispositivo extraño, pegatinas o cables** → `seguridad`.
  Indica al local que **no lo use ni lo toque** y retire el kiosko de servicio.
- **Datos de tarjeta**: si el mensaje trae un número de tarjeta o CVV, **no lo copies** en el
  ticket ni en tu respuesta; basta con los 4 últimos dígitos, importe y hora del cobro. El
  servidor lo redacta igualmente, pero es tu primera barrera (PCI-DSS).

### 5. Simular → `mcp__kioskos__proponer_ticket`
Pasa todos los campos (`kiosko_id` siempre que se conozca, o `local_id`). Revisa:
- `prioridad` y `reglas_aplicadas` → explica por qué sale esa prioridad.
- `grupo_asignado` → si es *Proyectos y Despliegues*, dilo: lo lleva el jefe de proyecto.
- `datos_redactados` no vacío → avisa de que se eliminaron datos sensibles.
- Error de solicitante no registrado o de otro cliente → **no** cambies el email por otro
  inventado; pregunta al técnico.

### 6. Confirmar y crear → `mcp__kioskos__crear_ticket`
Muestra la propuesta así y **espera un "sí"** explícito:

```
Propuesta de ticket
- Local / kiosko: Wok & Go Sevilla Nervión · KSK-0401 (offline 95 min, único kiosko)
- Título: …
- Categoría / Impacto / Urgencia: hardware_kiosko / alto / alta
- Prioridad calculada: P1   (Matriz alto×alta → P1)
- Grupo: Soporte de campo (hardware) · SLA respuesta 15:45 · resolución 19:30
- Vinculado a: —
¿Lo registro?
```

Tras el "sí", llama a `crear_ticket` con **exactamente los mismos argumentos**.

### 7. Cerrar el ciclo
Nada más crear el ticket, devuelve **siempre** estos tres bloques:
1. **ID del ticket**, prioridad, grupo y SLA de resolución.
2. **Borrador de respuesta al encargado** con `reference/plantillas-respuesta.md`: qué hacer
   ya en el local (workaround) y cuándo esperar al técnico. Sin jerga ni datos de tarjeta.
3. **Siguiente acción interna** si procede: avisar a N2 de la versión implicada, a Pagos del
   cobro a devolver, o al jefe de proyecto si es un despliegue.

## Ejemplos

**1 — Kiosko único apagado en hora punta → P1**
> Lucía (Wok & Go Sevilla): "El kiosko no enciende desde que abrimos, pantalla negra. Es el único."

`buscar_kiosko("sevilla.nervion@wokandgo.example")` → KSK-0401, `online: false`, 95 min sin
conexión, `kioskos_en_local: 1`, `en_horario_servicio: true`. → `hardware_kiosko`, impacto
`alto` (local sin autoservicio), urgencia `alta` (en servicio) → **P1**, Soporte de campo.
Workaround: pedidos por caja, cartel "kiosko fuera de servicio", comprobar enchufe/regleta.

**2 — Error de pago masivo con tarjeta pegada → vincular**
> Elena (Parrilla Urbana Valencia): "El kiosko 2 da 'Error de comunicación con TPV'. A un cliente
> le ha cobrado y no ha salido el ticket; su tarjeta es 4111 1111 1111 1111."

`buscar_incidencias_similares(..., categoria="pago_tpv")` → 3 abiertas en 24 h, 2 locales,
todas en versión **4.2.1** → `ticket_padre: INC-000001`. `pago_tpv`; impacto `alto` porque la
masiva ya afecta a 2 locales, urgencia `alta` (en servicio) → **P1**.
No copies la tarjeta. Siguiente acción: avisar a N2 del posible fallo de la 4.2.1 y a Pagos
para revisar la devolución del cobro.

**3 — Kiosko en instalación → Proyectos**
> Rocío (Café Mediterráneo Málaga): "El pinpad del kiosko 1 no empareja, abrimos el lunes."

KSK-0601 `en_despliegue`, apertura en 5 días → el servidor asigna **Proyectos y Despliegues**.

**4 — No es una incidencia (anti-trigger)**
> "Wok & Go quiere presupuesto para 3 kioskos más en su nuevo local de Madrid."

No uses esta Skill: es una **oportunidad comercial / proyecto**. Indica el canal de preventa.

## Errores del servidor y cómo reaccionar

| Mensaje | Qué hacer |
|---|---|
| `no es un contacto registrado` | Pregunta quién es; si es personal del local no registrado, pide que reporte el encargado o registra el contacto. No inventes otro email. |
| `pertenece a otro cliente` | Hay un error de local/kiosko o de contacto. Revisa con `buscar_kiosko`. |
| `kiosko ... no existe` | Reintenta con `local_id` y describe el kiosko ("el 2 de la entrada"). |
| `Transición no permitida` | Lee los estados permitidos y propón uno válido. |
| `modo solo lectura` | Entrega la propuesta en texto para registrarla a mano. |
