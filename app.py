from fastapi import FastAPI, status, HTTPException
from database import db_session, Products, Sales
from schema import ProductCreate, SaleCreate, SaleResponse

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
        
        response = {"product": product}
        return response
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
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

@app.delete("/product/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id):
    try:
        product = Products.query.get(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        db_session.delete(product)
        db_session.commit()
        return {"message": "Product deleted successfully", "product": product}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to delete product with id {product_id}: {e}")

## ********* VENTAS ******************************************************************************

@app.get("/sales", status_code=status.HTTP_200_OK, response_model=list[SaleResponse])
async def get_sales():
    try:
        sales = Sales.query.all()
        return sales
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get sales: {e}")    
    

@app.get("/sales/{sale_id}", status_code=status.HTTP_200_OK)
async def get_sale(sale_id):
    try:
        sale = Sales.query.get(sale_id)

        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        
        return sale
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get sale with id {sale_id}: {e}")    



@app.post("/sales", status_code=status.HTTP_201_CREATED, response_model=SaleResponse)
async def create_sale(sale_data: SaleCreate):
    try:
        product = Products.query.get(sale_data.product_id)
        
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product does not exist")
        
        sale = Sales(
            date=sale_data.date,
            time=sale_data.time,
            quantity=sale_data.quantity,
            product_id=sale_data.product_id,
            total_price=(product.price * sale_data.quantity)
        )

        db_session.add(sale)
        db_session.commit()
        db_session.refresh(sale)

        return sale
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to create sale: {e}")    

@app.put("/sales/{sale_id}", status_code=status.HTTP_200_OK)
async def update_sale(sale_id, sale_data: SaleCreate):
    try:
        sale = Sales.query.get(sale_id)
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

        product = Products.query.get(sale_data.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product does not exist")

        sale.date = sale_data.date or sale.date
        sale.time = sale_data.time or sale.time
        sale.quantity = sale_data.quantity or sale.quantity
        sale.product_id = sale_data.product_id or sale.product_id
        sale.total_price = product.price * (sale_data.quantity or sale.quantity)

        db_session.commit()
        db_session.refresh(sale)

        return sale

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
      

    
