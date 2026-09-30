# Plantillas de respuesta al local

Reglas comunes:
- Tutea, frases cortas: el encargado lo lee en el móvil con el local lleno.
- **Primero** lo que puede hacer ya en el local (workaround); después el ticket y el plazo.
- Sin jerga interna (nada de "P1", "KDS", "N2"): di "pantalla de cocina", "el técnico".
- **Nunca** repitas un número de tarjeta, CVV o contraseña. Si te lo enviaron, recuérdalo.

Plazo en lenguaje natural: P1 "en las próximas horas, hoy mismo", P2 "a lo largo del día",
P3 "en 1 día", P4 "en los próximos días".

---

## A. Kiosko caído / no enciende

> Hola {nombre}:
>
> Mientras tanto, para no perder ventas:
> 1. Pon el cartel de "Kiosko fuera de servicio" y dirige los pedidos a caja.
> 2. Comprueba que la regleta del kiosko tiene luz y que el interruptor trasero está encendido.
>
> Hemos abierto la incidencia **{ticket_id}**; el técnico se pondrá en contacto contigo
> {plazo}. Si vuelve a encender, respóndenos para cerrarla.

## B. Error de pago / cobro sin pedido

> Hola {nombre}:
>
> Estamos trabajando en un problema de pagos con tarjeta que afecta a varios locales. Hemos
> vinculado tu aviso (**{ticket_id}**) a la incidencia general, así que no hace falta abrir
> otra.
>
> Mientras tanto:
> - Si el kiosko sigue fallando, indica a los clientes que paguen en caja.
> - Para el cliente al que se cobró sin pedido: anota **hora, importe y los 4 últimos dígitos**
>   de la tarjeta y entrégale su pedido; el equipo de Pagos gestionará la devolución si procede.
>
> {si_envio_tarjeta: "Hemos eliminado de tu mensaje el número de tarjeta: por seguridad, no nos
> envíes nunca el número completo, solo los 4 últimos dígitos."}

## C. No imprime el ticket del pedido

> Hola {nombre}:
>
> Prueba esto (2 minutos): abre la tapa de la impresora, comprueba que queda papel y que el
> rollo sale **por debajo** (cara térmica hacia fuera), y cierra hasta oír el clic.
> Si el pedido llega a cocina, puedes seguir usando el kiosko y dar el número al cliente de
> palabra. Incidencia **{ticket_id}**: el técnico te contactará {plazo}.

## D. Kiosko en instalación / apertura

> Hola {nombre}:
>
> Hemos registrado **{ticket_id}** y lo lleva directamente el equipo de proyecto de tu
> apertura, que ya conoce la fecha prevista ({apertura_prevista}). Te contactarán {plazo}
> para confirmar si afecta al calendario.

## E. Posible manipulación del pinpad (seguridad)

> Hola {nombre}:
>
> Gracias por avisar. Por favor, **ahora mismo**:
> 1. No uses ni toques el kiosko ni el datáfono; pon el cartel de fuera de servicio.
> 2. Si puedes hacerlo sin tocarlo, haz fotos del datáfono.
> 3. No retires tú nada de lo que haya pegado o conectado.
>
> Hemos abierto **{ticket_id}** con el equipo de Seguridad, que te llamará {plazo}.

## F. Ya existía un ticket

> Hola {nombre}:
>
> Tu aviso ya está registrado como **{ticket_id}** (estado: {estado_humano}). He añadido tu
> nuevo comentario para que el técnico lo tenga en cuenta.
