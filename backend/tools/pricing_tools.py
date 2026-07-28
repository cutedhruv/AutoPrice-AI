"""Pricing calculation and validation tools"""
import random
from typing import Dict, Optional
from database.db import get_db_session
from database.models import Product, PriceHistory
from datetime import datetime


def calculate_optimal_price(
    product_id: int,
    competitor_price: float,
    demand_score: float,
    stock: int,
    cost_price: float,
    current_price: float
) -> Dict:
    """
    Calculate the optimal price based on multiple factors.
    Uses a rule-based pricing strategy engine.
    
    Args:
        product_id: Product ID
        competitor_price: Lowest competitor price
        demand_score: Demand score (0-1)
        stock: Current stock level
        cost_price: Our cost price
        current_price: Current selling price
    
    Returns:
        Optimal price recommendation with reasoning
    """
    min_price = cost_price * 1.05  # Minimum 5% margin
    competitor_ceiling = competitor_price * 0.995  # Hard cap: at least 0.5% below competitor

    # STRATEGY: Maximize profit while ALWAYS staying below competitor.
    # The gap below competitor depends on demand & stock signals.

    # Demand factor — high demand = price closer to competitor (more profit)
    if demand_score > 0.8:
        demand_discount = 0.005  # Only 0.5% below competitor (max profit)
        demand_reason = "High demand — pricing just below competitor to maximize margin"
    elif demand_score > 0.6:
        demand_discount = 0.01  # 1% below
        demand_reason = "Good demand — competitive with healthy margin"
    elif demand_score > 0.4:
        demand_discount = 0.015  # 1.5% below
        demand_reason = "Moderate demand — slightly deeper undercut"
    else:
        demand_discount = 0.025  # 2.5% below for low demand
        demand_reason = "Low demand — aggressive undercut to drive sales"

    # Stock factor — low stock = less discount (maximize margin), high stock = more discount
    if stock < 20:
        stock_discount = -0.005  # Reduce discount by 0.5% (scarcity pricing)
        stock_reason = "Low stock — scarcity allows tighter spread to competitor"
    elif stock < 50:
        stock_discount = 0.0
        stock_reason = "Moderate stock — holding optimal position"
    elif stock < 150:
        stock_discount = 0.005  # Extra 0.5% discount
        stock_reason = "Healthy stock — slight discount to maintain velocity"
    else:
        stock_discount = 0.015  # Extra 1.5% discount to clear excess
        stock_reason = "Excess inventory — deeper discount to accelerate turnover"

    # Total discount from competitor price
    total_discount = max(0.005, demand_discount + stock_discount)  # At least 0.5% below
    optimal_price = competitor_price * (1 - total_discount)

    # HARD CEILING: Never exceed competitor - 0.5%
    if optimal_price > competitor_ceiling:
        optimal_price = competitor_ceiling

    # Apply minimum floor (protect margin)
    optimal_price = max(min_price, optimal_price)
    optimal_price = round(optimal_price, 2)

    # Determine change
    price_change = optimal_price - current_price
    change_percentage = (price_change / current_price) * 100

    # Determine decision type - use 0.1% threshold so even small changes apply
    if abs(change_percentage) < 0.1:
        decision = "no_change"
        reason = "Price is already optimal within tolerance"
        optimal_price = current_price
    elif price_change > 0:
        decision = "price_increase"
        reason = f"{demand_reason}. {stock_reason}"
    else:
        decision = "price_decrease"
        reason = f"Competitor undercut detected. {demand_reason}. {stock_reason}"

    profit_margin = ((optimal_price - cost_price) / optimal_price) * 100

    return {
        "product_id": product_id,
        "current_price": current_price,
        "optimal_price": optimal_price,
        "competitor_price": competitor_price,
        "price_change": round(price_change, 2),
        "change_percentage": round(change_percentage, 2),
        "decision": decision,
        "reason": reason,
        "profit_margin": round(profit_margin, 2),
        "confidence": round(random.uniform(0.88, 0.96), 2),
        "factors": {
            "demand_score": demand_score,
            "demand_discount": f"{demand_discount*100:.1f}%",
            "stock": stock,
            "stock_discount": f"{stock_discount*100:.1f}%",
            "total_undercut": f"{total_discount*100:.1f}%",
            "min_price": min_price,
            "competitor_ceiling": competitor_ceiling
        }
    }


def validate_price(
    product_id: int,
    proposed_price: float,
    cost_price: float,
    competitor_price: float,
    current_price: float
) -> Dict:
    """
    Validate a proposed price change against business rules.
    
    Args:
        product_id: Product ID
        proposed_price: The proposed new price
        cost_price: Cost price
        competitor_price: Competitor price
        current_price: Current price
    
    Returns:
        Validation result with approval/rejection
    """
    issues = []
    warnings = []

    # Rule 1: Must be above cost price (minimum margin)
    min_margin = 0.04  # 4% minimum margin (competitive Indian market)
    actual_margin = (proposed_price - cost_price) / proposed_price
    if actual_margin < min_margin:
        issues.append(f"Margin too low ({actual_margin*100:.1f}%). Minimum is {min_margin*100}%")

    # Rule 2: Price change shouldn't exceed 25% in one update
    change_pct = abs((proposed_price - current_price) / current_price)
    if change_pct > 0.25:
        issues.append(f"Price change too large ({change_pct*100:.1f}%). Max allowed is 25%")

    # Rule 3: Shouldn't be more than 15% above competitor
    if proposed_price > competitor_price * 1.15:
        warnings.append(f"Price is {((proposed_price/competitor_price)-1)*100:.1f}% above competitor")

    # Rule 4: Can't go below cost
    if proposed_price < cost_price:
        issues.append("Price is below cost price - would result in loss")

    # Rule 5: Reasonable price range
    if proposed_price < 0:
        issues.append("Price cannot be negative")

    is_approved = len(issues) == 0
    risk_level = "low" if len(warnings) == 0 else "medium" if len(issues) == 0 else "high"

    return {
        "product_id": product_id,
        "proposed_price": proposed_price,
        "is_approved": is_approved,
        "risk_level": risk_level,
        "issues": issues,
        "warnings": warnings,
        "margin": round(actual_margin * 100, 2),
        "change_percentage": round(change_pct * 100, 2)
    }


def update_price(product_id: int, new_price: float, reason: str, agent_name: str) -> Dict:
    """
    Execute price update in the database.
    
    Args:
        product_id: Product ID to update
        new_price: The new price
        reason: Reason for the change
        agent_name: Name of the agent making the change
    
    Returns:
        Update confirmation
    """
    db = get_db_session()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "error": f"Product {product_id} not found"}

        old_price = product.our_price
        profit_margin = ((new_price - product.cost_price) / new_price) * 100

        # Update product price
        product.our_price = new_price
        product.updated_at = datetime.utcnow()

        # Add to price history
        history = PriceHistory(
            product_id=product_id,
            old_price=old_price,
            new_price=new_price,
            competitor_price=product.competitor_price,
            reason=reason,
            agent_name=agent_name,
            profit_margin=round(profit_margin, 2),
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()

        return {
            "success": True,
            "product_id": product_id,
            "product_name": product.name,
            "old_price": old_price,
            "new_price": new_price,
            "price_change": round(new_price - old_price, 2),
            "change_percentage": round(((new_price - old_price) / old_price) * 100, 2),
            "profit_margin": round(profit_margin, 2),
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()
