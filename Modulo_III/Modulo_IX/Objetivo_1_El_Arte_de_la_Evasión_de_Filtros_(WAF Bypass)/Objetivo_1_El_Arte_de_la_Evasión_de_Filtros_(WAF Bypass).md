# Objetivo 1: El Arte de la Evasión de Filtros (WAF Bypass)

## 1. Introducción y Análisis del Filtro Naive

El uso de mecanismos de filtrado basados en listas negras o desinfección mediante reemplazo simple de texto (por ejemplo, buscar y eliminar la subcadena `<script>` y `</script>`) es un error común en la implementación de seguridad web.

Esta estrategia es ineficaz debido a dos razones técnicas principales:

1. **Incompletes del Modelo de Amenaza (Falso Supuesto):** Asume que la etiqueta `<script>` es el único vector de ejecución de JavaScript dentro del analizador HTML (*HTML Parser*) de un navegador.
2. **Defectos de Implementación Algorítmica (Eliminación No Recursiva):** Si el algoritmo de eliminación de subcadenas se ejecuta una sola vez de forma lineal sin recursividad, permite la reconstrucción de la etiqueta bloqueada mediante anidamiento.

## 2. Por Qué la Defensa es Inútil (Mecanismos Técnicos)

### A. Ejecución Basada en Manejadores de Eventos (Event Handlers)

El motor de renderizado del navegador (*DOM*) soporta una amplia variedad de atributos de eventos en elementos HTML estándar (tales como `onload`, `onerror`, `onmouseover`, `onclick`, `onfocus`, entre otros).

Cuando el navegador procesa un elemento HTML con un manejador de eventos, ejecuta automáticamente el código JavaScript especificado en el valor del atributo cuando se cumple la condición del evento, sin necesidad de que exista una etiqueta `<script>` explicita.

### B. Pseudoprotocolos en Atributos URI

Ciertos atributos que aceptan URLs (`href`, `src`, `action`, `data`) soportan el pseudoprotocolo `javascript:`. Al interactuar con el elemento o al cargarse en el contexto de navegación, el navegador interpreta el contenido que sigue al esquema `javascript:` como código ejecutable.

### C. Bypass por Anidamiento (Non-Recursive Sanitization)

Si la función del lado del servidor se limita a realizar un reemplazo simple como:

```text
Entrada -> Sanitizar con String.replace("<script>", "") -> Salida
```

Un atacante puede estructurar una cadena anidada:

```html
<scr<script>ipt>alert(1)</script>
```

Al procesar la entrada, el motor de reemplazo elimina la etiqueta `<script>` interna. Al concatenarse los fragmentos restantes (`<scr` + `ipt>`), la etiqueta `<script>` se reconstruye en el resultado final servido al navegador.

---

## 3. Vectores de Prueba de Concepto (PoC)

A continuación se presentan vectores de prueba de concepto legítimos utilizados en auditorías de seguridad que ejecutan código JavaScript sin emplear la etiqueta `<script>`:

### Vector 1: Manejador de Eventos en Elemento de Imagen (`<img>`)

```html
<img src="path_invalido.png" onerror="alert(1)">
```

* **Explicación Técnica:** El navegador intenta cargar la imagen desde la ruta indicada en el atributo `src`. Al ser una ruta inválida o inexistente, se dispara inmediatamente el evento de error `onerror`. El código asignado al atributo se ejecuta de forma sincrónica dentro del contexto de la sesión actual.

### Vector 2: Elemento Gráfico Vectorial (`<svg>`) con Evento de Carga

```html
<svg onload="alert(1)">
```

* **Explicación Técnica:** Los elementos `<svg>` son procesados por el parser HTML/XML del navegador. A diferencia de otros elementos que requieren interacción del usuario o fallos de carga, la etiqueta `<svg>` ejecuta el manejador `onload` tan pronto como el elemento es parseado e incorporado al DOM.

### Vector 3: Manipulación de Enlaces mediante Pseudoprotocolos (`<a>`)

```html
<a href="javascript:alert(1)">Haga clic aquí</a>
```

* **Explicación Técnica:** Se utiliza el pseudoprotocolo `javascript:` dentro del atributo `href`. Al hacer clic en el enlace, el navegador ejecuta el script especificado en lugar de realizar una redirección HTTP.

---

## 4. Estrategia de Remediación Definitiva

Para prevenir vulnerabilidades de Cross-Site Scripting (XSS) de forma robusta, se deben implementar las siguientes prácticas de arquitectura segura:

### A. Codificación de Salida Contextual (Context-Aware Output Encoding)

En lugar de intentar filtrar la entrada, el servidor debe codificar los datos devueltos al cliente según el contexto HTML en el que se rendericen (Cuerpo HTML, Atributos HTML, JavaScript, CSS, URL):

* **Contexto Cuerpo HTML:** Convertir caracteres especiales a sus correspondientes entidades HTML:
  * `<` $\rightarrow$ `&lt;`
  * `>` $\rightarrow$ `&gt;`
  * `&` $\rightarrow$ `&amp;`
  * `"` $\rightarrow$ `&quot;`
  * `'` $\rightarrow$ `&#x27;`

### B. Sanitización Estricta mediante Librerías Consolidadas

Si la aplicación requiere permitir marcado HTML enriquecido (por ejemplo, en editores de texto enriquecido), **nunca** se deben escribir filtros personalizados mediante expresiones regulares. Se deben utilizar librerías de sanitización basadas en arboles de parseo (como **DOMPurify** en el cliente/Node.js o **Bleach**):

```javascript
// Ejemplo con DOMPurify (Cliente o Node.js)
const cleanHTML = DOMPurify.sanitize(dirtyInput);
```

### C. Implementación de Content Security Policy (CSP)

Implementar una cabecera de respuesta HTTP `Content-Security-Policy` estricta para restringir los orígenes de ejecución de scripts y deshabilitar scripts en línea (*inline scripts*):

```http
Content-Security-Policy: default-src 'self'; script-src 'self' https://scripts-confiables.com;
```

---

## 5. Matriz Comparativa de Enfoques Defensivos

| Enfoque Defensivo | Eficacia | Riesgo de Bypass | Recomendación |
| :--- | :--- | :--- | :--- |
| **Lista Negra (`replace('<script>')`)** | Nula | Extremadamente Alto | **Inaceptable** |
| **Filtros por Regex Personalizados** | Muy Baja | Alto | **No Recomendado** |
| **Codificación Contextual (HTML Entities)** | Muy Alta | Muy Bajo | **Obligatorio para Texto** |
| **Sanitización con Librerías (DOMPurify)** | Muy Alta | Bajo | **Obligatorio para HTML Enriquecido** |
| **Content Security Policy (CSP)** | Alta (Defensa en Profundidad) | Bajo | **Altamente Recomendado** |

