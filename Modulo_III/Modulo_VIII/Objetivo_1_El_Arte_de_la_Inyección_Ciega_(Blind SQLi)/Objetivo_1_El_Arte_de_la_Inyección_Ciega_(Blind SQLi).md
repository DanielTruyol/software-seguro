# Objetivo 1: El Arte de la Inyección Ciega (Blind SQLi)

## 1. Introducción a la Inyección SQL Ciega

En los escenarios tradicionales de inyección SQL (conocidos como *In-Band* o *Error-Based SQLi*), la aplicación web expone directamente los resultados de la consulta o mensajes de error detallados del motor de base de datos (DBMS) en la respuesta HTTP. Esto permite al atacante volcar información directamente en pantalla.

Sin embargo, cuando una aplicación está configurada para ocultar errores del motor de base de datos y no refleja datos de la consulta en la interfaz, la vulnerabilidad sigue estando presente si las entradas del usuario se concatenan directamente en la sentencia SQL. En este contexto, se habla de **Inyección SQL Ciega (Blind SQLi)**.

Al no recibir datos devueltos explícitamente, el atacante debe formular preguntas de tipo **Verdadero/Falso** al motor de base de datos y deducir la respuesta observando sutiles diferencias en el comportamiento del servidor.

---

## 2. Boolean-Based Blind SQLi (Basada en Booleanos)

### Concepto Técnico
La inyección ciega basada en booleanos consiste en inyectar condiciones lógicas que evalúan a `TRUE` o `FALSE`. Aunque la respuesta no muestre datos de la base de datos, el comportamiento de la aplicación varía según la validez de la condición inyectada.

### Mecanismo de Inferencia
El atacante evalúa dos peticiones con respuestas diferenciables:

1. **Condición Verdadera (`TRUE`):**
   ```sql
   SELECT * FROM products WHERE id = 1 AND 1=1;
   ```
   La consulta devuelve el producto normalmente. El servidor responde con HTTP `200 OK` y el contenido esperado.

2. **Condición Falsa (`FALSE`):**
   ```sql
   SELECT * FROM products WHERE id = 1 AND 1=2;
   ```
   La consulta no retorna filas. El servidor puede responder con un mensaje como `"Producto no encontrado"`, omitir cierta sección del HTML o devolver un código de estado distinto.

A través de esta discrepancia en la respuesta (diferencia en longitud de contenido, palabras clave presentes o código HTTP), el atacante confirma si la suposición inyectada fue verdadera o falsa.

---

## 3. Time-Based Blind SQLi (Basada en Tiempo)

### Concepto Técnico
En escenarios donde la aplicación devuelve exactamente la misma respuesta HTTP (mismo código de estado, mismo cuerpo HTML o pantallas neutras como *"Cargando..."* o *"Procesando..."*) independientemente de si la consulta es verdadera o falsa, el canal de comunicación inferencial tradicional se bloquea.

La **Inyección Ciega Basada en Tiempo** supera este obstáculo obligando a la base de datos a pausar su ejecución durante un intervalo de tiempo predeterminado ($\Delta t$) únicamente cuando una condición inyectada se evalúa como `TRUE`.

### Funciones de Retardo según la Base de Datos
Cada motor de base de datos dispone de funciones específicas para pausar la ejecución:

* **MySQL / MariaDB:** `SLEEP(5)`
* **PostgreSQL:** `pg_sleep(5)`
* **Microsoft SQL Server:** `WAITFOR DELAY '0:0:5'`
* **Oracle:** `DBMS_PIPE.RECEIVE_MESSAGE('RDS', 5)`

### Comportamiento en la Aplicación
Consideremos la inyección de la siguiente sentencia condicional:

```sql
SELECT * FROM users WHERE id = 1 AND IF(1=1, SLEEP(5), 0);
```

* **Si la condición es `TRUE` ($1=1$):** El servidor tardará $\ge 5$ segundos en responder.
* **Si la condición es `FALSE` ($1=2$):** El servidor responderá de forma casi instantánea ($< 0.5$ segundos).

El atacante utiliza la **latencia de respuesta del servidor** como su único canal de salida (*out-of-band/side-channel*).

---

## 4. Algoritmo de Extracción Carácter por Carácter

Dado que solo se puede transmitir $1$ bit de información por cada petición (Verdadero/Falso o Demora/No Demora), la extracción del nombre de la base de datos o de cualquier dato requiere un proceso de inferencia iterativo.

### Pasos Algorítmicos

#### Paso 1: Determinar la Longitud del Nombre de la Base de Datos
Antes de extraer caracteres, se debe identificar cuántos caracteres $N$ tiene la cadena objetivo mediante la función `LENGTH()` o `CHAR_LENGTH()`:

