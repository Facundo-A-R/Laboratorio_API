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
    cart_id: int

    class Config:
        from_attributes = True


class SaleResponse(BaseModel):
    id: int
    date: date
    time: time
    cart_id: int
    total_price: float

    class Config:
        from_attributes = True

class CartCreate(BaseModel):
    date: date
    state: str

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    date: date
    state: str

    class Config:
        from_attributes = True

class CartProductCreate(BaseModel):
    cart_id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True

class CartProductResponse(BaseModel):
    id: int
    cart_id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True
