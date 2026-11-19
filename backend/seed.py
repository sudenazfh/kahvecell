"""Demo data: 3 plans, 5 Ankara shops with menus, and customer / shop owner / admin test accounts.
Safe to re-run: anything that already exists is skipped.

Run from the backend folder:  .venv\\Scripts\\python.exe seed.py
"""

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Plan, PlanType, Product, Role, Shop, Subscription, User

TEST_PHONE = "5551234567"   # customer
OWNER_PHONE = "5550000001"  # shop owner of the first shop
ADMIN_PHONE = "5550000000"  # admin

PLANS = [
    Plan(type=PlanType.STARTER, name="Starter", price_kurus=8999, monthly_credits=10),
    Plan(type=PlanType.PREMIUM, name="Premium", price_kurus=14999, monthly_credits=20, guest_passes=2),
    Plan(type=PlanType.UNLIMITED, name="Unlimited", price_kurus=24999, monthly_credits=None,
         guest_passes=5, has_priority=True),
]

# (name, description, price in TL) — approximate 2026 Ankara cafe prices.
MENU = {
    "espresso": ("Espresso", "Tek shot, yoğun", 110),
    "turk": ("Türk Kahvesi", "Lokum ile", 120),
    "americano": ("Americano", "Espresso + sıcak su", 140),
    "filtre": ("Filtre Kahve", "Günün çekirdeği", 135),
    "cappuccino": ("Cappuccino", "Bol köpüklü", 165),
    "latte": ("Caffè Latte", "Sütlü, yumuşak", 175),
    "flatwhite": ("Flat White", "Çift shot, ince köpük", 180),
    "mocha": ("Mocha", "Çikolatalı latte", 195),
    "coldbrew": ("Cold Brew", "16 saat soğuk demleme", 185),
}

# Fictional shop names; coordinates are real points in each district.
SHOPS = [
    ("Kızılay Kahve Durağı", "Atatürk Bulvarı, Kızılay, Çankaya/Ankara", 39.9208, 32.8541,
     time(7, 0), time(23, 0), 4.3, ["espresso", "turk", "americano", "cappuccino", "latte"]),
    ("Tunalı Çekirdek", "Tunalı Hilmi Caddesi, Kavaklıdere, Çankaya/Ankara", 39.9036, 32.8601,
     time(8, 0), time(0, 0), 4.7, ["espresso", "flatwhite", "latte", "coldbrew", "mocha", "filtre"]),
    ("Bahçeli 7 Kahvecisi", "7. Cadde, Bahçelievler, Çankaya/Ankara", 39.9220, 32.8235,
     time(8, 0), time(22, 0), 4.5, ["turk", "espresso", "cappuccino", "latte", "mocha"]),
    ("Çayyolu Demlik", "Alacaatlı Caddesi, Çayyolu, Çankaya/Ankara", 39.8853, 32.6896,
     time(7, 30), time(21, 30), 4.1, ["americano", "filtre", "latte", "cappuccino", "coldbrew"]),
    ("Hoşdere Köşe Kahve", "Hoşdere Caddesi, Ayrancı, Çankaya/Ankara", 39.8930, 32.8590,
     time(9, 0), time(20, 0), 4.6, ["espresso", "turk", "flatwhite", "mocha", "filtre"]),
]


def seed() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.query(Plan).first():
            print("Paketler ve dükkânlar zaten var, atlandı.")
        else:
            db.add_all(PLANS)
            for name, address, lat, lng, opens, closes, rating, items in SHOPS:
                shop = Shop(name=name, address=address, latitude=lat, longitude=lng,
                            opens_at=opens, closes_at=closes, rating=rating)
                shop.products = [
                    Product(name=MENU[k][0], description=MENU[k][1], price_kurus=MENU[k][2] * 100)
                    for k in items
                ]
                db.add(shop)
            db.flush()
            print(f"Eklendi: {len(PLANS)} paket, {len(SHOPS)} dükkân, "
                  f"{sum(len(s[-1]) for s in SHOPS)} ürün.")

        existing = set(db.scalars(select(User.phone_number)))

        if TEST_PHONE not in existing:
            user = User(phone_number=TEST_PHONE, full_name="Test Kullanıcı", email="test@kahvecell.local",
                        preferences={"coffee": ["latte", "türk kahvesi"], "allergens": []})
            now = datetime.now(timezone.utc)
            user.subscriptions = [Subscription(plan_type=PlanType.STARTER, remaining_credits=10,
                                               started_at=now, expires_at=now + timedelta(days=30))]
            db.add(user)
            print(f"Eklendi: müşteri {TEST_PHONE} (Starter abonelik).")

        if OWNER_PHONE not in existing:
            owner = User(phone_number=OWNER_PHONE, full_name="Dükkân Sahibi", role=Role.SHOP_OWNER)
            db.add(owner)
            first_shop = db.scalar(select(Shop).where(Shop.name == SHOPS[0][0]))
            if first_shop is not None and first_shop.owner_id is None:
                first_shop.owner = owner
            print(f"Eklendi: dükkân sahibi {OWNER_PHONE} ({SHOPS[0][0]}).")

        if ADMIN_PHONE not in existing:
            db.add(User(phone_number=ADMIN_PHONE, full_name="Admin", role=Role.ADMIN))
            print(f"Eklendi: admin {ADMIN_PHONE}.")

        db.commit()
        print("Tüm hesaplarda OTP: 1234")


if __name__ == "__main__":
    seed()
