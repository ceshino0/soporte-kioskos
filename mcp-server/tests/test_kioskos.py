from datetime import datetime, timedelta, timezone

import pytest

from kioskos_mcp.config import Config
from kioskos_mcp.redaction import redactar
from kioskos_mcp.rules import calcular_prioridad, en_horario, grupo_resolutor
from kioskos_mcp.service import ErrorValidacion, KioskosService

# Reloj fijo: miércoles 13:30 hora de Madrid (en plena hora de comidas)
HORA_COMIDAS = datetime(2026, 9, 30, 11, 30, tzinfo=timezone.utc)


def cfg(tmp_path, **kw):
    base = dict(data_dir=tmp_path, dominios_internos=("empresa.example",), solo_lectura=False,
                actor="test", zona_horaria="Europe/Madrid")
    return Config(**{**base, **kw})


@pytest.fixture
def svc(tmp_path):
    return KioskosService(cfg(tmp_path), ahora=lambda: HORA_COMIDAS)


# ---------------------------------------------------------------- reglas puras
def test_matriz_y_reglas_de_negocio():
    assert calcular_prioridad("alto", "alta", "hardware_kiosko", "silver")[0] == "P1"
    assert calcular_prioridad("bajo", "baja", "pago_tpv", "bronze")[0] == "P2"      # suelo pagos
    assert calcular_prioridad("bajo", "baja", "seguridad", None)[0] == "P2"         # suelo seguridad
    assert calcular_prioridad("medio", "media", "impresion_ticket", "gold")[0] == "P2"  # gold sube
    assert calcular_prioridad("medio", "media", "impresion_ticket", "bronze")[0] == "P3"


def test_grupo_proyectos_si_en_despliegue():
    assert grupo_resolutor("conectividad", "en_despliegue", "en_despliegue")[0] == "Proyectos y Despliegues"
    assert grupo_resolutor("pago_tpv", "operativo", "operativo")[0] == "Pagos y TPV"


def test_horario():
    hora = datetime(2026, 9, 30, 13, 30)
    assert en_horario("11:00-16:30,19:00-23:59", hora)
    assert not en_horario("11:00-16:30,19:00-23:59", hora.replace(hour=17))


def test_redaccion_pci():
    texto, tipos = redactar("Tarjeta del cliente 4111 1111 1111 1111, CVV 123, pedido 4587")
    assert "4111" not in texto and "123" not in texto and "4587" in texto
    assert set(tipos) == {"tarjeta", "cvv"}


# -------------------------------------------------------------------- lectura
def test_buscar_por_contacto_devuelve_telemetria_y_contexto(svc):
    r = svc.buscar_kiosko("sevilla.nervion@wokandgo.example")
    assert r.contacto.startswith("Lucía Romero")
    k = r.kioskos[0]
    assert k.id == "KSK-0401" and k.online is False and k.minutos_sin_conexion >= 90
    assert k.kioskos_en_local == 1 and k.kioskos_online_en_local == 0
    assert k.en_horario_servicio is True and k.nivel_contrato == "silver"


def test_contacto_de_cliente_ve_todos_sus_locales(svc):
    r = svc.buscar_kiosko("operaciones@parrillaurbana.example")
    assert {k.local_id for k in r.kioskos} == {"LOC-001", "LOC-002", "LOC-003"}


def test_masiva_de_pagos_por_version(svc):
    r = svc.buscar_similares("error comunicacion TPV pago tarjeta", dias=7, limite=5, categoria="pago_tpv")
    assert r.posible_incidencia_masiva and r.ticket_padre_sugerido == "INC-000001"
    assert r.versiones_software_afectadas == {"4.2.1": 3}
    assert len(r.locales_afectados) == 2


# ------------------------------------------------------------------ escritura
def test_kiosko_unico_caido_en_hora_punta_es_p1(svc):
    r = svc.crear_ticket(
        titulo="Kiosko no enciende", descripcion="Pantalla negra desde la apertura, único kiosko",
        categoria="hardware_kiosko", impacto="alto", urgencia="alta",
        solicitante_email="sevilla.nervion@wokandgo.example", kiosko_id="KSK-0401", dry_run=True,
    )
    assert r.simulacion and r.prioridad == "P1" and r.grupo_asignado == "Soporte de campo (hardware)"
    assert r.local_id == "LOC-004"
    assert not svc.config.audit_path.exists()


def test_despliegue_va_a_proyectos(svc):
    r = svc.crear_ticket(
        titulo="Pinpad no enlaza en instalación", descripcion="El pinpad del kiosko 1 no empareja",
        categoria="pago_tpv", impacto="medio", urgencia="media",
        solicitante_email="apertura.malaga@cafemediterraneo.example", kiosko_id="KSK-0601",
    )
    assert r.grupo_asignado == "Proyectos y Despliegues" and r.prioridad == "P2"


