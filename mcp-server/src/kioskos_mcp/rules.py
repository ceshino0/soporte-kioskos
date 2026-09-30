"""Reglas de negocio del soporte de kioskos de autoservicio (restauración).

Todo lo que decide prioridad, SLA y grupo resolutor vive aquí, en el servidor,
para que el modelo NO pueda "negociar" una prioridad: la Skill propone impacto
y urgencia, y el servidor calcula el resultado de forma determinista.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

Categoria = Literal[
    "pago_tpv",
    "impresion_ticket",
    "hardware_kiosko",
    "software_kiosko",
    "integracion_pos_kds",
    "conectividad",
    "contenido_menu",
    "seguridad",
    "otro",
]
Nivel = Literal["alto", "medio", "bajo"]
Urgencia = Literal["alta", "media", "baja"]
Prioridad = Literal["P1", "P2", "P3", "P4"]
Estado = Literal[
    "nuevo", "asignado", "en_curso", "pendiente_cliente", "resuelto", "cerrado"
]

# Matriz ITIL impacto x urgencia -> prioridad
MATRIZ_PRIORIDAD: dict[tuple[str, str], Prioridad] = {
    ("alto", "alta"): "P1",
    ("alto", "media"): "P2",
    ("alto", "baja"): "P3",
    ("medio", "alta"): "P2",
    ("medio", "media"): "P3",
    ("medio", "baja"): "P4",
    ("bajo", "alta"): "P3",
    ("bajo", "media"): "P4",
    ("bajo", "baja"): "P4",
}

# SLA en horas naturales: (primera respuesta, resolución)
SLA_HORAS: dict[str, tuple[float, float]] = {
    "P1": (0.25, 4),
    "P2": (0.5, 8),
    "P3": (4, 24),
    "P4": (8, 72),
}

GRUPO_POR_CATEGORIA: dict[str, str] = {
    "pago_tpv": "Pagos y TPV",
    "impresion_ticket": "Soporte de campo (hardware)",
    "hardware_kiosko": "Soporte de campo (hardware)",
    "software_kiosko": "Soporte N2 - Aplicación kiosko",
    "contenido_menu": "Soporte N2 - Aplicación kiosko",
    "integracion_pos_kds": "Integraciones POS / KDS",
    "conectividad": "Redes y conectividad",
    "seguridad": "Seguridad y cumplimiento PCI",
    "otro": "Service Desk N1",
}
GRUPO_PROYECTOS = "Proyectos y Despliegues"

# Categorías que nunca bajan de P2 y por qué
SUELO_P2 = {
    "pago_tpv": "afecta al cobro (pérdida de ventas / cargos a clientes finales)",
    "seguridad": "posible incidente de seguridad o PCI-DSS",
}

TRANSICIONES: dict[str, set[str]] = {
    "nuevo": {"asignado", "en_curso", "resuelto"},
    "asignado": {"en_curso", "pendiente_cliente", "resuelto"},
    "en_curso": {"pendiente_cliente", "resuelto"},
    "pendiente_cliente": {"en_curso", "resuelto"},
    "resuelto": {"cerrado", "en_curso"},  # en_curso = reapertura
    "cerrado": set(),
}

ORDEN = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
SUBIR = {"P4": "P3", "P3": "P2", "P2": "P2", "P1": "P1"}


def calcular_prioridad(
    impacto: str, urgencia: str, categoria: str, nivel_contrato: str | None
) -> tuple[Prioridad, list[str]]:
    """Devuelve la prioridad y la lista de reglas aplicadas (trazabilidad)."""
    reglas: list[str] = []
    prioridad: str = MATRIZ_PRIORIDAD[(impacto, urgencia)]
    reglas.append(f"Matriz: impacto={impacto} x urgencia={urgencia} -> {prioridad}")

    # Regla 1: pagos y seguridad nunca por debajo de P2
    if categoria in SUELO_P2 and ORDEN[prioridad] > 2:
        reglas.append(f"Suelo P2 ({categoria}: {SUELO_P2[categoria]}): {prioridad} -> P2")
        prioridad = "P2"

    # Regla 2: contrato Gold sube un nivel (máximo hasta P2; P1 solo sale de la matriz)
    if nivel_contrato == "gold" and ORDEN[prioridad] > 2:
        reglas.append(f"Contrato gold: {prioridad} -> {SUBIR[prioridad]}")
        prioridad = SUBIR[prioridad]

    return prioridad, reglas  # type: ignore[return-value]


def grupo_resolutor(categoria: str, estado_kiosko: str | None, estado_local: str | None) -> tuple[str, str | None]:
    """Los kioskos o locales en despliegue los atiende el equipo de proyecto, no soporte."""
    if "en_despliegue" in (estado_kiosko, estado_local):
        return GRUPO_PROYECTOS, "Kiosko/local en despliegue -> grupo Proyectos y Despliegues"
    return GRUPO_POR_CATEGORIA[categoria], None


def calcular_sla(prioridad: str, desde: datetime) -> tuple[datetime, datetime]:
    resp_h, resol_h = SLA_HORAS[prioridad]
    return desde + timedelta(hours=resp_h), desde + timedelta(hours=resol_h)


def en_horario(horario: str, momento: datetime) -> bool:
    """horario = 'HH:MM-HH:MM,HH:MM-HH:MM' en hora local del local."""
    hm = momento.strftime("%H:%M")
    for tramo in horario.split(","):
        ini, fin = tramo.strip().split("-")
        if ini <= hm <= fin:
            return True
    return False


def transicion_valida(actual: str, nuevo: str) -> bool:
    return nuevo in TRANSICIONES.get(actual, set())
