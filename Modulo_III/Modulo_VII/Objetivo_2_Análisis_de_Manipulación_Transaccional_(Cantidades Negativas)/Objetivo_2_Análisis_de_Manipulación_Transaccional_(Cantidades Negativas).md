# Objetivo 2: Análisis de Manipulación Transaccional (Cantidades Negativas)

## 1. Resumen del Escenario

En aplicaciones de comercio electrónico, los flujos de trabajo transaccionales dependen de la integridad de los datos transmitidos entre el cliente y el servidor. Un fallo común en la fase de diseño e implementación de la lógica de negocio ocurre cuando la aplicación permite al usuario manipular el parámetro de cantidad de un producto en la solicitud HTTP (por ejemplo, cambiando la cantidad solicitada de $1$ a $-5$).

Si el servidor backend procesa este valor sin validación, el cálculo matemático del subtotal resulta en un número negativo:

$$
Subtotal = Precio \times Cantidad
$$

Donde si $Precio > 0$ y $Cantidad < 0$, entonces $Subtotal < 0$. Al acumular subtotales negativos en el total general del carrito de compras, la transacción final puede resultar en un saldo a favor del usuario o en la deducción arbitraria del costo total del pedido.

## 2. Análisis de Causa Raíz

Esta vulnerabilidad pertenece a la categoría de **Fallas en la Lógica de Negocio (Business Logic Flaws)** y **Manipulación de Parámetros (Parameter Tampering)**. Ocurre debido a los siguientes factores técnicos principales:

### A. Confianza Implícita en el Cliente (Front-end Control Bypass)

La aplicación suele implementar validaciones únicamente en la interfaz de usuario (HTML5 `min="1"`, reglas de JavaScript en el navegador). Dado que el atacante puede interceptar y modificar la petición HTTP con herramientas como *Burp Suite* o *OWASP ZAP*, cualquier validación realizada exclusivamente en el cliente es completamente inútil desde la perspectiva de la seguridad.

### B. Ausencia de Sanitización y Validación de Tipos en el Backend

El endpoint receptivo en el servidor (por ejemplo, `POST /api/cart/add` o `PUT /api/cart/update`) no verifica los dominios numéricos permitidos antes de realizar operaciones matemáticas o persistir los datos en la base de datos.

### C. Lógica de Modificación de Estado Defectuosa

El servidor utiliza la misma ruta y la misma lógica matemática para agregar, reducir o eliminar ítems del carrito:

* Suma/Multiplicación directa del valor entrante sin evaluar el signo algebraico.

* Permisión implícita de valores negativos para simular "devoluciones" o "resta de artículos", en lugar de mantener métodos independientes (como un endpoint `DELETE /api/cart/item` específico para eliminar o reducir).

## 3. Demostración Teórica del Impacto

### Petición Interceptada (Vulnerable)

```
POST /api/cart/item HTTP/1.1
Host: ecommerce.local
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "product_id": 402,
  "quantity": -5
}
```

### Código Vulnerable en Backend (Ejemplo en Node.js / Express)

```
// CÓDIGO VULNERABLE: No valida si la cantidad es un entero positivo
app.post('/api/cart/item', async (req, res) => {
    const { product_id, quantity } = req.body;
    const product = await Product.findById(product_id);

    // Se calcula el subtotal sin validar si quantity <= 0
    const subtotal = product.price * quantity;

    // Se añade al carrito del usuario
    await Cart.addItem({
        userId: req.user.id,
        productId: product_id,
        quantity: quantity,
        subtotal: subtotal
    });

    return res.status(200).json({ message: "Carrito actualizado correctamente" });
});
```

### Consecuencias Secundarias

1. **Fraude Financiero:** Creación de crédito artificial a favor del usuario o reducción indebida del costo total a pagar a $0$.

2. **Inconsistencia de Inventario:** Si el sistema actualiza el stock restando la cantidad vendida ($Stock_{nuevo} = Stock_{actual} - Cantidad$), al restar un número negativo ($Stock_{actual} - (-5)$) el stock aumentará de manera no justificada.

## 4. Guía de Remediación y Validación Estricta

Para mitigar esta vulnerabilidad de forma definitiva, se debe aplicar el principio de **Defensa en Profundidad** y la política de **Zero Trust** sobre los datos provistos por el usuario.

### A. Validación Estricta de Rangos y Tipos (Server-Side)

Cada entrada de usuario debe ser sometida a reglas estrictas antes de ser procesada por la lógica de negocio o la base de datos:

* La cantidad $n$ debe pertenecer al conjunto de los números enteros strictly positivos: $n \in \mathbb{Z}^+ \quad \text{donde} \quad n > 0$.

* Establecer un límite máximo razonable por transacción ($n \le MaxQuantity$).

### B. Separación de Responsabilidades en la Lógica de Negocio

* **Agregar productos:** Usar solo cantidades estrictamente positivas ($n > 0$).

* **Eliminar/Reducir productos:** Crear endpoints dedicados (`DELETE` o `POST` específicos) donde la lógica interna maneje la disminución de forma controlada sin aceptar cantidades negativas enviadas por el usuario.

### C. Implementación de Código Seguro (Ejemplo con Validación en Node.js)

```
const { z } = require('zod');

// 1. Definición del Esquema de Validación Estricto
const cartItemSchema = z.object({
    product_id: z.number().int().positive("El ID de producto debe ser un entero positivo"),
    quantity: z.number().int().min(1, "La cantidad debe ser como mínimo 1").max(99, "La cantidad excede el límite permitido por transacción")
});

app.post('/api/cart/item', async (req, res) => {
    try {
        // 2. Validación de Entrada del Lado del Servidor
        const validatedData = cartItemSchema.parse(req.body);
        const { product_id, quantity } = validatedData;

        // 3. Obtención del precio real desde la Base de Datos (Nunca confiar en precios del cliente)
        const product = await Product.findById(product_id);
        if (!product) {
            return res.status(404).json({ error: "Producto no encontrado" });
        }

        // 4. Cálculo seguro
        const subtotal = product.price * quantity;

        await Cart.addItem({
            userId: req.user.id,
            productId: product_id,
            quantity: quantity,
            subtotal: subtotal
        });

        return res.status(200).json({ message: "Producto añadido con éxito al carrito" });

    } catch (error) {
        if (error instanceof z.ZodError) {
            return res.status(400).json({ error: "Parámetros inválidos", details: error.errors });
        }
        return res.status(500).json({ error: "Error interno del servidor" });
    }
});
```

## 5. Matriz de Verificación Recomendada para Auditar Carritos

| Control de Seguridad | Descripción | Estado Deseado | 
| ----- | ----- | ----- | 
| **Validación del Servidor** | Verificar que $Cantidad \in [1, MaxLimit]$ en todos los endpoints de carrito. | **Obligatorio** | 
| **Fuente del Precio** | El precio debe extraerse directamente de la base de datos y no de la petición HTTP. | **Obligatorio** | 
| **Recálculo del Total** | El total general debe ser la suma calculada en el backend en el momento del *Checkout*. | **Obligatorio** | 
| **Pruebas de Límites** | Automatizar pruebas con valores como $0$, $-1$, $-999999$, $1.5$ (decimales) y cadenas de texto. | **Recomendado** | 
