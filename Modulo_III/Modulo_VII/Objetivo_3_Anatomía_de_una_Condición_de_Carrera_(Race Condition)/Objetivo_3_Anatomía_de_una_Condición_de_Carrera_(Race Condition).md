Objetivo 3: Anatomía de una Condición de Carrera (Race Condition)
Las vulnerabilidades de tiempo de procesamiento (Race Conditions / TOCTOU) son críticas en sistemas financieros o de inventario. Investiga y explica con tus palabras cómo un atacante podría utilizar herramientas (como el Turbo Intruder de Burp Suite) para enviar 50 peticiones simultáneas y lograr canjear un código de descuento de un solo uso múltiples veces antes de que el servidor actualice la base de datos. Formato de entrega: Enlace al archivo .md.

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

### Ejemplo de Script de Turbo Intruder (Python)

El siguiente script en Turbo Intruder demuestra cómo se envían 50 peticiones agrupadas en un único pulso de sincronización:

```python
def queueRequests(target, wordlists):
    engine = RequestEngine(
        endpoint=target.endpoint,
        concurrentConnections=1,
        requestsPerConnection=100,
        pipeline=False
    )

    # Cadena HTTP de la petición de canje interceptada
    req = '''POST /api/v1/coupons/redeem HTTP/2
Host: ecommerce.local
Authorization: Bearer EYE...
Content-Type: application/json

{"coupon_code": "PROMO2026"}
'''

    # Encadenamos 50 peticiones en la cola de envío
    for i in range(50):
        engine.queue(req, gate='race_gate')

    # Liberamos el 'gate' para enviar los últimos bytes simultáneamente
    engine.openGate('race_gate')

def handleResponse(req, interesting):
    table.add(req)
```

Al revisar la tabla de resultados en Burp Suite, se observará que múltiples peticiones (por ejemplo, 12 de las 50) devuelven un código de respuesta HTTP `200 OK` con la confirmación del descuento aplicado, mientras que el resto devolverá `400 Bad Request` (cupón ya utilizado) una vez que el estado se consolidó en la base de datos.

---

## 4. Impacto en Sistemas Financieros y de Inventario

La explotación de condiciones de carrera genera consecuencias severas en la lógica del negocio:

* **Fraude Monetario:** Duplicación de saldo en billeteras virtuales (*re-spending*), canje múltiple de cupones, tarjetas de regalo o reembolsos simulados.
* **Agotamiento de Inventario (Over-booking):** Venta de más unidades de las existentes en stock durante eventos de alta demanda (como lanzamientos o *Flash Sales*).
* **Bypass de Votaciones o Encuestas:** Alteración de puntuaciones o límites de votación de usuario por sesión.

---

## 5. Remediación y Estrategias de Código Seguro

Para eliminar el riesgo de condiciones de carrera, la lógica de verificación y actualización debe ejecutarse de forma **atómica** o mediante **mecanismos de bloqueo** que impidan la lectura concurrente de datos no consolidados.

### A. Operaciones Atómicas a Nivel de Base de Datos

En lugar de realizar una consulta `SELECT` seguida de un `UPDATE` condicionado por código de aplicación, se debe realizar la verificación y la actualización en un único comando SQL atómico:

```sql
-- Operación Atómica
UPDATE coupons 
SET is_used = TRUE, used_by = :user_id, used_at = NOW() 
WHERE code = :coupon_code AND is_used = FALSE;
```

Si la base de datos devuelve que se modificó $1$ fila, la transacción fue exitosa. Si devuelve $0$ filas modificadas, significa que otra petición ya utilizó el cupón y la aplicación debe rechazar la solicitud.

### B. Bloqueo a Nivel de Fila (*Row-Level Locking*)

Dentro de una transacción explícita de base de datos, se puede utilizar la cláusula `FOR UPDATE` para bloquear la fila correspondiente hasta que la transacción se complete:

```sql
BEGIN TRANSACTION;

-- Bloquea la fila del cupón para otros hilos concurrentes hasta hacer COMMIT
SELECT is_used FROM coupons WHERE code = :coupon_code FOR UPDATE;

-- (Lógica de la aplicación: si is_used == false, proceder)

UPDATE coupons SET is_used = TRUE WHERE code = :coupon_code;

COMMIT;
```

### C. Bloqueos Distribuidos (*Distributed Locks*)

En arquitecturas de microservicios o aplicaciones distribuidas con múltiples instancias de backend y bases de datos NoSQL, se utilizan cerrojos distribuidos respaldados por motores como Redis (ej. mediante *Redlock* o comandos `SET key value NX PX`):

```javascript
// Ejemplo conceptual en Node.js / Redis
const lockAcquired = await redis.set(`lock:coupon:${couponCode}`, userId, 'NX', 'PX', 5000);

if (!lockAcquired) {
    return res.status(429).json({ error: "Transacción en proceso. Intente nuevamente." });
}

try {
    // Procesar el canje de forma segura
} finally {
    // Liberar el cerrojo
    await redis.del(`lock:coupon:${couponCode}`);
}
```

### D. Restricciones de Unicidad en la Base de Datos

Para evitar que un usuario registre el mismo cupón más de una vez, se puede definir un índice único compuesto en la tabla de canjes:

```sql
CREATE UNIQUE INDEX idx_unique_user_coupon ON coupon_redemptions (user_id, coupon_id);
```

Cualquier intento concurrente de insertar una fila duplicada fallará a nivel de motor de base de datos arrojando una violación de restricción de clave única (*Unique Constraint Violation*).

---

## 6. Resumen de Controles

| Control | Capa de Aplicación | Eficacia contra Race Conditions |
| --- | --- | --- |
| **Consultas Atómicas (`UPDATE ... WHERE is_used = false`)** | Base de Datos | **Alta (Solución Recomendada)** |
| **Bloqueos de Fila (`SELECT FOR UPDATE`)** | Base de Datos | **Alta** |
| **Bloqueo Distribuido (Redis Lock)** | Middleware / Backend | **Alta** |
| **Restricciones Únicas (`UNIQUE Index`)** | Base de Datos | **Alta** |
| **Rate Limiting Convencional (por IP/Minuto)** | API Gateway | **Baja** (no detiene la ráfaga simultánea en microsegundos) |