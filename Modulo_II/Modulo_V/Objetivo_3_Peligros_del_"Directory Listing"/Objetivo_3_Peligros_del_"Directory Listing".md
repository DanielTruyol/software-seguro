# Objetivo 3: Peligros del "Directory Listing"

## 1. Resumen Ejecutivo
El **Directory Listing** (listado de directorios o *autoindex*) es una función de los servidores web que genera y devuelve automáticamente un listado HTML con los archivos y subdirectorios contenidos en una carpeta cuando se solicita su ruta y no existe un archivo de índice predeterminado (como `index.html`, `index.php` o `default.aspx`).

Cuando esta directiva queda habilitada en producción por error de configuración (*Security Misconfiguration* / CWE-548), el servidor expone la estructura de archivos del proyecto y facilita el descubrimiento de recursos internos, respaldos, credenciales o código fuente que nunca debieron ser accesibles públicamente.

---

## 2. Comportamiento Técnico en Servidores Web

Cuando un cliente (navegador, `curl`, `gobuster`, `ffuf`, etc.) realiza una petición `GET /ruta/a/carpeta/` sobre un servidor web:

1. **Resolución de ruta física:** El servidor mapea la URI solicitada al directorio correspondiente dentro del *document root* o de una ruta configurada.
2. **Búsqueda de archivo índice:** Verifica secuencialmente si existe alguno de los archivos configurados como índice (por ejemplo, `index.html`, `index.htm`, `index.php`).
3. **Evaluación de la directiva de listado:**
   * **Si existe un archivo índice:** El servidor lo procesa o sirve y no genera listado de directorios.
   * **Si NO existe un archivo índice y el listado está deshabilitado:** El servidor responde habitualmente con `403 Forbidden` (o `404 Not Found` según la configuración o el módulo).
   * **Si NO existe un archivo índice y el listado está habilitado:** El módulo encargado del índice lee las entradas del directorio en el sistema de archivos y construye dinámicamente una respuesta `200 OK` con `Content-Type: text/html` conteniendo enlaces a cada archivo y subcarpeta (junto con metadatos como fecha de modificación y tamaño).

### Apache HTTP Server (`mod_autoindex`)
* Se controla mediante la directiva `Options Indexes` (o `Options +Indexes`).
* Si falta `DirectoryIndex` (o el archivo no está presente) y `Indexes` está activo, `mod_autoindex` genera el listado HTML del directorio.
* Si se usa `Options -Indexes`, Apache deniega el listado y devuelve `403 Forbidden`.

### Nginx (`ngx_http_autoindex_module`)
* Se controla con la directiva `autoindex on;` (por defecto está en `off`).
* Cuando `index` no encuentra coincidencias y `autoindex` está en `on`, Nginx devuelve un listado HTML generado por `ngx_http_autoindex_module` (o JSON/XML si se configura `autoindex_format`).
* Con `autoindex off;`, si no hay archivo índice, Nginx suele devolver `403 Forbidden` o `404 Not Found` según la regla aplicada.

---

## 3. Archivos y Recursos Sensibles Expuestos

Habilitar el Directory Listing permite que cualquier visitante o herramienta automatizada enumere rápidamente el árbol de directorios y descargue archivos sensibles mal ubicados:

* **Archivos de configuración y secretos:** `.env`, `config.php`, `appsettings.json`, `web.config`, `credentials.json`, archivos con cadenas de conexión a bases de datos, *API keys*, *JWT secrets* o claves privadas (`*.pem`, `*.key`, `id_rsa`).
* **Repositorios y metadatos de control de versiones:** directorios `.git/` (incluyendo `HEAD`, `config`, `logs/`, `objects/`) o `.svn/`. A partir de un `.git/` expuesto es posible reconstruir código fuente e historial de *commits*.
* **Copias de seguridad y archivos comprimidos:** `backup.zip`, `site.tar.gz`, `db.sql`, `dump.sql.gz`, `old.rar` o archivos temporales/editores como `index.php.bak`, `config.php~` o `*.swp`.
* **Archivos de registro (*logs*) y depuración:** `error.log`, `access.log`, `debug.log` o volcados de errores que pueden revelar rutas internas del sistema, versiones de software, consultas SQL, direcciones IP internas o datos de usuarios.
* **Código fuente, scripts administrativos y paneles internos:** scripts de despliegue, utilidades de mantenimiento, paneles de administración no protegidos o archivos de prueba olvidados en producción.
* **Archivos de usuarios o documentos privados:** facturas, exportaciones CSV/XLSX, reportes o adjuntos subidos sin control de acceso directo.

---

## 4. Impacto en Seguridad

* **Reconocimiento acelerado:** Reduce drásticamente el esfuerzo de enumeración de rutas y nombres de archivos.
* **Compromiso de credenciales y datos:** Un solo archivo `.env`, volcado SQL o clave privada descargable puede comprometer la base de datos, servicios externos o el servidor completo.
* **Encadenamiento de vulnerabilidades:** La información obtenida (rutas internas, versiones exactas, lógica del código fuente o *endpoints* ocultos) suele servir como base para explotar otras fallas como inyecciones, autenticación débil o escalada de privilegios.

---

## 5. Mitigación y Buenas Prácticas

### A. Deshabilitar el Directory Listing en el servidor web

**Apache (`httpd.conf`, `apache2.conf`, *virtual host* o `.htaccess`):**
```apache
<Directory /var/www/html>
    Options -Indexes
</Directory>