# Transcript real: cliente MCP ↔ kioskos-mcp (stdio)
_Generado con `scripts/demo_client.py` el 2026-09-30 17:53. Salidas copiadas tal cual del servidor. Datos ficticios._

## 0. Handshake
Servidor: `kioskos` (SDK MCP Python v1.30.0), transporte stdio

| Tool | readOnly | Parámetros |
|---|---|---|
| `buscar_kiosko` | True | consulta |
| `buscar_incidencias_similares` | True | texto, dias, limite, categoria |
| `obtener_ticket` | True | ticket_id |
| `proponer_ticket` | True | titulo, descripcion, categoria, impacto, urgencia, solicitante_email, kiosko_id, local_id, ticket_padre |
| `crear_ticket` | False | titulo, descripcion, categoria, impacto, urgencia, solicitante_email, kiosko_id, local_id, ticket_padre |
| `actualizar_ticket` | False | ticket_id, nuevo_estado, comentario, vincular_a |

---
# Caso A — Kiosko único que no enciende en hora de comidas
> **Lucía Romero** (Wok & Go Sevilla Nervión) llama: _"El kiosko no enciende desde que abrimos, pantalla negra. Es el único que tenemos y la cola en caja llega a la puerta."_

## A1. Contexto del kiosko y del local
### → `buscar_kiosko`
```json
{
  "consulta": "sevilla.nervion@wokandgo.example"
}
```
**←**
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
      "en_horario_servicio": false,
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

## A2. ¿Es un problema general?
### → `buscar_incidencias_similares`
```json
{
  "texto": "kiosko no enciende pantalla negra",
  "categoria": "hardware_kiosko"
}
```
**←**
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
      "creado_en": "2026-09-29T21:53+02:00",
      "similitud": 0.33
    }
  ]
}
```

## A3. Propuesta (solo lectura)
### → `proponer_ticket`
```json
{
  "titulo": "Kiosko único no enciende (pantalla negra) en hora de servicio",
  "descripcion": "Pantalla negra desde la apertura. Telemetría: sin conexión desde hace más de 90 min. Es el único kiosko del local; clientes derivados a caja.",
  "categoria": "hardware_kiosko",
  "impacto": "alto",
  "urgencia": "alta",
  "solicitante_email": "sevilla.nervion@wokandgo.example",
  "kiosko_id": "KSK-0401"
}
```
**←**
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
  "sla_respuesta_limite": "2026-09-30T18:08+02:00",
  "sla_resolucion_limite": "2026-09-30T21:53+02:00",
  "datos_redactados": [],
  "kiosko_id": "KSK-0401",
  "local_id": "LOC-004",
  "ticket_padre": null,
  "mensaje": "Simulación: nada guardado. Confirma con el usuario y llama a crear_ticket con los mismos datos."
}
```

## A4. Creación tras confirmación
### → `crear_ticket`
```json
{
  "titulo": "Kiosko único no enciende (pantalla negra) en hora de servicio",
  "descripcion": "Pantalla negra desde la apertura. Telemetría: sin conexión desde hace más de 90 min. Es el único kiosko del local; clientes derivados a caja.",
  "categoria": "hardware_kiosko",
  "impacto": "alto",
  "urgencia": "alta",
  "solicitante_email": "sevilla.nervion@wokandgo.example",
  "kiosko_id": "KSK-0401"
}
```
**←**
```json
{
  "simulacion": false,
  "duplicado": false,
  "ticket_id": "INC-000008",
  "prioridad": "P1",
  "reglas_aplicadas": [
    "Matriz: impacto=alto x urgencia=alta -> P1"
  ],
  "grupo_asignado": "Soporte de campo (hardware)",
  "sla_respuesta_limite": "2026-09-30T18:08+02:00",
  "sla_resolucion_limite": "2026-09-30T21:53+02:00",
  "datos_redactados": [],
  "kiosko_id": "KSK-0401",
  "local_id": "LOC-004",
  "ticket_padre": null,
  "mensaje": "Ticket INC-000008 creado y asignado a 'Soporte de campo (hardware)'."
}
```

