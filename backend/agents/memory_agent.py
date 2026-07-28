"""Memory Agent - Maintains system memory and history"""
import logging
from typing import Dict, List
from tools.explanation_tools import log_agent_activity
from agent_framework.agent_operations_bridge import fetch_agent_activity_sync, fetch_recent_decisions_sync

logger = logging.getLogger(__name__)


class MemoryAgent:
    """
    Memory Agent
    Responsible for maintaining system memory, history, and providing context.
    """
    
    name = "Memory Agent"

    def __init__(self):
        self.cycle_count = 0
        self.total_updates = 0
        self.last_decisions = []

    async def record_cycle(self, cycle_results: List[Dict], broadcast_fn=None) -> Dict:
        """
        Record a complete pricing cycle.
        
        Args:
            cycle_results: Results from all product analyses
            broadcast_fn: Optional callback to broadcast status updates
        
        Returns:
            Cycle summary
        """
        try:
            self.cycle_count += 1
            
            updates_this_cycle = sum(
                1 for r in cycle_results 
                if r.get("action") == "price_updated"
            )
            self.total_updates += updates_this_cycle

            log_agent_activity(
                self.name,
                "Cycle recorded",
                f"Cycle #{self.cycle_count}: {updates_this_cycle} updates, "
                f"{len(cycle_results)} products analyzed",
                "completed"
            )

            summary = {
                "cycle_number": self.cycle_count,
                "products_analyzed": len(cycle_results),
                "prices_updated": updates_this_cycle,
                "total_updates": self.total_updates,
                "results": cycle_results
            }

            if broadcast_fn:
                await broadcast_fn({
                    "type": "cycle_complete",
                    "cycle_number": self.cycle_count,
                    "products_analyzed": len(cycle_results),
                    "prices_updated": updates_this_cycle,
                    "total_updates": self.total_updates
                })

            return summary

        except Exception as e:
            logger.error(f"Memory Agent error: {e}")
            return {"error": str(e)}

    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        return {
            "total_cycles": self.cycle_count,
            "total_updates": self.total_updates,
            "recent_decisions": fetch_recent_decisions_sync(10),
            "recent_activity": fetch_agent_activity_sync(20),
        }
