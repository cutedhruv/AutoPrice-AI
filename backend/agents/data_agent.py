"""Data Agent - Handles internal data retrieval and analysis"""
import logging
from typing import Dict
from agent_framework.agent_operations_bridge import (
    fetch_internal_price_history,
    fetch_internal_product_rows,
)
from tools.explanation_tools import log_agent_activity

logger = logging.getLogger(__name__)


class DataAgent:
    """
    Internal Data Agent
    Responsible for gathering and analyzing internal product data.
    """
    
    name = "Data Agent"

    async def analyze(self, product_id: int, broadcast_fn=None) -> Dict:
        """
        Gather internal data for a product.
        
        Args:
            product_id: Product to analyze
            broadcast_fn: Optional callback to broadcast status updates
        
        Returns:
            Internal data analysis
        """
        try:
            log_agent_activity(
                self.name,
                "Retrieving product data",
                f"Loading internal metrics for product #{product_id}",
                "running",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "running",
                    "step": "Analyzing internal data",
                    "product_id": product_id
                })

            # Get product data (LangChain → SK → tools)
            products = await fetch_internal_product_rows(product_id)
            if not products:
                return {"success": False, "error": f"Product {product_id} not found"}

            product = products[0]

            # Get price history
            history = await fetch_internal_price_history(product_id, limit=10)

            # Calculate trends
            if len(history) >= 2:
                recent_prices = [h["new_price"] for h in history[:5]]
                avg_recent = sum(recent_prices) / len(recent_prices)
                price_trend = "increasing" if avg_recent > product["our_price"] * 0.99 else "decreasing"
            else:
                price_trend = "stable"

            result = {
                "success": True,
                "product": product,
                "history_count": len(history),
                "price_trend": price_trend,
                "current_margin": product["profit_margin"],
                "stock_level": product["stock"],
                "demand_score": product["demand_score"]
            }

            log_agent_activity(
                self.name,
                "Data analysis complete",
                f"Margin: {product['profit_margin']:.1f}%, Stock: {product['stock']}, Trend: {price_trend}",
                "completed",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "completed",
                    "step": "Internal data analyzed",
                    "product_id": product_id,
                    "result": {
                        "margin": product["profit_margin"],
                        "stock": product["stock"],
                        "trend": price_trend
                    }
                })

            return result

        except Exception as e:
            logger.error(f"Data Agent error for product {product_id}: {e}")
            log_agent_activity(self.name, "Error", str(e), "error", product_id)
            return {"success": False, "error": str(e)}
