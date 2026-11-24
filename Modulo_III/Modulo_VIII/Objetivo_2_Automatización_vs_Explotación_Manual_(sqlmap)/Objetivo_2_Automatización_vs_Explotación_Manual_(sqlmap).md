
Objetivo 2: Automatización vs Explotación Manual (sqlmap)
sqlmap es la herramienta de explotación de inyecciones SQL más potente del mercado, pero depender exclusivamente de ella es un error de novatos. Enumera y explica al menos dos escenarios técnicos del mundo real donde sqlmap fallaría estrepitosamente, pero un atacante manual (o un pentester experimentado manipulando la petición en Burp Suite) sí lograría explotar la vulnerabilidad. Formato de entrega: Enlace al archivo .md.

# Objetivo 2: Automatización vs Explotación Manual (sqlmap)

## 1. Introducción

`sqlmap` es la herramienta de código abierto de referencia para la automatización de la detección y explotación de inyecciones SQL. Su motor es capaz de identificar dialectos SQL, fingerprinting de base de datos y ejecución de cargas útiles dinámicas mediante diversas técnicas (In-band, Error-based, Blind, Time-based, Out-of-band).

Sin embargo, `sqlmap` opera bajo heurísticas presuntivas y patrones de tráfico automatizados. En entornos reales con arquitecturas modernas, mecanismos defensivos avanzados o lógica de negocio compleja, la herramienta suele fallar en identificar o explotar la vulnerabilidad. En estos escenarios, la intervención manual por parte de un auditor mediante proxies como **Burp Suite** o scripts ad-hoc marca la diferencia entre un falso negativo y una explotación exitosa.

---

## 2. Escenario 1: Inyección SQL de Segunda Orden (*Second-Order SQLi*) con Flujos Multietapa

### Descripción Técnica del Escenario

En una **Inyección de Segunda Orden**, el vector malicioso inyectado en el primer paso no se ejecuta de forma inmediata en la consulta inicial. En su lugar, el servidor almacena de forma segura (o sin procesar) la entrada en la base de datos o en una sesión. Posteriormente, en una segunda acción desacoplada (por ejemplo, la generación de un reporte administrativo, la actualización del perfil o el procesamiento de un trabajo en segundo plano), la aplicación lee el dato almacenado y lo concatena dentro de una nueva consulta SQL vulnerable.

```
┌─────────────────┐       1. POST /api/register (Input Malicioso)     ┌────────────────┐
│                 │ ────────────────────────────────────────────────> │                │
│                 │                                                   │   Servidor     │
│                 │ <──────────────────────────────────────────────── │   Backend      │
│  Atacante /     │       2. HTTP 201 Created (Almacenado en DB)      └───────┬────────┘
│  Burp Suite     │                                                           │
│                 │       3. GET /api/admin/reports/user-summary              │ 4. Exec Query
│                 │ ────────────────────────────────────────────────> ┌───────▼────────┐
│                 │                                                   │ Base de Datos  │
│                 │ <──────────────────────────────────────────────── │ (SQLi Dispara) │
└─────────────────┘       5. HTTP 200 OK (Respuesta Afectada)         └────────────────┘
```

### Por Qué `sqlmap` Falla

1. **Desconexión entre Inyección y Ejecución:** `sqlmap` asume de forma predeterminada una relación unívoca de causa-efecto: envía una carga útil en una petición y busca el impacto (error, diferencia de longitud o retardo) en la respuesta a esa *misma* petición.
2. **Pérdida de Contexto de Estado:** Aunque `sqlmap` cuenta con opciones como `--second-url` o `--second-req`, estas son rígidas. Si la consulta vulnerable requiere una secuencia compleja (por ejemplo, crear un usuario con un correo único en cada intento, esperar un job asíncrono o ejecutar 3 peticiones intermedias de token de estado), la automatización de `sqlmap` se interrumpe y falla estrepitosamente.

### Explotación Manual (Burp Suite)

Un auditor manual resuelve este escenario de la siguiente forma:

1. **Mapeo de la Secuencia:** Identifica con Burp Suite que la cadena enviada en `POST /api/user/profile` con el campo `display_name` infectado resuena únicamente cuando se invoca `POST /api/admin/generate-pdf`.
2. **Automatización Personalizada:** En lugar de depender de la heurística genérica de `sqlmap`, el auditor escribe un script en Python (o utiliza extensiones de Burp Suite como *Match and Replace* / *Macro*) que en cada iteración:
   * Genera un identificador único en el paso 1.
   * Ejecuta el paso 2 que invoca la consulta vulnerable.
   * Extrae la respuesta de forma inferencial por tiempo o contenido.

---

## 2. Escenario 2: Firma Dinámica de Peticiones, Tokens Anti-Replay y HMAC

### Descripción Técnica del Escenario

Las aplicaciones financieras y de alta seguridad suelen implementar controles de integridad a nivel de aplicación para prevenir la manipulación de peticiones en tránsito. Un esquema común consiste en incluir en cada petición HTTP cabeceras con:

* Un timestamp actual ($t$).
* Un número aleatorio único (*Nonce* $n$).
* Un código de autenticación de mensajes basado en hash (**HMAC**), calculado como $HMAC = \text{Hash}(K, \text{URL} + t + n + \text{Body})$.

```http
POST /api/v2/transfer HTTP/1.1
Host: api.banco.local
X-Signature: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
X-Timestamp: 1774348800
X-Nonce: 9a8b7c6d
Content-Type: application/json

{"account": "12345' AND 1=1--", "amount": 100}
```

### Por Qué `sqlmap` Falla

