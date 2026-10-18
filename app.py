from fastapi import FastAPI, status, HTTPException
from database import db_session, Products, Sales, Carts, Cart_Product
from schema import ProductCreate, SaleCreate, SaleResponse, CartCreate, CartProductCreate, CartProductResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/products", status_code=status.HTTP_200_OK)
async def get_product():
    try:
        products = Products.query.all()
        response = {"products": products}
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get products: {e}")    


@app.get("/products/{product_id}", status_code=status.HTTP_200_OK)
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

@app.post("/products", status_code=status.HTTP_201_CREATED)
# Post con varios productos
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
        "total_price": total_price,
    }


@app.get("/sales", status_code=status.HTTP_200_OK, response_model=list[SaleResponse])
async def get_sales():
    try:
        sales = Sales.query.all()
        return [sale_response(sale) for sale in sales]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get sales: {e}")    

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

@app.post("/sales", status_code=status.HTTP_201_CREATED, response_model=SaleResponse)
async def create_sale(sale_data: SaleCreate):
    try:
        cart = Carts.query.get(sale_data.cart_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        if cart.state == 'cerrado':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create sale for a closed cart")

        sale = Sales(
            date=sale_data.date,
            time=sale_data.time,
            cart_id=sale_data.cart_id
        )

        db_session.add(sale)
        db_session.commit()
        db_session.refresh(sale)

        return sale_response(sale)
    except HTTPException:
        raise
    except Exception as e:
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
      


# *********************************** Cart *******************************************************************************************}

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
    

@app.get("/carts/{cart_id}", status_code=status.HTTP_200_OK)
async def get_cart(cart_id):
    try:
        cart = Carts.query.get(cart_id)   
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")         
        return cart
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get cart with id {cart_id}: {e}")

@app.post("/carts", status_code=status.HTTP_201_CREATED)
async def create_cart(cart_data: CartCreate):
    try:
        cart = Carts(
            date=cart_data.date,
            state=cart_data.state
        )

        db_session.add(cart)
        db_session.commit()
        db_session.refresh(cart)

        return cart
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to create cart: {e}")

@app.post("/carts/{cart_id}/products", status_code=status.HTTP_200_OK)
async def add_product_to_cart(cart_id, product_data: CartProductCreate):
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
                cart_id=cart_id,
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

@app.put("/carts/{cart_id}", status_code=status.HTTP_200_OK)
async def update_cart(cart_id, cart_data: CartCreate):
    try:
        cart = Carts.query.get(cart_id)

        cart.date = cart_data.date or cart.date
        cart.state = cart_data.state or cart.state
        # TODO 
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



@app.delete("/carts/{cart_id}", status_code=status.HTTP_200_OK)
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

@app.delete("/carts/{cart_id}/products/{product_id}", status_code=status.HTTP_200_OK)
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

# *************************************** Cart_Product *******************************************************************************************}
@app.get("/cart_products", status_code=status.HTTP_200_OK)
async def get_cart_products():
    try:
        cart_products = Cart_Product.query.all()
        return cart_products
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart products not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get cart products: {e}")
    
@app.get("/cart_products/{cart_product_id}", status_code=status.HTTP_200_OK)
async def get_cart_product(cart_product_id):
    try:
        cart_product = Cart_Product.query.get(cart_product_id)
        return cart_product
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart product not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get cart product with id {cart_product_id}: {e}")

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



        