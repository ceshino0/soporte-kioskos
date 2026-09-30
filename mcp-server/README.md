# kioskos-mcp

Servidor MCP (Python, SDK oficial `mcp` / FastMCP) para el **soporte de kioskos de autoservicio
en restauración**. Expone el parque instalado (clientes, locales, kioskos con telemetría,
contactos autorizados) y el sistema de tickets.

- Transporte **stdio**: el cliente (Claude Code) lanza el proceso; no abre puertos de red.
- **SQLite** local, sembrado automáticamente la primera vez con datos ficticios.
- **Sin secretos**: toda la configuración va por variables de entorno.

## Modelo de datos

```
clientes (nivel_contrato gold/silver/bronze)
   └─< locales (ciudad, horario_servicio, estado operativo/en_despliegue, apertura_prevista)
          └─< kioskos (nº serie, modelo, versión software, pinpad, impresora, estado, ultima_conexion)
clientes └─< contactos (email, rol, local opcional)   ← quién puede abrir tickets
tickets (kiosko, local, categoría, impacto, urgencia, prioridad, grupo, SLA, padre) └─< comentarios
```

## Tools

| Tool | Tipo | Qué hace | Entradas clave |
|---|---|---|---|
| `buscar_kiosko` | lectura | Por email de contacto (devuelve los kioskos de su local o cliente), id, nº de serie, local, ciudad o cliente. Calcula `online`, `minutos_sin_conexion`, `kioskos_online_en_local`, `en_horario_servicio`. | `consulta` (2-120) |
| `buscar_incidencias_similares` | lectura | Tickets parecidos en todo el parque; masiva (3+ abiertas en 24 h), padre sugerido, `locales_afectados`, `versiones_software_afectadas`. | `texto`, `dias` (1-90), `limite` (1-20), `categoria?` (enum) |
| `obtener_ticket` | lectura | Detalle, SLA, incumplimiento e historial. | `ticket_id` (`^INC-\d{6}$`) |
| `proponer_ticket` | lectura | **Simula** la creación: prioridad, reglas aplicadas, grupo, SLA y datos que se redactarían. No guarda nada. | mismos campos que `crear_ticket` |
| `crear_ticket` | **escritura** | Crea el ticket. Idempotente (no duplica uno idéntico de los últimos 10 min). | `titulo`, `descripcion`, `categoria` (enum 9), `impacto` (enum 3), `urgencia` (enum 3), `solicitante_email`, `kiosko_id?` (`^KSK-\d{4}$`), `local_id?` (`^LOC-\d{3}$`), `ticket_padre?` |
| `actualizar_ticket` | **escritura** | Cambia estado (máquina de estados), añade comentario, vincula a masiva. | `ticket_id`, `nuevo_estado` (enum 6), `comentario`, `vincular_a?` |

Categorías: `pago_tpv`, `impresion_ticket`, `hardware_kiosko`, `software_kiosko`,
`integracion_pos_kds`, `conectividad`, `contenido_menu`, `seguridad`, `otro`.

Todas llevan `ToolAnnotations` y devuelven **salida estructurada** (modelos Pydantic).

### Decisiones de diseño

- **La prioridad y el grupo no son parámetros.** El modelo propone impacto y urgencia; el
  servidor aplica la matriz ITIL, el suelo P2 de pagos y seguridad, la subida por contrato gold
  y la derivación a *Proyectos y Despliegues*, y devuelve `reglas_aplicadas`.
- **El contexto se calcula en el servidor**, no se deja al modelo: si el kiosko está online,
  si el local está en servicio, cuántos kioskos le quedan, qué versiones comparten los
  tickets de una masiva.
- **`proponer_ticket` y `crear_ticket` separadas** para dar permisos distintos.
- **No existe tool de borrado.**
- **Errores accionables**: dicen cómo corregir la llamada.

## Seguridad

