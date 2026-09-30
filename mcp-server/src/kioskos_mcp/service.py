"""Lógica del soporte de kioskos sobre SQLite.

Separada del servidor MCP para poder probarla con pytest sin levantar el
protocolo. El servidor (server.py) solo valida entradas y delega aquí.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from importlib import resources
from typing import Iterator
from zoneinfo import ZoneInfo

from . import rules
from .config import Config
from .models import (
    Comentario,
    Kiosko,
    ResultadoActualizacion,
    ResultadoBusquedaKiosko,
    ResultadoCreacion,
    ResultadoSimilares,
    TicketDetalle,
    TicketResumen,
)
from .redaction import redactar

ESTADOS_ABIERTOS = ("nuevo", "asignado", "en_curso", "pendiente_cliente")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})$")
TICKET_RE = re.compile(r"^INC-\d{6}$")

STOPWORDS = set(
    """a al algo ante con de del desde el ella en entre es esta este esto hay la las le
    lo los me mi mis muy no nos o para pero por que se sin su sus te tengo un una uno y ya
    cada otros otras puedo cuando como mas más también tambien hoy mañana manana kiosko
    kioskos kiosco local""".split()
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    id TEXT PRIMARY KEY, nombre TEXT NOT NULL, dominio TEXT NOT NULL,
    nivel_contrato TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS locales (
    id TEXT PRIMARY KEY, cliente_id TEXT NOT NULL REFERENCES clientes(id),
    nombre TEXT NOT NULL, ciudad TEXT NOT NULL, horario_servicio TEXT NOT NULL,
    estado TEXT NOT NULL, apertura_prevista TEXT
);
CREATE TABLE IF NOT EXISTS kioskos (
    id TEXT PRIMARY KEY, local_id TEXT NOT NULL REFERENCES locales(id),
    numero_serie TEXT NOT NULL UNIQUE, modelo TEXT NOT NULL, version_software TEXT NOT NULL,
    pinpad TEXT NOT NULL, impresora TEXT NOT NULL, estado TEXT NOT NULL,
    ultima_conexion TEXT,
    -- Solo demo: minutos sin conexión fijos (telemetría simulada que no envejece).
    -- En producción queda a NULL y se usa ultima_conexion, que envía el propio kiosko.
    demo_min_sin_conexion INTEGER
);
CREATE TABLE IF NOT EXISTS contactos (
    email TEXT PRIMARY KEY, nombre TEXT NOT NULL,
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    local_id TEXT REFERENCES locales(id), rol TEXT
);
CREATE TABLE IF NOT EXISTS tickets (
    num INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT UNIQUE, titulo TEXT NOT NULL, descripcion TEXT NOT NULL,
    categoria TEXT NOT NULL, impacto TEXT NOT NULL, urgencia TEXT NOT NULL,
    prioridad TEXT NOT NULL, estado TEXT NOT NULL, grupo_asignado TEXT NOT NULL,
    solicitante_email TEXT NOT NULL,
    kiosko_id TEXT REFERENCES kioskos(id), local_id TEXT REFERENCES locales(id),
    creado_en TEXT NOT NULL, actualizado_en TEXT NOT NULL,
    sla_respuesta_limite TEXT NOT NULL, sla_resolucion_limite TEXT NOT NULL,
    hash_dedup TEXT, ticket_padre TEXT
);
CREATE TABLE IF NOT EXISTS comentarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id TEXT NOT NULL REFERENCES tickets(id),
    autor TEXT NOT NULL, texto TEXT NOT NULL, creado_en TEXT NOT NULL,
    estado_anterior TEXT, estado_nuevo TEXT
);
CREATE INDEX IF NOT EXISTS idx_tickets_hash ON tickets(hash_dedup);
CREATE INDEX IF NOT EXISTS idx_tickets_estado ON tickets(estado);
"""

SQL_KIOSKO = """
SELECT k.*, l.nombre AS local_nombre, l.ciudad, l.estado AS estado_local,
       l.horario_servicio, l.apertura_prevista, l.cliente_id,
       c.nombre AS cliente, c.nivel_contrato,
       (SELECT COUNT(*) FROM tickets t WHERE t.kiosko_id = k.id
            AND t.estado IN ('nuevo','asignado','en_curso','pendiente_cliente')) AS abiertas
FROM kioskos k JOIN locales l ON l.id = k.local_id JOIN clientes c ON c.id = l.cliente_id
"""


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def _tokens(texto: str) -> set[str]:
    """Palabras significativas reducidas a su raíz aproximada (6 primeros caracteres),
    para que 'imprime', 'imprimir' e 'impresión' cuenten como el mismo término."""
    return {
        t[:6] for t in re.findall(r"[a-z0-9/]{3,}", _normalizar(texto)) if t not in STOPWORDS
    }


