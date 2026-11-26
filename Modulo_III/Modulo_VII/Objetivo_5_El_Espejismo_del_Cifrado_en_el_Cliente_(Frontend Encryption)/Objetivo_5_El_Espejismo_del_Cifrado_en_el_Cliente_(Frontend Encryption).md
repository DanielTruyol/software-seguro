# Objetivo 5: El Espejismo del Cifrado en el Cliente (Frontend Encryption)

## 1. Resumen del Escenario

En un intento por impedir la manipulación de datos en tránsito y el análisis mediante proxies de intercepción como Burp Suite u OWASP ZAP, ciertos equipos de desarrollo implementan esquemas de **cifrado en el lado del cliente** (*Frontend Encryption*). 

Bajo este modelo, la aplicación ejecuta scripts de JavaScript en el navegador del usuario para cifrar el cuerpo (*body*) de las peticiones HTTP (o parámetros sensibles) antes de transmitirlos mediante solicitudes `POST` hacia el servidor backend.

Los arquitectos del sistema asumen la siguiente premisa:

> *"Al viajar la carga útil ($Payload$) cifrada desde el navegador, un atacante que intercepte la petición solo verá un bloque ininteligible de texto cifrado, imposibilitando la modificación de los parámetros."*

Esta afirmación constituye una **falsa sensación de seguridad** basada en la confusión entre la protección del canal de comunicación (*Seguridad en Tránsito*) y la integridad de los controles del lado del servidor (*Confianza en el Cliente*).

---

## 2. Fallo Fundamental de Diseño

El fallo principal de esta arquitectura reside en la **violación del principio de control del entorno de ejecución**:

### A. El Atacante Posee Dominio Absoluto sobre el Cliente

A diferencia de un canal de comunicación entre dos servidores aislados, el navegador del usuario es un entorno completamente controlado por el cliente. El atacante posee acceso total a:

* El código fuente de JavaScript entregado por la aplicación.
* Las claves simétricas, vectores de inicialización ($IV$) o claves públicas utilizadas en el script.
* La memoria RAM y el motor de ejecución de JavaScript (V8, SpiderMonkey, etc.).
* El depurador (*Debugger*) y las herramientas de desarrollo (*DevTools*).

### B. El Cifrado en Cliente es Equivalente a Obfuscación

Dado que tanto el algoritmo de cifrado como la clave de cifrado $K$ o los métodos de generación de claves deben ser descargados e interpretados por el navegador para poder cifrar el mensaje $M$:

$$
C = E_K(M)
$$

El atacante tiene acceso ilimitado a $E$, a $K$ y a $M$. Por lo tanto, el cifrado en el frontend no proporciona confidencialidad ni integridad frente al usuario local; únicamente añade una capa de **ofuscación operacional**.

### C. Redundancia e Ineficacia respecto a TLS/HTTPS

El protocolo **TLS/HTTPS** ya proporciona un túnel cifrado punto a punto seguro entre el navegador y el servidor final, protegiendo los datos contra atacantes en la red (*Man-in-the-Middle* o MitM pasivos/activos). Cifrar la carga útil con JavaScript sobre un túnel TLS no aporta ningún valor adicional contra interceptores externos y es completamente inútil contra el propio usuario del navegador.

---

## 3. Pasos Tácticos para Evadir la Protección

Un auditor de seguridad o atacante no necesita romper el algoritmo criptográfico (como AES o RSA); en su lugar, ataca el entorno de ejecución donde se procesan los datos antes de ser cifrados.

```
                  FLUJO DE INTERCEPCIÓN Y MANIPULACIÓN
                  
┌─────────────────────────────────────────────────────────────────┐
│ NAVEGADOR DEL ATACANTE (Entorno Controlado)                     │
│                                                                 │
│  [ Input Datos ] ──> [ Puntos de Intercepción ] ──> [ Cifrado ] │
│                             │                            │      │
│                             ▼                            │      │
│                     Manipulación Directa                 │      │
│                     (DevTools / Console)                 │      │
└──────────────────────────────────────────────────────────┼──────┘
                                                           │
                                                           ▼
                                               [ Burp Suite / Proxy ]
                                               (Carga útil cifrada o 
                                                re-cifrada con script)
                                                           │
                                                           ▼
                                               [ Backend Server ]
```

### Paso 1: Inspección y Análisis del Código JavaScript

El atacante abre las herramientas de desarrollo (*DevTools*) del navegador (F12) o utiliza Burp Suite para analizar los archivos `.js` cargados por la aplicación:

1. Busca funciones asociadas a librerías criptográficas conocidas (ej. `CryptoJS`, `Web Crypto API`, `forge`, `sjcl`).
2. Identifica el punto exacto donde la petición pasa de texto plano a texto cifrado (por ejemplo, funciones denominadas `encryptPayload()`, `encryptJSON()`, `doRSA()`).

