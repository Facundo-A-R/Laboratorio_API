from pydantic import BaseModel
from datetime import date, time


class ProductCreate(BaseModel):
    name: str
    price: float

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    name: str
    price: float

    class Config:
        from_attributes = True


class SaleCreate(BaseModel):
    date: date
    time: time
    quantity: int
    product_id: int

    class Config:
        from_attributes = True


class SaleResponse(BaseModel):
    id: int
    date: date
    time: time
    quantity: int
    product: ProductResponse
    total_price: float

    class Config:
        from_attributes = True