1. **Rechazo en el Middleware (Gateway/WAF):** Cada vez que `sqlmap` modifica el parámetro `"account"` para probar un payload SQLi, el `X-Signature` transmitido en la cabecera original queda obsoleto o resulta inválido.
2. **Falla Pre-Inyección:** El servidor web o el API Gateway verifica el HMAC antes de entregar la petición a la capa de aplicación o base de datos. Como la firma no coincide, el servidor devuelve un error `401 Unauthorized` o `403 Forbidden` de inmediato. `sqlmap` concluirá erróneamente que el parámetro no es vulnerable.
3. **Incompatibilidad con Tamper Scripts Simples:** Aunque `sqlmap` permite el uso de `--tamper`, implementar lógica criptográfica dinámica compleja que requiera calcular claves derivadas de la sesión activa en tiempo real suele ser poco práctico o inviable únicamente mediante las estructuras simples de `tamper`.

### Explotación Manual (Burp Suite)

Un pentester experimentado supera esta barrera utilizando el entorno extensible de Burp Suite:

1. **Reverse Engineering del Cliente:** Analiza el código JavaScript o el binario cliente para obtener la fórmula y la clave secreta utilizada para la firma HMAC.
2. **Intercepción con Extender (Burp Scripting / Custom Extension):** Desarrolla una extensión ligera en Python (Jython) o Java dentro de Burp Suite (o utiliza herramientas como *mitmproxy*).
3. **Re-calculado Transparente en Tiempo Real:** 
   * Configura `sqlmap` para canalizar todas sus peticiones a través del proxy local de Burp Suite (`--proxy=http://127.0.0.1:8080`).
   * Cada vez que `sqlmap` envía un payload de prueba, la extensión de Burp intercepta la petición saliente, extrae el nuevo cuerpo con el payload SQLi, recalcula el `X-Signature` válido en tiempo real con el timestamp actual y reenvía la petición al servidor.
   * El servidor valida el HMAC correctamente, permite que la petición alcance la base de datos vulnerable y la inyección es explotada exitosamente.

---

## 4. Escenario 3 (Bonus): Sanitización con Filtros Basados en Contexto y Evasión Personalizada (*Custom WAF / Nested JSON*)

### Descripción Técnica del Escenario

Determinadas aplicaciones procesan entradas JSON altamente anidadas o utilizan serialización propietaria (como Protobuf o GraphQL). Además, pueden contar con un filtro básico que bloquea palabras clave SQL estándar como `SELECT`, `UNION`, `SLEEP` o espacios en blanco.

```json
{
  "filter": {
    "query": {
      "conditions": [
        "user_id = 1001 /*custom_comment*/ UNION/**/SELECT/**/null,group_concat(table_name)/**/FROM/**/information_schema.tables"
      ]
    }
  }
}
```

### Por Qué `sqlmap` Falla

1. **Interpretación Estructural Errónea:** `sqlmap` puede no identificar los puntos de inyección si la estructura del cuerpo es un JSON complejo anidado con arreglos mixtos, a menos que se marque explícitamente cada punto con un asterisco (`*`).
2. **Falsos Positivos de Cierre de Pruebas:** Ante respuestas inusuales del WAF (como un corte abrupto de conexión `TCP RST` en lugar de una respuesta HTTP `403`), `sqlmap` suele asumir que el destino no está disponible o que el parámetro no es inyectable, abortando la fase de detección.

### Explotación Manual (Burp Suite)

El auditor analiza manualmente el comportamiento del filtro enviando solicitudes a través de **Burp Repeater**:

1. **Aislación de la Regla del WAF:** Determina exactamente qué término dispara el bloqueo (por ejemplo, descubre que el WAF bloquea espacios y la palabra `UNION SELECT`, pero permite la concatenación con comentarios en línea `/**/` o el uso de sintaxis alternativa como `UNION DISTINCT`).
2. **Construcción Manual del Payload:** Diseña a mano un payload adaptado al motor SQL y al parser del backend que evade el filtro específico de la aplicación.
3. **Explotación Controlada:** Utiliza Burp Intruder o scripts de automatización a medida para volcar la información respetando las limitaciones exactas del entorno vulnerable.

---

## 5. Matriz Comparativa: `sqlmap` vs. Explotación Manual

| Criterio | `sqlmap` (Automatizado) | Explotación Manual (Burp Suite / Scripts) |
| :--- | :--- | :--- |
| **Velocidad de Volcado** | **Extremadamente Alta** (cuando el escenario es estándar). | **Lenta / Moderada** (requiere construcción manual). |
| **Flujos de Trabajo Multietapa** | **Baja** (dificultad para mantener estados dinámicos). | **Alta** (control total sobre la secuencia de peticiones). |
| **Cabeceras Criptográficas (HMAC/Nonce)** | **Muy Baja** (falla sin proxies o Tampers complejos). | **Alta** (vía extensiones de Burp / *Hooking*). |
| **Evasión de WAFs Propietarios** | **Media** (limitado a scripts tamper predefinidos). | **Alta** (diseño del payload adaptado al parser). |
| **Inyección de Segunda Orden Complex** | **Limitada** (requiere rutas estáticas y conocidas). | **Alta** (mapeo contextual del comportamiento del sistema). |

---

## 6. Conclusión

`sqlmap` es una herramienta excepcionalmente eficiente para escenarios estándar y pruebas de concepto rápidas. Sin embargo, confiar de manera ciega en la automatización genera un margen crítico de **falsos negativos** en auditorías de seguridad. 

La capacidad de un auditor para interpretar el contexto de negocio, evadir firmas criptográficas mediante la manipulación de tráfico en proxies como Burp Suite y reconstruir flujos multietapa demuestra por qué la experiencia técnica manual es irremplazable frente a la automatización.