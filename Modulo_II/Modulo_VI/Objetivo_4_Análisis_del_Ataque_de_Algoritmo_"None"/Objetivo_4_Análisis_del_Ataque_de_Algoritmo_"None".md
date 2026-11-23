# Objetivo 4: Análisis del Ataque de Algoritmo "None"

## 1. Introducción y Contexto

Un **JSON Web Token (JWT)** es un estándar abierto ([RFC 7519](https://tools.ietf.org/html/rfc7519)) ampliamente utilizado para la transmisión segura de información entre partes en forma de objeto JSON. Su uso principal radica en la autenticación y autorización stateless en APIs web y microservicios.

La estructura estándar de un JWT consta de tres partes separadas por puntos (`.`):

$$\text{JWT} = \text{Base64Url}(\text{Header}) + "." + \text{Base64Url}(\text{Payload}) + "." + \text{Signature}$$

* **Header (Cabecera):** Especifica los metadatos del token, incluyendo el tipo de token (`typ`) y el algoritmo criptográfico utilizado para la firma (`alg`).
* **Payload (Carga útil):** Contiene los *claims* (afirmaciones) sobre el usuario o la sesión, como el identificador (`sub`), el rol (`role`) o la fecha de expiración (`exp`).
* **Signature (Firma):** Garantiza la integridad del token y la autenticidad del emisor mediante una clave secreta o un par de claves pública/privada.

---

## 2. Definición del Algoritmo `none`

El borrador del estándar RFC 7519 contempla explícitamente el valor `"none"` para el parámetro `alg` dentro de las Especificaciones de Firmas Criptográficas JSON ([RFC 7515 - JWS](https://tools.ietf.org/html/rfc7515)). La intención original era permitir el intercambio de datos estructurados en escenarios donde la integridad y la autenticidad del mensaje ya estuvieran garantizadas por otros medios (como dentro de un túnel TLS seguro entre servidores de confianza).

En un token con algoritmo `none`, la tercera sección (la firma) queda completamente vacía:

$$\text{JWT Unsigned} = \text{Base64Url}(\text{Header}) + "." + \text{Base64Url}(\text{Payload}) + "."$$

---

## 3. Mecanismo Técnico del Ataque

El ataque ocurre cuando una librería de procesamiento de JWT o el backend de la aplicación acepta tokens con `alg: "none"` en endpoints protegidos que requieren autenticación.

### Flujo de Verificación Normal vs. Flujo Vulnerable

```
[Flujo Normal]
Token Recibido -> Lee 'alg: HS256' -> Calcula Firma con Clave Secreta -> Compara Firmas -> [OK / Denegado]

[Flujo Vulnerable]
Token Recibido -> Lee 'alg: none' -> Salta la verificación criptográfica -> Acepta Payload -> [Acceso Concedido]
```

### Paso a Paso de la Explotación:

1. **Captura del Token:** El atacante obtiene un token JWT válido emitido por la aplicación tras iniciar sesión con una cuenta estándar.
2. **Decodificación del Token:** Utilizando la decodificación Base64URL, el atacante inspecciona el `Header` y el `Payload`.
3. **Modificación del Header:** El atacante altera el campo de algoritmo en la cabecera:
   ```json
   {
     "alg": "none",
     "typ": "JWT"
   }
   ```
4. **Modificación del Payload (Suplantación de Identidad):** El atacante altera los *claims* del cuerpo para asumir otra identidad o elevar privilegios. Por ejemplo:
   ```json
   {
     "sub": "105",
     "username": "usuario_comun",
     "role": "user"
   }
   ```
   Se modifica a:
   ```json
   {
     "sub": "1",
     "username": "admin",
     "role": "administrator"
   }
   ```
5. **Construcción del Token Malicioso:** Se codifican ambas estructuras modificadas en Base64URL y se unen con puntos, eliminando la firma original pero manteniendo el segundo punto final:
   ```text
   eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.ZXlKaGJHY2lPaUp1YjI1bElpd2lkSGx3SWpvaUpWZFVJbjAuZXlKemRXSWlPaUF4SWl3aWQzQnljMjl1WVdSbElqb2lZV1J0YVc1cGMzUnlZWFJ2Y2lJc0luSnZiR1VpT2lKaGpHMWpiaTFoYkhScGJXRmVkRzkxY2lJc0luVjphVzVpSWpvaU1UQTFJbjAu.
   ```
6. **Envío y Validación:** El atacante envía el token alterado en el encabezado `Authorization: Bearer <token>`. Al leer `alg: "none"`, el backend vulnerable asume que no requiere validación criptográfica, omite la comprobación con la clave secreta y procesa el `Payload` arbitrario proporcionado.

---

## 4. ¿Por qué se permite la suplantación sin conocer la clave secreta?

La clave secreta del servidor sirve para ejecutar una función Hash encriptada (como HMAC-SHA256) sobre las dos primeras partes del token. 

Cuando el backend acepta `alg: "none"`, **la librería ignora por completo la ejecución de la función de verificación de la clave secreta**. Al no ejecutarse el algoritmo de firma, la falta de conocimiento de la clave privada/secreta por parte del atacante se vuelve irrelevante, ya que el sistema simplemente confía en los datos decodificados de la carga útil sin validar si provienen de una fuente legítima.

---

## 5. Variantes e Implementaciones Inseguras Frecuentes

El bypass del algoritmo `none` no siempre ocurre escribiendo estrictamente `"none"`. Muchas bibliotecas históricas intentaron implementar filtros ingenuos que eran evadidos mediante variaciones como:

* **Mayúsculas/Minúsculas mezcladas (Case Sensitivity):** `"None"`, `"NONE"`, `"nOnE"`. Si el filtro usaba comparaciones de cadenas estrictas (ej. `if (alg == "none")`), podía fallar al evaluar variantes con mayúsculas.
* **Firmas no vacías:** Enviar una firma arbitraria al final del token mientras se especifica `alg: "none"`. Algunas librerías no verificaban si la firma estaba vacía y procedían a aceptar el token omitiendo el cálculo del Hash.

---

## 6. Impacto en la Seguridad

La vulnerabilidad del algoritmo `none` representa un fallo crítico de **Broken Access Control (OWASP A01:2021)** y **Cryptographic Failures (OWASP A02:2021)**:

* **Bypass Completo de Autenticación:** Cualquier usuario no autenticado o atacante externo puede generar tokens arbitrarios.
* **Escalada Vertical de Privilegios:** Modificación de *claims* de rol para adquirir permisos de administrador.
* **Escalada Horizontal de Privilegios:** Modificación de identificadores (`user_id`, `sub`) para acceder a la cuenta de cualquier otro usuario de la plataforma.

---

## 7. Estrategias de Mitigación

Para prevenir esta vulnerabilidad en entornos de producción, se deben aplicar las siguientes buenas prácticas:

1. **Forzar la Lista Blanca de Algoritmos Permitidos:** 
   No permitir que el cliente/token decida dinámicamente el algoritmo. En el backend, al llamar a la función de verificación, se deben declarar explícitamente los algoritmos aceptados:
   ```javascript
   // Ejemplo en Node.js (jsonwebtoken)
   jwt.verify(token, secretKey, { algorithms: ['HS256'] });
   ```
   ```python
   # Ejemplo en Python (PyJWT)
   jwt.decode(token, secret_key, algorithms=["HS256"])
   ```

2. **Rechazar Expresamente el Algoritmo `none`:**
   Asegurar que la biblioteca de manejo de JWT rechace por defecto cualquier token cuya cabecera contenga `alg: "none"` (o variaciones de mayúsculas y minúsculas).

3. **Mantener Dependencias Actualizadas:**
   Las versiones modernas de la gran mayoría de librerías populares (como `PyJWT`, `jsonwebtoken`, `Nimbus JOSE+JWT`, etc.) ya han corregido el soporte involuntario de `none`, deshabilitándolo por defecto.

4. **Pruebas de Seguridad Automatizadas:**
   Incluir pruebas unitarias e integraciones en el pipeline CI/CD que envíen deliberadamente tokens manipulados con `alg: "none"` para validar que los endpoints protegidos devuelvan respuestas `401 Unauthorized` o `403 Forbidden`.