* Petición 1: `LENGTH(database()) = 1` $\rightarrow$ Respuesta: `FALSE` (Sin retardo)
* Petición 2: `LENGTH(database()) = 2` $\rightarrow$ Respuesta: `FALSE` (Sin retardo)
* ...
* Petición $k$: `LENGTH(database()) = 8` $\rightarrow$ Respuesta: `TRUE` (Retardo de 5s)

Resultado: El nombre de la base de datos contiene $N = 8$ caracteres.

#### Paso 2: Inferencia de Cada Carácter por Código ASCII
Para extraer la letra en la posición $i \in \{1, 2, \dots, N\}$, se emplean funciones de subcadena y conversión a código ASCII:

* `SUBSTRING(cadena, posicion, longitud)`: Extrae el carácter de la posición requerida.
* `ASCII(caracter)`: Convierte el carácter a su valor numérico decimal en la tabla ASCII.

##### Inyección de Ejemplo (Time-Based en MySQL):
```sql
SELECT * FROM products 
WHERE id = 1 AND IF(ASCII(SUBSTRING(database(), 1, 1)) = 115, SLEEP(5), 0);
```

Si el servidor tarda $5$ segundos en responder, el valor ASCII del primer carácter es $115$, el cual corresponde a la letra `'s'` en minúscula.

---

### Búsqueda Lineal vs. Búsqueda Binaria

#### Búsqueda Lineal ($O(N \cdot M)$)
Si el atacante prueba secuencialmente cada valor ASCII posible entre el rango imprimible (ASCII $32$ a $126$, $M \approx 95$ caracteres), para un nombre de base de datos de longitud $N = 8$, requeriría en el peor de los casos:

$$
\text{Total Peticiones} = N \times M = 8 \times 95 = 760 \text{ peticiones}
$$

En una inyección basada en tiempo con un retardo de $5$ segundos por acierto, esto requeriría un tiempo considerable.

#### Búsqueda Binaria ($O(N \cdot \log_2 M)$)
Para optimizar el proceso, el atacante utiliza un algoritmo de búsqueda binaria evaluando operadores de desigualdad ($>$ o $<$):

1. **¿`ASCII(SUBSTRING(database(), 1, 1)) > 79`?** $\rightarrow$ `TRUE` (Filtra la mitad inferior).
2. **¿`ASCII(SUBSTRING(database(), 1, 1)) > 103`?** $\rightarrow$ `TRUE`.
3. **¿`ASCII(SUBSTRING(database(), 1, 1)) > 115`?** $\rightarrow$ `FALSE`.
4. **¿`ASCII(SUBSTRING(database(), 1, 1)) = 115`?** $\rightarrow$ `TRUE` (Se determina el carácter `'s'`).

Con búsqueda binaria, encontrar cada carácter requiere un máximo de $\lceil \log_2(95) \rceil = 7$ peticiones.

Para $N = 8$ caracteres:

$$
\text{Total Peticiones} = 8 \times 7 = 56 \text{ peticiones}
$$

Esto reduce el número de solicitudes en más de un $90\%$, haciendo viable la extracción masiva de información a través de la inyección ciega.

---

## 5. Matriz Comparativa

| Criterio | Boolean-Based Blind SQLi | Time-Based Blind SQLi |
| :--- | :--- | :--- |
| **Mapeo de Respuesta** | Cambios en el cuerpo HTML, cabeceras o estado HTTP | Latencia en el tiempo de respuesta del servidor |
| **Ruido / Impacto en Red** | Menor latencia, alto número de peticiones HTTP | Mayor consumo de tiempo por retardo (`SLEEP`) |
| **Susceptibilidad a Ruido de Red** | Baja (respuestas deterministas) | Alta (la latencia de red variable puede causar falsos positivos/negativos) |
| **Complejidad de Automatización** | Media | Media-Alta (requiere umbrales dinámicos de tiempo) |

---

## 6. Remediación Definitiva

El tipo de inyección (ya sea directa, basada en errores o ciega) es irrelevante para el método de remediación. La causa raíz es la concatenación de datos del usuario en la estructura del comando SQL.

### Solución: Sentencias Preparadas (Prepared Statements)

Las sentencias preparadas con parámetros vinculados garantizan que el motor de base de datos trate la entrada del usuario estrictamente como datos y jamás como código interpretable.

```python
# Ejemplo en Python / MySQL Connector (Remediación Segura)
cursor = db.cursor()
query = "SELECT * FROM products WHERE id = %s"
cursor.execute(query, (user_input,)) # El parámetro se pasa de forma separada
results = cursor.fetchall()
```

Al utilizar consultas parametrizadas, incluso si `user_input` contiene cargas útiles como `1 AND IF(1=1, SLEEP(5), 0)`, el motor evaluará toda la cadena como el valor literal del `id`, neutralizando por completo el intento de inyección.