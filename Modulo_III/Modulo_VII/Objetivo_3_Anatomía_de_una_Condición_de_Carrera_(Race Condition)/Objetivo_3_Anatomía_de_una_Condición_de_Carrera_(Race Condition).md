# Objetivo 3: Anatomía de una Condición de Carrera (Race Condition)

## 1. Concepto Fundamental: El Problema TOCTOU

Una **Condición de Carrera** (*Race Condition*) en aplicaciones web ocurre cuando el resultado de una operación depende del orden o del tiempo en que se ejecutan hilos o procesos concurrentes. 

En el ámbito de la seguridad y el desarrollo de software, esta vulnerabilidad suele responder al patrón **TOCTOU** (*Time-of-Check to Time-of-Use*), donde existe un desfase temporal entre dos acciones secuenciales del backend:

1. **Time-of-Check ($T_{check}$):** El servidor verifica si se cumplen las condiciones de negocio (por ejemplo, comprobar si un cupón de descuento de un solo uso sigue estando activo).
2. **Time-of-Use ($T_{use}$):** El servidor ejecuta la acción basada en el resultado de la comprobación previa (aplica el descuento y marca el cupón como "usado" en la base de datos).

```
    Flujo Vulnerable (Secuencial sin Bloqueo)
    
       Cliente                     Servidor / Backend                    Base de Datos
          |                               |                                    |
          |--- POST /canjear (Req 1) ---->|                                    |
          |                               |--- SELECT is_used FROM coupons --->|
          |                               |<-- false (No usado) ---------------|
          |--- POST /canjear (Req 2) ---->|                                    |
          |                               |--- SELECT is_used FROM coupons --->|
          |                               |<-- false (No usado) ---------------|
          |                               |                                    |
          |                               |--- Aplica Descuento (Req 1) ------>|
          |                               |--- Aplica Descuento (Req 2) ------>|
          |                               |                                    |
          |                               |--- UPDATE is_used=true (Req 1) --->|
          |                               |--- UPDATE is_used=true (Req 2) --->|
          v                               v                                    v
```

Si el servidor atiende múltiples solicitudes de manera asíncrona o multi-hilo, un atacante puede enviar peticiones concurrentes dentro de la ventana de tiempo $\Delta t = T_{use} - T_{check}$. Como la verificación ($T_{check}$) ocurre para todas las peticiones antes de que la primera actualice el estado ($T_{use}$), el backend invalida el cupón demasiado tarde, permitiendo canjearlo múltiples veces.

---

## 2. Ventana de Tiempo (*Race Window*) en Canje de Cupones

Consideremos una función tradicional de procesamiento en el servidor para canjear un código promocional de un solo uso:

1. La Petición 1 llega al servidor. Se consulta la base de datos: `is_used` es `FALSE`.
2. Microsegundos después (antes de completar el `UPDATE`), llega la Petición 2. Se consulta la base de datos: `is_used` sigue siendo `FALSE`.
3. El backend procesa la Petición 1, descontando el saldo del carrito y registrando el uso.
4. El backend procesa la Petición 2, descontando nuevamente el saldo del carrito porque la verificación previa arrojó `FALSE`.
5. Ambas peticiones finalizan con éxito, resultando en una multiplicación indebida del beneficio.

---

## 3. Explotación con Turbo Intruder (Burp Suite)

Para explotar con éxito una condición de carrera, las peticiones deben llegar al servidor backend de forma casi perfectamente simultánea (con una diferencia de microsegundos). Las herramientas de envío secuencial o con hilos convencionales a menudo introducen latencia de red (*jitter*) que invalida la ventana de tiempo.

### El Ataque de Paquete Único (*Single-Packet Attack*)

Herramientas avanzadas como la extensión **Turbo Intruder** de Burp Suite utilizan características del protocolo HTTP/2 (o sincronización de socket en HTTP/1.1 mediante *Last-Byte Synchronization*) para lograr una coincidencia temporal casi perfecta:

* En lugar de enviar 50 peticiones completas una por una, la herramienta prepara los 50 *sockets* TCP y transmite casi todo el cuerpo de las peticiones HTTP.
* Retiene únicamente el **último byte** de cada petición.
* Una vez que las 50 conexiones están listas en el búfer de red del servidor, transmite simultáneamente el último byte de las 50 peticiones en un solo paquete TCP (o en una ráfaga agrupada).
* El servidor backend recibe y comienza a procesar los 50 hilos en el mismo instante exacto.