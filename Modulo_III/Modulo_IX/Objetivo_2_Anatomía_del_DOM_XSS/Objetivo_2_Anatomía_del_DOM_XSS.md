Objetivo 2: Anatomía del DOM XSS
A diferencia del XSS Almacenado y Reflejado, el DOM-Based XSS es indetectable para muchos sistemas de prevención de intrusos (IPS) y firewalls (WAF). Investiga y explica por qué ocurre esto (Pista: analiza cómo manejan los navegadores el fragmento # en una URL y qué sucede cuando el código JavaScript procesa entradas como location.hash de forma insegura Formato de entrega: Enlace al archivo .md.

# Objetivo 2: Anatomía del DOM XSS

## 1. Resumen del Escenario

A diferencia de las variantes tradicionales de Cross-Site Scripting (**XSS Reflejado** y **XSS Almacenado**), donde el vector malicioso viaja explícitamente en la petición HTTP hacia el servidor web y se incluye en la respuesta enviada por este, el **DOM-Based XSS** (XSS basado en el Modelo de Objetos del Documento) ocurre íntegramente en la capa del cliente (*Navegador Web*).

En esta vulnerabilidad, el código JavaScript legítimo de la aplicación lee datos desde una fuente del DOM controlada por el usuario (como la URL) y los transmite a un método ejecutable o receptor inseguro sin la debida sanitización.

Esta característica de ejecución *exclusivamente local* convierte a DOM XSS en uno de los puntos ciegos más críticos para los sistemas de prevención de intrusos (**IPS**) y los cortafuegos de aplicaciones web (**WAF**).

## 2. El Punto Ciego Arquitectónico: El Manejo del Fragmento (`#`) en el Protocolo HTTP

### A. Especificación RFC 3986 y el Comportamiento del Navegador

De acuerdo con el estándar de direccionamiento de internet (RFC 3986), un identificador de recurso uniforme (**URI**) puede incluir un componente opcional llamado **Fragmento**, delimitado por el carácter numeral (`#`):

$$
\text{URI} = \text{scheme} \text{://} \text{authority} \text{/} \text{path} \text{?} \text{query} \text{\#} \mathbf{fragment}
$$

El propósito técnico del fragmento `#` es hacer referencia a una sección secundaria o ancla dentro del documento (por ejemplo, `#contacto` o `#seccion2`).

Por especificación estricta del protocolo web, **el fragmento de la URL es procesado de manera local por el Agente de Usuario (Navegador) y JAMÁS es transmitido al servidor en la petición HTTP**.

### B. Invisibilidad ante WAF e IPS

Imaginemos que un atacante induce a una víctima a hacer clic en la siguiente URL maliciosa:

```text
https://banco.local/dashboard#<img src=x onerror=alert(document.cookie)>
```

1. **En el Navegador de la Víctima:** El cliente procesa la URL completa.
2. **En la Red (Tráfico TCP/HTTP):** El navegador extrae la parte previa al fragmento y realiza la solicitud HTTP saliente:

```http
GET /dashboard HTTP/1.1
Host: banco.local
User-Agent: Mozilla/5.0 ...
Accept: text/html
```

3. **En el WAF / IPS / Logs del Servidor:** El WAF únicamente analiza la cadena `GET /dashboard HTTP/1.1`. Dado que el paquete no contiene caracteres especiales (`<`, `>`, `onerror`, `alert`), el IPS/WAF clasifica la solicitud como $100\%$ legítima.
4. **En el Procesamiento Backend:** El servidor devuelve el HTML y los scripts estándar de la página sin haber visto jamás la carga útil.
5. **En el Frontend (Ejecución):** El JavaScript del cliente lee `location.hash` y renderiza el payload malicioso en el DOM, ejecutando el código del atacante.

## 3. Fuentes (Sources) y Sumideros (Sinks)

El flujo de un ataque DOM XSS requiere la interacción de dos componentes dentro del código JavaScript del cliente:

```
┌────────────────────────────────────────┐
│         FUENTE (SOURCE)                │ 
│  Entrada controlable por el usuario    │
│  Ejemplo: location.hash, window.name   │
└───────────────────┬────────────────────┘
                    │
                    ▼  (Flujo de datos sin sanitizar)
┌────────────────────────────────────────┐
│         SUMIDERO (SINK)                │ 
│  Función/Propiedad peligrosa del DOM   │
│  Ejemplo: innerHTML, eval(), write()   │
└────────────────────────────────────────┘
```

### A. Fuentes Comunes (*Sources*)

Una **Fuente** es cualquier propiedad del DOM o API de JavaScript que un atacante puede manipular directa o indirectamente. Entre las más habituales se encuentran:

* `location.hash` (El fragmento de la URL después del `#`).
* `location.search` (Los parámetros de la cadena de consulta después del `?`).
* `document.referrer` (La URL de la página previa que redirigió al usuario).
* `window.name` (El nombre de la ventana o pestaña actual del navegador).
* `postMessage()` (Mensajes recibidos mediante eventos de comunicación entre frames u orígenes).

### B. Sumideros Peligrosos (*Sinks*)

Un **Sumidero** es una función nativa de JavaScript o propiedad del DOM que, si recibe cadenas arbitrarias sin codificar, interpreta y ejecuta el contenido como código ejecutable HTML/JavaScript:

* **Sumideros de Inyección HTML:** `element.innerHTML`, `element.outerHTML`, `document.write()`, `document.writeln()`.
* **Sumideros de Ejecución de Código:** `eval()`, `setTimeout(string)`, `setInterval(string)`, `Function()`.
* **Sumideros de Navegación/URL:** `location.href`, `location.assign()`, `window.open()`.

## 4. Escenario Práctico de Explotación

### Código JavaScript Vulnerable en el Cliente (`app.js`)

Considere una página que muestra un saludo personalizado en función de la sección indicada en la URL:

```javascript
// CÓDIGO VULNERABLE (DOM-Based XSS)
window.addEventListener('DOMContentLoaded', () => {
    // 1. FUENTE: Extrae el fragmento de la URL omitiendo el '#'
    const section = window.location.hash.substring(1);

    if (section) {
        // 2. SUMIDERO: Asigna directamente la cadena al DOM mediante innerHTML
        document.getElementById('content-area').innerHTML = "<h2>Bienvenido a " + section + "</h2>";
    }
});
```

### Paso a Paso de la Explotación

1. El atacante construye la URL:
   `https://victima.local/app.html#<svg onload=alert(document.cookie)>`
2. La víctima abre el enlace. El navegador descarga `app.html` y `app.js`.
3. El script ejecuta `window.location.hash.substring(1)`, obteniendo la cadena:
   `<svg onload=alert(document.cookie)>`
4. El script ejecuta `document.getElementById('content-area').innerHTML = ...`.
5. Al asignar el fragmento HTML al atributo `innerHTML`, el parser del navegador instancia el elemento `<svg>`, evalúa el manejador de eventos `onload` y ejecuta `alert(document.cookie)` dentro de la sesión de la víctima.

## 5. Matriz Comparativa: Reflejado vs. Almacenado vs. DOM-Based

| Característica | XSS Reflejado | XSS Almacenado | DOM-Based XSS |
| :--- | :--- | :--- | :--- |
| **Lugar de Ejecución** | Navegador del Cliente | Navegador del Cliente | Navegador del Cliente |
| **Intervención del Servidor** | El payload viaja al servidor y es devuelto en la respuesta | El payload se guarda en la DB del servidor y se sirve a otros usuarios | El payload **nunca** llega al servidor |
| **Detectabilidad en WAF/IPS** | **Alta** (el payload está en la petición HTTP) | **Alta** (el payload está en la petición HTTP o DB) | **Nula o Muy Baja** (el payload viaja en el `#` o variables locales) |
| **Causa Raíz** | Falta de codificación al construir respuestas HTML en backend | Falta de sanitización/codificación al guardar o mostrar datos en backend | Uso inseguro de *Sources* y *Sinks* en scripts JavaScript |

## 6. Estrategia de Remediación Definitiva

Para remediar el DOM XSS, los desarrolladores deben aplicar controles seguros directamente en la lógica del cliente:

### A. Sustitución de Sumideros Peligrosos por APIs Seguras

En lugar de utilizar `innerHTML` para insertar texto, se deben emplear propiedades que traten la entrada estrictamente como datos literales:

```javascript
// REMEDIACIÓN SEGURA: Uso de textContent
const section = window.location.hash.substring(1);
if (section) {
    // textContent codifica automáticamente caracteres HTML
    document.getElementById('content-area').textContent = "Bienvenido a " + section;
}
```

### B. Sanitización en el Cliente con DOMPurify

Si la aplicación requiere insertar marcado HTML dinámico proveniente de una fuente no confiable, se debe purificar la entrada utilizando librerías validadas como **DOMPurify**:

```javascript
// REMEDIACIÓN SEGURA: Sanitización previa con DOMPurify
const section = window.location.hash.substring(1);
if (section) {
    const cleanHTML = DOMPurify.sanitize("<h2>Bienvenido a " + section + "</h2>");
    document.getElementById('content-area').innerHTML = cleanHTML;
}
```

### C. Implementación de Trusted Types

En navegadores modernos, se puede habilitar la política de **Trusted Types** mediante la cabecera `Content-Security-Policy`. Esto bloquea de forma nativa las asignaciones directas de cadenas de texto a sumideros peligrosos como `innerHTML` o `eval()`, exigiendo objetos tipados sanitizados previamente.

```http
Content-Security-Policy: require-trusted-types-for 'script';
```