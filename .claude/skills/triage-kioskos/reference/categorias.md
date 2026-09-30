# Categorías de incidencia de kiosko

`crear_ticket` solo admite estos 9 valores. El grupo resolutor lo asigna el servidor
(si el kiosko o el local está `en_despliegue`, siempre **Proyectos y Despliegues**).

| Categoría | Grupo | Señales en el mensaje | Diagnóstico rápido con el local |
|---|---|---|---|
| `pago_tpv` | Pagos y TPV | "no cobra", "rechaza la tarjeta", "Error de comunicación con TPV", "cobra pero no sale el pedido", "cobrado dos veces", contactless | ¿Falla con todas las tarjetas? ¿El pinpad tiene luz? ¿Hay cobro en el banco sin pedido? (hora, importe, 4 últimos dígitos) |
| `impresion_ticket` | Soporte de campo (hardware) | "no imprime el ticket del pedido", "sale en blanco", "atasca", "luz roja en la impresora" | ¿Hay papel? ¿Rollo térmico colocado del lado correcto? ¿Tapa cerrada? |
| `hardware_kiosko` | Soporte de campo (hardware) | "no enciende", "pantalla negra", "la táctil no responde", "pantalla rota", "hace ruido", "se reinicia solo" | ¿Hay luz en la regleta? ¿Otros equipos del mismo enchufe funcionan? |
| `software_kiosko` | Soporte N2 - Aplicación kiosko | "se queda colgado", "pantalla de error", "vuelve al inicio a mitad de pedido", "idioma no cambia", tras una actualización | ¿Aparece un código de error? ¿Desde la última actualización? |
| `integracion_pos_kds` | Integraciones POS / KDS | "el pedido no llega a cocina", "no aparece en caja", "número de pedido duplicado", "no descuenta stock" | ¿Se imprimió el ticket al cliente? ¿Los pedidos de caja sí llegan a cocina? |
| `conectividad` | Redes y conectividad | "sin conexión", "modo offline", "wifi", "no hay red en el local", "router" | ¿Tiene internet el resto del local (caja, wifi clientes)? |
| `contenido_menu` | Soporte N2 - Aplicación kiosko | "precio mal", "falta un producto", "sale un producto agotado", "alérgenos", "foto equivocada", "promoción no aplica" | ¿En caja el precio es correcto? ¿Desde cuándo? (posible carga de carta) |
| `seguridad` | Seguridad y cumplimiento PCI | pinpad con aspecto manipulado, dispositivo o cable extraño, carcasa forzada, alguien pidió el PIN, robo | **No tocar ni usar el kiosko.** Retirar de servicio, fotos si es seguro |
| `otro` | Service Desk N1 | nada de lo anterior | Úsala poco y explica por qué |

## Casos frontera

- **"Cobra pero no sale el ticket"**: si el pedido **sí** llega a cocina → `impresion_ticket`.
  Si **no** hay pedido (ni ticket ni cocina) y hay cargo → `pago_tpv` (hay dinero de por medio).
- **"No enciende"** con el kiosko `online` en telemetría → la CPU funciona: es la pantalla
  (`hardware_kiosko`) o la aplicación (`software_kiosko`), no la alimentación.
- **Kiosko offline pero con imagen en pantalla** → `conectividad`, sobre todo si otros kioskos
  del local también están offline.
- **Pedido no llega a cocina en todos los kioskos del local** → `integracion_pos_kds`; si es un
  solo kiosko y está offline → `conectividad`.
- **Cualquier indicio de manipulación gana**: si además de "no lee la tarjeta" el pinpad "tiene
  algo pegado", es `seguridad`.

## Lo que NO es una incidencia (no uses esta Skill)

| Petición | Qué es | Canal |
|---|---|---|
| Presupuesto o más kioskos para un local | Oportunidad comercial | Preventa |
| Planificar la instalación o apertura de un local | Proyecto | Jefe de proyecto / PMO |
| Cambio de carta o precios programado | Petición de cambio de contenido | Portal de contenidos del cliente |
| "¿Cómo se anula un pedido en el kiosko?" | Consulta / formación | Base de conocimiento para locales |
| Dudas de la factura del mantenimiento | Administración | Gestión de contratos |
