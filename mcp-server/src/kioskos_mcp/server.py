"""Servidor MCP 'kioskos': soporte de kioskos de autoservicio para restauración.

Tools (6):
  Lectura   -> buscar_kiosko, buscar_incidencias_similares, obtener_ticket, proponer_ticket
  Escritura -> crear_ticket, actualizar_ticket

No existe ninguna tool de borrado: es una decisión de diseño deliberada.
Transporte: stdio (el cliente lanza el proceso; no abre puertos de red).
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .config import Config
from .models import (
    ResultadoActualizacion,
    ResultadoBusquedaKiosko,
    ResultadoCreacion,
    ResultadoSimilares,
    TicketDetalle,
)
from .rules import Categoria, Estado, Nivel, Urgencia
from .service import KioskosService

# En stdio, stdout es el canal del protocolo: los logs SIEMPRE a stderr.
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("kioskos-mcp")

mcp = FastMCP(
    "kioskos",
    instructions=(
        "Soporte de kioskos de autoservicio en restaurantes. Consulta el kiosko (telemetría, "
        "local, contrato, horario) y los tickets similares antes de crear nada. La prioridad y "
        "el grupo los calcula el servidor a partir de impacto y urgencia: no los inventes. Usa "
        "proponer_ticket, muestra la propuesta y solo tras la confirmación llama a crear_ticket "
        "con los mismos datos."
    ),
)

_servicio: KioskosService | None = None


def servicio() -> KioskosService:
    global _servicio
    if _servicio is None:
        _servicio = KioskosService(Config.desde_entorno())
    return _servicio


TicketId = Annotated[str, Field(pattern=r"^INC-\d{6}$", description="Identificador de ticket, p. ej. INC-000123")]


# --------------------------------------------------------------------- lectura
@mcp.tool(annotations=ToolAnnotations(title="Buscar kiosko", readOnlyHint=True, openWorldHint=False))
def buscar_kiosko(
    consulta: Annotated[
        str,
        Field(
            min_length=2, max_length=120,
            description="Email del contacto que reporta (devuelve los kioskos de su local), id de "
            "kiosko (KSK-0401), nº de serie, id de local (LOC-004), nombre del local, ciudad o cliente.",
        ),
    ],
) -> ResultadoBusquedaKiosko:
    """Devuelve kioskos con su telemetría (online, minutos sin conexión), versión de software,
    pinpad e impresora, y el contexto del local: kioskos totales y online, si está ahora en
    horario de servicio, cliente, nivel de contrato y si está en despliegue. Úsala ANTES de
    clasificar: es lo que determina el impacto real."""
    return servicio().buscar_kiosko(consulta)


@mcp.tool(annotations=ToolAnnotations(title="Buscar incidencias similares", readOnlyHint=True, openWorldHint=False))
def buscar_incidencias_similares(
    texto: Annotated[str, Field(min_length=3, max_length=500, description="Síntoma resumido, p. ej. 'error comunicación TPV pago tarjeta'")],
    dias: Annotated[int, Field(ge=1, le=90, description="Ventana de búsqueda en días")] = 7,
    limite: Annotated[int, Field(ge=1, le=20, description="Máximo de resultados")] = 5,
    categoria: Annotated[Optional[Categoria], Field(description="Categoría provisional; los tickets de la misma categoría puntúan más")] = None,
) -> ResultadoSimilares:
    """Busca tickets parecidos en todo el parque. Indica si hay una posible incidencia masiva
    (3+ similares abiertas en 24 h), el ticket padre sugerido, los locales afectados y las
    versiones de software implicadas (una sola versión apunta a un fallo de release)."""
    return servicio().buscar_similares(texto, dias, limite, categoria)


@mcp.tool(annotations=ToolAnnotations(title="Consultar ticket", readOnlyHint=True, openWorldHint=False))
def obtener_ticket(ticket_id: TicketId) -> TicketDetalle:
    """Devuelve el detalle completo de un ticket: estado, SLA, incumplimiento e historial."""
    return servicio().obtener_ticket(ticket_id)


# Campos comunes a proponer_ticket y crear_ticket (mismo schema = misma llamada)
Titulo = Annotated[str, Field(min_length=5, max_length=120, description="Resumen en una línea")]
Descripcion = Annotated[str, Field(min_length=10, max_length=4000, description="Síntomas, desde cuándo, qué se ha probado, impacto en el servicio")]
CategoriaF = Annotated[Categoria, Field(description="Categoría según reference/categorias.md")]
ImpactoF = Annotated[Nivel, Field(description="alto = local sin autoservicio o varios locales; medio = parte de los kioskos o función parcial; bajo = molestia con alternativa")]
UrgenciaF = Annotated[Urgencia, Field(description="alta = en horario de servicio o apertura inminente; media = degradado; baja = puede esperar")]
Email = Annotated[str, Field(max_length=254, description="Email del contacto registrado del cliente o email interno")]
KioskoId = Annotated[Optional[str], Field(pattern=r"^KSK-\d{4}$", description="Id de kiosko (de buscar_kiosko)")]
LocalId = Annotated[Optional[str], Field(pattern=r"^LOC-\d{3}$", description="Id de local si el problema no es de un kiosko concreto")]
Padre = Annotated[Optional[str], Field(pattern=r"^INC-\d{6}$", description="Ticket de incidencia masiva al que vincular")]


@mcp.tool(annotations=ToolAnnotations(title="Proponer ticket (simulación)", readOnlyHint=True, openWorldHint=False))
def proponer_ticket(
    titulo: Titulo, descripcion: Descripcion, categoria: CategoriaF, impacto: ImpactoF,
    urgencia: UrgenciaF, solicitante_email: Email, kiosko_id: KioskoId = None,
    local_id: LocalId = None, ticket_padre: Padre = None,
) -> ResultadoCreacion:
    """SIMULA la creación de un ticket SIN guardar nada: devuelve prioridad, reglas aplicadas,
    grupo resolutor, SLA y qué datos sensibles se redactarían. Úsala antes de crear_ticket para
    mostrar la propuesta al técnico."""
    return servicio().crear_ticket(
        titulo=titulo, descripcion=descripcion, categoria=categoria, impacto=impacto,
        urgencia=urgencia, solicitante_email=solicitante_email, kiosko_id=kiosko_id,
        local_id=local_id, ticket_padre=ticket_padre, dry_run=True,
    )


# ------------------------------------------------------------------- escritura
@mcp.tool(
    annotations=ToolAnnotations(
        title="Crear ticket de incidencia", readOnlyHint=False, destructiveHint=False,
        idempotentHint=True, openWorldHint=False,
    )
)
def crear_ticket(
    titulo: Titulo, descripcion: Descripcion, categoria: CategoriaF, impacto: ImpactoF,
    urgencia: UrgenciaF, solicitante_email: Email, kiosko_id: KioskoId = None,
    local_id: LocalId = None, ticket_padre: Padre = None,
) -> ResultadoCreacion:
    """Crea y guarda un ticket. EFECTO SECUNDARIO: llámala solo tras la confirmación explícita
    sobre la propuesta de proponer_ticket. El servidor calcula prioridad, SLA y grupo, valida que
    el solicitante sea un contacto autorizado de ese cliente, redacta tarjetas/CVV/contraseñas y
    no duplica un ticket idéntico de los últimos 10 min."""
    return servicio().crear_ticket(
        titulo=titulo, descripcion=descripcion, categoria=categoria, impacto=impacto,
        urgencia=urgencia, solicitante_email=solicitante_email, kiosko_id=kiosko_id,
        local_id=local_id, ticket_padre=ticket_padre, dry_run=False,
    )


@mcp.tool(
    annotations=ToolAnnotations(
        title="Actualizar estado de ticket", readOnlyHint=False, destructiveHint=False,
        idempotentHint=False, openWorldHint=False,
    )
)
def actualizar_ticket(
    ticket_id: TicketId,
    nuevo_estado: Annotated[Estado, Field(description="Estado destino; se validan las transiciones permitidas")],
    comentario: Annotated[str, Field(min_length=5, max_length=2000, description="Motivo del cambio (queda en el historial)")],
    vincular_a: Annotated[Optional[str], Field(pattern=r"^INC-\d{6}$", description="Opcional: ticket padre de incidencia masiva")] = None,
) -> ResultadoActualizacion:
    """Cambia el estado de un ticket y añade un comentario al historial. EFECTO SECUNDARIO.
    Puede vincular el ticket a una incidencia masiva. No permite borrar tickets."""
    return servicio().actualizar_ticket(
        ticket_id=ticket_id, nuevo_estado=nuevo_estado, comentario=comentario, vincular_a=vincular_a,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor MCP de soporte de kioskos (stdio)")
    parser.add_argument("--init", action="store_true", help="Crea y siembra la base de datos y sale")
    args = parser.parse_args()
    s = servicio()
    log.info("kioskos-mcp listo. Datos en %s (solo_lectura=%s)", s.config.data_dir, s.config.solo_lectura)
    if args.init:
        print(f"Base de datos lista en {s.config.db_path}", file=sys.stderr)
        return
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