### Paso 2: Intercepción en Tiempo de Ejecución (Runtime Hooking / Patching)

El atacante evita revertir el cifrado manualmente sobre la red; en su lugar, intercepta la información **antes** de que sea procesada por el método de cifrado mediante varios enfoques:

#### Enfoque A: Puntos de Interrupción (*Breakpoints*) en DevTools
* Coloca un *Breakpoint* en la línea de JavaScript previa a la invocación de la función de cifrado.
* Cuando la aplicación se pausa, modifica el valor de las variables en la consola interactiva (ej. cambiando `price = 1000` a `price = 1`).
* Reanuda la ejecución. El script de la aplicación cifra los datos ya manipulados y envía la petición legítimamente cifrada al servidor.

#### Enfoque B: Sobrescritura de Funciones (*Monkey Patching*)
El atacante ejecuta un script simple en la consola del navegador para alterar la lógica de cifrado:

```javascript
// Ejemplo de Monkey Patching en la consola del cliente
(function() {
    // 1. Guardar referencia de la función original
    const originalEncrypt = window.CryptoService.encrypt;

    // 2. Sobrescribir la función para interceptar y manipular
    window.CryptoService.encrypt = function(data) {
        console.warn("[+] Datos capturados en texto plano:", data);
        
        // Manipulación de parámetros en memoria
        if (data.amount) {
            data.amount = 0.01; // Cambiar monto a pagar
        }
        
        // Invocar la función original con la carga útil manipulada
        return originalEncrypt(data);
    };
})();
```

### Paso 3: Automatización del Flujo mediante Proxy (Burp Suite Extension)

Para pruebas repetitivas, el atacante automatiza el proceso dentro del proxy:

1. **Extrae la clave y el algoritmo:** Identifica la clave simétrica (o par de claves) y la rutina de derivación desde la memoria del navegador.
2. **Implementa un script en Burp Suite:** Utiliza extensiones como *Custom TLS*, *Burp Jython*, *AES Killer* o scripts de *Mitmproxy*.
3. El proxy descifra automáticamente el cuerpo de la petición cuando sale del navegador, permite al auditor editar los parámetros en texto plano desde la interfaz de Burp Suite, y vuelve a cifrar la petición con la clave/algoritmo adecuado antes de remitirla al servidor backend.

---

## 4. Matriz de Mitos vs. Realidad Arquitectónica

| Mito de los Arquitectos | Realidad de Seguridad |
| :--- | :--- |
| *"Burp Suite no puede leer los datos porque viajan cifrados."* | **Falso:** Los datos se pueden leer y modificar directamente en el navegador **antes** de ejecutarse la función de cifrado, o descifrar en el proxy reutilizando las claves extraídas de JavaScript. |
| *"El cifrado en cliente reemplaza la validación de integridad en el backend."* | **Falso:** El servidor debe tratar toda entrada recibida como potencialmente maliciosa, sin importar si viene dentro de una estructura JSON plana o de un bloque cifrado. |
| *"El atacante no puede adivinar la clave de cifrado."* | **Falso:** La clave no necesita ser adivinada; ya reside en el código, en la memoria o en la respuesta previa del servidor entregada al cliente. |

---

## 5. Estrategia de Remediación Definitiva

Para construir una arquitectura resiliente, el equipo de desarrollo debe erradicar la dependencia del cifrado en el cliente y adoptar las siguientes prácticas:

1. **Confiar Exclusivamente en TLS/HTTPS Estándar:**
   * Utilizar HTTPS con configuraciones modernas (TLS 1.3, TLS 1.2 con suites de cifrado fuertes). El transporte seguro garantiza la privacidad de los datos frente a terceros en la red de forma transparente y estandarizada.

2. **Validación y Autorización Obligatoria en Backend:**
   * Aplicar validación estricta de esquemas, tipos y rangos de datos en el servidor para cada petición entrante.
   * Verificar la autorización del usuario a nivel de objeto (*Broken Object Level Authorization - BOLA*) en la capa del backend antes de procesar cualquier transacción.

3. **No Depender de la Seguridad por Oscuridad:**
   * El código JavaScript enviado al navegador debe considerarse de acceso público. No debe contener lógica crítica de negocio, claves secretas ni asumir que los flujos no serán inspeccionados o alterados.

---

## 6. Conclusión

El cifrado de peticiones mediante JavaScript en el navegador no constituye una barrera infranqueable de seguridad, sino una capa de **seguridad por oscuridad**. Dado que el cliente controla el entorno de ejecución, las herramientas de inspección y las claves criptográficas, cualquier intento de reemplazar los controles de validación del servidor con cifrado en el frontend resulta ineficaz contra atacantes determinados.