class ErrorValidacion(ValueError):
    """Error de negocio con mensaje pensado para que el modelo lo corrija."""


class KioskosService:
    def __init__(self, config: Config, ahora=None) -> None:
        self.config = config
        self._ahora = ahora or (lambda: datetime.now(timezone.utc))
        self.tz = ZoneInfo(config.zona_horaria)
        config.data_dir.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    # ------------------------------------------------------------------ infra
    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.config.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _iso(self, dt: datetime) -> str:
        return dt.astimezone(self.tz).isoformat(timespec="minutes")

    def _inicializar(self) -> None:
        with self._conn() as c:
            c.executescript(SCHEMA)
            if c.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0:
                self._sembrar(c)

    def _sembrar(self, c: sqlite3.Connection) -> None:
        seed = resources.files("kioskos_mcp") / "seed"
        parque = json.loads((seed / "parque.json").read_text(encoding="utf-8"))
        ahora = self._ahora()
        for x in parque["clientes"]:
            c.execute("INSERT INTO clientes VALUES (?,?,?,?)",
                      (x["id"], x["nombre"], x["dominio"], x["nivel_contrato"]))
        for x in parque["locales"]:
            apertura = (
                (ahora + timedelta(days=x["apertura_en_dias"])).astimezone(self.tz).date().isoformat()
                if x["apertura_en_dias"] is not None else None
            )
            c.execute("INSERT INTO locales VALUES (?,?,?,?,?,?,?)",
                      (x["id"], x["cliente_id"], x["nombre"], x["ciudad"],
                       x["horario_servicio"], x["estado"], apertura))
        for x in parque["kioskos"]:
            # Telemetría simulada: se guarda el desfase, no una fecha, para que la demo
            # muestre lo mismo tanto si se ejecuta hoy como dentro de un mes.
            c.execute("INSERT INTO kioskos VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (x["id"], x["local_id"], x["numero_serie"], x["modelo"],
                       x["version_software"], x["pinpad"], x["impresora"], x["estado"], None,
                       x["min_desde_ultima_conexion"]))
        for x in parque["contactos"]:
            c.execute("INSERT INTO contactos VALUES (?,?,?,?,?)",
                      (x["email"], x["nombre"], x["cliente_id"], x["local_id"], x["rol"]))

        for t in json.loads((seed / "tickets.json").read_text(encoding="utf-8")):
            creado = ahora - timedelta(hours=t["hace_horas"])
            k = self._fila_kiosko(c, t["kiosko_id"])
            prioridad, _ = rules.calcular_prioridad(
                t["impacto"], t["urgencia"], t["categoria"], k["nivel_contrato"]
            )
            grupo, _ = rules.grupo_resolutor(t["categoria"], k["estado"], k["estado_local"])
            datos = {**t, "local_id": k["local_id"]}
            self._insertar_ticket(c, datos, prioridad, grupo, creado, estado=t["estado"], hash_dedup=None)

    def _auditar(self, accion: str, detalle: dict) -> None:
        registro = {"ts": self._iso(self._ahora()), "actor": self.config.actor, "accion": accion, **detalle}
        with open(self.config.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

    def _exigir_escritura(self) -> None:
        if self.config.solo_lectura:
            raise ErrorValidacion(
                "El servidor está en modo solo lectura (KIOSKOS_READ_ONLY=true). "
                "No se pueden crear ni modificar tickets."
            )

    @staticmethod
    def _fila_kiosko(c: sqlite3.Connection, kiosko_id: str) -> sqlite3.Row | None:
        return c.execute(SQL_KIOSKO + " WHERE k.id = ?", (kiosko_id,)).fetchone()

    def _validar_solicitante(self, c, email: str, cliente_kiosko: str | None) -> tuple[str, str | None]:
        """Solo pueden abrir tickets el personal interno o contactos registrados del cliente.
        Un contacto de un cliente no puede abrir tickets sobre kioskos de otro cliente."""
        email = email.strip().lower()
        m = EMAIL_RE.match(email)
        if not m:
            raise ErrorValidacion(f"'{email}' no es un email válido.")
        if m.group(1) in self.config.dominios_internos:
            return email, None
        contacto = c.execute("SELECT * FROM contactos WHERE email = ?", (email,)).fetchone()
        if not contacto:
            raise ErrorValidacion(
                f"'{email}' no es un contacto registrado de ningún cliente ni un email interno. "
                "Pide al cliente que reporte desde un contacto autorizado o regístralo antes."
            )
        if cliente_kiosko and contacto["cliente_id"] != cliente_kiosko:
            raise ErrorValidacion(
                f"El contacto {email} pertenece a otro cliente ({contacto['cliente_id']}) y no puede "
                "abrir incidencias sobre este kiosko."
            )
        return email, contacto["local_id"]

    def _insertar_ticket(
        self, c, datos: dict, prioridad: str, grupo: str, creado: datetime, estado: str,
        hash_dedup, padre=None,
    ) -> str:
        resp, resol = rules.calcular_sla(prioridad, creado)
        cur = c.execute(
            """INSERT INTO tickets (titulo, descripcion, categoria, impacto, urgencia, prioridad,
               estado, grupo_asignado, solicitante_email, kiosko_id, local_id, creado_en,
               actualizado_en, sla_respuesta_limite, sla_resolucion_limite, hash_dedup, ticket_padre)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                datos["titulo"], datos["descripcion"], datos["categoria"], datos["impacto"],
                datos["urgencia"], prioridad, estado, grupo, datos["solicitante_email"],
                datos.get("kiosko_id"), datos.get("local_id"), self._iso(creado), self._iso(creado),
                self._iso(resp), self._iso(resol), hash_dedup, padre,
            ),
        )
        ticket_id = f"INC-{cur.lastrowid:06d}"
        c.execute("UPDATE tickets SET id = ? WHERE num = ?", (ticket_id, cur.lastrowid))
        return ticket_id

    @staticmethod
    def _resumen(row: sqlite3.Row, similitud: float | None = None) -> TicketResumen:
        return TicketResumen(
            id=row["id"], titulo=row["titulo"], categoria=row["categoria"],
            prioridad=row["prioridad"], estado=row["estado"],
            grupo_asignado=row["grupo_asignado"], solicitante_email=row["solicitante_email"],
            kiosko_id=row["kiosko_id"], local_id=row["local_id"], creado_en=row["creado_en"],
            similitud=similitud,
        )

    def _minutos_sin_conexion(self, fila) -> int | None:
        if fila["demo_min_sin_conexion"] is not None:      # telemetría simulada (demo)
            return fila["demo_min_sin_conexion"]
        if fila["ultima_conexion"]:                         # telemetría real
            return int((self._ahora() - datetime.fromisoformat(fila["ultima_conexion"])).total_seconds() // 60)
        return None                                         # nunca se ha conectado

    def _kiosko(self, c, f: sqlite3.Row) -> Kiosko:
        ahora = self._ahora()
        minutos = self._minutos_sin_conexion(f)
        online = minutos is not None and minutos <= self.config.minutos_online
        otros = c.execute("SELECT ultima_conexion, demo_min_sin_conexion FROM kioskos WHERE local_id = ?",
                          (f["local_id"],)).fetchall()
        online_local = sum(
            1 for o in otros
            if (m := self._minutos_sin_conexion(o)) is not None and m <= self.config.minutos_online
        )
        return Kiosko(
            id=f["id"], numero_serie=f["numero_serie"], modelo=f["modelo"],
            version_software=f["version_software"], pinpad=f["pinpad"], impresora=f["impresora"],
            estado=f["estado"], online=online, minutos_sin_conexion=minutos,
            incidencias_abiertas=f["abiertas"], local_id=f["local_id"], local_nombre=f["local_nombre"],
            ciudad=f["ciudad"], estado_local=f["estado_local"], horario_servicio=f["horario_servicio"],
            en_horario_servicio=rules.en_horario(f["horario_servicio"], ahora.astimezone(self.tz)),
            kioskos_en_local=len(otros), kioskos_online_en_local=online_local,
            cliente_id=f["cliente_id"], cliente=f["cliente"], nivel_contrato=f["nivel_contrato"],
            apertura_prevista=f["apertura_prevista"],
        )

    # ---------------------------------------------------------------- lectura
    def buscar_kiosko(self, consulta: str) -> ResultadoBusquedaKiosko:
        q = consulta.strip()
        with self._conn() as c:
            contacto = c.execute("SELECT * FROM contactos WHERE lower(email) = lower(?)", (q,)).fetchone()
            if contacto:
                # Contacto de local -> sus kioskos; contacto de cliente -> todos los del cliente
                if contacto["local_id"]:
                    filas = c.execute(SQL_KIOSKO + " WHERE k.local_id = ? ORDER BY k.id",
                                      (contacto["local_id"],)).fetchall()
                else:
                    filas = c.execute(SQL_KIOSKO + " WHERE l.cliente_id = ? ORDER BY k.id",
                                      (contacto["cliente_id"],)).fetchall()
                etiqueta = f"{contacto['nombre']} ({contacto['rol']})"
            else:
                like = f"%{q}%"
                filas = c.execute(
                    SQL_KIOSKO + """ WHERE lower(k.id) = lower(?) OR lower(k.numero_serie) = lower(?)
                       OR lower(l.id) = lower(?) OR lower(l.nombre) LIKE lower(?)
                       OR lower(l.ciudad) LIKE lower(?) OR lower(c.nombre) LIKE lower(?)
                       ORDER BY k.id LIMIT ?""",
                    (q, q, q, like, like, like, self.config.max_resultados),
                ).fetchall()
                etiqueta = None
            kioskos = [self._kiosko(c, f) for f in filas]
        return ResultadoBusquedaKiosko(consulta=q, total=len(kioskos), contacto=etiqueta, kioskos=kioskos)

    def buscar_similares(
        self, texto: str, dias: int, limite: int, categoria: str | None = None
    ) -> ResultadoSimilares:
        consulta = _tokens(texto)
        if not consulta:
            raise ErrorValidacion("El texto no contiene términos significativos para buscar.")
        ahora = self._ahora()
        desde = self._iso(ahora - timedelta(days=dias))
        hace_24h = ahora - timedelta(hours=24)
        with self._conn() as c:
            filas = c.execute(
                """SELECT t.*, k.version_software, l.nombre AS local_nombre FROM tickets t
                   LEFT JOIN kioskos k ON k.id = t.kiosko_id LEFT JOIN locales l ON l.id = t.local_id
                   WHERE t.creado_en >= ? ORDER BY t.creado_en DESC""", (desde,)
            ).fetchall()
        puntuados = []
        for f in filas:
            doc = _tokens(f"{f['titulo']} {f['descripcion']}")
            if not doc:
                continue
            sim = len(consulta & doc) / len(consulta)
            if categoria and f["categoria"] == categoria:
                sim += 0.25  # misma categoría: señal fuerte de que es el mismo problema
            sim = round(min(sim, 1.0), 2)
            if sim >= 0.15:
                puntuados.append((sim, f))
        puntuados.sort(key=lambda x: (-x[0], x[1]["creado_en"]))
        # Para la masiva solo cuentan tickets del mismo tipo de problema: con categoría, solo
        # los de esa categoría (evita que "pedido/ticket" mezcle pagos con cocina).
        abiertas_24h = [
            f for s, f in puntuados
            if s >= 0.25 and f["estado"] in ESTADOS_ABIERTOS
            and datetime.fromisoformat(f["creado_en"]) >= hace_24h
            and (categoria is None or f["categoria"] == categoria)
        ]
        masiva = len(abiertas_24h) >= 3
        padre = None
        if masiva:
            primero = min(abiertas_24h, key=lambda f: f["creado_en"])
            padre = primero["ticket_padre"] or primero["id"]
        return ResultadoSimilares(
            consulta=texto, ventana_dias=dias, total=len(puntuados[:limite]),
            abiertas_ultimas_24h=len(abiertas_24h), posible_incidencia_masiva=masiva,
            ticket_padre_sugerido=padre,
            locales_afectados=sorted({f["local_nombre"] for f in abiertas_24h if f["local_nombre"]}),
            versiones_software_afectadas=dict(Counter(f["version_software"] for f in abiertas_24h if f["version_software"])),
            tickets=[self._resumen(f, s) for s, f in puntuados[:limite]],
        )

    def obtener_ticket(self, ticket_id: str) -> TicketDetalle:
        ticket_id = ticket_id.strip().upper()
        if not TICKET_RE.match(ticket_id):
            raise ErrorValidacion("Formato de ticket inválido. Esperado: INC-000123.")
        with self._conn() as c:
            f = c.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
            if not f:
                raise ErrorValidacion(f"No existe el ticket {ticket_id}.")
            coms = c.execute("SELECT * FROM comentarios WHERE ticket_id = ? ORDER BY id", (ticket_id,)).fetchall()
        incumplido = (
            f["estado"] in ESTADOS_ABIERTOS
            and datetime.fromisoformat(f["sla_resolucion_limite"]) < self._ahora()
        )
        return TicketDetalle(
            **self._resumen(f).model_dump(), descripcion=f["descripcion"], impacto=f["impacto"],
            urgencia=f["urgencia"], actualizado_en=f["actualizado_en"],
            sla_respuesta_limite=f["sla_respuesta_limite"], sla_resolucion_limite=f["sla_resolucion_limite"],
            sla_resolucion_incumplido=incumplido, ticket_padre=f["ticket_padre"],
            comentarios=[
                Comentario(autor=x["autor"], texto=x["texto"], creado_en=x["creado_en"],
                           estado_anterior=x["estado_anterior"], estado_nuevo=x["estado_nuevo"])
                for x in coms
            ],
        )

    # --------------------------------------------------------------- escritura
    def crear_ticket(
        self, *, titulo: str, descripcion: str, categoria: str, impacto: str, urgencia: str,
        solicitante_email: str, kiosko_id: str | None = None, local_id: str | None = None,
        ticket_padre: str | None = None, dry_run: bool = True,
    ) -> ResultadoCreacion:
        if not dry_run:
            self._exigir_escritura()
        titulo_r, red1 = redactar(titulo.strip())
        desc_r, red2 = redactar(descripcion.strip())
        redactados = sorted(set(red1 + red2))

        with self._conn() as c:
            k = None
            if kiosko_id:
                kiosko_id = kiosko_id.strip().upper()
                k = self._fila_kiosko(c, kiosko_id)
                if not k:
                    raise ErrorValidacion(
                        f"El kiosko {kiosko_id} no existe. Usa buscar_kiosko primero o indica solo local_id."
                    )
                if local_id and local_id.strip().upper() != k["local_id"]:
                    raise ErrorValidacion(f"El kiosko {kiosko_id} pertenece a {k['local_id']}, no a {local_id}.")
                local_id = k["local_id"]
            elif local_id:
                local_id = local_id.strip().upper()
            loc = None
            if local_id:
                loc = c.execute(
                    """SELECT l.*, cl.nivel_contrato FROM locales l JOIN clientes cl ON cl.id = l.cliente_id
                       WHERE l.id = ?""", (local_id,)
                ).fetchone()
                if not loc:
                    raise ErrorValidacion(f"El local {local_id} no existe. Usa buscar_kiosko para localizarlo.")
            email, _ = self._validar_solicitante(c, solicitante_email, loc["cliente_id"] if loc else None)
            if ticket_padre:
                ticket_padre = ticket_padre.strip().upper()
                if not c.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_padre,)).fetchone():
                    raise ErrorValidacion(f"El ticket padre {ticket_padre} no existe.")

            prioridad, reglas_ap = rules.calcular_prioridad(
                impacto, urgencia, categoria, loc["nivel_contrato"] if loc else None
            )
            grupo, regla_grupo = rules.grupo_resolutor(
                categoria, k["estado"] if k else None, loc["estado"] if loc else None
            )
            if regla_grupo:
                reglas_ap.append(regla_grupo)
            ahora = self._ahora()
            resp, resol = rules.calcular_sla(prioridad, ahora)

            # Idempotencia: mismo solicitante + kiosko + contenido en la ventana -> no duplicar
            huella = hashlib.sha256(
                f"{email}|{kiosko_id}|{_normalizar(titulo_r)}|{_normalizar(desc_r)}".encode()
            ).hexdigest()
            limite = self._iso(ahora - timedelta(minutes=self.config.ventana_duplicados_min))
            previo = c.execute(
                "SELECT * FROM tickets WHERE hash_dedup = ? AND creado_en >= ?", (huella, limite)
            ).fetchone()
            if previo:
                return ResultadoCreacion(
                    simulacion=False, duplicado=True, ticket_id=previo["id"], prioridad=previo["prioridad"],
                    reglas_aplicadas=reglas_ap, grupo_asignado=previo["grupo_asignado"],
                    sla_respuesta_limite=previo["sla_respuesta_limite"],
                    sla_resolucion_limite=previo["sla_resolucion_limite"], datos_redactados=redactados,
                    kiosko_id=previo["kiosko_id"], local_id=previo["local_id"], ticket_padre=previo["ticket_padre"],
                    mensaje=f"Ya existía {previo['id']} con el mismo contenido; no se ha duplicado.",
                )

            comunes = dict(
                prioridad=prioridad, reglas_aplicadas=reglas_ap, grupo_asignado=grupo,
                sla_respuesta_limite=self._iso(resp), sla_resolucion_limite=self._iso(resol),
                datos_redactados=redactados, kiosko_id=kiosko_id, local_id=local_id, ticket_padre=ticket_padre,
            )
            if dry_run:
                return ResultadoCreacion(
                    simulacion=True, duplicado=False, ticket_id=None, **comunes,
                    mensaje="Simulación: nada guardado. Confirma con el usuario y llama a crear_ticket con los mismos datos.",
                )

            datos = dict(
                titulo=titulo_r, descripcion=desc_r, categoria=categoria, impacto=impacto,
                urgencia=urgencia, solicitante_email=email, kiosko_id=kiosko_id, local_id=local_id,
            )
            ticket_id = self._insertar_ticket(
                c, datos, prioridad, grupo, ahora, estado="nuevo", hash_dedup=huella, padre=ticket_padre
            )
            c.execute(
                "INSERT INTO comentarios (ticket_id, autor, texto, creado_en, estado_nuevo) VALUES (?,?,?,?,?)",
                (ticket_id, self.config.actor, "Ticket creado por triage asistido. " + "; ".join(reglas_ap),
                 self._iso(ahora), "nuevo"),
            )
        self._auditar("crear_ticket", {
            "ticket_id": ticket_id, "prioridad": prioridad, "categoria": categoria, "grupo": grupo,
            "solicitante": email, "kiosko_id": kiosko_id, "local_id": local_id,
            "ticket_padre": ticket_padre, "redactados": redactados,
        })
        return ResultadoCreacion(
            simulacion=False, duplicado=False, ticket_id=ticket_id, **comunes,
            mensaje=f"Ticket {ticket_id} creado y asignado a '{grupo}'.",
        )

    def actualizar_ticket(
        self, *, ticket_id: str, nuevo_estado: str, comentario: str, vincular_a: str | None = None,
    ) -> ResultadoActualizacion:
        self._exigir_escritura()
        actual = self.obtener_ticket(ticket_id)
        if actual.estado == nuevo_estado and not vincular_a:
            raise ErrorValidacion(f"{actual.id} ya está en estado '{nuevo_estado}'.")
        if actual.estado != nuevo_estado and not rules.transicion_valida(actual.estado, nuevo_estado):
            permitidas = sorted(rules.TRANSICIONES[actual.estado]) or ["ninguna (estado final)"]
            raise ErrorValidacion(
                f"Transición no permitida: {actual.estado} -> {nuevo_estado}. "
                f"Desde '{actual.estado}' se puede ir a: {', '.join(permitidas)}."
            )
        texto, redactados = redactar(comentario.strip())
        ahora = self._iso(self._ahora())
        with self._conn() as c:
            if vincular_a:
                vincular_a = vincular_a.strip().upper()
                if vincular_a == actual.id:
                    raise ErrorValidacion("Un ticket no puede vincularse a sí mismo.")
                if not c.execute("SELECT 1 FROM tickets WHERE id = ?", (vincular_a,)).fetchone():
                    raise ErrorValidacion(f"El ticket padre {vincular_a} no existe.")
                c.execute("UPDATE tickets SET ticket_padre = ? WHERE id = ?", (vincular_a, actual.id))
            c.execute("UPDATE tickets SET estado = ?, actualizado_en = ? WHERE id = ?",
                      (nuevo_estado, ahora, actual.id))
            c.execute(
                """INSERT INTO comentarios (ticket_id, autor, texto, creado_en, estado_anterior, estado_nuevo)
                   VALUES (?,?,?,?,?,?)""",
                (actual.id, self.config.actor, texto, ahora, actual.estado, nuevo_estado),
            )
        self._auditar("actualizar_ticket", {
            "ticket_id": actual.id, "de": actual.estado, "a": nuevo_estado,
            "vincular_a": vincular_a, "redactados": redactados,
        })
        return ResultadoActualizacion(
            ticket_id=actual.id, estado_anterior=actual.estado, estado_nuevo=nuevo_estado,
            grupo_asignado=actual.grupo_asignado, datos_redactados=redactados,
            mensaje=f"{actual.id}: {actual.estado} -> {nuevo_estado}"
            + (f", vinculado a {vincular_a}" if vincular_a else "") + ".",
        )
