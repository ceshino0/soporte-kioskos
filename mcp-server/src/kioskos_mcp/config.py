"""Configuración por variables de entorno. Sin secretos en el código."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(valor: str | None, defecto: bool) -> bool:
    if valor is None:
        return defecto
    return valor.strip().lower() in {"1", "true", "si", "sí", "yes", "on"}


@dataclass(frozen=True)
class Config:
    data_dir: Path
    dominios_internos: tuple[str, ...]
    solo_lectura: bool
    actor: str
    zona_horaria: str
    ventana_duplicados_min: int = 10
    max_resultados: int = 20
    minutos_online: int = 5

    @property
    def db_path(self) -> Path:
        return self.data_dir / "kioskos.db"

    @property
    def audit_path(self) -> Path:
        return self.data_dir / "audit.log"

    @classmethod
    def desde_entorno(cls) -> "Config":
        data_dir = Path(
            os.environ.get("KIOSKOS_DATA_DIR", str(Path.home() / ".kioskos-mcp"))
        ).expanduser()
        dominios = tuple(
            d.strip().lower()
            for d in os.environ.get("KIOSKOS_INTERNAL_DOMAINS", "empresa.example").split(",")
            if d.strip()
        )
        return cls(
            data_dir=data_dir,
            dominios_internos=dominios,
            solo_lectura=_bool(os.environ.get("KIOSKOS_READ_ONLY"), False),
            actor=os.environ.get("KIOSKOS_ACTOR", "claude-agent"),
            zona_horaria=os.environ.get("KIOSKOS_TZ", "Europe/Madrid"),
        )
