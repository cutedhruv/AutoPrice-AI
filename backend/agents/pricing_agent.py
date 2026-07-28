"""Pricing Agent - Makes pricing decisions using LLM intelligence"""
import logging
from typing import Dict
from agent_framework.agent_operations_bridge import (
    fetch_llm_pricing_decision,
    fetch_optimal_price_rule_based,
)
from tools.explanation_tools import log_agent_activity, generate_explanation

logger = logging.getLogger(__name__)


class PricingAgent:
    """
    Pricing Decision Agent (LLM-Powered)
    Uses Groq LLM to analyze competitor pricing and market data,
    then makes intelligent pricing decisions.
    Falls back to rule-based if LLM is unavailable.
    """
    
    name = "Pricing Agent"

    async def decide(self, product_data: Dict, market_data: Dict, broadcast_fn=None) -> Dict:
        """
        Make a pricing decision using LLM analysis.
        
        Args:
            product_data: Internal product data from Data Agent
            market_data: Market data from Market Agent
            broadcast_fn: Optional callback to broadcast status updates
        
        Returns:
            Pricing decision
        """
        try:
            product = product_data["product"]
            product_id = product["id"]

            log_agent_activity(
                self.name,
                "Analyzing with AI",
                f"LLM analyzing pricing for {product['name']}",
                "running",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "running",
                    "step": "AI analyzing pricing strategy",
                    "product_id": product_id
                })

            # Get market data
            competitor_price = market_data["competitor_data"]["lowest_competitor_price"]
            demand_score = market_data["demand_data"].get("demand_score", product["demand_score"])
            stock = market_data["demand_data"].get("stock", product["stock"])
            trends_data = market_data.get("trends_data", {})

            # Try LLM-based decision first (LangChain async tool → direct Groq)
            llm_result = await fetch_llm_pricing_decision(
                product_name=product["name"],
                our_price=product["our_price"],
                cost_price=product["cost_price"],
                competitor_price=competitor_price,
                demand_score=demand_score,
                stock=stock,
                category=product.get("category", "General"),
                brand=product.get("brand", "Unknown"),
                trends_context=trends_data,
            )

            if llm_result:
                # LLM provided a decision
                logger.info(f"LLM decision for {product['name']}: {llm_result['decision']} → ₹{llm_result['new_price']:,.0f}")

                pricing_result = {
                    "product_id": product_id,
                    "current_price": product["our_price"],
                    "optimal_price": llm_result["new_price"],
                    "competitor_price": competitor_price,
                    "price_change": round(llm_result["new_price"] - product["our_price"], 2),
                    "change_percentage": llm_result["change_percentage"],
                    "decision": llm_result["decision"],
                    "reason": llm_result["reason"],
                    "profit_margin": round(((llm_result["new_price"] - product["cost_price"]) / llm_result["new_price"]) * 100, 2),
                    "confidence": llm_result["confidence"],
                    "source": "llm",
                    "factors": {
                        "demand_score": demand_score,
                        "stock": stock,
                        "competitor_price": competitor_price,
                        "min_price": product["cost_price"] * 1.08
                    }
                }

                explanation = f"AI Agent decision for {product['name']}: {llm_result['reason']}"
                pricing_result["explanation"] = explanation

            else:
                # Fallback to rule-based if LLM fails
                logger.warning(f"LLM unavailable for {product['name']}, using rule-based fallback")
                
                pricing_result = await fetch_optimal_price_rule_based(
                    product_id=product_id,
                    competitor_price=competitor_price,
                    demand_score=demand_score,
                    stock=stock,
                    cost_price=product["cost_price"],
                    current_price=product["our_price"],
                )

                explanation = generate_explanation(
                    product_name=product["name"],
                    old_price=product["our_price"],
                    new_price=pricing_result["optimal_price"],
                    competitor_price=competitor_price,
                    demand_score=demand_score,
                    stock=stock,
                    decision_type=pricing_result["decision"],
                    factors=pricing_result["factors"]
                )
                pricing_result["explanation"] = explanation
                pricing_result["source"] = "rule_based"

            log_agent_activity(
                self.name,
                f"Decision: {pricing_result['decision']}",
                f"₹{product['our_price']:,.0f} → ₹{pricing_result['optimal_price']:,.0f} "
                f"({pricing_result['change_percentage']:+.1f}%) [{'AI' if pricing_result.get('source') == 'llm' else 'Rules'}]",
                "completed",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "completed",
                    "step": f"AI Decision: {pricing_result['decision']}",
                    "product_id": product_id,
                    "result": {
                        "decision": pricing_result["decision"],
                        "new_price": pricing_result["optimal_price"],
                        "change": pricing_result["change_percentage"],
                        "source": pricing_result.get("source", "unknown")
                    }
                })

            return {
                "success": True,
                "pricing": pricing_result
            }

        except Exception as e:
            logger.error(f"Pricing Agent error: {e}")
            log_agent_activity(self.name, "Error", str(e), "error")
            return {"success": False, "error": str(e)}
