# Objetivo 3: La Única Mitigación Definitiva (Prepared Statements)

## 1. El Fracaso de los Parches Defensivos Insuficientes

Frecuentemente, las aplicaciones intentan solucionar vulnerabilidades de inyección SQL (SQLi) mediante filtros superficiales en la capa de aplicación. Aunque estas medidas intentan restringir la entrada maliciosa, suelen fallar debido a la enorme flexibilidad sintáctica de los dialectos SQL y los parsers del backend.

### A. Listas Negras (Blacklisting)

Consisten en bloquear palabras clave (`SELECT`, `UNION`, `AND`, `OR`, `SLEEP`) o caracteres especiales. Este enfoque es fundamentalmente ineficaz debido a múltiples métodos de evasión:

* **Técnicas de Evasión Sintáctica:** Alternancia de mayúsculas y minúsculas (`sElEcT`), uso de comentarios en línea para romper palabras claves (`UNI/**/ON`), o inclusión de caracteres de control nulos y saltos de línea.
* **Codificaciones Alternativas:** Uso de valores hexadecimales (`0x...`), funciones de conversión como `CHAR()`, o codificaciones URL anidadas que el parser de la base de datos interpreta después de pasar la lista negra.
* **Inyección Sin Palabras Clave:** En muchos casos no se requieren palabras bloqueadas para causar estragos; basta con manipular condiciones booleanas o subconsultas que utilicen operadores matemáticos y lógicos no contemplados en la lista.

### B. Escapado de Caracteres (Character Escaping)

