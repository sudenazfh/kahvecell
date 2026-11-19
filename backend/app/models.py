import enum
import uuid
from datetime import datetime, time, timezone

from sqlalchemy import JSON, CheckConstraint, Enum, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    SHOP_OWNER = "SHOP_OWNER"
    ADMIN = "ADMIN"


class PlanType(str, enum.Enum):
    STARTER = "STARTER"
    PREMIUM = "PREMIUM"
    UNLIMITED = "UNLIMITED"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class Size(str, enum.Enum):
    S = "S"
    M = "M"
    L = "L"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True)
    # Empty until the user completes the profile step after OTP login.
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.CUSTOMER)
    preferences: Mapped[dict | None] = mapped_column(JSON)  # coffee types, allergens
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    shops: Mapped[list["Shop"]] = relationship(back_populates="owner")


class Plan(Base):
    """Package catalogue, so prices live in one row instead of being copied into every subscription."""

    __tablename__ = "plans"

    type: Mapped[PlanType] = mapped_column(Enum(PlanType), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    price_kurus: Mapped[int]  # 89,99 TL -> 8999; integers avoid float rounding on money
    monthly_credits: Mapped[int | None]  # None = unlimited
    guest_passes: Mapped[int] = mapped_column(default=0)
    has_priority: Mapped[bool] = mapped_column(default=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (Index("ix_subscriptions_user_status", "user_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    plan_type: Mapped[PlanType] = mapped_column(ForeignKey("plans.type"))
    remaining_credits: Mapped[int | None]  # None = unlimited plan
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE
    )
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    expires_at: Mapped[datetime]

    user: Mapped[User] = relationship(back_populates="subscriptions")
    plan: Mapped[Plan] = relationship()


class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_shops_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_shops_longitude"),
        Index("ix_shops_lat_lng", "latitude", "longitude"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float]
    longitude: Mapped[float]
    opens_at: Mapped[time]
    closes_at: Mapped[time]
    rating: Mapped[float] = mapped_column(default=0)
    photo_url: Mapped[str | None] = mapped_column(String(500))

    owner: Mapped[User | None] = relationship(back_populates="shops")
    products: Mapped[list["Product"]] = relationship(back_populates="shop")
    orders: Mapped[list["Order"]] = relationship(back_populates="shop")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    shop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shops.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255))
    price_kurus: Mapped[int]  # shown for reference; subscribers pay with one credit
    is_available: Mapped[bool] = mapped_column(default=True)

    shop: Mapped[Shop] = relationship(back_populates="products")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_shop_status", "shop_id", "status"),
        CheckConstraint("extra_shots BETWEEN 0 AND 3", name="ck_orders_extra_shots"),
        CheckConstraint("sugar BETWEEN 0 AND 3", name="ck_orders_sugar"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    shop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shops.id"))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscriptions.id"))
    # ponytail: one drink per order (case flow orders a single coffee); add an order_items table for baskets.
    size: Mapped[Size] = mapped_column(Enum(Size), default=Size.M)
    sugar: Mapped[int] = mapped_column(default=0)  # spoons
    milk: Mapped[str | None] = mapped_column(String(30))  # e.g. "oat", "lactose-free"
    extra_shots: Mapped[int] = mapped_column(default=0)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    qr_signature: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="orders")
    shop: Mapped[Shop] = relationship(back_populates="orders")
    product: Mapped[Product] = relationship()
    subscription: Mapped[Subscription] = relationship()
