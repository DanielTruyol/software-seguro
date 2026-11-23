# Objetivo 4: Manejo Inseguro de Errores (Stack Traces)

## 1. Resumen Ejecutivo
Cuando una aplicación web o API sufre una excepción no controlada, la forma en que el servidor responde ante la falla define de forma crítica su postura de seguridad. 

El manejo inseguro de errores se clasifica habitualmente dentro de:
* **CWE-209:** *Generation of Error Message Containing Sensitive Information*.
* **OWASP Top 10:** *A05:2021 - Security Misconfiguration*.

Configurar entornos de producción para volcar detalles técnicos internos en lugar de respuestas sanitizadas transforma fallos operacionales ordinarios en canales directos de fuga de información (*information disclosure*).

---

## 2. Mensaje de Error Genérico vs. Stack Trace Expuesto

| Criterio | Mensaje de Error Genérico | Stack Trace Expuesto (Traza de Pila) |
| :--- | :--- | :--- |
| **Audiencia prevista** | Usuario final / Cliente externo | Desarrollador en entorno local o de pruebas |
| **Contenido típico** | Código de estado HTTP estándar (`500 Internal Server Error`), mensaje amigable ("Ha ocurrido un error inesperado") y un identificador de seguimiento único (*Correlation ID / Incident ID*). | Tipo exacto de excepción, mensaje de error detallado, cadena de llamadas a métodos/funciones, archivos de código fuente, números de línea y volcados de contexto. |
| **Impacto en seguridad** | **Nulo o mínimo:** No aporta datos internos ni detalles arquitectónicos al cliente. | **Severo:** Filtra componentes internos, rutas físicas, consultas SQL, versiones de dependencias y lógica de negocio. |
| **Depuración** | Requiere que el administrador busque el `Correlation ID` en registros internos protegidos (*logs* del servidor). | Permite al visitante deducir la causa raíz del fallo directamente en la respuesta HTTP. |

### Ejemplo: Mensaje Genérico Seguro
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "InternalServerError",
  "message": "No se pudo procesar la solicitud. Intente nuevamente más tarde.",
  "incident_id": "c9b2f1e4-7d5a-4b82-9e28-1b9a82e74c10"
}
```

### Ejemplo: Stack Trace Expuesto (Inseguro)
```http
HTTP/1.1 500 Internal Server Error
Content-Type: text/plain

org.postgresql.util.PSQLException: ERROR: syntax error at or near "'"
  Position: 68
  at org.postgresql.core.v3.QueryExecutorImpl.receiveErrorResponse(QueryExecutorImpl.java:2553)
  at org.postgresql.jdbc.PgStatement.executeInternal(PgStatement.java:484)
  at com.example.service.UserService.findUserByUsername(UserService.java:42)
  at com.example.controller.AuthController.login(AuthController.java:28)
  ... 28 more
```

---

## 3. Por qué el Stack Trace Facilita la Fase de Explotación

La traza de la pila acelera y simplifica drásticamente el proceso de ataque durante las etapas de **reconocimiento**, **análisis de vulnerabilidades** y **explotación activa**:

### A. Reconocimiento pasivo de tecnologías y versiones (*Fingerprinting*)
* **Identificación del stack exacto:** Nombres de paquetes como `org.springframework`, `express`, `django`, `laravel` o `sqlalchemy` revelan los frameworks subyacentes.
* **Versiones específicas de dependencias:** Los nombres de archivos (`postgresql-42.2.14.jar`, `lodash@4.17.15`) o llamadas a métodos obsoletos permiten buscar vulnerabilidades conocidas (CVEs) públicas sin necesidad de adivinarlas.

### B. Mapeo de rutas físicas del servidor
* Expone rutas absolutas del sistema operativo (`/var/www/app/src/controllers/`, `C:\inetpub\wwwroot\backend\`).
* Facilita ataques posteriores como **Path Traversal / Local File Inclusion (LFI)**, al conocer exactamente la profundidad del directorio y la ubicación de archivos sensibles (como `.env` o archivos de configuración).

### C. Confirmación instantánea de vulnerabilidades de inyección
* **SQL Injection / NoSQL Injection:** Si una comilla `'` genera una traza de base de datos (`SQLException`, `MongoDB driver error`), el atacante confirma al 100% que la entrada interactúa de forma insegura con la capa de persistencia, conociendo además el motor exacto (PostgreSQL, MariaDB, Oracle).
* **Deserialización insegura / RCE:** Muestra las clases que procesan la carga útil (por ejemplo, Jackson, Pickle o bibliotecas XML), guiando la creación de *gadgets* de explotación.

### D. Exposición de lógica interna y nombres de base de datos
* Revela nombres de tablas, columnas, esquemas de bases de datos, variables privadas, llamadas a microservicios internos y métodos protegidos.
* En casos críticos, mensajes de excepción incluyen cadenas de conexión incompletas, claves de API mal formateadas o datos de otros usuarios volcados en memoria.

---

## 4. Clasificación del Riesgo

| Atributo | Detalle |
| :--- | :--- |
| **CWE ID** | [CWE-209: Generation of Error Message Containing Sensitive Information](https://cwe.mitre.org/data/definitions/209.html) |
| **Categoría OWASP** | OWASP Top 10 - A05:2021 (Security Misconfiguration) |
| **Impacto Técnico** | Fuertes fugas de información (*Information Disclosure*), facilitación de *exploits* para RCE, SQLi, LFI. |
| **Severidad** | **Media a Alta** (dependiendo del tipo de datos expuestos). |

---

## 5. Mitigación y Buenas Prácticas

1. **Desactivar modos de depuración (*debug modes*) en producción:**
   * En frameworks y entornos como Express (`NODE_ENV=production`), Django (`DEBUG = False`), Flask (`FLASK_ENV=production`), PHP (`display_errors = Off`) o Spring Boot (`server.error.include-stacktrace = never`).
2. **Implementar manejadores globales de excepciones (*Global Exception Handlers*):**
   * Capturar excepciones no controladas antes de que alcancen el servidor web, registrándolas internamente y devolviendo respuestas estandarizadas al cliente.
3. **Mecanismo de correlación (*Correlation / Incident ID*):**
   * Asignar un UUID a cada error para permitir a los desarrolladores buscar la traza completa en sistemas de logging centralizados (ELK, Datadog, CloudWatch, Loki) sin revelar la traza al usuario.
4. **Defensa en profundidad en el servidor inverso / proxy:**
   * Configurar directivas como `error_page 500 502 503 504 /50x.html;` en Nginx o páginas de error personalizadas en Apache/Cloudflare para interceptar fallos que escapen al backend.