Objetivo 3: Armado de Plantilla Base de Reporte
Como pentester, tu entregable final es el reporte. Diseña y personaliza tu propia plantilla de reporte profesional. Esta será la herramienta que utilizarás en el resto del curso y en tu vida profesional. La plantilla debe contener obligatoriamente las siguientes secciones: Resumen Ejecutivo (para directivos), Detalles Técnicos, Métricas CVSS, Prueba de Concepto (PoC) detallada paso a paso, y Recomendaciones de Remediación. Explicar la estructura de la plantilla y que valor genera al usuario final que lee un ticket realizado con dicha plantilla. Formato de entrega: Enlace al archivo .md.

# Objetivo 3: Armado de Plantilla Base de Reporte

# Informe Técnico: Plantilla Base de Reporte de Auditoría de Seguridad

## 1. Introducción
En el ejercicio del hacking ético y las auditorías de seguridad, el informe final es el único entregable tangible que recibe el cliente o el equipo de desarrollo. Una plantilla estandarizada y profesional garantiza que los hallazgos se comuniquen con claridad, permitiendo a los directivos dimensionar el riesgo de negocio y a los desarrolladores replicar y solucionar las vulnerabilidades de manera eficiente.

---

## 2. Estructura de la Plantilla Base de Reporte

A continuación se detalla la estructura oficial de la plantilla diseñada para las auditorías de seguridad, junto con una explicación de su contenido y el valor que aporta a cada perfil receptor.

### A. Resumen Ejecutivo (Executive Summary)
* **Descripción:** Sección orientada a gerentes, directores y C-level. Explica en lenguaje de negocio (sin tecnicismos excesivos) el estado general de la seguridad de la aplicación, el impacto potencial de los hallazgos críticos y un resumen métrico del riesgo global.
* **Valor generado:** Permite a los directivos tomar decisiones informadas sobre la asignación de presupuestos y recursos para la mitigación de riesgos sin necesidad de leer detalles de código fuente.

### B. Detalles Técnicos (Technical Details)
* **Descripción:** Apartado riguroso que documenta la naturaleza técnica de cada hallazgo. Incluye:
  * **Título descriptivo y Severidad** (Crítica, Alta, Media, Baja).
  * **Clasificación asociada:** Identificadores **CWE** (debilidad de código) y **CVE** (si aplica a componentes de terceros).
  * **Endpoint / Componente afectado:** URL exacta, parámetro vulnerable o librería comprometida.
* **Valor generado:** Proporciona a los ingenieros y desarrolladores el contexto exacto del fallo para comprender por qué la arquitectura o el código son vulnerables.

### C. Métricas CVSS (Common Vulnerability Scoring System)
* **Descripción:** Evaluación estandarizada del riesgo mediante el vector y la puntuación **CVSS v3.1 / v4.0**. Desglosa métricas como Vector de Ataque (AV), Complejidad (AC), Privilegios Requeridos (PR), Interacción de Usuario (UI