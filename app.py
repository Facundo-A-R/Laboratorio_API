from fastapi import FastAPI, status, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from database import Client, db_session, Products, Sales, Carts, Cart_Product
from schema import ProductCreate, SaleCreate, SaleResponse, ProductResponse, CartCreate, CartProductCreate, CartProductAdd, CartProductResponse, ClientCreate
from typing import Optional 
from datetime import date 

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/products", status_code=status.HTTP_200_OK)
async def get_product():
    try:
        products = Products.query.all()
        
        if not products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Products not found")

        response = {"products": products}
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get products: {e}")    

@app.get("/products/filter/name", status_code=status.HTTP_200_OK)
async def filter_products_by_name( 
    # Query(None, description="Nombre del producto a filtrar") recibe 2 parametros. el primero .. es el valor por defecto, y el segundo es la descripción que se mostrará en la documentación de la API. En este caso, el valor por defecto es None, lo que significa que si no se proporciona un valor para el parámetro name, se considerará como no especificado. La descripción indica que este parámetro se utiliza para filtrar los productos por su nombre.
    name: str | None = Query(None, description="Nombre del producto a filtrar"),
    page: int = Query(1, description="Número de página"),
    limit: int =  Query(10, description="Número de página")
    ):

    try:
        query_name = Products.query

        if name is not None:
            query_name = query_name.filter(Products.name.ilike(f"%{name}%"))
        if not query_name:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found with the specified name")

        offset_value = (page - 1) * limit
        products = query_name.order_by(Products.name.asc()).limit(limit).offset(offset_value).all()

        return {
            "page": page,
            "limit": limit,
            "total_results": len(products),
            "products": products
            }
    except HTTPException:
        raise   
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to filter products by name: {e}")
    
@app.get("/products/filter/price", status_code=status.HTTP_200_OK)
async def filter_products_by_price(
    min_price: Optional[float] = Query(None, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, description="Precio máximo"),
    page: int = 1,
    limit: int = 10
    ):

    try:
        query_price = Products.query

        if min_price is not None:
            query_price = query_price.filter(Products.price >= min_price)
        if max_price is not None:
            query_price = query_price.filter(Products.price <= max_price)

        if not query_price:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found within the specified price range")


# offset_value hace que la paginación funcione correctamente, ya que calcula el número de registros que se deben omitir en función de la página actual y el límite de resultados por página. Esto permite que la consulta devuelva solo los registros correspondientes a la página solicitada, en lugar de devolver todos los registros filtrados.
# Ejemplo: Si limit=10 y page=2, offset_value = (2 - 1) * 10 = 10. Esto significa que la consulta omitirá los primeros 10 registros y devolverá los siguientes 10 registros, que corresponden a la página 2.
        offset_value = (page - 1) * limit
        products = query_price.order_by(Products.name.asc()).limit(limit).offset(offset_value).all()

        return {
            "page": page,
            "limit": limit,
            "total_results": len(products),
            "products": products
            }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error al filtrar los productos: {e}"
        )


@app.get("/product/{product_id}", status_code=status.HTTP_200_OK)
async def get_product(product_id):
    try:
        product = Products.query.get(product_id)

        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        response = {"product": product}
        
        return response
    
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get product with id {product_id}: {e}")    

# post con un solo producto
@app.post("/product", status_code=status.HTTP_201_CREATED)
async def create_product(product_data: ProductCreate):
    try:
        product = Products.query.filter_by(name=product_data.name).first()

        if product:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product already exists")
        
        product = Products(
            name=product_data.name,
            price=product_data.price
        )

        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)
        
        response = {"product": product}
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to create product: {e}")    

