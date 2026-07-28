"""
Orchestrator Agent - Coordinates all other agents in the pricing pipeline.
Implements the autonomous pricing loop.
"""
import asyncio
import logging
from typing import Dict, Callable, Optional
from config import USE_LANGGRAPH_PIPELINE
from tools.product_tools import get_product_data
from tools.explanation_tools import log_agent_activity
from agents.market_agent import MarketAgent
from agents.data_agent import DataAgent
from agents.pricing_agent import PricingAgent
from agents.risk_agent import RiskAgent
from agents.execution_agent import ExecutionAgent
from agents.memory_agent import MemoryAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Orchestrator Agent
    Coordinates the full pricing pipeline across all specialized agents.
    Runs the autonomous pricing loop.
    """
    
    name = "Orchestrator"

    def __init__(self):
        self.market_agent = MarketAgent()
        self.data_agent = DataAgent()
        self.pricing_agent = PricingAgent()
        self.risk_agent = RiskAgent()
        self.execution_agent = ExecutionAgent()
        self.memory_agent = MemoryAgent()
        self.is_running = False
        self.broadcast_fn: Optional[Callable] = None
        self._pricing_graph_app = None
        if USE_LANGGRAPH_PIPELINE:
            try:
                from agent_framework.pricing_graph import build_pricing_product_graph

                self._pricing_graph_app = build_pricing_product_graph(self)
                logger.info("LangGraph pricing pipeline enabled for single-product processing")
            except Exception as e:
                logger.warning("LangGraph pipeline unavailable — using sequential implementation: %s", e)

        try:
            from agent_framework.kernel_factory import get_shared_kernel

            get_shared_kernel()
        except Exception as e:
            logger.debug("Semantic Kernel lazy init deferred or skipped: %s", e)

    def set_broadcast(self, broadcast_fn: Callable):
        """Set the broadcast function for real-time updates"""
        self.broadcast_fn = broadcast_fn

    async def process_product(self, product_id: int) -> Dict:
        """
        Process a single product through the full agent pipeline.
        
        Pipeline: Market → Data → Pricing → Risk → Execution
        
        Args:
            product_id: Product ID to process
        
        Returns:
            Processing result
        """
        if self._pricing_graph_app is not None:
            try:
                end_state = await self._pricing_graph_app.ainvoke(
                    {
                        "product_id": product_id,
                        "broadcast_fn": self.broadcast_fn,
                    }
                )
                final_out = end_state.get("final_output")
                if isinstance(final_out, dict) and final_out:
                    return final_out
                return {
                    "product_id": product_id,
                    "action": "error",
                    "error": "Incomplete pipeline state",
                }
            except Exception as e:
                logger.exception("LangGraph pipeline failed — falling back to sequential path")
        return await self._process_product_sequential(product_id)

    async def _process_product_sequential(self, product_id: int) -> Dict:
        """Original linear pipeline — kept as a safe fallback."""
        try:
            # Step 1: Market Analysis
            market_result = await self.market_agent.analyze(product_id, self.broadcast_fn)
            if not market_result.get("success"):
                return {"product_id": product_id, "action": "error", "error": market_result.get("error")}

            # Step 2: Internal Data
            data_result = await self.data_agent.analyze(product_id, self.broadcast_fn)
            if not data_result.get("success"):
                return {"product_id": product_id, "action": "error", "error": data_result.get("error")}

            # Step 3: Pricing Decision
            pricing_result = await self.pricing_agent.decide(data_result, market_result, self.broadcast_fn)
            if not pricing_result.get("success"):
                return {"product_id": product_id, "action": "error", "error": pricing_result.get("error")}

            # Step 4: Risk Validation
            risk_result = await self.risk_agent.validate(data_result, pricing_result, self.broadcast_fn)
            if not risk_result.get("success"):
                return {"product_id": product_id, "action": "error", "error": risk_result.get("error")}

            # Step 5: Execution
            exec_result = await self.execution_agent.execute(
                data_result, pricing_result, risk_result, self.broadcast_fn,
                market_result=market_result,
            )

            return {
                "product_id": product_id,
                "action": exec_result.get("action", "error"),
                "success": exec_result.get("success", False),
                "details": exec_result
            }

        except Exception as e:
            logger.error(f"Pipeline error for product {product_id}: {e}")
            return {"product_id": product_id, "action": "error", "error": str(e)}

    async def run_cycle(self) -> Dict:
        """
        Run one complete pricing cycle for all products.
        
        Returns:
            Cycle results summary
        """
        try:
            log_agent_activity(
                self.name,
                "Starting pricing cycle",
                f"Cycle #{self.memory_agent.cycle_count + 1}",
                "running"
            )

            if self.broadcast_fn:
                await self.broadcast_fn({
                    "type": "cycle_start",
                    "agent": self.name,
                    "cycle_number": self.memory_agent.cycle_count + 1
                })

            # Get all active products
            products = get_product_data()
            cycle_results = []

            for product in products:
                result = await self.process_product(product["id"])
                cycle_results.append(result)
                # Small delay between products for readability on UI
                await asyncio.sleep(0.5)

            # Record cycle in memory
            summary = await self.memory_agent.record_cycle(cycle_results, self.broadcast_fn)

            log_agent_activity(
                self.name,
                "Pricing cycle complete",
                f"Processed {len(products)} products, "
                f"{summary.get('prices_updated', 0)} updates made",
                "completed"
            )

            return summary

        except Exception as e:
            logger.error(f"Orchestrator cycle error: {e}")
            log_agent_activity(self.name, "Cycle error", str(e), "error")
            return {"error": str(e)}

    async def start_loop(self, interval: int = 15):
        """
        Start the autonomous pricing loop.
        
        Args:
            interval: Seconds between cycles
        """
        self.is_running = True
        logger.info(f"Autonomous pricing loop started (interval: {interval}s)")

        while self.is_running:
            try:
                await self.run_cycle()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info("Pricing loop cancelled")
                break
            except Exception as e:
                logger.error(f"Loop error: {e}")
                await asyncio.sleep(interval)

    def stop_loop(self):
        """Stop the autonomous pricing loop"""
        self.is_running = False
        logger.info("Autonomous pricing loop stopped")

    def get_status(self) -> Dict:
        """Get current orchestrator status"""
        return {
            "is_running": self.is_running,
            "stats": self.memory_agent.get_system_stats()
        }
