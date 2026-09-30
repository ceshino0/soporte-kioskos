"""Cliente MCP de demostración: lanza el servidor por stdio (como hace Claude Code),
recorre el flujo de la Skill con dos casos reales de kioskos y guarda el transcript.

Uso:
    python scripts/demo_client.py
    python scripts/demo_client.py --out ../docs/transcript-mcp.md

Usa un directorio de datos temporal: no toca tu base de datos real.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

LINEAS: list[str] = []


def out(texto: str = "") -> None:
    LINEAS.append(texto)
    print(texto)


async def llamar(sesion: ClientSession, tool: str, args: dict) -> dict:
    out(f"### → `{tool}`")
    out("```json\n" + json.dumps(args, ensure_ascii=False, indent=2) + "\n```")
    res = await sesion.call_tool(tool, args)
    if res.isError:
        texto = res.content[0].text if res.content else "(sin detalle)"
        out(f"**← error (isError=true)**\n```\n{texto}\n```\n")
        return {}
    datos = res.structuredContent or {}
    out("**←**\n```json\n" + json.dumps(datos, ensure_ascii=False, indent=2) + "\n```\n")
    return datos


async def main(ruta_salida: str | None) -> None:
    data_dir = tempfile.mkdtemp(prefix="kioskos-demo-")
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "kioskos_mcp.server"],
        env={**os.environ, "KIOSKOS_DATA_DIR": data_dir, "KIOSKOS_ACTOR": "demo-client"},
    )
    out("# Transcript real: cliente MCP ↔ kioskos-mcp (stdio)")
    out(f"_Generado con `scripts/demo_client.py` el {datetime.now():%Y-%m-%d %H:%M}. "
        "Salidas copiadas tal cual del servidor. Datos ficticios._\n")

    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            init = await s.initialize()
            out(f"## 0. Handshake\nServidor: `{init.serverInfo.name}` (SDK MCP Python "
                f"v{init.serverInfo.version}), transporte stdio\n")
            tools = await s.list_tools()
            out("| Tool | readOnly | Parámetros |\n|---|---|---|")
            for t in tools.tools:
                out(f"| `{t.name}` | {t.annotations.readOnlyHint} | "
                    f"{', '.join(t.inputSchema.get('properties', {}).keys())} |")
            out()

            # ------------------------------------------------------------ caso A
            out("---\n# Caso A — Kiosko único que no enciende en hora de comidas")
            out("> **Lucía Romero** (Wok & Go Sevilla Nervión) llama: _\"El kiosko no enciende desde "
                "que abrimos, pantalla negra. Es el único que tenemos y la cola en caja llega a la "
                "puerta.\"_\n")
            out("## A1. Contexto del kiosko y del local")
            await llamar(s, "buscar_kiosko", {"consulta": "sevilla.nervion@wokandgo.example"})
            out("## A2. ¿Es un problema general?")
            await llamar(s, "buscar_incidencias_similares",
                         {"texto": "kiosko no enciende pantalla negra", "categoria": "hardware_kiosko"})
            out("## A3. Propuesta (solo lectura)")
            caso_a = {
                "titulo": "Kiosko único no enciende (pantalla negra) en hora de servicio",
                "descripcion": "Pantalla negra desde la apertura. Telemetría: sin conexión desde hace "
                               "más de 90 min. Es el único kiosko del local; clientes derivados a caja.",
                "categoria": "hardware_kiosko", "impacto": "alto", "urgencia": "alta",
                "solicitante_email": "sevilla.nervion@wokandgo.example", "kiosko_id": "KSK-0401",
            }
            await llamar(s, "proponer_ticket", caso_a)
            out("## A4. Creación tras confirmación")
            await llamar(s, "crear_ticket", caso_a)

            # ------------------------------------------------------------ caso B
            out("---\n# Caso B — Error de pago: incidencia masiva por versión de software")
            out("> **Elena Ferrer** (La Parrilla Urbana Valencia Ruzafa) escribe: _\"El kiosko 2 da "
                "'Error de comunicación con TPV'. A un cliente le ha cobrado y no ha salido el ticket "
                "del pedido; su tarjeta es 4111 1111 1111 1111 por si la necesitáis.\"_\n")
            out("## B1. Contexto")
            await llamar(s, "buscar_kiosko", {"consulta": "KSK-0202"})
            out("## B2. Similares en todo el parque")
            sim = await llamar(s, "buscar_incidencias_similares", {
                "texto": "error comunicación TPV pago tarjeta cobrado sin ticket", "categoria": "pago_tpv"})
            caso_b = {
                "titulo": "Error de comunicación con TPV y cobro sin ticket de pedido",
                "descripcion": "Kiosko 2 muestra 'Error de comunicación con TPV'. Un cliente ha sido "
                               "cobrado sin generarse pedido ni ticket. Tarjeta aportada por el local: "
                               "4111 1111 1111 1111.",
                "categoria": "pago_tpv", "impacto": "medio", "urgencia": "alta",
                "solicitante_email": "encargada.ruzafa@parrillaurbana.example",
                "kiosko_id": "KSK-0202", "ticket_padre": sim.get("ticket_padre_sugerido"),
            }
            out("## B3. Propuesta: el servidor detecta la tarjeta y la redactará")
            out("> _En esta demo se envía la tarjeta **a propósito** para comprobar la última barrera: "
                "aunque el modelo la copiara (la Skill le indica que no lo haga), el servidor no la guarda._\n")
            await llamar(s, "proponer_ticket", caso_b)
            out("## B4. Creación y reintento accidental (idempotencia)")
            creado = await llamar(s, "crear_ticket", caso_b)
            await llamar(s, "crear_ticket", caso_b)
            out("## B5. Vincular otro ticket suelto a la incidencia masiva")
            await llamar(s, "actualizar_ticket", {
                "ticket_id": "INC-000003", "nuevo_estado": "en_curso",
                "comentario": "Mismo fallo de TPV en kioskos con v4.2.1",
                "vincular_a": sim.get("ticket_padre_sugerido"),
            })
            out("## B6. Verificación: la tarjeta no se ha guardado")
            await llamar(s, "obtener_ticket", {"ticket_id": creado.get("ticket_id", "INC-000009")})

            # ---------------------------------------------------------- guardarraíles
            out("---\n# Guardarraíles: peticiones que el servidor rechaza")
            await llamar(s, "crear_ticket", {**caso_a, "solicitante_email": "desconocido@gmail.com"})
            await llamar(s, "crear_ticket", {**caso_b, "solicitante_email": "diagonal@wokandgo.example"})
            await llamar(s, "actualizar_ticket", {"ticket_id": "INC-000006", "nuevo_estado": "en_curso",
                                                  "comentario": "Intento reabrir un cerrado"})
            await llamar(s, "crear_ticket", {**caso_a, "categoria": "urgentisimo"})

    with open(os.path.join(data_dir, "audit.log"), encoding="utf-8") as f:
        out("## Log de auditoría (`audit.log`)\n```jsonl\n" + f.read().strip() + "\n```")

    if ruta_salida:
        with open(ruta_salida, "w", encoding="utf-8") as f:
            f.write("\n".join(LINEAS) + "\n")
        print(f"\nTranscript guardado en {ruta_salida}", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="Ruta del Markdown de salida")
    asyncio.run(main(ap.parse_args().out))
