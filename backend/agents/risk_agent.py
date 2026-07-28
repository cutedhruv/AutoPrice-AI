"""Risk Agent - Validates pricing decisions"""
import logging
from typing import Dict
from agent_framework.agent_operations_bridge import fetch_validate_price
from tools.explanation_tools import log_agent_activity

logger = logging.getLogger(__name__)


class RiskAgent:
    """
    Risk Validation Agent
    Responsible for validating pricing decisions against business rules.
    """
    
    name = "Risk Agent"

    async def validate(self, product_data: Dict, pricing_decision: Dict, broadcast_fn=None) -> Dict:
        """
        Validate a pricing decision.
        
        Args:
            product_data: Internal product data
            pricing_decision: Decision from Pricing Agent
            broadcast_fn: Optional callback to broadcast status updates
        
        Returns:
            Validation result
        """
        try:
            product = product_data["product"]
            product_id = product["id"]
            pricing = pricing_decision["pricing"]

            log_agent_activity(
                self.name,
                "Validating price change",
                f"Checking risk for {product['name']}",
                "running",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "running",
                    "step": "Validating pricing decision",
                    "product_id": product_id
                })

            # Skip validation if no change
            if pricing["decision"] == "no_change":
                result = {
                    "success": True,
                    "validation": {
                        "is_approved": True,
                        "risk_level": "low",
                        "issues": [],
                        "warnings": [],
                        "reason": "No price change required"
                    }
                }
            else:
                # Validate the proposed price (LangChain → SK → tools)
                validation = await fetch_validate_price(
                    product_id=product_id,
                    proposed_price=pricing["optimal_price"],
                    cost_price=product["cost_price"],
                    competitor_price=pricing["competitor_price"],
                    current_price=product["our_price"],
                )

                result = {
                    "success": True,
                    "validation": validation
                }

            validation_data = result["validation"]
            status_msg = "APPROVED" if validation_data["is_approved"] else "REJECTED"
            
            log_agent_activity(
                self.name,
                f"Validation: {status_msg}",
                f"Risk: {validation_data['risk_level']}, Issues: {len(validation_data.get('issues', []))}",
                "completed",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "completed",
                    "step": f"Validation: {status_msg} (Risk: {validation_data['risk_level']})",
                    "product_id": product_id,
                    "result": {
                        "approved": validation_data["is_approved"],
                        "risk_level": validation_data["risk_level"]
                    }
                })

            return result

        except Exception as e:
            logger.error(f"Risk Agent error: {e}")
            log_agent_activity(self.name, "Error", str(e), "error")
            return {"success": False, "error": str(e)}
