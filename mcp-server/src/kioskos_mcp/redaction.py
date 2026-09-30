"""Redacción de secretos y datos sensibles antes de persistir texto libre.

En soporte de kioskos es habitual que un encargado pegue el número de tarjeta
de un cliente final "para localizar el cobro", o la contraseña del back-office.
Nada de eso debe acabar en la base de datos ni en el log de auditoría
(PCI-DSS prohíbe almacenar el PAN en claro y el CVV en ningún caso).
"""

from __future__ import annotations

import re

MARCA = "[REDACTADO]"

_PATRONES: list[tuple[str, re.Pattern[str]]] = [
    # "contraseña: xxx", "password=xxx", "pwd xxx", "clave: xxx"
    (
        "credencial",
        re.compile(
            r"(?i)\b(contrase(?:ñ|n)a|password|passwd|pwd|clave|pin)\b(\s*(?:es|is)?\s*[:=]?\s*)(\S+)"
        ),
    ),
    # Código de seguridad de tarjeta: "CVV 123", "cvc: 4567"
    (
        "cvv",
        re.compile(r"(?i)\b(cvv2?|cvc|c[oó]digo de seguridad)\b(\s*[:=]?\s*)(\d{3,4})\b"),
    ),
    # Claves de API típicas (sk-..., ghp_..., AKIA..., xoxb-...)
    (
        "api_key",
        re.compile(r"\b(sk-[A-Za-z0-9_\-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9\-]{10,})\b"),
    ),
    # Bearer tokens / JWT
    ("token", re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b")),
    # IBAN (ES y genérico)
    ("iban", re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,4})?\b")),
    # Números de tarjeta (13-19 dígitos, con o sin separadores)
    ("tarjeta", re.compile(r"\b(?:\d[ \-]?){12,18}\d\b")),
]


def redactar(texto: str) -> tuple[str, list[str]]:
    """Devuelve (texto_redactado, tipos_detectados)."""
    detectados: list[str] = []
    resultado = texto
    for tipo, patron in _PATRONES:
        if tipo in ("credencial", "cvv"):
            resultado, n = patron.subn(lambda m: f"{m.group(1)}{m.group(2)}{MARCA}", resultado)
        else:
            resultado, n = patron.subn(MARCA, resultado)
        if n:
            detectados.append(tipo)
    return resultado, detectados
