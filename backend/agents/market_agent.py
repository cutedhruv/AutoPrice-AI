"""Market Agent - Monitors competitor pricing, market conditions, and Google Trends"""
import logging
from typing import Dict, List
from agent_framework.market_framework_bridge import (
    fetch_competitor_data,
    fetch_google_trends,
    fetch_simulated_demand,
)
from tools.explanation_tools import log_agent_activity

logger = logging.getLogger(__name__)


class MarketAgent:
    """
    Market Intelligence Agent
    Responsible for monitoring competitor prices, market dynamics, and Google Trends.
    """
    
    name = "Market Agent"

    async def analyze(self, product_id: int, broadcast_fn=None) -> Dict:
        """
        Analyze market conditions for a product.
        
        Args:
            product_id: Product to analyze
            broadcast_fn: Optional callback to broadcast status updates
        
        Returns:
            Market analysis results
        """
        try:
            # Log activity
            log_agent_activity(
                self.name,
                "Fetching competitor prices",
                f"Scanning market for product #{product_id}",
                "running",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "running",
                    "step": "Fetching competitor prices",
                    "product_id": product_id
                })

            # Competitor data: LangChain tool → Semantic Kernel plugin → direct tools (bridge)
            competitor_data = await fetch_competitor_data(product_id)
            
            if "error" in competitor_data:
                log_agent_activity(self.name, "Error fetching prices", competitor_data["error"], "error", product_id)
                return {"success": False, "error": competitor_data["error"]}

            # Simulate demand changes (LangChain → SK → tools)
            demand_data = await fetch_simulated_demand(product_id)

            # Google Trends — fetch market interest (cached, won't slow pipeline)
            trends_data = {"available": False}
            try:
                product_name = competitor_data.get("product_name", "")
                if product_name:
                    trends_data = await fetch_google_trends(product_name)
                    if trends_data.get("available"):
                        # Boost demand score if Google Trends shows high interest
                        trend_signal = trends_data.get("demand_signal", "unknown")
                        if trend_signal == "high" and demand_data.get("demand_score", 0) < 0.8:
                            demand_data["demand_score"] = min(1.0, demand_data.get("demand_score", 0.5) + 0.1)
                            demand_data["trend_boost"] = True
                        elif trend_signal == "low" and demand_data.get("demand_score", 0) > 0.5:
                            demand_data["demand_score"] = max(0.1, demand_data.get("demand_score", 0.5) - 0.05)
                            demand_data["trend_dampen"] = True
            except Exception as e:
                logger.debug(f"Trends lookup skipped for product #{product_id}: {e}")

            # Log completion
            trends_info = ""
            if trends_data.get("available"):
                trends_info = f", Trends: {trends_data.get('demand_signal', '?')} (interest: {trends_data.get('avg_interest', 0)})"
            log_agent_activity(
                self.name,
                "Market analysis complete",
                f"Lowest competitor: ₹{competitor_data['lowest_competitor_price']:,.0f}, "
                f"Demand: {demand_data.get('demand_score', 'N/A')}{trends_info}",
                "completed",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "completed",
                    "step": "Market analysis complete",
                    "product_id": product_id,
                    "result": {
                        "competitor_price": competitor_data["lowest_competitor_price"],
                        "demand_score": demand_data.get("demand_score")
                    }
                })

            return {
                "success": True,
                "competitor_data": competitor_data,
                "demand_data": demand_data,
                "trends_data": trends_data
            }

        except Exception as e:
            logger.error(f"Market Agent error for product {product_id}: {e}")
            log_agent_activity(self.name, "Error", str(e), "error", product_id)
            return {"success": False, "error": str(e)}
