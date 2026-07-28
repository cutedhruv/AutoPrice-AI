"""Product data tools"""
from database.db import get_db_session
from database.models import Product, PriceHistory
from datetime import datetime
from typing import Optional, Dict, List


def get_product_data(product_id: Optional[int] = None) -> List[Dict]:
    """
    Fetch product data from the database.
    
    Args:
        product_id: Optional specific product ID. If None, returns all active products.
    
    Returns:
        List of product dictionaries with all relevant pricing data.
    """
    db = get_db_session()
    try:
        if product_id:
            products = db.query(Product).filter(Product.id == product_id, Product.is_active == True).all()
        else:
            products = db.query(Product).filter(Product.is_active == True).all()

        result = []
        for p in products:
            profit_margin = ((p.our_price - p.cost_price) / p.our_price) * 100
            price_diff = p.our_price - p.competitor_price
            price_diff_pct = (price_diff / p.competitor_price) * 100

            result.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "description": p.description,
                "image_url": p.image_url,
                "our_price": p.our_price,
                "cost_price": p.cost_price,
                "competitor_price": p.competitor_price,
                "stock": p.stock,
                "demand_score": p.demand_score,
                "rating": p.rating,
                "reviews_count": p.reviews_count,
                "brand": p.brand,
                "profit_margin": round(profit_margin, 2),
                "price_difference": round(price_diff, 2),
                "price_diff_percentage": round(price_diff_pct, 2),
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            })

        return result
    finally:
        db.close()


def get_product_by_id(product_id: int) -> Optional[Dict]:
    """Get a single product by ID"""
    products = get_product_data(product_id)
    return products[0] if products else None


def get_price_history(product_id: int, limit: int = 20) -> List[Dict]:
    """
    Get price history for a product.
    
    Args:
        product_id: The product ID
        limit: Maximum number of records
    
    Returns:
        List of price history records
    """
    db = get_db_session()
    try:
        history = db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id
        ).order_by(PriceHistory.timestamp.desc()).limit(limit).all()

        return [{
            "id": h.id,
            "product_id": h.product_id,
            "old_price": h.old_price,
            "new_price": h.new_price,
            "competitor_price": h.competitor_price,
            "reason": h.reason,
            "agent_name": h.agent_name,
            "profit_margin": h.profit_margin,
            "timestamp": h.timestamp.isoformat()
        } for h in history]
    finally:
        db.close()
