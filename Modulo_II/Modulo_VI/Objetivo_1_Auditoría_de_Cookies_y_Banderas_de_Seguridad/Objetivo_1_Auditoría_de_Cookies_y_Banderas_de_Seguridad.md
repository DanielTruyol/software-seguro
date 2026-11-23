# Objetivo 1: Auditoría de Cookies y Banderas de Seguridad

## Auditoría de Cookies de Sesión (3 Sitios Web Públicos)

| Sitio Web | Cookie Analizada | `HttpOnly` | `Secure` | `SameSite` | Observaciones de Seguridad |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **GitHub** (`github.com`) | `user_session` / `__Host-user_session_same_site` | Sí | Sí | Lax / Strict | Protegida contra lectura por JS (`HttpOnly`) y envío sobre canales no cifrados (`Secure`). |
| **Wikipedia** (`es.wikipedia.org`) | `WMF-Last-Access` / sesión de usuario | Sí / Varía | Sí | Lax / None | Verifica que las cookies de autenticación/sesión tengan `HttpOnly` y `Secure` activos en HTTPS. |
| **MDN Web Docs** (`developer.mozilla.org`) | `sessionid` / cookies de preferencia | Sí | Sí | Lax | Confirmar en DevTools que el identificador de sesión restringe acceso vía JS y exige HTTPS. |
---

## Explicación Técnica: `HttpOnly` y `Secure`

* **¿Qué protege exactamente la bandera `HttpOnly`?**
  Protege la cookie frente al acceso desde el entorno de ejecución de scripts en el navegador (como `document.cookie` en JavaScript). Si un atacante logra inyectar y ejecutar JavaScript mediante una vulnerabilidad **Cross-Site Scripting (XSS)**, la bandera `HttpOnly` impide que el script lea directamente el valor de la cookie de sesión y lo exfiltre a un servidor externo. *(Nota: no evita que un script malicioso realice peticiones autenticadas en nombre de la sesión activa si el XSS ocurre, pero bloquea el robo directo del token/cookie vía DOM).*

* **¿Qué riesgo corre el usuario si la cookie de sesión no tiene la bandera `Secure` activada?**
  Si falta la bandera `Secure`, el navegador puede transmitir la cookie a través de conexiones **HTTP** sin cifrar (por ejemplo, si el usuario accede por `http://`, si ocurre una degradación de conexión / *SSL stripping* o si se realiza alguna petición no cifrada hacia un subdominio/ruta que aplique). En redes locales inseguras, Wi-Fi públicas o nodos intermedios comprometidos, un atacante que capture el tráfico en texto plano puede interceptar el identificador de sesión y realizar **Session Hijacking** (secuestro de sesión).

---