# Post con varios productos
@app.post("/products", status_code=status.HTTP_201_CREATED)
async def create_products(products_data: list[ProductCreate]):
    try:
        products = []
        for product_data in products_data:
            product = Products.query.filter_by(name=product_data.name).first()

            if product:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Product {product_data.name} already exists")
            
            product = Products(
                name=product_data.name,
                price=product_data.price
            )

            db_session.add(product)
            db_session.commit()
            db_session.refresh(product)
            products.append(product)
        
        response = {"products": products}
        return [
                    {
                        "id": product.id,
                        "name": product.name,
                        "price": product.price,
                    }
                    for product in products
                ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to create products: {e}")

# put de un producto   
@app.put("/product/{product_id}", status_code=status.HTTP_200_OK)
async def update_product(product_id, product_data: ProductCreate):
    try:
        product = Products.query.get(product_id)

        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        product.name = product_data.name or product.name
        product.price = product_data.price or product.price

        db_session.commit()
        db_session.refresh(product)

        return {"product modified": product}
    
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to update product with id {product_id}: {e}")

# No se debe permitir eliminar un producto que se encuentre registrado en algún carrito
@app.delete("/product/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id):
    try:
        product = Products.query.get(product_id)

        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        # Check if the product is associated with any cart
        cart_product = Cart_Product.query.filter_by(product_id=product.id).first()
        if cart_product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete product associated with a cart")
        
        db_session.delete(product)
        db_session.commit()

        return {"message": "Product deleted successfully", "product": product}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to delete product with id {product_id}: {e}")

## ********* VENTAS ******************************************************************************

# Función para formatear la respuesta de una venta
def sale_response(sale: Sales) -> dict:
    total_price = sum(
        cart_product.product.price * cart_product.quantity
        for cart_product in sale.cart.cart_product
    )
    return {
        "id": sale.id,
        "date": sale.date,
        "time": sale.time,
        "cart_id": sale.cart_id,
        "client_id": sale.client_id,
        "total_price": total_price,
    }

# get todas las ventas
@app.get("/sales", status_code=status.HTTP_200_OK, response_model=list[SaleResponse])
async def get_sales():
    try:
        sales = Sales.query.all()
        if not sales:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales not found")
        
        return [sale_response(sale) for sale in sales]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get sales: {e}")    

# get filter date
@app.get("/sales/filter/date", status_code=status.HTTP_200_OK)
async def get_sale_filter_date (
        date_start: date | None = Query(None, description="Fecha Minina de la venta a filtrar"),
        date_finish: date | None = Query(None, description= "Fecha Maxima de la venta a filtrar"),
        page: int = 1,
        limit: int = 5
):
    try:
        query_date = Sales.query

        if date_start is not None and date_finish is not None:
            # between incluye los valores de date_start y date_finish, es decir, si la fecha de la venta es igual a date_start o date_finish, también se incluirá en los resultados.
            query_date = query_date.filter(Sales.date.between(date_start, date_finish))
        else:
            if date_start is not None:
                query_date = query_date.filter(Sales.date >= date_start)
            if date_finish is not None:
                query_date = query_date.filter(Sales.date <= date_finish)


        if not query_date:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sales found within the specified date range")

        # productos a ignorar en la paginacion
        offset_value = (page - 1) * limit
        sales = query_date.order_by(Sales.date.asc()).limit(limit).offset(offset_value).all()

        return {
            "page": page,
            "limit": limit,
            "total_results": len(sales),
            "sales": [sale_response(sale) for sale in sales]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to filter sales by date: {e}")

# get una venta por id
@app.get("/sales/{sale_id}", status_code=status.HTTP_200_OK)
async def get_sale(sale_id):
    try:
        sale = Sales.query.get(sale_id)

        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        
        return sale_response(sale)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get sale with id {sale_id}: {e}")    

# crear una venta
@app.post("/sale", status_code=status.HTTP_201_CREATED, response_model=SaleResponse)
async def create_sale(sale_data: SaleCreate):
    try:
        cart = Carts.query.get(sale_data.cart_id)
        client = Client.query.get(sale_data.client_id) if sale_data.client_id else None

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        if cart.state == 'cerrado':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create sale for a closed cart")
        if Sales.query.filter_by(cart_id=cart.id).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cart is already associated with a sale"
            )

        sale = Sales(
            date=sale_data.date,
            time=sale_data.time,
            client_id=client.id if client else None,
            cart_id=cart.id
        )

        cart.state = 'cerrado'
        db_session.add(sale)
        db_session.commit()
        db_session.refresh(sale)
        db_session.refresh(cart)

        return sale_response(sale)
    
    except HTTPException:
        raise
    except IntegrityError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cart is already associated with a sale"
        )
    except Exception as e:
        db_session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to create sale: {e}")   
     
# primero debe desvincularse mediante POST /ventas/{id}/carrito, y su estado debe permanecer "cerrado".
@app.post("/sales/{sale_id}/cart", status_code=status.HTTP_200_OK)
async def assign_cart_to_sale(sale_id, cart_data: CartCreate):
    try:
        sale = Sales.query.get(sale_id)

        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

        cart = Carts.query.get(cart_data.id)

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        
        existing_sale = Sales.query.filter_by(cart_id=cart.id).first()

        if existing_sale and existing_sale.id != sale_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is already associated with another sale")
        
        sale.cart_id = cart.id
        cart.state = "cerrado"

        db_session.commit()
        db_session.refresh(sale)
        db_session.refresh(cart)

        return {"message": "Cart assigned to sale successfully", "sale": sale}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to assign cart to sale with id {sale_id}: {e}")

# put una venta con validaciones: no se puede cambiar el carrito a uno que ya esté asociado a otra venta, y no se puede cambiar el carrito a uno que esté cerrado.
@app.put("/sales/{sale_id}", status_code=status.HTTP_200_OK)
async def update_sale(sale_id, sale_data: SaleCreate):
    try:
        sale = Sales.query.get(sale_id)

        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

        cart = Carts.query.get(sale_data.cart_id)

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

        existing_sale = Sales.query.filter(
            Sales.cart_id == sale_data.cart_id,
            Sales.id != sale.id,
        ).first()

        if existing_sale:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cart is already associated with another sale",
            )

        sale.date = sale_data.date
        sale.time = sale_data.time
        sale.cart_id = sale_data.cart_id

        db_session.commit()
        db_session.refresh(sale)

        return sale_response(sale)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to update sale with id {sale_id}: {e}")

