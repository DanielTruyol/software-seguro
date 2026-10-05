# Objetivo 1: Man-in-the-Middle Local (Configuración y Certificado CA)

## Gran rifa 2019

    https://chl-64bc2091-17b2-42f8-bf1d-eea4c6b9a358-gran-rifa-2019.softwareseguro.com.ar/

### Endpoints encontrados junto con sus métodos

    1.  https://chl-64bc2091-17b2-42f8-bf1d-eea4c6b9a358-gran-rifa-2019.softwareseguro.com.ar/login/?next=/

    GET - Nos redirige al panel de los compradores si el proceso de login fue exitoso
    POST - Envia las credenciales del login txt-username=guido&txt-password=RIFA_2019

    2.  https://chl-64bc2091-17b2-42f8-bf1d-eea4c6b9a358-gran-rifa-2019.softwareseguro.com.ar/api/numeros/

    GET - Nos trae un archivo Json con los datos de todos los compradores compradores "id", "numero", "vendedor", "comprador", "esta_pago"

    3.  https://chl-64bc2091-17b2-42f8-bf1d-eea4c6b9a358-gran-rifa-2019.softwareseguro.com.ar/ 

    GET - Nos trae el panel principal de la aplicación
    
    4.  https://chl-64bc2091-17b2-42f8-bf1d-eea4c6b9a358-gran-rifa-2019.softwareseguro.com.ar/cdn-cgi/rum?

    POST - Envia la cookie junto con datos de nuestro sistema

    5.  https://chl-64bc2091-17b2-42f8-bf1d-eea4c6b9a358-gran-rifa-2019.softwareseguro.com.ar/api/numeros/1/editar/

    POST - Manda el nuevo nombre del comprador del campo editado junto con la id correspondiente
