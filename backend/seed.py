"""One-time demo data: 3 plans, 5 Ankara shops with menus, 1 test user with a Starter subscription.

Run from the backend folder:  .venv\\Scripts\\python.exe seed.py
"""

from datetime import datetime, time, timedelta, timezone

from app.database import Base, SessionLocal, engine
from app.models import Plan, PlanType, Product, Shop, Subscription, User

TEST_PHONE = "5551234567"

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
            print("Veri zaten var, hiçbir şey eklenmedi.")
            return

        db.add_all(PLANS)

        for name, address, lat, lng, opens, closes, rating, items in SHOPS:
            shop = Shop(name=name, address=address, latitude=lat, longitude=lng,
                        opens_at=opens, closes_at=closes, rating=rating)
            shop.products = [
                Product(name=MENU[k][0], description=MENU[k][1], price_kurus=MENU[k][2] * 100)
                for k in items
            ]
            db.add(shop)

        user = User(phone_number=TEST_PHONE, full_name="Test Kullanıcı", email="test@kahvecell.local",
                    preferences={"coffee": ["latte", "türk kahvesi"], "allergens": []})
        now = datetime.now(timezone.utc)
        user.subscriptions = [Subscription(plan_type=PlanType.STARTER, remaining_credits=10,
                                           started_at=now, expires_at=now + timedelta(days=30))]
        db.add(user)

        db.commit()
        print(f"Eklendi: {len(PLANS)} paket, {len(SHOPS)} dükkân, "
              f"{sum(len(s[-1]) for s in SHOPS)} ürün, test kullanıcısı {TEST_PHONE} (OTP: 1234).")


if __name__ == "__main__":
    seed()
