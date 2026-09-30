# Transcripts reales: Claude Code + Skill `triage-kioskos` + MCP `kioskos`

Sesiones ejecutadas el 30/09/2026 (hora de comidas) con **Claude Code 2.1.285** en modo no
interactivo (`claude -p`) dentro de la carpeta del proyecto, con el `.mcp.json` y el
`.claude/settings.json` de esta entrega. Convertidas a Markdown automáticamente desde
`--output-format stream-json`; el texto de Claude no se ha editado. Datos 100 % ficticios.

**Índice**
1. [Caso 1 — Error de pago con cobro sin pedido (incidencia masiva)](#caso-1)
2. [Caso 2 — Kiosko único que no enciende en hora punta](#caso-2)
3. [Anti-trigger — petición de presupuesto](#anti-trigger)
4. [Hallazgos durante las pruebas y correcciones](#hallazgos)

---

<a id="caso-1"></a>
## Caso 1 — Error de pago con cobro sin pedido

### Turno 1 · Triage (la Skill se carga, lee `reference/` y consulta el MCP 3 veces)

**👤 Técnico:** Me escribe por WhatsApp Elena Ferrer, encargada de La Parrilla Urbana Valencia Ruzafa (encargada.ruzafa@parrillaurbana.example): 'El kiosko 2 nos da Error de comunicación con TPV!! A un cliente le ha cobrado 18,40 y no le ha salido el ticket del pedido. Su tarjeta es 4111 1111 1111 1111 por si la necesitáis'. Haz el triage.

_Inicio de sesión: servidor MCP `kioskos` → **connected**._

**🔧 `Skill`**
```json
{
  "skill": "triage-kioskos"
}
```
_✅ Skill `triage-kioskos` cargada: el contenido de SKILL.md entra en el contexto._

**📄 Lee** `.claude/skills/triage-kioskos/reference/matriz-prioridad.md`

**📄 Lee** `.claude/skills/triage-kioskos/reference/categorias.md`

**🔧 `mcp__kioskos__buscar_kiosko`**
```json
{
  "consulta": "encargada.ruzafa@parrillaurbana.example"
}
```
<details><summary>↩️ resultado de mcp__kioskos__buscar_kiosko</summary>

```json
{
  "consulta": "encargada.ruzafa@parrillaurbana.example",
  "total": 2,
  "contacto": "Elena Ferrer (encargada de local)",
  "kioskos": [
    {
      "id": "KSK-0201",
      "numero_serie": "K32-24-00201",
      "modelo": "Kiosko K32 táctil 32\"",
      "version_software": "4.2.1",
      "pinpad": "Ingenico Lane/3000",
      "impresora": "Epson TM-T88VI",
      "estado": "operativo",
      "online": true,
      "minutos_sin_conexion": 1,
      "incidencias_abiertas": 1,
      "local_id": "LOC-002",
      "local_nombre": "La Parrilla Urbana Valencia Ruzafa",
      "ciudad": "Valencia",
      "estado_local": "operativo",
      "horario_servicio": "11:00-16:30,19:00-23:59",
      "en_horario_servicio": true,
      "kioskos_en_local": 2,
      "kioskos_online_en_local": 2,
      "cliente_id": "CLI-01",
      "cliente": "La Parrilla Urbana",
      "nivel_contrato": "gold",
      "apertura_prevista": null
    },
    {
      "id": "KSK-0202",
      "numero_serie": "K32-24-00202",
      "modelo": "Kiosko K32 táctil 32\"",
      "version_software": "4.2.1",
      "pinpad": "Ingenico Lane/3000",
      "impresora": "Epson TM-T88VI",
      "estado": "operativo",
      "online": true,
      "minutos_sin_conexion": 3,
      "incidencias_abiertas": 0,
      "local_id": "LOC-002",
      "local_nombre": "La Parrilla Urbana Valencia Ruzafa",
      "ciudad": "Valencia",
      "estado_local": "operativo",
      "horario_servicio": "11:00-16:30,19:00-23:59",
      "en_horario_servicio": true,
      "kioskos_en_local": 2,
      "kioskos_online_en_local": 2,
      "cliente_id": "CLI-01",
      "cliente": "La Parrilla Urbana",
      "nivel_contrato": "gold",
      "apertura_prevista": null
    }
  ]
}
```
</details>

**🔧 `mcp__kioskos__buscar_incidencias_similares`**
```json
{
  "texto": "error comunicación TPV cobro sin pedido ticket",
  "categoria": "pago_tpv"
}
```
<details><summary>↩️ resultado de mcp__kioskos__buscar_incidencias_similares</summary>

```json
{
  "consulta": "error comunicación TPV cobro sin pedido ticket",
  "ventana_dias": 7,
  "total": 4,
  "abiertas_ultimas_24h": 3,
  "posible_incidencia_masiva": true,
  "ticket_padre_sugerido": "INC-000001",
  "locales_afectados": [
    "La Parrilla Urbana Madrid Gran Vía",
    "La Parrilla Urbana Valencia Ruzafa"
  ],
  "versiones_software_afectadas": {
    "4.2.1": 3
  },
  "tickets": [
    {
      "id": "INC-000001",
      "titulo": "Datáfono rechaza pagos con tarjeta en kiosko 2",
      "categoria": "pago_tpv",
      "prioridad": "P2",
      "estado": "asignado",
      "grupo_asignado": "Pagos y TPV",
      "solicitante_email": "encargado.granvia@parrillaurbana.example",
      "kiosko_id": "KSK-0102",
      "local_id": "LOC-001",
      "creado_en": "2026-09-30T12:35+02:00",
      "similitud": 0.75
    },
    {
      "id": "INC-000002",
      "titulo": "No deja pagar con tarjeta en el kiosko",
      "categoria": "pago_tpv",
      "prioridad": "P2",
      "estado": "nuevo",
      "grupo_asignado": "Pagos y TPV",
      "solicitante_email": "encargada.ruzafa@parrillaurbana.example",
      "kiosko_id": "KSK-0201",
      "local_id": "LOC-002",
      "creado_en": "2026-09-30T13:35+02:00",
      "similitud": 0.75
    },
    {
      "id": "INC-000003",
      "titulo": "Kiosko cobra pero da error y no genera pedido",
      "categoria": "pago_tpv",
      "prioridad": "P2",
      "estado": "nuevo",
      "grupo_asignado": "Pagos y TPV",
      "solicitante_email": "encargado.granvia@parrillaurbana.example",
      "kiosko_id": "KSK-0103",
      "local_id": "LOC-001",
      "creado_en": "2026-09-30T14:35+02:00",
      "similitud": 0.75
    },
    {
      "id": "INC-000004",
      "titulo": "Pedidos del kiosko no llegan a la pantalla de cocina",
      "categoria": "integracion_pos_kds",
      "prioridad": "P3",
      "estado": "en_curso",
      "grupo_asignado": "Integraciones POS / KDS",
      "solicitante_email": "diagonal@wokandgo.example",
      "kiosko_id": "KSK-0501",
      "local_id": "LOC-005",
      "creado_en": "2026-09-29T19:35+02:00",
      "similitud": 0.33
    }
  ]
}
```
</details>

**🔧 `mcp__kioskos__proponer_ticket`**
```json
{
  "titulo": "Cobro de 18,40 € sin pedido ni ticket en kiosko 2: Error de comunicación con TPV",
  "descripcion": "La encargada (Elena Ferrer) reporta que el kiosko 2 muestra \"Error de comunicación con TPV\". A un cliente se le ha cobrado 18,40 € y no se ha generado el ticket del pedido (cliente final afectado económicamente; pendiente confirmar si el pedido llegó a cocina). Local en horario de servicio; kiosko online, versión 4.2.1. Quedan 2 kioskos online en el local. Posible incidencia masiva: 3 tickets abiertos en 24 h en 2 locales (Madrid Gran Vía y Valencia Ruzafa), todos en versión 4.2.1, lo que apunta a un fallo de release. Datos de tarjeta omitidos; pendiente que el local facilite hora del cobro y últimos 4 dígitos.",
  "categoria": "pago_tpv",
  "impacto": "alto",
  "urgencia": "alta",
  "solicitante_email": "encargada.ruzafa@parrillaurbana.example",
  "kiosko_id": "KSK-0202",
  "ticket_padre": "INC-000001"
}
```
<details><summary>↩️ resultado de mcp__kioskos__proponer_ticket</summary>

```json
{
  "simulacion": true,
  "duplicado": false,
  "ticket_id": null,
  "prioridad": "P1",
  "reglas_aplicadas": [
    "Matriz: impacto=alto x urgencia=alta -> P1"
  ],
  "grupo_asignado": "Pagos y TPV",
  "sla_respuesta_limite": "2026-09-30T15:50+02:00",
  "sla_resolucion_limite": "2026-09-30T19:35+02:00",
  "datos_redactados": [],
  "kiosko_id": "KSK-0202",
  "local_id": "LOC-002",
  "ticket_padre": "INC-000001",
  "mensaje": "Simulación: nada guardado. Confirma con el usuario y llama a crear_ticket con los mismos datos."
}
```
</details>

**🤖 Claude:**

## Propuesta de ticket

- **Local / kiosko:** La Parrilla Urbana Valencia Ruzafa (LOC-002) · KSK-0202. Está online, en versión 4.2.1, y el local está en horario de servicio. Quedan 2 de 2 kioskos online.
- **Título:** Cobro de 18,40 € sin pedido ni ticket en kiosko 2: Error de comunicación con TPV
- **Categoría / impacto / urgencia:** `pago_tpv` / alto / alta
- **Prioridad calculada:** P1 (matriz alto×alta). El servidor no aplica ninguna otra regla.
- **Grupo:** Pagos y TPV
- **SLA:** respuesta 15:50, resolución 19:35
- **Vinculado a:** INC-000001 (incidencia masiva)
- **Datos redactados:** ninguno. No he copiado el número de tarjeta al ticket.

**Por qué impacto alto:** hay 3 tickets de pago abiertos en 24 h en 2 locales (Madrid Gran Vía y Valencia Ruzafa). Todos están en la versión 4.2.1, lo que apunta a un fallo de release. Con solo este kiosko afectado en Ruzafa habría salido impacto medio y P2.

**Antes de confirmar:**
- **Qué kiosko es:** he asumido que "kiosko 2" es KSK-0202. Elena ya tiene abierto INC-000002 sobre KSK-0201 con un síntoma parecido. Si el afectado fuera el 0201, habría que añadir un comentario a ese ticket en lugar de crear uno nuevo.
- **Tarjeta del cliente:** Elena ha enviado el número completo de la tarjeta por WhatsApp. Conviene pedirle que borre ese mensaje y que no envíe más datos de tarjeta. Para localizar el cobro bastan la hora, el importe y los 4 últimos dígitos.

¿Lo registro?

## Cuando lo registres

**Borrador de respuesta a Elena:**
> Hola Elena, gracias por avisarnos. Ya tenemos registrada la incidencia con prioridad máxima y la está revisando el equipo de Pagos. Mientras tanto:
> 1. Deja el kiosko 2 fuera de servicio con un cartel y cobrad esos pedidos en caja o en el kiosko 1.
> 2. Al cliente afectado, dile que se revisa su cobro y que se le devolverá si no hay pedido.
> 3. Anota la hora aproximada del cobro y los 4 últimos dígitos de su tarjeta, y confirma si el pedido llegó a cocina.
> 4. Por seguridad, borra el mensaje con el número completo de la tarjeta y no lo compartas por este canal. No hace falta.
>
> Te escribimos en cuanto haya novedades.

**Siguiente acción interna:** avisar a N2 de que la 4.2.1 puede ser la causa del fallo en 2 locales, y a Pagos para revisar la devolución de los 18,40 €.


### Turno 2 · "Regístralo" → la regla `ask` bloquea la escritura

Sin diálogo de permisos (modo no interactivo) y aun lanzando con
`--permission-mode bypassPermissions`, la regla `"ask"` de `.claude/settings.json` impide
ejecutar `crear_ticket`. Ninguna escritura ocurre sin aprobación humana.

**👤 Técnico:** Sí, es el KSK-0202 (distinto del de INC-000002). Regístralo.

_Inicio de sesión: servidor MCP `kioskos` → **connected**._

**🔧 `mcp__kioskos__crear_ticket`**
```json
{
  "titulo": "Cobro de 18,40 € sin pedido ni ticket en kiosko 2: Error de comunicación con TPV",
  "descripcion": "La encargada (Elena Ferrer) reporta que el kiosko 2 muestra \"Error de comunicación con TPV\". A un cliente se le ha cobrado 18,40 € y no se ha generado el ticket del pedido (cliente final afectado económicamente; pendiente confirmar si el pedido llegó a cocina). Local en horario de servicio; kiosko online, versión 4.2.1. Quedan 2 kioskos online en el local. Posible incidencia masiva: 3 tickets abiertos en 24 h en 2 locales (Madrid Gran Vía y Valencia Ruzafa), todos en versión 4.2.1, lo que apunta a un fallo de release. Datos de tarjeta omitidos; pendiente que el local facilite hora del cobro y últimos 4 dígitos.",
  "categoria": "pago_tpv",
  "impacto": "alto",
  "urgencia": "alta",
  "solicitante_email": "encargada.ruzafa@parrillaurbana.example",
  "kiosko_id": "KSK-0202",
  "ticket_padre": "INC-000001"
}
```
<details><summary>↩️ resultado de mcp__kioskos__crear_ticket</summary>

```json
Claude requested permissions to use mcp__kioskos__crear_ticket, but you haven't granted it yet.
```
</details>

**🤖 Claude:**

No he podido registrar el ticket. Claude Code me ha denegado el permiso para usar `crear_ticket`, y esa herramienta necesita tu aprobación explícita. No se ha guardado nada.

Para que lo registre, aprueba el permiso cuando salga el aviso y dime que reintente. Lo lanzaré con los mismos datos que la propuesta: KSK-0202, P1, Pagos y TPV, vinculado a INC-000001.

Si prefieres registrarlo a mano, la propuesta anterior tiene todos los campos. Mientras tanto, Elena sigue sin respuesta. El SLA de primera respuesta de un P1 es de 15 min, y el límite calculado en la simulación era las 15:50.


### Turno 3 · Aprobación humana → ticket creado

Para simular el clic en **"Permitir"** del modo interactivo, este turno se lanzó con
`--setting-sources user --mcp-config .mcp.json --allowedTools mcp__kioskos__crear_ticket`.

**👤 Técnico:** Ya he aprobado el permiso de crear_ticket. Regístralo.

_Inicio de sesión: servidor MCP `kioskos` → **connected**._

**🔧 `mcp__kioskos__crear_ticket`**
```json
{
  "titulo": "Cobro de 18,40 € sin pedido ni ticket en kiosko 2: Error de comunicación con TPV",
  "descripcion": "La encargada (Elena Ferrer) reporta que el kiosko 2 muestra \"Error de comunicación con TPV\". A un cliente se le ha cobrado 18,40 € y no se ha generado el ticket del pedido (cliente final afectado económicamente; pendiente confirmar si el pedido llegó a cocina). Local en horario de servicio; kiosko online, versión 4.2.1. Quedan 2 kioskos online en el local. Posible incidencia masiva: 3 tickets abiertos en 24 h en 2 locales (Madrid Gran Vía y Valencia Ruzafa), todos en versión 4.2.1, lo que apunta a un fallo de release. Datos de tarjeta omitidos; pendiente que el local facilite hora del cobro y últimos 4 dígitos.",
  "categoria": "pago_tpv",
  "impacto": "alto",
  "urgencia": "alta",
  "solicitante_email": "encargada.ruzafa@parrillaurbana.example",
  "kiosko_id": "KSK-0202",
  "ticket_padre": "INC-000001"
}
```
<details><summary>↩️ resultado de mcp__kioskos__crear_ticket</summary>

```json
{
  "simulacion": false,
  "duplicado": false,
  "ticket_id": "INC-000008",
  "prioridad": "P1",
  "reglas_aplicadas": [
    "Matriz: impacto=alto x urgencia=alta -> P1"
  ],
  "grupo_asignado": "Pagos y TPV",
  "sla_respuesta_limite": "2026-09-30T15:50+02:00",
  "sla_resolucion_limite": "2026-09-30T19:35+02:00",
  "datos_redactados": [],
  "kiosko_id": "KSK-0202",
  "local_id": "LOC-002",
  "ticket_padre": "INC-000001",
  "mensaje": "Ticket INC-000008 creado y asignado a 'Pagos y TPV'."
}
```
</details>

**🤖 Claude:**

## Ticket registrado: INC-000008

- **Prioridad:** P1
- **Grupo:** Pagos y TPV
- **SLA:** primera respuesta antes de las 15:50, resolución antes de las 19:35
- **Vinculado a:** INC-000001 (incidencia masiva)
- **Datos de tarjeta:** el número no está en el ticket.

**Respuesta a Elena (para enviar por WhatsApp):**
> Hola Elena, gracias por avisarnos. Ya tenemos registrada la incidencia (INC-000008) con prioridad máxima y la está revisando el equipo de Pagos. Mientras tanto:
> 1. Deja el kiosko 2 fuera de servicio con un cartel y cobrad esos pedidos en caja o en el kiosko 1.
> 2. Al cliente afectado, dile que se revisa su cobro y que se le devolverá si no hay pedido.
> 3. Anota la hora aproximada del cobro y los 4 últimos dígitos de su tarjeta, y confirma si el pedido llegó a cocina.
> 4. Por seguridad, borra el mensaje con el número completo de la tarjeta y no lo compartas por este canal. No hace falta.
>
> Te escribimos en cuanto haya novedades.

**Siguiente acción interna:**
- **N2:** avisar de que el fallo aparece en 2 locales, y que los 3 tickets abiertos en las últimas 24 h son todos de la versión 4.2.1. Puede ser un fallo de esa release.
- **Pagos:** revisar la devolución de los 18,40 € cuando Elena facilite la hora y los 4 últimos dígitos.


**Log de auditoría escrito por el servidor:**
```jsonl
{"ts": "2026-09-30T15:35+02:00", "actor": "claude-code", "accion": "crear_ticket", "ticket_id": "INC-000008", "prioridad": "P1", "categoria": "pago_tpv", "grupo": "Pagos y TPV", "solicitante": "encargada.ruzafa@parrillaurbana.example", "kiosko_id": "KSK-0202", "local_id": "LOC-002", "ticket_padre": "INC-000001", "redactados": []}
```

> El número de tarjeta que pegó la encargada no aparece ni en el ticket ni en el log: Claude no
> lo copió (`redactados: []`). Si lo hubiera copiado, el servidor lo habría eliminado igualmente
> (ver `transcript-mcp.md`, caso B).

---

<a id="caso-2"></a>
## Caso 2 — Kiosko único que no enciende en hora punta

La telemetría confirma el fallo (95 min sin conexión), el local no tiene más kioskos y está en
servicio → **P1** a Soporte de campo, con workaround para la encargada.

**👤 Técnico:** Llama Lucía Romero, encargada de Wok & Go Sevilla Nervión (sevilla.nervion@wokandgo.example): 'El kiosko no enciende desde que abrimos, pantalla negra. Es el único que tenemos y la cola en caja llega a la puerta'. Haz el triage.

_Inicio de sesión: servidor MCP `kioskos` → **connected**._

**🔧 `Skill`**
```json
{
  "skill": "triage-kioskos"
}
```
_✅ Skill `triage-kioskos` cargada: el contenido de SKILL.md entra en el contexto._

**📄 Lee** `.claude/skills/triage-kioskos/reference/matriz-prioridad.md`

**📄 Lee** `.claude/skills/triage-kioskos/reference/categorias.md`

**🔧 `mcp__kioskos__buscar_kiosko`**
```json
{
  "consulta": "sevilla.nervion@wokandgo.example"
}
```
<details><summary>↩️ resultado de mcp__kioskos__buscar_kiosko</summary>

```json
{
  "consulta": "sevilla.nervion@wokandgo.example",
  "total": 1,
  "contacto": "Lucía Romero (encargada de local)",
  "kioskos": [
    {
      "id": "KSK-0401",
      "numero_serie": "K24-23-00401",
      "modelo": "Kiosko K24 sobremesa 24\"",
      "version_software": "4.2.0",
      "pinpad": "Verifone P400",
      "impresora": "Star TSP143IV",
      "estado": "operativo",
      "online": false,
      "minutos_sin_conexion": 95,
      "incidencias_abiertas": 0,
      "local_id": "LOC-004",
      "local_nombre": "Wok & Go Sevilla Nervión",
      "ciudad": "Sevilla",
      "estado_local": "operativo",
      "horario_servicio": "12:00-16:30,20:00-23:59",
      "en_horario_servicio": true,
      "kioskos_en_local": 1,
      "kioskos_online_en_local": 0,
      "cliente_id": "CLI-02",
      "cliente": "Wok & Go",
      "nivel_contrato": "silver",
      "apertura_prevista": null
    }
  ]
}
```
</details>

**🔧 `mcp__kioskos__buscar_incidencias_similares`**
```json
{
  "texto": "kiosko no enciende pantalla negra",
  "categoria": "hardware_kiosko"
}
```
<details><summary>↩️ resultado de mcp__kioskos__buscar_incidencias_similares</summary>

```json
{
  "consulta": "kiosko no enciende pantalla negra",
  "ventana_dias": 7,
  "total": 1,
  "abiertas_ultimas_24h": 0,
  "posible_incidencia_masiva": false,
  "ticket_padre_sugerido": null,
  "locales_afectados": [],
  "versiones_software_afectadas": {},
  "tickets": [
    {
      "id": "INC-000004",
      "titulo": "Pedidos del kiosko no llegan a la pantalla de cocina",
      "categoria": "integracion_pos_kds",
      "prioridad": "P3",
      "estado": "en_curso",
      "grupo_asignado": "Integraciones POS / KDS",
      "solicitante_email": "diagonal@wokandgo.example",
      "kiosko_id": "KSK-0501",
      "local_id": "LOC-005",
      "creado_en": "2026-09-29T19:34+02:00",
      "similitud": 0.33
    }
  ]
}
```
</details>

**🔧 `mcp__kioskos__proponer_ticket`**
```json
{
  "titulo": "Kiosko único sin encender (pantalla negra) en Wok & Go Sevilla Nervión, en servicio",
  "descripcion": "La encargada (Lucía Romero) informa de que el kiosko KSK-0401 no enciende desde la apertura, pantalla negra. Es el único kiosko del local. Telemetría: offline desde hace 95 min, 0 de 1 kioskos online. Local en horario de servicio (12:00-16:30) y la cola en caja llega a la puerta. Pendiente de confirmar con el local: luz en regleta/enchufe y si otros equipos del mismo enchufe funcionan.",
  "categoria": "hardware_kiosko",
  "impacto": "alto",
  "urgencia": "alta",
  "solicitante_email": "sevilla.nervion@wokandgo.example",
  "kiosko_id": "KSK-0401"
}
```
<details><summary>↩️ resultado de mcp__kioskos__proponer_ticket</summary>

```json
{
  "simulacion": true,
  "duplicado": false,
  "ticket_id": null,
  "prioridad": "P1",
  "reglas_aplicadas": [
    "Matriz: impacto=alto x urgencia=alta -> P1"
  ],
  "grupo_asignado": "Soporte de campo (hardware)",
  "sla_respuesta_limite": "2026-09-30T15:49+02:00",
  "sla_resolucion_limite": "2026-09-30T19:34+02:00",
  "datos_redactados": [],
  "kiosko_id": "KSK-0401",
  "local_id": "LOC-004",
  "ticket_padre": null,
  "mensaje": "Simulación: nada guardado. Confirma con el usuario y llama a crear_ticket con los mismos datos."
}
```
</details>

**🤖 Claude:**

## Triage: Wok & Go Sevilla Nervión

**Qué muestran los datos**
- KSK-0401 está offline desde hace 95 min, lo que confirma el fallo. Es el único kiosko del local, así que hay 0 de 1 online.
- El local está en horario de servicio (12:00-16:30) y hay cola hasta la puerta.
- No hay incidencia masiva ni ticket abierto del mismo kiosko. El único parecido es INC-000004 (KSK-0501, otro local, otra categoría), sin relación.

**Propuesta de ticket** (todavía no creado)
- **Local / kiosko:** Wok & Go Sevilla Nervión · KSK-0401 (offline 95 min, único kiosko)
- **Título:** Kiosko único sin encender (pantalla negra) en Wok & Go Sevilla Nervión, en servicio
- **Categoría / Impacto / Urgencia:** hardware_kiosko / alto / alta
- **Prioridad calculada:** P1 (matriz alto × alta)
- **Grupo:** Soporte de campo (hardware)
- **SLA:** respuesta hasta las 15:49, resolución hasta las 19:34
- **Vinculado a:** —
- **Solicitante:** sevilla.nervion@wokandgo.example (Lucía Romero)

**¿Lo registro?** Responde "sí" y lo creo con estos mismos datos.

**Borrador de respuesta a Lucía** (para enviar tras crear el ticket)
> Hola Lucía, hemos abierto una incidencia prioritaria (P1) por el kiosko y ya está asignada a nuestro equipo técnico de campo. Mientras tanto:
> 1. Comprueba que el kiosko y su regleta están enchufados y con luz, y prueba otro equipo en el mismo enchufe.
> 2. Si no hay luz, prueba a conectarlo a otra toma.
> 3. Atiende los pedidos por caja y pon un cartel de "kiosko fuera de servicio" para reducir la cola.
> Avísanos de lo que veas en el punto 1 y te confirmaremos la visita del técnico en cuanto se asigne.

Si en la regleta y el enchufe todo está bien, el fallo será de la fuente del kiosko o de la pantalla, y la visita del técnico de campo es lo que lo resuelve.


---

<a id="anti-trigger"></a>
## Anti-trigger — petición de presupuesto

Sesión independiente. Claude **no invoca la Skill ni crea tickets**: la `description` excluye
presupuestos y altas de kioskos nuevos.

**👤 Técnico:** Marc Puig de Wok & Go Barcelona Diagonal nos pide presupuesto para instalar 3 kioskos más en su nuevo local de Madrid, ¿lo gestionas?

_Inicio de sesión: servidor MCP `kioskos` → **connected**._

**🤖 Claude:**

No lo puedo gestionar de principio a fin, y conviene no registrarlo como incidencia. El sistema de kioskos que tengo conectado sirve para tickets de soporte (fallos, caídas, cobros). No tiene tarifas, catálogo ni proceso de alta o instalación, así que no puedo emitir ni enviar un presupuesto oficial.

Lo que sí puedo hacer:

1. **Consultar el contrato y los kioskos actuales de Wok & Go Diagonal** (solo lectura), para ver modelo, condiciones y si hay tarifa pactada que sirva de referencia.
2. **Redactar el borrador del presupuesto** para Marc Puig: 3 kioskos, instalación en Madrid, puesta en marcha, formación, cuota o contrato de soporte, y desplazamiento.
3. **Redactar la respuesta al cliente** acusando recibo y pidiendo lo que falte.

Para el punto 2 necesito estos datos, porque no los tengo y no los voy a inventar:
- Precio por kiosko (compra, renting o cuota mensual) y modelo.
- Coste de instalación y desplazamiento a Madrid.
- Si el nuevo local entra en el contrato actual o requiere uno nuevo.
- Dirección del local y fecha prevista de apertura.
- Requisitos técnicos: datáfonos, impresoras, integración con cocina/KDS y red.

Dime si consulto primero el contrato de Diagonal o si me pasas directamente las tarifas para preparar el borrador.


---

<a id="hallazgos"></a>
## Hallazgos durante las pruebas y correcciones

Las sesiones reales sacaron a la luz tres problemas que los tests unitarios no detectaban:

| # | Qué pasó | Causa | Corrección |
|---|---|---|---|
| 1 | En una primera sesión del caso 1, `buscar_incidencias_similares` sugirió como padre **INC-000004** (pedidos que no llegan a cocina) para un error de **pago**. Claude lo detectó y **se negó a vincularlo** ("es de otro tema… similitud 0,33"). | Palabras como "pedido" y "ticket" hacían coincidir tickets de otra categoría en el cálculo de incidencia masiva. | Con `categoria` informada, la masiva solo cuenta tickets de esa categoría (`service.py`) + test de regresión `test_masiva_no_mezcla_categorias`. |
| 2 | Claude elegía la Skill correctamente, pero en modo no interactivo la llamada a la herramienta `Skill` quedaba **denegada** y trabajaba solo con las descripciones de las tools del MCP. | La herramienta `Skill` también pasa por el sistema de permisos. | Se añade `"Skill(triage-kioskos)"` a `permissions.allow`. Desde entonces la Skill se carga y lee sus ficheros de `reference/`. |
| 3 | En la prueba en **Windows**, Claude informó de *"0 de 2 kioskos conectados, 9 min sin conexión"* en un local que debía tener ambos online. | La telemetría de demo se guardaba como fecha fija al crear la base de datos y "envejecía": a los 5 min todos los kioskos parecían caídos. | Se guarda un desfase fijo (`demo_min_sin_conexion`) en vez de una fecha + test `test_telemetria_demo_no_envejece`. |