---
# Caso B — Error de pago: incidencia masiva por versión de software
> **Elena Ferrer** (La Parrilla Urbana Valencia Ruzafa) escribe: _"El kiosko 2 da 'Error de comunicación con TPV'. A un cliente le ha cobrado y no ha salido el ticket del pedido; su tarjeta es 4111 1111 1111 1111 por si la necesitáis."_

## B1. Contexto
### → `buscar_kiosko`
```json
{
  "consulta": "KSK-0202"
}
```
**←**
```json
{
  "consulta": "KSK-0202",
  "total": 1,
  "contacto": null,
  "kioskos": [
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
      "en_horario_servicio": false,
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

## B2. Similares en todo el parque
### → `buscar_incidencias_similares`
```json
{
  "texto": "error comunicación TPV pago tarjeta cobrado sin ticket",
  "categoria": "pago_tpv"
}
```
**←**
```json
{
  "consulta": "error comunicación TPV pago tarjeta cobrado sin ticket",
  "ventana_dias": 7,
  "total": 3,
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
      "creado_en": "2026-09-30T14:53+02:00",
      "similitud": 0.82
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
      "creado_en": "2026-09-30T15:53+02:00",
      "similitud": 0.82
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
      "creado_en": "2026-09-30T16:53+02:00",
      "similitud": 0.82
    }
  ]
}
```

## B3. Propuesta: el servidor detecta la tarjeta y la redactará
> _En esta demo se envía la tarjeta **a propósito** para comprobar la última barrera: aunque el modelo la copiara (la Skill le indica que no lo haga), el servidor no la guarda._

### → `proponer_ticket`
```json
{
  "titulo": "Error de comunicación con TPV y cobro sin ticket de pedido",
  "descripcion": "Kiosko 2 muestra 'Error de comunicación con TPV'. Un cliente ha sido cobrado sin generarse pedido ni ticket. Tarjeta aportada por el local: 4111 1111 1111 1111.",
  "categoria": "pago_tpv",
  "impacto": "medio",
  "urgencia": "alta",
  "solicitante_email": "encargada.ruzafa@parrillaurbana.example",
  "kiosko_id": "KSK-0202",
  "ticket_padre": "INC-000001"
}
```
**←**
```json
{
  "simulacion": true,
  "duplicado": false,
  "ticket_id": null,
  "prioridad": "P2",
  "reglas_aplicadas": [
    "Matriz: impacto=medio x urgencia=alta -> P2"
  ],
  "grupo_asignado": "Pagos y TPV",
  "sla_respuesta_limite": "2026-09-30T18:23+02:00",
  "sla_resolucion_limite": "2026-10-01T01:53+02:00",
  "datos_redactados": [
    "tarjeta"
  ],
  "kiosko_id": "KSK-0202",
  "local_id": "LOC-002",
  "ticket_padre": "INC-000001",
  "mensaje": "Simulación: nada guardado. Confirma con el usuario y llama a crear_ticket con los mismos datos."
}
```

## B4. Creación y reintento accidental (idempotencia)
### → `crear_ticket`
```json
{
  "titulo": "Error de comunicación con TPV y cobro sin ticket de pedido",
  "descripcion": "Kiosko 2 muestra 'Error de comunicación con TPV'. Un cliente ha sido cobrado sin generarse pedido ni ticket. Tarjeta aportada por el local: 4111 1111 1111 1111.",
  "categoria": "pago_tpv",
  "impacto": "medio",
  "urgencia": "alta",
  "solicitante_email": "encargada.ruzafa@parrillaurbana.example",
  "kiosko_id": "KSK-0202",
  "ticket_padre": "INC-000001"
}
```
**←**
```json
{
  "simulacion": false,
  "duplicado": false,
  "ticket_id": "INC-000009",
  "prioridad": "P2",
  "reglas_aplicadas": [
    "Matriz: impacto=medio x urgencia=alta -> P2"
  ],
  "grupo_asignado": "Pagos y TPV",
  "sla_respuesta_limite": "2026-09-30T18:23+02:00",
  "sla_resolucion_limite": "2026-10-01T01:53+02:00",
  "datos_redactados": [
    "tarjeta"
  ],
  "kiosko_id": "KSK-0202",
  "local_id": "LOC-002",
  "ticket_padre": "INC-000001",
  "mensaje": "Ticket INC-000009 creado y asignado a 'Pagos y TPV'."
}
```

### → `crear_ticket`
```json
{
  "titulo": "Error de comunicación con TPV y cobro sin ticket de pedido",
  "descripcion": "Kiosko 2 muestra 'Error de comunicación con TPV'. Un cliente ha sido cobrado sin generarse pedido ni ticket. Tarjeta aportada por el local: 4111 1111 1111 1111.",
  "categoria": "pago_tpv",
  "impacto": "medio",
  "urgencia": "alta",
  "solicitante_email": "encargada.ruzafa@parrillaurbana.example",
  "kiosko_id": "KSK-0202",
  "ticket_padre": "INC-000001"
}
```
**←**
```json
{
  "simulacion": false,
  "duplicado": true,
  "ticket_id": "INC-000009",
  "prioridad": "P2",
  "reglas_aplicadas": [
    "Matriz: impacto=medio x urgencia=alta -> P2"
  ],
  "grupo_asignado": "Pagos y TPV",
  "sla_respuesta_limite": "2026-09-30T18:23+02:00",
  "sla_resolucion_limite": "2026-10-01T01:53+02:00",
  "datos_redactados": [
    "tarjeta"
  ],
  "kiosko_id": "KSK-0202",
  "local_id": "LOC-002",
  "ticket_padre": "INC-000001",
  "mensaje": "Ya existía INC-000009 con el mismo contenido; no se ha duplicado."
}
```

## B5. Vincular otro ticket suelto a la incidencia masiva
### → `actualizar_ticket`
```json
{
  "ticket_id": "INC-000003",
  "nuevo_estado": "en_curso",
  "comentario": "Mismo fallo de TPV en kioskos con v4.2.1",
  "vincular_a": "INC-000001"
}
```
**←**
```json
{
  "ticket_id": "INC-000003",
  "estado_anterior": "nuevo",
  "estado_nuevo": "en_curso",
  "grupo_asignado": "Pagos y TPV",
  "datos_redactados": [],
  "mensaje": "INC-000003: nuevo -> en_curso, vinculado a INC-000001."
}
```

## B6. Verificación: la tarjeta no se ha guardado
### → `obtener_ticket`
```json
{
  "ticket_id": "INC-000009"
}
```
**←**
```json
{
  "id": "INC-000009",
  "titulo": "Error de comunicación con TPV y cobro sin ticket de pedido",
  "categoria": "pago_tpv",
  "prioridad": "P2",
  "estado": "nuevo",
  "grupo_asignado": "Pagos y TPV",
  "solicitante_email": "encargada.ruzafa@parrillaurbana.example",
  "kiosko_id": "KSK-0202",
  "local_id": "LOC-002",
  "creado_en": "2026-09-30T17:53+02:00",
  "similitud": null,
  "descripcion": "Kiosko 2 muestra 'Error de comunicación con TPV'. Un cliente ha sido cobrado sin generarse pedido ni ticket. Tarjeta aportada por el local: [REDACTADO].",
  "impacto": "medio",
  "urgencia": "alta",
  "actualizado_en": "2026-09-30T17:53+02:00",
  "sla_respuesta_limite": "2026-09-30T18:23+02:00",
  "sla_resolucion_limite": "2026-10-01T01:53+02:00",
  "sla_resolucion_incumplido": false,
  "ticket_padre": "INC-000001",
  "comentarios": [
    {
      "autor": "demo-client",
      "texto": "Ticket creado por triage asistido. Matriz: impacto=medio x urgencia=alta -> P2",
      "creado_en": "2026-09-30T17:53+02:00",
      "estado_anterior": null,
      "estado_nuevo": "nuevo"
    }
  ]
}
```

---
# Guardarraíles: peticiones que el servidor rechaza
### → `crear_ticket`
```json
{
  "titulo": "Kiosko único no enciende (pantalla negra) en hora de servicio",
  "descripcion": "Pantalla negra desde la apertura. Telemetría: sin conexión desde hace más de 90 min. Es el único kiosko del local; clientes derivados a caja.",
  "categoria": "hardware_kiosko",
  "impacto": "alto",
  "urgencia": "alta",
  "solicitante_email": "desconocido@gmail.com",
  "kiosko_id": "KSK-0401"
}
```
**← error (isError=true)**
```
Error executing tool crear_ticket: 'desconocido@gmail.com' no es un contacto registrado de ningún cliente ni un email interno. Pide al cliente que reporte desde un contacto autorizado o regístralo antes.
```

### → `crear_ticket`
```json
{
  "titulo": "Error de comunicación con TPV y cobro sin ticket de pedido",
  "descripcion": "Kiosko 2 muestra 'Error de comunicación con TPV'. Un cliente ha sido cobrado sin generarse pedido ni ticket. Tarjeta aportada por el local: 4111 1111 1111 1111.",
  "categoria": "pago_tpv",
  "impacto": "medio",
  "urgencia": "alta",
  "solicitante_email": "diagonal@wokandgo.example",
  "kiosko_id": "KSK-0202",
  "ticket_padre": "INC-000001"
}
```
**← error (isError=true)**
```
Error executing tool crear_ticket: El contacto diagonal@wokandgo.example pertenece a otro cliente (CLI-02) y no puede abrir incidencias sobre este kiosko.
```

### → `actualizar_ticket`
```json
{
  "ticket_id": "INC-000006",
  "nuevo_estado": "en_curso",
  "comentario": "Intento reabrir un cerrado"
}
```
**← error (isError=true)**
```
Error executing tool actualizar_ticket: Transición no permitida: cerrado -> en_curso. Desde 'cerrado' se puede ir a: ninguna (estado final).
```

### → `crear_ticket`
```json
{
  "titulo": "Kiosko único no enciende (pantalla negra) en hora de servicio",
  "descripcion": "Pantalla negra desde la apertura. Telemetría: sin conexión desde hace más de 90 min. Es el único kiosko del local; clientes derivados a caja.",
  "categoria": "urgentisimo",
  "impacto": "alto",
  "urgencia": "alta",
  "solicitante_email": "sevilla.nervion@wokandgo.example",
  "kiosko_id": "KSK-0401"
}
```
**← error (isError=true)**
```
Error executing tool crear_ticket: 1 validation error for crear_ticketArguments
categoria
  Input should be 'pago_tpv', 'impresion_ticket', 'hardware_kiosko', 'software_kiosko', 'integracion_pos_kds', 'conectividad', 'contenido_menu', 'seguridad' or 'otro' [type=literal_error, input_value='urgentisimo', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/literal_error
```

## Log de auditoría (`audit.log`)
```jsonl
{"ts": "2026-09-30T17:53+02:00", "actor": "demo-client", "accion": "crear_ticket", "ticket_id": "INC-000008", "prioridad": "P1", "categoria": "hardware_kiosko", "grupo": "Soporte de campo (hardware)", "solicitante": "sevilla.nervion@wokandgo.example", "kiosko_id": "KSK-0401", "local_id": "LOC-004", "ticket_padre": null, "redactados": []}
{"ts": "2026-09-30T17:53+02:00", "actor": "demo-client", "accion": "crear_ticket", "ticket_id": "INC-000009", "prioridad": "P2", "categoria": "pago_tpv", "grupo": "Pagos y TPV", "solicitante": "encargada.ruzafa@parrillaurbana.example", "kiosko_id": "KSK-0202", "local_id": "LOC-002", "ticket_padre": "INC-000001", "redactados": ["tarjeta"]}
{"ts": "2026-09-30T17:53+02:00", "actor": "demo-client", "accion": "actualizar_ticket", "ticket_id": "INC-000003", "de": "nuevo", "a": "en_curso", "vincular_a": "INC-000001", "redactados": []}
```
