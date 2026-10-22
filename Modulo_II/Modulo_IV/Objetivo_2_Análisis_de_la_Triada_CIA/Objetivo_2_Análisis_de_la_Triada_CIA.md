Objetivo 2: Análisis de la Triada CIA
La seguridad de la información se sostiene sobre tres pilares fundamentales: Confidencialidad, Integridad y Disponibilidad (CIA). Explica con tus propias palabras cada uno de estos pilares. Luego, da un ejemplo concreto de una vulnerabilidad web (o un tipo de ataque) que comprometa principal y directamente a cada pilar por separado. Formato de entrega: Enlace al archivo .md.

# Objetivo 2: Análisis de la Triada CIA

# Informe Técnico: Análisis de la Triada CIA

## 1. Introducción
En el ámbito de la seguridad de la información, la **Tríada CIA** (Confidencialidad, Integridad y Disponibilidad) constituye el modelo normativo fundamental sobre el cual se diseñan, evalúan y auditan las políticas de seguridad y la arquitectura defensiva de cualquier sistema informático o aplicación web.

---

## 2. Los Pilares de la Tríada CIA

### Confidencialidad
Garantiza que la información y los datos sensibles sean accesibles **únicamente por las personas, entidades o procesos autorizados**, previniendo la divulgación no autorizada. Esto se logra mediante mecanismos como el control estricto de accesos, el cifrado de datos (en tránsito y en reposo) y la segmentación de privilegios.

### Integridad
Asegura que los datos y los sistemas de información se mantengan **exactos, completos y confiables**, protegiéndolos contra modificaciones, alteraciones, borrados o falsificaciones no autorizadas, ya sea de forma maliciosa o accidental.

### Disponibilidad
Garantiza que los recursos, servicios, aplicaciones y datos estén **operativos y accesibles para los usuarios legítimos** en el momento en que los necesiten, evitando interrupciones indebidas o bloqueos de servicio.

---

## 3. Vulnerabilidades y Ataques que Comprometen la Tríada CIA

Cada pilar puede verse afectado de manera directa por diferentes fallas o vectores de ataque comunes en entornos web:

### A. Compromiso de la Confidencialidad: Vulnerabilidad de Exposición de Datos (ej. Path Traversal / Broken Object Level Authorization - BOLA)
* **Descripción del impacto:** Ocurre cuando un atacante logra acceder a información confidencial (como credenciales, datos de tarjetas de crédito o registros de otros usuarios) que debería estar protegida.
* **Ejemplo práctico:** Una vulnerabilidad de *Path Traversal* mal gestionada en el servidor que permite a un usuario no autorizado leer archivos del sistema (como `/etc/passwd` o archivos de configuración con claves de base de datos) mediante la manipulación de rutas en la URL (`../../`), o bien un fallo de control de acceso donde un usuario puede consultar los datos de perfil de cualquier otro cliente simplemente cambiando un ID en la API.

### B. Compromiso de la Integridad: Vulnerabilidad de Modificación No Autorizada (ej. Inyección SQL / SQLi)
* **Descripción del impacto:** Se vulnera cuando un agente externo logra alterar el contenido, los estados de los datos o la lógica de negocio de la aplicación sin autorización.
* **Ejemplo práctico:** Una vulnerabilidad de **Inyección SQL (SQLi)** en un formulario de pago o perfil de usuario. Si las entradas no se sanitizan ni parametrizan correctamente, un atacante puede inyectar sentencias maliciosas para modificar directamente los registros de la base de datos (por ejemplo, alterando el saldo de una cuenta, cambiando el rol de un usuario de "cliente" a "administrador", o modificando los precios de los productos en una tienda online).

### C. Compromiso de la Disponibilidad: Ataque de Denegación de Servicio (ej. Ataque DoS por Agotamiento de Recursos / Algorithmic Complexity)
* **Descripción del impacto:** Ocurre cuando el sistema se vuelve inaccesible para los usuarios legítimos, ya sea por saturación del ancho de banda, consumo masivo de memoria/CPU, o bloqueo intencional de hilos de ejecución.
* **Ejemplo práctico:** Un ataque de **Denegación de Servicio (DoS)** o un ataque automatizado de alto volumen (fuerza bruta masiva sin *Rate Limiting*) que inunda el servidor con miles de peticiones concurrentes `POST` al endpoint de autenticación. Esto agota las conexiones disponibles en el pool de la base de datos o satura los hilos del servidor web, provocando que la aplicación deje de responder a los usuarios legítimos (`HTTP 503 Service Unavailable`).