Consiste en anteponer barras invertidas (`\`) a caracteres como comillas simples (`'`) o dobles (`"`) para evitar que el intérprete SQL reconozca el cierre de la cadena de texto (ej. `mysql_real_escape_string`). 

A pesar de ser más sólido que las listas negras, el escapado de caracteres presenta vulnerabilidades críticas:

1. **Inyección en Parámetros Numéricos (Sin Comillas):**
   Si la consulta SQL no utiliza comillas alrededor del parámetro del usuario:
   
   ```sql
   SELECT * FROM users WHERE id = INPUT_USUARIO;
   ```
   
   Si `INPUT_USUARIO` es `1 OR 1=1`, no hay comillas que escapar. La sintaxis SQL se altera directamente sin necesidad de enviar caracteres delimitadores de texto.

2. **Ataques de Codificación Multi-Byte (GBK / Big5):**
   En motores donde se utilizan codificaciones de caracteres multi-byte no configuradas en sincronización estricta entre la aplicación y la base de datos, un atacante puede enviar secuencias de bytes como `%bf%27`. Al intentar escapar la comilla (`%27` $\rightarrow$ `\''` o `%5c%27`), el byte `%bf%5c` se fusiona en un único carácter multi-byte (ej. en GBK), dejando la comilla `%27` libre para romper el contexto SQL.

---

## 2. Ciclo de Vida de una Consulta SQL Tradicional

Para entender por qué fallan los métodos basados en texto y por qué funcionan las consultas parametrizadas, es necesario analizar el flujo interno de procesamiento en el motor de base de datos (**DBMS**).

Al recibir una consulta basada en concatenación de cadenas, el DBMS ejecuta cuatro fases secuenciales:

```
 Petición SQL Concatenada
         │
         ▼
┌─────────────────┐
│  1. Parsing     │ ──> Analiza la sintaxis y construye el Árbol de Sintaxis Abstracta (AST).
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Compilación  │ ──> Traduce el AST a código de ejecución interno.
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. Optimización │ ──> Selecciona el plan de ejecución de menor costo.
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. Ejecución    │ ──> Procesa los datos y devuelve el resultado.
└─────────────────┘
```

### El Problema de la Concatenación de Cadenas

En una consulta dinámica concatenada:

```sql
SELECT * FROM users WHERE username = 'admin' AND password = 'INPUT_USUARIO';
```

El parser analiza **toda la cadena recibida como un único bloque de código instruccional**. Si el parámetro introducido por el usuario es `' OR '1'='1`, la estructura lógica del árbol de sintaxis abstracta (**AST**) se modifica **durante la fase de Parsing**:

```
           AST de Consulta Inyectada (Modificada)
                          WHERE
                            │
                     ┌──────┴──────┐
                     │             OR (Instrucción Logica Inyectada)
               AND (Original)      │
               /     \          ┌──┴──┐
     username='admin'  pass='' '1'   '1'
```

Dado que el AST cambia su estructura antes de ser compilado, la intención original del desarrollador es destruida y el motor ejecuta la instrucción inyectada con plenos derechos de sintaxis.

---

## 3. Arquitectura Interna de las Consultas Parametrizadas

Una **Consulta Parametrizada** (*Prepared Statement*) resuelve el problema desacoplando la fase de **Compilación de la Estructura** de la fase de **Paso de Datos**.

A nivel de protocolo de base de datos (por ejemplo, en el protocolo binario de MySQL o PostgreSQL), la comunicación se divide explícitamente en dos etapas independientes:

```
          ETAPA 1: Preparación (PREPARE)
   Cliente ───────────────────────────────> DBMS
   Envía la PLANTILLA fija con placeholders:
   "SELECT * FROM users WHERE user = ? AND pass = ?"
                                             │
                                             ▼
                                     [ Parsing & AST Fijo ]
                                     [ Plan de Ejecución  ]
                                     [ Retorna Statement ID ]

          ETAPA 2: Ejecución (EXECUTE)
   Cliente ───────────────────────────────> DBMS
   Envía el Statement ID + Datos puros:
   ID: 1, Param1: "admin", Param2: "' OR '1'='1"
                                             │
                                             ▼
                                     [ Ejecuta el Plan Fijo ]
                                     [ Trata Param2 como LITERAL ]
```

### Paso 1: Preparación (`PREPARE`)

La aplicación envía únicamente la **plantilla instruccional** de la consulta al DBMS, utilizando marcadores de posición (*placeholders*) como `?` o `:param`:

```sql
PREPARE stmt1 FROM 'SELECT * FROM users WHERE username = ? AND password = ?';
```

El motor de base de datos realiza el **Parsing**, la **Compilación** y genera el **Árbol de Sintaxis Abstracta (AST)** de forma fija. En este punto, la estructura de la consulta queda **sellada e inmutable** en la memoria del motor.

### Paso 2: Ejecución (`EXECUTE`)

Posteriormente, la aplicación envía de forma independiente los valores de los parámetros vinculados a través del canal de datos:

```sql
EXECUTE stmt1 USING @input_user, @input_pass;
```

El DBMS toma los parámetros recibidos y los inserta directamente en los nodos de datos del AST ya compilado, **sin volver a pasar por la fase de Parsing**.

---

## 4. Por Qué Neutraliza Completamente la Inyección SQL

La razón técnica por la cual una consulta parametrizada neutraliza el 100% de los intentos de SQLi radica en la **imposibilidad de alterar la gramática del AST**:

1. **Inmutabilidad del Plan de Ejecución:** Dado que el Parsing sintáctico ya ocurrió en el paso `PREPARE`, ningún carácter enviado en la etapa `EXECUTE` puede ser interpretado como un comando, palabra clave o delimitador sintáctico.
2. **Tratamiento Literal Absoluto:** Si el usuario envía la cadena `' OR '1'='1` dentro del parámetro, el motor de la base de datos la trata mecánicamente como el texto literal de la contraseña (una cadena exacta de 14 caracteres: `[',  , O, R,  , ', 1, ', =, ', 1]`).
3. **Pérdida de Significado de Caracteres Especiales:** Las comillas (`'`), los guiones dobles (`--`) o los puntos y comas (`;`) pierden por completo su significado semántico de control y se almacenan/comparan literalmente en memoria como simples bytes de datos.

---

## 5. Comparativa de Implementación en Código

### Ejemplo Vulnerable (Node.js con PostgreSQL - Concatenación)

```javascript
// CÓDIGO VULNERABLE: Susceptible a SQLi
const userInput = req.body.username; // Valor enviado: "admin' --"

const query = `SELECT * FROM users WHERE username = '${userInput}'`;
// La cadena final compilada es: SELECT * FROM users WHERE username = 'admin' --'
const result = await db.query(query); 
```

### Ejemplo Remediado Seguro (Node.js con PostgreSQL - Prepared Statement)

```javascript
// CÓDIGO SEGURO: Utiliza parametrización nativa
const userInput = req.body.username; // Valor enviado: "admin' --"

// El cliente PG envía la plantilla y los parámetros mediante el protocolo binario
const query = 'SELECT * FROM users WHERE username = $1';
const values = [userInput];

const result = await db.query(query, values);
// El DBMS busca literalmente el usuario cuya cadena sea "admin' --"
```

### Ejemplo Remediado Seguro (PHP con PDO)

```php
// CÓDIGO SEGURO: Preparación explícita con PDO
$userInput = $_POST['username'];

$stmt = $pdo->prepare('SELECT id, password_hash FROM users WHERE username = :username');
// Vinculación estricta del parámetro
$stmt->execute(['username' => $userInput]);
$user = $stmt->fetch();
```

---

## 6. Casos Límite: Dónde los Prepared Statements No Aplican Directamente

Es crucial entender que las consultas parametrizadas **solo permiten reemplazar valores de datos** (literales en cláusulas `WHERE`, `VALUES`, `SET`). No se pueden utilizar marcadores de posición (`?`) para identificadores del motor como:

* Nombres de tablas (`FROM ?`)
* Nombres de columnas (`SELECT ? FROM users`)
* Ordenamiento (`ORDER BY ?`)
* Operadores o palabras clave (`SELECT * FROM users ? ASC`)

Si una aplicación requiere parametrizar dinámicamente nombres de columnas o criterios de ordenamiento, **no debe recurrir a la concatenación directa de la entrada del usuario**. En su lugar, se debe implementar una **Lista Blanca Estricta (Whitelisting)** a nivel de código de aplicación:

```php
// Ejemplo de Lista Blanca Estricta para Ordenamiento Dinámico
$allowedColumns = ['username', 'created_at', 'email'];
$sortColumn = $_GET['sort'];

// Verificación estricta contra la lista blanca
if (!in_array($sortColumn, $allowedColumns, true)) {
    $sortColumn = 'created_at'; // Valor por defecto seguro
}

// Es seguro concatenar $sortColumn porque ha sido validada contra un conjunto cerrado
$stmt = $pdo->prepare("SELECT id, username FROM users ORDER BY {$sortColumn} ASC");
$stmt->execute();
```

---

## 7. Conclusión

Las soluciones defensivas basadas en la modificación del texto enviado por el usuario (listas negras o escapado de caracteres) intentan resolver un problema de diseño mediante remiendos en la capa de transporte, manteniendo abierta la ventana de evasión sintáctica.

Las **Consultas Parametrizadas (Prepared Statements)** representan la única solución definitiva contra la inyección SQL porque transforman la arquitectura de ejecución del problema: separan de forma tajante la **lógica del código** de los **datos del usuario** en la capa del motor de base de datos, imposibilitando que cualquier entrada del cliente altere el comportamiento del programa.