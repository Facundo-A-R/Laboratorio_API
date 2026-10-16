# API de productos y ventas

API desarrollada con FastAPI para el Laboratorio 1 de UNLa. La aplicación utiliza
SQLite como base de datos y SQLAlchemy para el acceso a los datos.

## Instalación

Desde la carpeta raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecución

```powershell
fastapi run
```

La API queda disponible en `http://127.0.0.1:8000`.

Para desarrollo, se puede ejecutar con recarga automática:

```powershell
uvicorn app:app --reload
```

La documentación interactiva está disponible en:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Productos

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/products` | Lista todos los productos |
| GET | `/products/{product_id}` | Obtiene un producto por su ID |
| POST | `/product` | Crea un producto |
| POST | `/products` | Crea varios productos |
| PUT | `/product/{product_id}` | Actualiza un producto |
| DELETE | `/product/{product_id}` | Elimina un producto |

### Crear un producto

`POST /product`

```json
{
  "name": "Teclado",
  "price": 8000
}
```

### Crear varios productos

`POST /products`

El cuerpo debe ser un arreglo JSON:

```json
[
  {
    "name": "Teclado",
    "price": 8000
  },
  {
    "name": "Mouse",
    "price": 4500
  }
]
```

La respuesta contiene la lista de productos creados:

```json
[
  {
    "id": 1,
    "name": "Teclado",
    "price": 8000
  },
  {
    "id": 2,
    "name": "Mouse",
    "price": 4500
  }
]
```

## Ventas

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/sales` | Lista todas las ventas |
| GET | `/sales/{sale_id}` | Obtiene una venta por su ID |
| POST | `/sales` | Registra una venta |
| PUT | `/sales/{sale_id}` | Actualiza una venta |
| DELETE | `/sale/{sale_id}` | Elimina una venta |

### Crear una venta

`POST /sales`

El producto indicado en `product_id` debe existir:

```json
{
  "date": "2026-10-16",
  "time": "12:45",
  "quantity": 5,
  "product_id": 10
}
```

El campo `total_price` se calcula automáticamente con el precio del producto
multiplicado por la cantidad.

### Actualizar una venta

`PUT /sales/{sale_id}`

```json
{
  "date": "2026-10-16",
  "time": "12:45",
  "quantity": 5,
  "product_id": 10
}
```

## Respuestas y errores

- `200 OK`: operación exitosa.
- `201 Created`: recurso creado correctamente.
- `404 Not Found`: producto o venta inexistente.
- `409 Conflict`: se intenta crear un producto con un nombre ya existente.
- `500 Internal Server Error`: error inesperado del servidor.