# Objetivo 3: XSS vs CSRF - Comparativa Técnica Directa

## 1. La Diferencia Fundamental: El Modelo de Confianza

A pesar de que tanto **Cross-Site Scripting (XSS)** como **Cross-Site Request Forgery (CSRF)** son vulnerabilidades centradas en el cliente que involucran el navegador de la víctima, sus mecánicas de ataque funcionan en direcciones opuestas debido a a quién engañan y de qué lado reside la falta de validación.

* **XSS explota la confianza que el usuario/navegador tiene en un sitio web particular.**  
  El navegador confía en que todo el código entregado por una aplicación legítima es seguro. El atacante logra inyectar código maligno (JavaScript) en la página, haciendo que el navegador ejecute instrucciones arbitrarias del atacante en el contexto del origen vulnerable.

* **CSRF explota la confianza que un sitio web tiene en el navegador del usuario.**  
  El servidor web confía en que cualquier solicitud recibida con las cookies de sesión válidas representa la voluntad explícita del usuario. El atacante induce al navegador a emitir una petición forzada hacia el servidor de destino, aprovechando que el navegador adjuntará implícitamente las credenciales del usuario.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MODELOS DE CONFIANZA                            │
├────────────────────────────────────────────────────────────────────────┤
│  XSS:  Usuario/Navegador  ──── Confía en ───►  Aplicación Web          │
│        (El atacante inyecta script en la aplicación que el navegador   │
│         ejecuta ciegamente).                                           │
│                                                                        │
│  CSRF: Aplicación Web     ──── Confía en ───►  Navegador del Usuario   │
│        (El atacante fuerza al navegador a enviar peticiones que el     │
│         servidor procesa ciegamente).                                  │
└────────────────────────────────────────────────────────────────────────┘

```

## 2. Comparativa Técnica Directa

### A. Mecánica de Ejecución

* **En XSS:** El atacante logra la **ejecución de código arbitrario** dentro de la pestaña del navegador de la víctima. El script del atacante tiene acceso completo a la API del DOM, al almacenamiento local (`localStorage`, `sessionStorage`), a las cookies no protegidas con `HttpOnly` y puede leer la respuesta de cualquier petición HTTP realizada dentro del mismo origen.

* **En CSRF:** El atacante logra la **emisión de una petición no autorizada** de cambio de estado. El atacante **no ejecuta JavaScript** en el contexto de la aplicación vulnerable ni puede leer el contenido de la respuesta (debido a la Política del Mismo Origen / SOP), pero logra que el servidor procese una orden maliciosa.

### B. Capacidad de Lectura vs. Capacidad de Escritura/Acción

* **XSS es un ataque de Lectura y Escritura (Read & Write):**  
  Al ejecutar script dentro de la aplicación, el atacante puede extraer información sensible de la pantalla (tokens, datos personales, cookies), modificar la apariencia visual del sitio (phishing in-situ) o enviar comandos a la API en segundo plano.

* **CSRF es un ataque estrictamente de "Solo Escritura" / Ejecución a Ciegas (Blind Write):**  
  El atacante solo puede forzar el envío de una petición que altera el estado (ej. cambiar clave, realizar transferencia). Debido a la *Same-Origin Policy* (SOP), el sitio atacante `https://atacante.local` no puede leer los datos devueltos en la respuesta enviada por `https://banco.local`.

## 3. Matriz Comparativa Detallada

| Criterio Técnico | Cross-Site Scripting (XSS) | Cross-Site Request Forgery (CSRF) |
| ----- | ----- | ----- |
| **Definición** | Inyección de script malicioso en una aplicación legítima. | Forzado de solicitudes HTTP no intencionadas mediante credenciales implícitas. |
| **Causa Raíz** | Falta de sanitización o codificación de salida (*Output Encoding*) en los datos renderizados. | Inclusión implícita/automática de credenciales (cookies) en peticiones de origen cruzado sin validación de origen o token. |
| **¿Inyecta Código JS?** | **Sí**, es la esencia del ataque. | **No**, se basa únicamente en la estructura de peticiones HTTP del navegador. |
| **¿Lee la Respuesta HTTP?** | **Sí**, el script inyectado puede leer el DOM y las respuestas del servidor. | **No**, la Política del Mismo Origen (SOP) bloquea la lectura trans-sitio de la respuesta. |
| **Alcance del Control** | Control total sobre la sesión del cliente en la aplicación vulnerada. | Limitado a ejecutar acciones predefinidas por el atacante (transacciones, cambios de estado). |
| **Requisito de Autenticación** | Puede afectar a usuarios autenticados o anónimos. | Requiere explícitamente que la víctima tenga una sesión activa (cookie) en el sitio objetivo. |
| **Mitigación Principal** | Codificación de Salida Contextual, Sanitización y Content Security Policy (CSP). | Tokens Anti-CSRF (Synchronizer Token Pattern), atributo `SameSite` en Cookies y verificación de cabeceras `Origin`/`Referer`. |