# borrar una venta
@app.delete("/sale/{sale_id}", status_code=status.HTTP_200_OK)
async def delete_sale(sale_id):
    try:
        sale = Sales.query.get(sale_id)

        db_session.delete(sale)   
        db_session.commit()

        return {"message": "Sale deleted successfully", "sale": sale}
    
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to delete sale with id {sale_id}: {e}") 
      


# *********************************** Cart ********************************************************************
# get todos los carritos
@app.get("/carts", status_code=status.HTTP_200_OK)
async def get_carts():
    try:
        carts = Carts.query.all()

        if not carts:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carts not found")
        
        return carts
    
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get carts: {e}")
    
# get de un carrito por id
@app.get("/cart/{cart_id}", status_code=status.HTTP_200_OK)
async def get_cart(cart_id):
    try:
        cart = Carts.query.get(cart_id)   

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")         
        
        return cart
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get cart with id {cart_id}: {e}")

# post de un carrito
@app.post("/cart", status_code=status.HTTP_201_CREATED)
async def create_cart(cart_data: CartCreate):
    try:
        cart = Carts(
            date=cart_data.date,
            state=cart_data.state
        )

        if cart.state.lower() not in ['abierto', 'cerrado']:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cart state. Must be 'abierto' or 'cerrado'.")

        db_session.add(cart)
        db_session.commit()
        db_session.refresh(cart)

        return cart
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to create cart: {e}")

