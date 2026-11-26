# Objetivo 1: Anatomía de un Ataque CSRF (Cross-Site Request Forgery)

## 1. Resumen y Concepto Fundamental

**Cross-Site Request Forgery (CSRF)**, o Falsificación de Peticiones en Sitios Cruzados, es una vulnerabilidad de seguridad web en la que un atacante engaña al navegador de una víctima autenticada para que ejecute acciones no intencionadas en una aplicación web en la que el usuario está actualmente autenticado.

En términos formales de la teoría de seguridad, CSRF es un problema de **autoridad ambiental** (*Confused Deputy Problem*): la aplicación receptora confía en la petición porque proviene del navegador de un usuario legítimo con credenciales válidas, sin percatarse de que la orden fue generada por un origen no autorizado.

## 2. Flujo Paso a Paso de un Ataque CSRF Exitoso

Para que un ataque CSRF ocurra, deben cumplirse tres condiciones previas:

1. **Una Acción Relevante:** Una operación de cambio de estado en la aplicación de destino (ej. cambiar correo electrónico, transferir fondos, cambiar contraseña).

2. **Manejo de Sesión Basado en Cookies:** La autenticación o sesión del usuario depende exclusivamente de cookies (o credenciales que el navegador adjunta de forma transparente).

3. **Ausencia de Parámetros Impredecibles:** La petición HTTP utiliza únicamente parámetros conocidos o predecibles por el atacante (sin tokens de validación adicionales).

```
   ┌─────────┐                ┌──────────────────┐                ┌───────────────────┐
   │ Atacante│                │ Navegador Víctima│                │ Servidor Web      │
   └────┬────┘                └────────┬─────────┘                │ (banco.local)     │
        │                              │                          └─────────┬─────────┘
        │                              │  1. Login legítimo                 │
        │                              ├───────────────────────────────────>│
        │                              │<───────────────────────────────────┤
        │                              │  Set-Cookie: session_id=XYZ123     │
        │                              │                                    │
        │  2. Engaña a la víctima      │                                    │
        │  para visitar sitio maligno  │                                    │
        │─────────────────────────────>│                                    │
        │                              │                                    │
        │                              │  3. Petición Cross-Site forzada    │
        │                              │     (POST /transfer)               │
        │                              │     Cookie: session_id=XYZ123      │
        │                              ├───────────────────────────────────>│
        │                              │                                    │
        │                              │  4. Operación procesada con éxito  │
        │                              │<───────────────────────────────────┤
```

### Detalle de las Etapas del Ataque

#### Paso 1: Autenticación de la Víctima
La víctima inicia sesión legítimamente en el sitio `https://banco.local`. El servidor responde con la cabecera `Set-Cookie: session_id=XYZ123`. El navegador almacena la cookie de sesión para el dominio `banco.local`.

#### Paso 2: Inducción a la Trampa
Mientras la sesión en `banco.local` permanece activa, la víctima navega e ingresa a un sitio malicioso o controlado por el atacante (`https://atacante.local`), atraída mediante ingeniería social (phishing, enlace acortado, anuncio malicioso).

#### Paso 3: Forzado de la Petición Cruzada (*Cross-Site Request*)
El sitio `https://atacante.local` contiene código HTML o JavaScript diseñado para disparar automáticamente una solicitud HTTP dirigida hacia `https://banco.local`. Por ejemplo, un formulario HTML oculto que se envía de forma automática:

```html
<!-- Formulario alojado en https://atacante.local -->
<form id="csrfForm" action="https://banco.local/api/v1/transfer" method="POST">
    <input type="hidden" name="account_to" value="cuenta_atacante_999" />
    <input type="hidden" name="amount" value="5000" />
</form>

<script>
    // Envío automático e imperceptible al cargar la página
    document.getElementById('csrfForm').submit();
</script>
```

#### Paso 4: Inclusión Automática de Credenciales
El navegador de la víctima recibe la orden de enviar una petición `POST` a `https://banco.local/api/v1/transfer`. Siguiendo el comportamiento histórico predeterminado del protocolo web, **el navegador adjunta automáticamente la cookie `session_id=XYZ123` pertenenciente a `banco.local`**, ya que el dominio de destino coincide con el ámbito de la cookie.

#### Paso 5: Procesamiento de la Transacción
El servidor de `banco.local` recibe la petición, valida la cookie `session_id=XYZ123`, confirma que pertenece a un usuario autenticado y ejecuta la transferencia de 5000 unidades a la cuenta del atacante. El servidor no tiene forma de saber si la petición se inició desde la interfaz propia del banco o desde `https://atacante.local`.

## 3. La Causa Raíz: Envío Automático de Cookies por el Navegador

El fallo fundamental que permite el ataque CSRF radica en la discrepancia entre el modelo de aislamiento de la **Política del Mismo Origen** (*Same-Origin Policy* o **SOP**) y la **inclusión implícita de credenciales de cookies en solicitudes de origen cruzado**.

* **Lo que la SOP Bloquea:** La SOP impide que un script en `https://atacante.local` lea el contenido de la respuesta devuelta por `https://banco.local`.

* **Lo que la SOP Permite:** La SOP **no impide** que `https://atacante.local` envíe solicitudes hacia `https://banco.local` (mediante etiquetas `<img>`, `<form>`, `<script>`, etc.).