def test_crear_real_redacta_tarjeta_y_deduplica(svc):
    kw = dict(
        titulo="Cobro sin pedido", descripcion="Cliente con tarjeta 4111 1111 1111 1111 cobrado sin ticket",
        categoria="pago_tpv", impacto="medio", urgencia="alta",
        solicitante_email="encargada.ruzafa@parrillaurbana.example", kiosko_id="KSK-0202",
        ticket_padre="INC-000001", dry_run=False,
    )
    r1 = svc.crear_ticket(**kw)
    assert r1.ticket_id == "INC-000008" and "tarjeta" in r1.datos_redactados
    assert "4111" not in svc.obtener_ticket(r1.ticket_id).descripcion
    r2 = svc.crear_ticket(**kw)
    assert r2.duplicado and r2.ticket_id == r1.ticket_id
    assert svc.config.audit_path.read_text(encoding="utf-8").count("crear_ticket") == 1


def test_solicitante_no_registrado(svc):
    with pytest.raises(ErrorValidacion, match="no es un contacto registrado"):
        svc.crear_ticket(titulo="Prueba externa", descripcion="Alguien desconocido reporta",
                         categoria="otro", impacto="bajo", urgencia="baja",
                         solicitante_email="alguien@gmail.com", kiosko_id="KSK-0401", dry_run=False)


def test_aislamiento_entre_clientes(svc):
    with pytest.raises(ErrorValidacion, match="pertenece a otro cliente"):
        svc.crear_ticket(titulo="Kiosko ajeno", descripcion="Contacto de Wok & Go sobre kiosko de Parrilla",
                         categoria="otro", impacto="bajo", urgencia="baja",
                         solicitante_email="diagonal@wokandgo.example", kiosko_id="KSK-0101")


def test_interno_puede_abrir_en_cualquier_cliente(svc):
    r = svc.crear_ticket(titulo="Revisión preventiva", descripcion="Técnico detecta ruido en impresora",
                         categoria="impresion_ticket", impacto="bajo", urgencia="baja",
                         solicitante_email="tecnico@empresa.example", kiosko_id="KSK-0101")
    assert r.prioridad == "P3"  # P4 por matriz, sube a P3 por contrato gold


def test_kiosko_y_local_incoherentes(svc):
    with pytest.raises(ErrorValidacion, match="pertenece a LOC-004"):
        svc.crear_ticket(titulo="Incoherente", descripcion="kiosko y local no cuadran",
                         categoria="otro", impacto="bajo", urgencia="baja",
                         solicitante_email="tecnico@empresa.example", kiosko_id="KSK-0401", local_id="LOC-001")


def test_transiciones_y_vinculo(svc):
    r = svc.actualizar_ticket(ticket_id="INC-000003", nuevo_estado="en_curso",
                              comentario="Mismo fallo de TPV v4.2.1", vincular_a="INC-000001")
    assert r.estado_nuevo == "en_curso"
    assert svc.obtener_ticket("INC-000003").ticket_padre == "INC-000001"
    with pytest.raises(ErrorValidacion, match="Transición no permitida"):
        svc.actualizar_ticket(ticket_id="INC-000006", nuevo_estado="en_curso", comentario="reabrir cerrado")


def test_solo_lectura(tmp_path):
    s = KioskosService(cfg(tmp_path, solo_lectura=True), ahora=lambda: HORA_COMIDAS)
    assert s.buscar_kiosko("Málaga").total == 2
    with pytest.raises(ErrorValidacion, match="solo lectura"):
        s.actualizar_ticket(ticket_id="INC-000001", nuevo_estado="en_curso", comentario="prueba ro")


def test_sla_incumplido(tmp_path):
    KioskosService(cfg(tmp_path), ahora=lambda: HORA_COMIDAS)
    futuro = KioskosService(cfg(tmp_path), ahora=lambda: HORA_COMIDAS + timedelta(days=10))
    assert futuro.obtener_ticket("INC-000002").sla_resolucion_incumplido is True


def test_masiva_no_mezcla_categorias(svc):
    # Consulta real que en la primera sesión con Claude mezcló pagos con cocina (KDS)
    r = svc.buscar_similares("error comunicación TPV cobro sin ticket pedido kiosko",
                             dias=7, limite=5, categoria="pago_tpv")
    assert r.ticket_padre_sugerido == "INC-000001"
    assert r.versiones_software_afectadas == {"4.2.1": 3}


def test_telemetria_demo_no_envejece(tmp_path):
    # Encontrado en la prueba real en Windows: a los 9 min todos los kioskos salían offline
    KioskosService(cfg(tmp_path), ahora=lambda: HORA_COMIDAS)
    horas_despues = KioskosService(cfg(tmp_path), ahora=lambda: HORA_COMIDAS + timedelta(hours=3))
    k = horas_despues.buscar_kiosko("KSK-0202").kioskos[0]
    assert k.online is True and k.kioskos_online_en_local == 2
