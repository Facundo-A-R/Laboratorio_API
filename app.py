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

        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        response = {"product": product}
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get product with id {product_id}: {e}")    


@app.post("/products", status_code=status.HTTP_201_CREATED)
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
    

@app.get("/sales", status_code=status.HTTP_200_OK, response_model=list[SaleResponse])
async def get_sales():
    try:
        sales = Sales.query.all()
        return sales
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while trying to get sales: {e}")    
    

@app.get("/sales/{sale_id}", status_code=status.HTTP_200_OK, response_model=SaleResponse)
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
    