| Control | Dónde |
|---|---|
| Solo pueden abrir tickets emails internos o **contactos registrados** | `service._validar_solicitante` |
| Un contacto **no puede** abrir tickets sobre kioskos de **otro cliente** | `service._validar_solicitante` |
| Redacción de nº de tarjeta, CVV, contraseñas, API keys, JWT e IBAN (PCI-DSS) | `redaction.py` |
| Modo solo lectura global | `KIOSKOS_READ_ONLY=true` |
| Schemas estrictos (enums, regex de ids, longitudes) | `server.py` |
| Coherencia kiosko ↔ local | `service.crear_ticket` |
| Máquina de estados (no se reabre un `cerrado`) | `rules.TRANSICIONES` |
| SQL 100 % parametrizado | `service.py` |
| Auditoría JSONL de cada escritura, sin datos sensibles | `<data_dir>/audit.log` |
| Logs a `stderr` (stdout es el canal MCP) | `server.py` |

## Instalación

Requisitos: **Python 3.10 o superior** (probado con 3.11 y 3.13).

### Windows (PowerShell)

```powershell
cd mcp-server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
kioskos-mcp --init        # crea y siembra la base de datos, y sale
```

> Si PowerShell bloquea `Activate.ps1`: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### Linux / macOS

```bash
cd mcp-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
kioskos-mcp --init
```

`requirements.txt` fija las versiones exactas probadas e instala el paquete en modo editable
(comando `kioskos-mcp`). Debe ejecutarse desde la carpeta `mcp-server`.

## Configuración

| Variable | Por defecto | Uso |
|---|---|---|
| `KIOSKOS_DATA_DIR` | `~/.kioskos-mcp` | Carpeta de `kioskos.db` y `audit.log` |
| `KIOSKOS_INTERNAL_DOMAINS` | `empresa.example` | Dominios del personal interno (pueden abrir tickets en cualquier cliente) |
| `KIOSKOS_READ_ONLY` | `false` | `true` bloquea `crear_ticket` y `actualizar_ticket` |
| `KIOSKOS_ACTOR` | `claude-agent` | Nombre en el historial y la auditoría |
| `KIOSKOS_TZ` | `Europe/Madrid` | Zona horaria para fechas y horario de servicio |

**Adaptarlo a un parque real:** edita `src/kioskos_mcp/seed/parque.json` (clientes, locales,
kioskos, contactos) y `tickets.json`, y borra `KIOSKOS_DATA_DIR` para volver a sembrar. Matriz,
SLA, grupos y suelos de prioridad están en `rules.py`.

Para **resetear** la demo (volver a los 7 tickets iniciales), borra la carpeta `KIOSKOS_DATA_DIR`.

## Probar

```bash
pip install -r requirements-dev.txt
pytest -q                                   # 19 tests: reglas, PCI, aislamiento, masivas…
python scripts/demo_client.py               # sesión MCP real por stdio (datos temporales)
python scripts/demo_client.py --out ../docs/transcript-mcp.md
npx @modelcontextprotocol/inspector kioskos-mcp   # inspector oficial (requiere Node.js)
```

## Conectarlo a Claude Code

El `.mcp.json` de la raíz ya lo registra como servidor `kioskos`. Con el entorno virtual
activado, abre Claude Code en la raíz del proyecto y comprueba con `/mcp` que aparece
**connected**. Alternativa manual:

```bash
claude mcp add kioskos --scope project -- kioskos-mcp
```

## Estructura

```
mcp-server/
├── pyproject.toml          # paquete + comando kioskos-mcp
├── requirements.txt        # versiones fijadas
├── requirements-dev.txt    # + pytest
├── .env.example
├── src/kioskos_mcp/
│   ├── server.py           # las 6 tools (schemas, anotaciones)
│   ├── service.py          # lógica + SQLite (testeable sin MCP)
│   ├── rules.py            # matriz, suelos, contrato, grupos, horario, transiciones
│   ├── redaction.py        # tarjeta, CVV, credenciales
│   ├── models.py           # modelos de salida tipados
│   ├── config.py           # variables de entorno
│   └── seed/               # parque y tickets de demostración (ficticios)
├── tests/test_kioskos.py
└── scripts/demo_client.py
```
