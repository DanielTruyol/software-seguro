Objetivo 1: Estandarización de Vulnerabilidades (CVE y CWE)
En la industria, las vulnerabilidades deben hablar un idioma universal. Investiga y redacta un informe breve explicando qué es un CVE (Common Vulnerabilities and Exposures) y qué es el catálogo CWE (Common Weakness Enumeration), marcando la diferencia entre ambos. Menciona quiénes son las autoridades que asignan los CVE (CNAs), dónde se consultan públicamente, y nombra al menos dos herramientas automatizadas de la industria que se utilizan para detectar vulnerabilidades con CVEs asignados. Formato de entrega: Enlace al archivo .md.

# Objetivo 1: Estandarización de Vulnerabilidades (CVE y CWE)

# Informe Técnico: Estandarización de Vulnerabilidades (CVE y CWE)

## 1. Introducción
En el ecosistema del desarrollo de software seguro y la ciberseguridad, la estandarización es fundamental para que equipos de desarrollo, investigadores y analistas de seguridad se comuniquen utilizando un lenguaje técnico universal. Para ello existen diccionarios y taxonomías oficiales como CVE y CWE.

---

## 2. Definiciones Clave

### CVE (Common Vulnerabilities and Exposures)
Es un diccionario o catálogo patrocinado por la organización MITRE que recopila **vulnerabilidades y exposiciones de ciberseguridad públicamente conocidas**. 
* Cada entrada de CVE posee un identificador único (por ejemplo: `CVE-2021-44228`).
* Su objetivo es proporcionar un nombre estándar único para cada fallo específico descubierto en un producto de software o hardware, facilitando compartir datos entre bases de datos de seguridad y herramientas de escaneo.

### CWE (Common Weakness Enumeration)
Es un catálogo formal que clasifica las **debilidades y errores de programación, arquitectura o diseño** que pueden aparecer en el software y que, de no corregirse, podrían derivar en vulnerabilidades.
* Funciona como una taxonomía o "árbol genealógico" de los errores de código (por ejemplo, el uso inseguro de funciones, desbordamientos de búfer, o fallos de validación de entradas).
* Ejemplo: **CWE-89** (Improper Neutralization of Special Elements used in an SQL Command).

---

## 3. Diferencia Principal entre CVE y CWE

La diferencia radica en el nivel de abstracción y el enfoque del problema:
* **CWE** clasifica el **tipo de debilidad** o error abstracto en el código (la causa raíz o categoría).
* **CVE** identifica una **instancia concreta de vulnerabilidad** en un producto y versión específica de un fabricante.

*Analógica rápida:* El **CWE** es el diagnóstico médico de una enfermedad genérica (ej. "infección bacteriana"), mientras que el **CVE** es el registro clínico específico del brote de esa bacteria en un paciente y fecha determinados.

---

## 4. Autoridades de Asignación (CNAs) y Fuentes de Consulta

### ¿Quiénes asignan los CVE? (CNAs)
Los identificadores CVE no son asignados por una sola entidad central exclusiva, sino por las **CNAs (CVE Numbering Authorities)**. 
* Las CNAs son organizaciones autorizadas en todo el mundo (proveedores de software como Microsoft o Red Hat, investigadores de seguridad, centros de respuesta a incidentes - CERTs, y proyectos open-source) encargadas de revisar, aprobar y asignar los identificadores CVE a las fallas descubiertas en sus respectivos ámbitos.

### ¿Dónde se consultan públicamente?
* **CVE.org:** El sitio oficial administrado por MITRE donde se gestiona el catálogo maestro y los detalles de cada identificador.
* **NVD (National Vulnerability Database - nvd.nist.gov):** Mantenido por el NIST, enlaza los CVEs con puntuaciones de severidad estandarizadas (**CVSS**) y clasificaciones **CWE**.

---

## 5. Herramientas Automatizadas de la Industria

Para la detección automatizada de componentes vulnerables asociados a CVEs conocidos, se emplean comúnmente soluciones de análisis de dependencias y vulnerabilidades en la cadena de suministro de software (SCA):

1. **OWASP Dependency-Check:** Herramienta open-source que detecta dependencias de proyectos (Maven, npm, Gradle, etc.) y verifica si contienen vulnerabilidades con CVEs conocidos registrados en la base de datos del NVD.
2. **Trivy / Snyk:** Soluciones modernas de análisis de seguridad integradas en flujos CI/CD capaces de escanear contenedores, sistemas de archivos y dependencias de código para identificar CVEs activos y sus rutas de remediación.