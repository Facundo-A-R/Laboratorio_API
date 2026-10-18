from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Time, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("sqlite:///database.db")
db_session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class Products(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)

    cart_product = relationship("Cart_Product", back_populates="product")

class Sales(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    cart_id = Column(
        Integer,
        ForeignKey("carts.id"),
        nullable=False,
        unique=True,
    )
    
    cart = relationship("Carts", back_populates="sales")

class Carts(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    state = Column(String(100), nullable=False)

    sales = relationship("Sales", back_populates="cart")
    cart_product = relationship("Cart_Product", back_populates="cart")
    
class Cart_Product(Base):
    __tablename__ = "cart_product"

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    cart = relationship("Carts", back_populates="cart_product")
    product = relationship("Products", back_populates="cart_product")

Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)