# agregar un producto a un carrito
@app.post("/cart/{cart_id}/product", status_code=status.HTTP_200_OK)
async def add_product_to_cart(cart_id: int, product_data: CartProductAdd):
    try:
        cart = Carts.query.get(cart_id)
        product = Products.query.get(product_data.product_id)

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if cart.state.lower() != 'abierto':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add product to a closed cart")
        if product_data.quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be greater than zero")

        # Check if the cart is associated with a sale
        sale = Sales.query.filter_by(cart_id=cart.id).first()
        if sale:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add product to a cart associated with a sale")

        cart_product = Cart_Product.query.filter_by(cart_id=cart.id, product_id=product_data.product_id).first()

        if cart_product:
            cart_product.quantity += product_data.quantity
        else:

            cart_product = Cart_Product(
                cart_id=cart.id,
                product_id=product_data.product_id,
                quantity=product_data.quantity
            )

            db_session.add(cart_product)

        db_session.commit()
        db_session.refresh(cart_product)

        return {"message": "Product added to cart successfully", "cart_product": cart_product}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to add product to cart with id {cart_id}: {e}")

#Un carrito que esté asociado a una venta no puede ser modificado (no admite PUT, ni agregar o quitar productos, ni volver a pasar a estado "abierto") ni eliminado; primero debe desvincularse mediante POST /ventas/{id}/carrito, y su estado debe permanecer "cerrado".
@app.put("/cart/{cart_id}", status_code=status.HTTP_200_OK)
async def update_cart(cart_id, cart_data: CartCreate):
    try:
        cart = Carts.query.get(cart_id)

        cart.date = cart_data.date or cart.date
        cart.state = cart_data.state or cart.state
 
        # Check if the cart is associated with a sale
        sale = Sales.query.filter_by(cart_id=cart.id).first()
        if sale:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot modify cart associated with a sale")

        db_session.commit()
        db_session.refresh(cart)

        return cart
    except HTTPException:
        raise   
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to update cart with id {cart_id}: {e}")

# delete de un carrito con validaciones: no se puede eliminar un carrito que esté asociado a una venta.
@app.delete("/cart/{cart_id}", status_code=status.HTTP_200_OK)
async def delete_cart(cart_id):
    try:
        cart = Carts.query.get(cart_id)

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

        # Check if the cart is associated with a sale
        sale = Sales.query.filter_by(cart_id=cart.id).first()
        if sale:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete cart associated with a sale")

        # Delete associated cart_product records
        Cart_Product.query.filter_by(cart_id=cart.id).delete()

        db_session.delete(cart)
        db_session.commit()

        return {"message": "Cart deleted successfully", "cart": cart}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to delete cart with id {cart_id}: {e}")

# elimina un producto de un carrito con validaciones: no se puede eliminar un producto de un carrito que esté asociado a una venta (cerrado), y el carrito debe estar abierto.
@app.delete("/cart/{cart_id}/products/{product_id}", status_code=status.HTTP_200_OK)
async def remove_product_from_cart(cart_id, product_id):
    try:
        cart = Carts.query.get(cart_id)
        product = Products.query.get(product_id)

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if cart.state.lower() != 'abierto':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove products from a closed cart")
        
        # Check if the cart is associated with a sale
        sale = Sales.query.filter_by(cart_id=cart.id).first()
        if sale:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove products from a cart associated with a sale")

        cart_product = Cart_Product.query.filter_by(cart_id=cart.id, product_id=product.id).first()

        if not cart_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in the cart")

        db_session.delete(cart_product)
        db_session.commit()

        return {"message": "Product removed from cart successfully", "cart_product": cart_product}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to remove product from cart with id {cart_id}: {e}")

# *************************************** Cart_Product ******************************************************

# get todos los cart_products
@app.get("/carts_products", status_code=status.HTTP_200_OK, response_model=list[CartProductResponse])
async def get_cart_products():
    try:
        cart_products = Cart_Product.query.all()

        if not cart_products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart products not found")
        
        return cart_products
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get cart products: {e}")

