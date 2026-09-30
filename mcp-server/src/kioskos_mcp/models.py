"""Modelos de salida tipados (se exponen como structuredContent en MCP)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Kiosko(BaseModel):
    id: str
    numero_serie: str
    modelo: str
    version_software: str
    pinpad: str
    impresora: str
    estado: str = Field(description="operativo | en_despliegue | retirado")
    online: bool = Field(description="True si ha enviado telemetría en los últimos 5 min")
    minutos_sin_conexion: int | None = Field(None, description="None = nunca se ha conectado")
    incidencias_abiertas: int
    # Contexto del local y del cliente
    local_id: str
    local_nombre: str
    ciudad: str
    estado_local: str
    horario_servicio: str
    en_horario_servicio: bool = Field(description="Si el local está ahora mismo en servicio")
    kioskos_en_local: int
    kioskos_online_en_local: int
    cliente_id: str
    cliente: str
    nivel_contrato: str = Field(description="gold | silver | bronze")
    apertura_prevista: str | None = Field(None, description="Solo para locales en despliegue")


class ResultadoBusquedaKiosko(BaseModel):
    consulta: str
    total: int
    contacto: str | None = Field(None, description="Si la consulta era el email de un contacto registrado")
    kioskos: list[Kiosko]


class TicketResumen(BaseModel):
    id: str
    titulo: str
    categoria: str
    prioridad: str
    estado: str
    grupo_asignado: str
    solicitante_email: str
    kiosko_id: str | None = None
    local_id: str | None = None
    creado_en: str
    similitud: float | None = Field(None, description="0-1, solo en búsquedas de similares")


class ResultadoSimilares(BaseModel):
    consulta: str
    ventana_dias: int
    total: int
    abiertas_ultimas_24h: int = Field(
        description="Similares abiertas creadas en las últimas 24 h (similitud >= 0.25)"
    )
    posible_incidencia_masiva: bool = Field(
        description="True si hay 3 o más similares abiertas en 24 h: vincular en vez de duplicar"
    )
    ticket_padre_sugerido: str | None = None
    locales_afectados: list[str] = Field(default_factory=list)
    versiones_software_afectadas: dict[str, int] = Field(
        default_factory=dict,
        description="Versión -> nº de tickets abiertos similares. Una sola versión apunta a un fallo de release",
    )
    tickets: list[TicketResumen]


class Comentario(BaseModel):
    autor: str
    texto: str
    creado_en: str
    estado_anterior: str | None = None
    estado_nuevo: str | None = None


class TicketDetalle(TicketResumen):
    descripcion: str
    impacto: str
    urgencia: str
    actualizado_en: str
    sla_respuesta_limite: str
    sla_resolucion_limite: str
    sla_resolucion_incumplido: bool
    ticket_padre: str | None = None
    comentarios: list[Comentario] = []


class ResultadoCreacion(BaseModel):
    simulacion: bool = Field(description="True si es una propuesta (proponer_ticket): no se ha escrito nada")
    duplicado: bool = Field(description="True si ya existía un ticket idéntico reciente")
    ticket_id: str | None
    prioridad: str
    reglas_aplicadas: list[str]
    grupo_asignado: str
    sla_respuesta_limite: str
    sla_resolucion_limite: str
    datos_redactados: list[str] = Field(
        description="Tipos de secretos/datos de tarjeta eliminados del texto antes de guardar"
    )
    kiosko_id: str | None = None
    local_id: str | None = None
    ticket_padre: str | None = None
    mensaje: str


class ResultadoActualizacion(BaseModel):
    ticket_id: str
    estado_anterior: str
    estado_nuevo: str
    grupo_asignado: str
    datos_redactados: list[str]
    mensaje: str
