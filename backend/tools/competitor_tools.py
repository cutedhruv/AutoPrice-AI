"""Competitor pricing tools - simulates real-time competitor price monitoring"""
import random
from typing import Dict, List
from database.db import get_db_session
from database.models import Product


def get_competitor_price(product_id: int) -> Dict:
    """
    Fetch the current competitor pricing from the database.
    The competitor_price field is the source of truth — it can be updated
    manually via the demo page or via external feeds.
    
    Args:
        product_id: The product ID to check
    
    Returns:
        Dictionary with competitor pricing data
    """
    db = get_db_session()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"error": f"Product {product_id} not found"}

        # Use the stored competitor price as the base (no random drift)
        base_competitor = product.competitor_price

        # Simulate multiple competitors around the base price (very small variance)
        competitors = [
            {
                "name": "Amazon",
                "price": round(base_competitor * random.uniform(0.99, 1.01), 2),
                "in_stock": random.choice([True, True, True, False]),
                "rating": round(random.uniform(4.0, 4.9), 1)
            },
            {
                "name": "Flipkart",
                "price": round(base_competitor * random.uniform(0.995, 1.005), 2),
                "in_stock": True,
                "rating": round(random.uniform(4.0, 4.8), 1)
            },
            {
                "name": "Croma",
                "price": round(base_competitor * random.uniform(1.0, 1.03), 2),
                "in_stock": random.choice([True, True, False]),
                "rating": round(random.uniform(3.8, 4.6), 1)
            }
        ]

        lowest_price = min(c["price"] for c in competitors)
        avg_price = sum(c["price"] for c in competitors) / len(competitors)

        return {
            "product_id": product_id,
            "product_name": product.name,
            "our_price": product.our_price,
            "competitors": competitors,
            "lowest_competitor_price": base_competitor,
            "average_market_price": round(avg_price, 2),
            "price_gap": round(product.our_price - base_competitor, 2),
            "price_gap_percentage": round(((product.our_price - base_competitor) / base_competitor) * 100, 2),
            "market_position": "above" if product.our_price > avg_price else "below"
        }
    finally:
        db.close()


def get_all_competitor_prices() -> List[Dict]:
    """Get competitor prices for all active products"""
    db = get_db_session()
    try:
        products = db.query(Product).filter(Product.is_active == True).all()
        results = []
        for product in products:
            result = get_competitor_price(product.id)
            if "error" not in result:
                results.append(result)
        return results
    finally:
        db.close()


def simulate_demand_change(product_id: int) -> Dict:
    """
    Get current demand metrics for a product with minor simulation variance.
    Does NOT save changes to DB to prevent random walk drift.
    
    Args:
        product_id: The product ID
    
    Returns:
        Current demand metrics with minor simulated variance
    """
    db = get_db_session()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"error": f"Product {product_id} not found"}

        # Return current values with tiny variance (for realism) but don't save
        demand_variance = random.uniform(-0.02, 0.02)
        simulated_demand = max(0.1, min(1.0, product.demand_score + demand_variance))

        return {
            "product_id": product_id,
            "product_name": product.name,
            "demand_score": round(simulated_demand, 2),
            "stock": product.stock,
            "demand_trend": "increasing" if demand_variance > 0 else "decreasing",
            "stock_status": "low" if product.stock < 20 else "normal" if product.stock < 100 else "high"
        }
    finally:
        db.close()
