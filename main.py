from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.database import engine, Base, SessionLocal
from models.user import User, SellerProfile, Category, Product, Order, OrderItem, SellerApplication, ProductVariant
from routers import auth, products, orders, sellers, ai, translation, admin, reviews
from routers import applications
from core.auth import hash_password
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HomeMarket UAE", version="1.0.0", description="Marketplace for home-based businesses in UAE")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads/products", exist_ok=True)
os.makedirs("uploads/logos", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(sellers.router)
app.include_router(ai.router)
app.include_router(translation.router)
app.include_router(reviews.router)
app.include_router(admin.router)
app.include_router(applications.router)

def seed_data():
    db = SessionLocal()
    try:
        if db.query(Category).count() > 0:
            return

        categories = [
            Category(name="Home Cooked Meals", name_ar="وجبات منزلية", icon="🍽️"),
            Category(name="Desserts & Sweets", name_ar="حلويات وسكريات", icon="🍰"),
            Category(name="Baked Goods", name_ar="مخبوزات", icon="🥖"),
            Category(name="Healthy Food", name_ar="طعام صحي", icon="🥗"),
            Category(name="Juices & Drinks", name_ar="عصائر ومشروبات", icon="🥤"),
            Category(name="Handmade Crafts", name_ar="مشغولات يدوية", icon="🎨"),
            Category(name="Beauty & Skincare", name_ar="جمال وعناية بالبشرة", icon="✨"),
            Category(name="Perfumes & Candles", name_ar="عطور وشموع", icon="🕯️"),
        ]
        db.add_all(categories)
        db.flush()

        admin = User(
            email="admin@homemarket.ae",
            full_name="Admin",
            hashed_password=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)

        demo_seller_user = User(
            email="fatima@homemarket.ae",
            full_name="Fatima Al Rashidi",
            phone="+971501234567",
            hashed_password=hash_password("seller123"),
            role="seller",
        )
        db.add(demo_seller_user)
        db.flush()

        demo_seller = SellerProfile(
            user_id=demo_seller_user.id,
            shop_name="Fatima's Kitchen",
            description="Authentic Emirati home-cooked meals made fresh daily. Specializing in Machboos, Harees, and traditional sweets.",
            area="Jumeirah",
            city="Dubai",
            is_approved=True,
            rating=4.8,
            total_orders=142,
        )
        db.add(demo_seller)
        db.flush()

        demo_products = [
            Product(seller_id=demo_seller.id, category_id=categories[0].id, name="Chicken Machboos", description="Traditional spiced rice with tender chicken, slow-cooked with baharat spices.", price=45.0, preparation_time=90, is_available=True),
            Product(seller_id=demo_seller.id, category_id=categories[0].id, name="Beef Harees", description="Slow-cooked wheat and beef porridge, a Ramadan classic.", price=35.0, preparation_time=120, is_available=True),
            Product(seller_id=demo_seller.id, category_id=categories[1].id, name="Luqaimat", description="Golden fried dumplings drizzled with date syrup and sesame.", price=25.0, preparation_time=30, is_available=True),
            Product(seller_id=demo_seller.id, category_id=categories[1].id, name="Balaleet", description="Sweet vermicelli with egg omelette on top — a breakfast favourite.", price=20.0, preparation_time=20, is_available=True),
        ]
        db.add_all(demo_products)
        db.commit()
        print("✅ Seed data created")
    except Exception as e:
        print(f"Seed skipped: {e}")
        db.rollback()
    finally:
        db.close()

@app.on_event("startup")
def startup():
    seed_data()

@app.get("/")
def root():
    return {"message": "HomeMarket UAE API", "docs": "/docs"}

@app.get("/api/categories")
def get_categories(db=__import__('fastapi', fromlist=['Depends']).Depends(__import__('core.database', fromlist=['get_db']).get_db), show_all: bool = False):
    from models.user import Category
    query = db.query(Category)
    if not show_all:
        query = query.filter(Category.is_active == True)
    return query.order_by(Category.sort_order).all()