## 4. Análisis mediante un Escenario Común: "Cambiar Correo Electrónico"

Para visualizar la diferencia práctica, observemos cómo ambos vectores abordan el mismo objetivo: cambiar la dirección de correo electrónico de la víctima a `atacante@evil.com` en la plataforma `https://aplicacion.local`.

### Escenario A: Ataque vía CSRF

1. El atacante crea un formulario en su propio sitio `https://sitio-malicioso.com`:
   ```html
   <form id="f" action="https://aplicacion.local/user/email" method="POST">
       <input type="hidden" name="email" value="atacante@evil.com" />
   </form>
   <script>document.getElementById('f').submit();</script>
   ```
2. La víctima ingresa a `https://sitio-malicioso.com` manteniendo abierta su sesión en `https://aplicacion.local`.
3. El navegador envía la petición `POST` a `https://aplicacion.local/user/email` e incluye automáticamente la cookie de sesión `session_id`.
4. El servidor procesa el cambio de correo. **El atacante nunca vio el token de sesión ni ejecutó código en la plataforma de destino.**

### Escenario B: Ataque vía XSS

1. El atacante inyecta una cadena JavaScript vulnerable en la sección de comentarios de `https://aplicacion.local`:
   ```html
   <script>
       fetch('/user/email', {
           method: 'POST',
           body: JSON.stringify({ email: 'atacante@evil.com' }),
           headers: { 'Content-Type': 'json' }
       });
   </script>
   ```
2. La víctima navega dentro de `https://aplicacion.local` y abre la sección de comentarios.
3. El navegador de la víctima interpreta el comentario como código legítimo y ejecuta el `fetch`.
4. El script no solo cambia el correo, sino que también **puede extraer las cookies del usuario**, leer sus mensajes privados o redirigirlo a otra web.

## 5. La Intersección: Cómo XSS Anula las Protecciones Anti-CSRF

Existe una relación jerárquica de severidad entre ambas vulnerabilidades: **un hallazgo de XSS invalida por completo cualquier defensa Anti-CSRF existente en la aplicación.**

Si una aplicación implementa correctamente Tokens Anti-CSRF (tokens impredecibles insertados en cada formulario):

* Un ataque **CSRF tradicional fallará**, porque el servidor malicioso `https://sitio-malicioso.com` no puede adivinar ni leer el token Anti-CSRF generado en `https://aplicacion.local`.

* Sin embargo, si existe una vulnerabilidad **XSS**, el script inyectado dentro de `https://aplicacion.local` puede:
  1. Leer directamente el token Anti-CSRF desde el DOM (ej. `<input type="hidden" name="csrf_token" value="...">`).
  2. Construir la petición `POST` e incluir el token legítimo extraído.
  3. Enviar la transacción con éxito.

Por esta razón, en la jerarquía de remediación de seguridad, **mitigar XSS es un prerrequisito obligatorio antes de garantizar la efectividad de las defensas contra CSRF**.

## 6. Resumen de Estrategias de Mitigación

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ESTRATEGIA DE DEFENSA                           │
├────────────────────────────────────────────────────────────────────────┤
│  Para Detener XSS:                                                     │
│  - Codificar la salida según el contexto (HTML, Atributo, JS).         │
│  - Desinfectar marcado con librerías validadas (DOMPurify).            │
│  - Implementar CSP estricto (Nonce / strict-dynamic).                  │
│                                                                        │
│  Para Detener CSRF:                                                    │
│  - Implementar Tokens Anti-CSRF en peticiones de cambio de estado.     │
│  - Configurar Cookies de Sesión con SameSite=Lax / SameSite=Strict.    │
│  - Validar cabeceras HTTP Origin y Referer en el backend.              │
└────────────────────────────────────────────────────────────────────────┘
```