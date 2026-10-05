# Objetivo 3: Análisis de Automatización y Fuerza Bruta

    Un ataque de fuerza bruta manda peticiones probando todas las combinaciones posibles de usuario y contraseña del login hasta encontrar credenciales. Es mucho más lento que el ataque de diccionario y se necesita poder de computo.

    El ataque con un diccionario manda peticiones de login con una lista conocida de usuarios y contraseñas hasta dar con una credencial si es que alguien uso patrones comunes incluidos en el diccionario. Es mucho mas rápido que el ataque de fuerza bruta si se da el caso.

    El mecanismo de defensa puede ser Rate Limiting (Limitación de Tasa de Peticiones), acompañado opcionalmente por un bloqueo temporal por IP o cuenta.
    El desarrollador define una regla en el servidor o middleware para controlar cuántas peticiones de inicio de sesión se permiten desde una misma dirección IP (o hacia una misma cuenta de usuario) dentro de un periodo de tiempo determinado.
    Al imponer un límite estricto de tiempo, la velocidad de prueba cae a niveles insignificantes, volviendo el ataque técnicamente inviable e ineficiente.
