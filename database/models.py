from sqlalchemy import Column, Integer, BigInteger, String, Boolean, ForeignKey, Numeric, Text, DateTime, func
from sqlalchemy.orm import relationship
from database.database import Base
from sqlalchemy import Column, DateTime, text

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    avatar_url = Column(Text)
    language = Column(String(5), default="ru")
    full_name = Column(String, nullable=True) 
    role = Column(String(20), nullable=False, default="user")
    # user | seller | admin | super_admin
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    age_confirmed = Column(Boolean, default=False)
    broadcast_enabled = Column(Boolean, default=False)

    seller_profile = relationship("Seller", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True)
    name_lv = Column(String(255), nullable=False)  
    name_ru = Column(String(255), nullable=False)

    products = relationship("Product", back_populates="city")
    sellers = relationship("Seller", back_populates="city")
    orders = relationship("Order", back_populates="city")

    
class Seller(Base):
    __tablename__ = "sellers"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    city_id = Column(Integer, ForeignKey("cities.id"))

    user = relationship("User", back_populates="seller_profile")
    city = relationship("City", back_populates="sellers")
    products = relationship("Product", back_populates="seller")
    orders = relationship("Order", back_populates="seller")

    is_active = Column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"))
    seller_id = Column(Integer, ForeignKey("sellers.id"))
    price = Column(Numeric, nullable=False)
    quantity_tyg = Column(Integer)
    strength_mg = Column(Integer)
    brand = Column(String(255))
    in_stock = Column(Boolean, default=True)
    image_path = Column(String(500)) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    city = relationship("City", back_populates="products")
    seller = relationship("Seller", back_populates="products")
    flavors = relationship("Flavor", back_populates="product")
    orders = relationship("Order", back_populates="product")

class Flavor(Base):
    __tablename__ = "flavors"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))

    product = relationship("Product", back_populates="flavors")
    order_flavors = relationship("OrderFlavor", back_populates="flavor")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)

    order_number = Column(Integer, unique=True, nullable=True) 

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    quantity_tyg = Column(Integer, nullable=False)
    total_price = Column(Numeric, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="pending"
    )
    # pending | confirmed | completed | cancelled

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="orders")
    seller = relationship("Seller", back_populates="orders")
    product = relationship("Product", back_populates="orders")
    city = relationship("City", back_populates="orders")
    flavors = relationship(
        "OrderFlavor",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class OrderFlavor(Base):
    __tablename__ = "order_flavors"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    flavor_id = Column(Integer, ForeignKey("flavors.id"))
    quantity = Column(Integer, default=1)

    order = relationship("Order", back_populates="flavors")
    flavor = relationship("Flavor")

class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    response = Column(Text)
    responded_at = Column(DateTime(timezone=True))
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)


    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("timezone('Europe/Riga', now())")
    )


    user = relationship("User", back_populates="feedbacks")