# get un cart_product por id 
@app.get("/cart_products/{cart_product_id}", status_code=status.HTTP_200_OK)
async def get_cart_product(cart_product_id):
    try:
        cart_product = Cart_Product.query.get(cart_product_id)

        if not cart_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart product not found")
        
        return cart_product
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get cart product with id {cart_product_id}: {e}")

# post de un cart_product con validaciones: no se puede agregar un producto a un carrito que esté asociado a una venta (cerrado), y el carrito debe estar abierto.
@app.post("/cart_products", status_code=status.HTTP_201_CREATED, response_model=SaleResponse)
async def create_cart_product(cart_product_data: CartProductCreate):
    try:
        cart = Carts.query.get(cart_product_data.cart_id)
        product = Products.query.get(cart_product_data.product_id)

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        cart_product = Cart_Product(
            cart_id=cart_product_data.cart_id,
            product_id=cart_product_data.product_id,
            quantity=cart_product_data.quantity
        )

        db_session.add(cart_product)
        db_session.commit()
        db_session.refresh(cart_product)

        return cart_product
    
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to create cart product: {e}")

# put de un cart_product por id con validaciones: no se puede modificar un producto de un carrito que esté asociado a una venta (cerrado), y el carrito debe estar abierto.
@app.put("/cart_products/{cart_product_id}", status_code=status.HTTP_200_OK)
async def update_cart_product(cart_product_id, cart_product_data: CartProductCreate):
    try:
        cart_product = Cart_Product.query.get(cart_product_id)
        cart = Carts.query.get(cart_product_data.cart_id)
        product = Products.query.get(cart_product_data.product_id)

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        if not product: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if not cart_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart-product not found")
        
        cart_product.cart_id = cart_product_data.cart_id or cart_product.cart_id
        cart_product.product_id = cart_product_data.product_id or cart_product.product_id
        cart_product.quantity = cart_product_data.quantity or cart_product.quantity

        db_session.commit()
        db_session.refresh(cart_product)

        return cart_product
    
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to update cart product with id {cart_product_id}: {e}")

# delete de un cart_product por id con validaciones: no se puede eliminar un producto de un carrito que esté asociado a una venta (cerrado), y el carrito debe estar abierto.
@app.delete("/cart_products/{cart_product_id}", status_code=status.HTTP_200_OK)
async def delete_cart_product(cart_product_id):
    try:
        cart_product = Cart_Product.query.get(cart_product_id)

        if not cart_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart product not found")
        
        db_session.delete(cart_product)
        db_session.commit()

        return {"message": "Cart product deleted successfully", "cart_product": cart_product}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to delete cart product with id {cart_product_id}: {e}")


## ------ Para el examen ------

@app.get("/clients", status_code=status.HTTP_200_OK)
async def get_clients():
    try:
        clients = Client.query.all()

        if not clients:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clients not found")
        
        return clients
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get clients: {e}")
    
@app.get("/client/{client_id}", status_code=status.HTTP_200_OK)
async def get_client(client_id):
    try:
        client = Client.query.get(client_id)

        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        
        return client
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get client with id {client_id}: {e}")

@app.post("/client", status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate):
    try:
        client = Client(
            name=client_data.name,
            email=client_data.email,
            phone=client_data.phone
        )

        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)

        return client
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to create client: {e}")

@app.put("/client/{client_id}", status_code=status.HTTP_200_OK)
async def update_client(client_id, client_data: ClientCreate):
    try:
        client = Client.query.get(client_id)

        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        client.name = client_data.name or client.name
        client.email = client_data.email or client.email
        client.phone = client_data.phone or client.phone

        db_session.commit()
        db_session.refresh(client)

        return client
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to update client with id {client_id}: {e}")

@app.delete("/client/{client_id}", status_code=status.HTTP_200_OK)
async def delete_client(client_id):
    try:
        client = Client.query.get(client_id)

        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        db_session.delete(client)
        db_session.commit()

        return {"message": "Client deleted successfully", "client": client}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to delete client with id {client_id}: {e}")
