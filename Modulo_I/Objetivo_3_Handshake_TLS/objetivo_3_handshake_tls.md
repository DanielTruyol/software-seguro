# Objetivo 3: Profundización Técnica (El "Handshake" TLS)

El TLS Handshake es una serie de mensajes negociados entre el navegador (cliente) y el servidor web para establecer un canal cifrado antes de transmitir cualquier dato de la aplicación.

Sus tres objetivos fundamentales son:

    1. Autenticar al servidor: Confirmar que el servidor es realmente quien dice ser y no un impostor.

    2. Acordar los algoritmos criptográficos: Decidir qué "idioma" de cifrado (la Cipher Suite) utilizarán ambos lados.

    3. Generar una clave secreta de sesión (Session Key): Crear una clave única compartida para cifrar el tráfico posterior, de modo que ningún intermediario en la red pueda leerla o alterarla.

El funcionamiento es el siguiente:

    1. ClientHello: El navegador le envía al servidor una lista de las versiones de TLS que soporta, las combinaciones de algoritmos criptográficos que conoce (Cipher Suites) y una cadena de datos aleatorios llamada Client Random.

    2. ServerHello & Certificado: El servidor responde eligiendo la versión de TLS y la suite de cifrado más segura compatible. Además, adjunta un Server Random y su Certificado Digital X.509, el cual contiene su Clave Pública.

    3. Validación del Certificado: El navegador comprueba si el certificado pertenece al dominio solicitado, si no ha caducado y si está firmado por una Autoridad Certificadora (CA) de confianza que el sistema operativo o el navegador reconozcan.

    4. Intercambio de Claves: Utilizando algoritmos de intercambio de claves (como ECDHE / Diffie-Hellman), cliente y servidor generan un secreto común (Pre-Master Secret).

    5. Generación de la Session Key: Ambas partes combinan el Client Random, el Server Random y el Pre-Master Secret para calcular exactamente la misma clave de sesión simétrica.

    6. Finished: Se envían mensajes confirmando que a partir de ese momento todo el tráfico estará cifrado con la clave de sesión recién generada.

## Certificados digitales

El certificado digital le garantiza al navegador que la clave pública que va a utilizar pertenece verdaderamente al sitio web legítimo y no a un suplantador.

    1. Es el pasaporte del servidor: Vincula legal y matemáticamente el nombre del dominio con la Clave Pública del servidor.

    2. Cadena de confianza (Chain of Trust): El certificado está firmado criptográficamente por una Autoridad Certificadora (CA) de confianza (como Let's Encrypt, DigiCert, etc.).

    3. Validación en el navegador: Durante el TLS Handshake, el navegador recibe el certificado y utiliza las claves públicas de las CAs que tiene preinstaladas en el sistema operativo para verificar que la firma digital sea auténtica, no haya caducado y no haya sido alterada.

## Cifrado

  Se utilizan ambos cifrados(asimétrico y simétrico) en fases distintas porque cada uno resuelve la debilidad del otro. Es un balance entre Seguridad/Intercambio de claves y Rendimiento/Velocidad.

    Fase 1 - Cifrado Asimétrico (La Puerta de Entrada): El cliente y el servidor usan el par de claves pública/privada y algoritmos como Diffie-Hellman (ECDHE) para validar la identidad y acordar en secreto una clave común (Session Key), sin que nadie en la red pueda descubrirla.

    Fase 2 - Cifrado Simétrico (La Navegación Diaria): Una vez que ambos lados tienen exactamente la misma Session Key, descartan el uso costoso de las claves pública/privada y pasan a utilizar cifrado simétrico (como AES-GCM o ChaCha20) para transferir todo el contenido web (HTML, imágenes, JSON) a máxima velocidad.