Históricamente, los navegadores trataban cualquier solicitud HTTP saliente hacia un dominio $D$ como equivalente, adjuntando todas las cookies almacenadas para $D$, independientemente de cuál fuera el sitio de origen ($Site_{origen} \neq D$) desde el que se originó la petición.

## 4. Mitigación con el Atributo de Cookie `SameSite`

Para resolver este problema estructural, se introdujo el atributo `SameSite` en las especificaciones de cookies (RFC 6265bis). Este atributo instruye al navegador sobre si debe adjuntar la cookie en solicitudes que se originen desde sitios externos (de origen cruzado).

Una cookie se define con el parámetro `SameSite` en la cabecera `Set-Cookie`:

```http
Set-Cookie: session_id=XYZ123; Secure; HttpOnly; SameSite=Lax
```

### A. `SameSite=Strict`

Bajo la regla `Strict`, el navegador **nunca** enviará la cookie en solicitudes de origen cruzado (*cross-site requests*).

* **Comportamiento:** La cookie solo se adjunta si el sitio mostrado en la barra de direcciones del navegador coincide exactamente con el dominio de la cookie elegible.

* **Impacto:** Si la víctima está en `https://atacante.local` y se dispara una petición hacia `https://banco.local` (ya sea por formulario, AJAX o incluso un enlace directo `<a>`), la cookie **no se envía**.

* **Ventaja:** Protección completa y absoluta contra ataques CSRF.

* **Inconveniente de UX:** Si un usuario hace clic en un enlace legítimo enviado por correo o publicado en un sitio externo hacia `https://banco.local/dashboard`, la cookie de sesión no se enviará en esa primera navegación inicial, por lo que el usuario aparecerá como "no autenticado" hasta que vuelva a cargar o interactúe dentro del mismo dominio.

### B. `SameSite=Lax`

`SameSite=Lax` proporciona un equilibrio entre seguridad y experiencia de usuario. Es el comportamiento predeterminado en navegadores modernos (como Chrome, Firefox y Edge) cuando no se especifica el atributo.

* **Regla de Envío:** La cookie se retiene en peticiones de origen cruzado, **excepto** en navegaciones de nivel superior (*Top-Level Navigations*) que utilicen métodos **HTTP seguros e idempotentes** (principalmente `GET`).

* **Peticiones Bloqueadas (Sin Cookie):**
  * Peticiones `POST`, `PUT`, `DELETE` de origen cruzado (ej. envíos de formularios o `fetch`/`XMLHttpRequest`).
  * Cargas de subrecursos cruzados (imágenes `<img>`, `<iframe>`, scripts `<script>`).

* **Peticiones Permitidas (Con Cookie):**
  * Enlaces HTML directos (`<a href="...">`) donde el usuario hace clic para navegar a un sitio de nivel superior mediante un método `GET`.

### C. `SameSite=None`

Indica que la cookie continuará enviándose en todas las solicitudes de origen cruzado, manteniendo el comportamiento histórico del navegador.

* **Requisito Obligatorio:** Para establecer `SameSite=None`, la cookie debe incluir obligatoriamente el atributo `Secure` (lo que exige transmitirla únicamente sobre conexiones cifradas HTTPS):

```http
Set-Cookie: session_id=XYZ123; Secure; SameSite=None
```

Si se declara `SameSite=None` sin el atributo `Secure`, los navegadores modernos rechazarán y descartarán la cookie por completo.

## 5. Matriz de Comportamiento `SameSite` según el Tipo de Petición

| Contexto / Método de Petición | Origen de la Petición | `SameSite=Strict` | `SameSite=Lax` | `SameSite=None` |
| ----- | ----- | ----- | ----- | ----- |
| Enlace `<a>` (GET) | Origen Cruzado | **Sin Cookie** | **Con Cookie** | **Con Cookie** |
| Formulario `<form method="GET">` | Origen Cruzado | **Sin Cookie** | **Con Cookie** | **Con Cookie** |
| Formulario `<form method="POST">` | Origen Cruzado | **Sin Cookie** | **Sin Cookie** (Bloquea CSRF) | **Con Cookie** |
| Petición AJAX (`fetch`/`XHR` POST/GET) | Origen Cruzado | **Sin Cookie** | **Sin Cookie** (Bloquea CSRF) | **Con Cookie** |
| Subrecursos (`<img>`, `<iframe>` GET) | Origen Cruzado | **Sin Cookie** | **Sin Cookie** (Bloquea CSRF) | **Con Cookie** |
| Cualquier Petición | Mismo Origen (*Same-Site*) | **Con Cookie** | **Con Cookie** | **Con Cookie** |

## 6. Estrategia de Defensa en Profundidad

Aunque `SameSite=Lax` o `SameSite=Strict` ofrece una capa de defensa primaria muy sólida contra CSRF, la estrategia de seguridad completa recomienda una combinación en profundidad:

1. **Uso por Defecto de `SameSite=Lax` o `Strict`:** Configurar todas las cookies de sesión y estado crítico con atributos `SameSite` adecuados.

2. **Tokens Anti-CSRF (Synchronizer Token Pattern):** Incluir un token criptográficamente seguro e impredecible vinculado a la sesión en todos los formularios e interfaces `POST`/`PUT`/`DELETE`.

3. **Verificación de Cabeceras `Origin` y `Referer`:** Validar en el backend que el origen de la solicitud coincida con el dominio esperado antes de procesar cambios de estado.