# Objetivo 2: Ingeniería Inversa a JSON Web Tokens (JWT)

## 2. Estructura Técnica del JWT

Un JSON Web Token se compone de tres partes distintas codificadas en Base64URL y separadas por puntos (`.`):

$$\text{JWT} = \text{Header (Encabezado)} . \text{Payload (Carga útil)} . \text{Signature (Firma)}$$

### Token Raw (Crudo)

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkFsZXhhbmRlcg0iLCJyb2xlIjoiYWRtaW4iLCJlbWFpbCI6ImFsZXhhbmRlckBleGFtcGxlLmNvbSIsImlhdCI6MTc5NTQzNjA2NSwiZXhwIjoxNzk1NDQzMjY1fQ
.
xR4c8z54vG6Xz2_R99U30ZlW938Jk40_LmNoPqRsTuV
```

---

## 3. Decodificación y Análisis Técnico

### A. Header (Encabezado)

Decodificado desde Base64URL:

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

* **`alg` (Algoritmo de Firma):** `HS256` (HMAC con SHA-256). Es un algoritmo simétrico que requiere una clave secreta compartida (*Secret Key*) tanto para firmar como para verificar el token.
* **`typ` (Tipo de Token):** `JWT`.

### B. Payload (Carga Útil)

Decodificado desde Base64URL:

```json
{
  "sub": "1234567890",
  "name": "Alexander",
  "role": "admin",
  "email": "alexander@example.com",
  "iat": 1795436065,
  "exp": 1795443265
}
```

#### Análisis de Claims (Campos):

1. **Claims Estándar (RFC 7519):**
   * **`sub` (Subject):** Identificador único del usuario (`1234567890`).
   * **`iat` (Issued At):** Fecha y hora de emisión en UNIX timestamp (`1795436065`).
   * **`exp` (Expiration Time):** Fecha de expiración (`1795443265`), lo que otorga una validez determinada al token.

2. **Claims Personalizados (Datos y Roles del Usuario):**
   * **`role`:** `"admin"` — Especifica el rol o nivel de privilegios dentro de la aplicación.
   * **`email`:** `"alexander@example.com"` — Identificador o correo electrónico del usuario.
   * **`name`:** `"Alexander"` — Nombre del usuario.

### C. Signature (Firma Digital)

La tercera sección corresponde al hash generado por la fórmula:

$$\text{HMACSHA256}\Big(\text{base64UrlEncode}(\text{Header}) + "." + \text{base64UrlEncode}(\text{Payload}),\ \text{secret}\Big)$$

Esta firma garantiza la **integridad** del token: si un atacante modifica el valor de `role` a `"superadmin"` en el payload, la firma se vuelve inválida a menos que el atacante conozca la `SECRET_KEY` del servidor.

---
### 1. ¿Qué algoritmo de firma se está utilizando en el Header?
Se está utilizando **`HS256` (HMAC-SHA256)**. Se trata de un algoritmo de firma de clave simétrica. *(En escenarios empresariales complejos a menudo se utiliza `RS256`, un algoritmo asimétrico de clave pública/privada).*

### 2. ¿Qué datos sensibles o roles se están enviando en el Payload en texto plano?
En el payload decodificado se están enviando en **texto plano (codificado en Base64URL, no cifrado)** los siguientes datos:
* **Rol de usuario:** `"role": "admin"`
* **Correo electrónico:** `"email": "alexander@example.com"`
* **Nombre de usuario:** `"name": "Alexander"`
* **ID de usuario:** `"sub": "1234567890"`

