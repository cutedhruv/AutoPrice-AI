"""Explanation generation and decision logging tools"""
from typing import Dict, List
from datetime import datetime
from database.db import get_db_session
from database.models import Decision, AgentLog
import json


def generate_explanation(
    product_name: str,
    old_price: float,
    new_price: float,
    competitor_price: float,
    demand_score: float,
    stock: int,
    decision_type: str,
    factors: Dict
) -> str:
    """
    Generate a human-readable explanation for a pricing decision.
    
    Args:
        product_name: Name of the product
        old_price: Previous price
        new_price: New price
        competitor_price: Current competitor price
        demand_score: Demand score (0-1)
        stock: Current stock
        decision_type: Type of decision
        factors: Contributing factors
    
    Returns:
        Human-readable explanation string
    """
    change = new_price - old_price
    change_pct = (change / old_price) * 100
    margin = ((new_price - factors.get("min_price", new_price * 0.92) / 1.05 * 1.0) / new_price) * 100 if new_price else 0

    if decision_type == "no_change":
        gap = ((old_price - competitor_price) / competitor_price * 100) if competitor_price else 0
        return (
            f"Price for {product_name} stays at ₹{old_price:,.0f}. "
            f"Already {abs(gap):.1f}% {'below' if gap < 0 else 'above'} competitor (₹{competitor_price:,.0f}). "
            f"Demand: {demand_score:.0%}, Stock: {stock} units. No adjustment needed."
        )

    direction = "increased" if change > 0 else "decreased"

    parts = []

    # Competitive positioning
    price_vs_competitor = ((new_price - competitor_price) / competitor_price) * 100
    if new_price < competitor_price:
        parts.append(f"Positioned {abs(price_vs_competitor):.1f}% below competitor (₹{competitor_price:,.0f}) to win the buy-box")
    elif new_price > competitor_price:
        parts.append(f"Priced {price_vs_competitor:.1f}% above competitor (₹{competitor_price:,.0f}); margin recovery while demand holds")
    else:
        parts.append(f"Matched competitor at ₹{competitor_price:,.0f}")

    # Demand insight
    if demand_score > 0.8:
        parts.append(f"high demand ({demand_score:.0%}) allows tighter spread to competitor")
    elif demand_score > 0.4:
        parts.append(f"moderate demand ({demand_score:.0%}) supports steady pricing")
    else:
        parts.append(f"low demand ({demand_score:.0%}) requires aggressive undercut")

    # Stock insight
    if stock < 20:
        parts.append(f"limited stock ({stock} units) supports price stability")
    elif stock > 150:
        parts.append(f"excess inventory ({stock} units) needs faster turnover")
    else:
        parts.append(f"healthy stock ({stock} units)")

    # Margin
    actual_margin = ((new_price - (factors.get("min_price", new_price * 0.92) / 1.05)) / new_price * 100)
    parts.append(f"projected margin ~{actual_margin:.1f}%")

    explanation = (
        f"{product_name} {direction} by {abs(change_pct):.1f}% "
        f"(₹{old_price:,.0f} → ₹{new_price:,.0f}). "
        + ". ".join(parts) + "."
    )

    return explanation


def log_decision(
    product_id: int,
    product_name: str,
    decision_type: str,
    old_price: float,
    new_price: float,
    competitor_price: float,
    reason: str,
    confidence: float,
    profit_impact: float,
    agent_chain: List[str]
) -> Dict:
    """
    Log a pricing decision to the database.
    
    Args:
        product_id: Product ID
        product_name: Product name
        decision_type: Type of decision
        old_price: Old price
        new_price: New price
        competitor_price: Competitor price
        reason: Explanation
        confidence: Confidence score
        profit_impact: Impact on profit
        agent_chain: List of agents involved
    
    Returns:
        Logged decision details
    """
    db = get_db_session()
    try:
        decision = Decision(
            product_id=product_id,
            product_name=product_name,
            decision_type=decision_type,
            old_price=old_price,
            new_price=new_price,
            competitor_price=competitor_price,
            reason=reason,
            confidence=confidence,
            profit_impact=profit_impact,
            agent_chain=json.dumps(agent_chain),
            timestamp=datetime.utcnow()
        )
        db.add(decision)
        db.commit()

        return {
            "decision_id": decision.id,
            "product_id": product_id,
            "decision_type": decision_type,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


def log_agent_activity(
    agent_name: str,
    action: str,
    details: str = "",
    status: str = "completed",
    product_id: int = None
) -> Dict:
    """
    Log agent activity.
    
    Args:
        agent_name: Name of the agent
        action: Action performed
        details: Additional details
        status: Status (running, completed, error)
        product_id: Related product ID
    
    Returns:
        Log entry details
    """
    db = get_db_session()
    try:
        log = AgentLog(
            agent_name=agent_name,
            action=action,
            details=details,
            status=status,
            product_id=product_id,
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()

        return {
            "log_id": log.id,
            "agent_name": agent_name,
            "action": action,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


def get_recent_decisions(limit: int = 20) -> List[Dict]:
    """Get recent pricing decisions"""
    db = get_db_session()
    try:
        decisions = db.query(Decision).order_by(
            Decision.timestamp.desc()
        ).limit(limit).all()

        return [{
            "id": d.id,
            "product_id": d.product_id,
            "product_name": d.product_name,
            "decision_type": d.decision_type,
            "old_price": d.old_price,
            "new_price": d.new_price,
            "competitor_price": d.competitor_price,
            "reason": d.reason,
            "confidence": d.confidence,
            "profit_impact": d.profit_impact,
            "agent_chain": json.loads(d.agent_chain) if d.agent_chain else [],
            "timestamp": d.timestamp.isoformat()
        } for d in decisions]
    finally:
        db.close()


def get_agent_activity(limit: int = 30) -> List[Dict]:
    """Get recent agent activity logs"""
    db = get_db_session()
    try:
        logs = db.query(AgentLog).order_by(
            AgentLog.timestamp.desc()
        ).limit(limit).all()

        return [{
            "id": l.id,
            "agent_name": l.agent_name,
            "action": l.action,
            "details": l.details,
            "status": l.status,
            "product_id": l.product_id,
            "timestamp": l.timestamp.isoformat()
        } for l in logs]
    finally:
        db.close()
