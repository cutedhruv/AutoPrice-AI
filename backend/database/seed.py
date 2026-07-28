"""Seed database with demo products"""
from database.models import Product, PriceHistory, AgentLog
from database.db import get_db_session, init_db
from datetime import datetime, timedelta
import random


DEMO_PRODUCTS = [
    {
        "name": "Apple MacBook Air M2",
        "category": "Laptops",
        "description": "13.6-inch Liquid Retina Display, 8GB RAM, 256GB SSD, Apple M2 Chip",
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400",
        "our_price": 94990,
        "cost_price": 78000,
        "competitor_price": 92999,
        "stock": 45,
        "demand_score": 0.85,
        "rating": 4.7,
        "reviews_count": 2340,
        "brand": "Apple"
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "category": "Smartphones",
        "description": "6.8-inch Dynamic AMOLED, 12GB RAM, 256GB, Snapdragon 8 Gen 3",
        "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400",
        "our_price": 129999,
        "cost_price": 98000,
        "competitor_price": 127999,
        "stock": 120,
        "demand_score": 0.92,
        "rating": 4.5,
        "reviews_count": 5670,
        "brand": "Samsung"
    },
    {
        "name": "Sony WH-1000XM5 Headphones",
        "category": "Audio",
        "description": "Industry Leading Noise Cancelling, 30hr Battery, Hi-Res Audio",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
        "our_price": 26990,
        "cost_price": 18000,
        "competitor_price": 25990,
        "stock": 200,
        "demand_score": 0.78,
        "rating": 4.6,
        "reviews_count": 8920,
        "brand": "Sony"
    },
    {
        "name": "Dell XPS 15 Laptop",
        "category": "Laptops",
        "description": "15.6-inch 4K OLED, Intel i7-13700H, 16GB RAM, 512GB SSD",
        "image_url": "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400",
        "our_price": 159990,
        "cost_price": 125000,
        "competitor_price": 156990,
        "stock": 30,
        "demand_score": 0.72,
        "rating": 4.4,
        "reviews_count": 1560,
        "brand": "Dell"
    },
    {
        "name": "iPhone 15 Pro Max",
        "category": "Smartphones",
        "description": "6.7-inch Super Retina XDR, A17 Pro, 256GB, Titanium Design",
        "image_url": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400",
        "our_price": 159900,
        "cost_price": 128000,
        "competitor_price": 157900,
        "stock": 85,
        "demand_score": 0.95,
        "rating": 4.8,
        "reviews_count": 12400,
        "brand": "Apple"
    },
    {
        "name": "LG 55-inch C3 OLED TV",
        "category": "Television",
        "description": "55-inch 4K OLED evo, α9 Gen6 AI Processor, Dolby Vision & Atmos",
        "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400",
        "our_price": 139990,
        "cost_price": 105000,
        "competitor_price": 136990,
        "stock": 25,
        "demand_score": 0.65,
        "rating": 4.6,
        "reviews_count": 3200,
        "brand": "LG"
    },
    {
        "name": "iPad Air M1 (5th Gen)",
        "category": "Tablets",
        "description": "10.9-inch Liquid Retina, M1 Chip, 64GB, Wi-Fi, All-day Battery",
        "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400",
        "our_price": 54990,
        "cost_price": 42000,
        "competitor_price": 53490,
        "stock": 150,
        "demand_score": 0.80,
        "rating": 4.7,
        "reviews_count": 4500,
        "brand": "Apple"
    },
    {
        "name": "Dyson V15 Detect Vacuum",
        "category": "Home Appliances",
        "description": "Laser Slim Fluffy Cleaner Head, LCD Screen, 60min Runtime",
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400",
        "our_price": 62990,
        "cost_price": 48000,
        "competitor_price": 61490,
        "stock": 60,
        "demand_score": 0.58,
        "rating": 4.3,
        "reviews_count": 890,
        "brand": "Dyson"
    },
    {
        "name": "Nike Air Jordan 1 Retro",
        "category": "Footwear",
        "description": "Classic High-Top, Genuine Leather, Iconic Colorway, Men's Size",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        "our_price": 14995,
        "cost_price": 8500,
        "competitor_price": 14495,
        "stock": 300,
        "demand_score": 0.88,
        "rating": 4.5,
        "reviews_count": 6700,
        "brand": "Nike"
    },
    {
        "name": "Canon EOS R6 Mark II",
        "category": "Cameras",
        "description": "24.2MP Full Frame Mirrorless, 4K 60fps, IBIS, Dual Card Slots",
        "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400",
        "our_price": 215990,
        "cost_price": 175000,
        "competitor_price": 212990,
        "stock": 15,
        "demand_score": 0.55,
        "rating": 4.8,
        "reviews_count": 920,
        "brand": "Canon"
    }
]


def seed_database():
    """Seed the database with demo data"""
    init_db()
    db = get_db_session()

    # Check if data already exists
    existing = db.query(Product).first()
    if existing:
        print("Database already seeded. Skipping...")
        db.close()
        return

    # Add products
    for product_data in DEMO_PRODUCTS:
        product = Product(**product_data)
        db.add(product)

    db.commit()

    # Add some price history for each product
    products = db.query(Product).all()
    for product in products:
        for i in range(10):
            days_ago = 10 - i
            price_variation = random.uniform(-0.05, 0.05)
            competitor_variation = random.uniform(-0.03, 0.03)

            history = PriceHistory(
                product_id=product.id,
                old_price=product.our_price * (1 + price_variation),
                new_price=product.our_price * (1 + price_variation * 0.5),
                competitor_price=product.competitor_price * (1 + competitor_variation),
                reason="Market adjustment" if i % 2 == 0 else "Competitor price change",
                agent_name="Pricing Agent",
                profit_margin=round(random.uniform(12, 28), 1),
                timestamp=datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
            )
            db.add(history)

    # Add some agent logs
    agent_names = ["Orchestrator", "Market Agent", "Data Agent", "Pricing Agent", "Risk Agent", "Execution Agent"]
    actions = [
        "Initiated pricing cycle",
        "Fetched competitor prices",
        "Analyzed demand metrics",
        "Calculated optimal price",
        "Validated price boundaries",
        "Updated product price"
    ]

    for i in range(20):
        log = AgentLog(
            agent_name=agent_names[i % len(agent_names)],
            action=actions[i % len(actions)],
            details=f"Processing product batch #{i+1}",
            status="completed",
            product_id=random.choice(products).id,
            timestamp=datetime.utcnow() - timedelta(minutes=random.randint(1, 120))
        )
        db.add(log)

    db.commit()
    db.close()
    print("Database seeded successfully with demo data!")


if __name__ == "__main__":
    seed_database()
