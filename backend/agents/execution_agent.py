"""Execution Agent - Executes approved pricing changes"""
import logging
from typing import Dict, Optional
from agent_framework.agent_operations_bridge import fetch_update_price
from tools.notification_tools import send_notification, send_rich_notification
from tools.explanation_tools import log_agent_activity, log_decision
from tools.email_builder import build_price_update_email

logger = logging.getLogger(__name__)


class ExecutionAgent:
    """
    Execution Agent
    Responsible for executing approved price changes and sending notifications.
    """
    
    name = "Execution Agent"

    async def execute(
        self,
        product_data: Dict,
        pricing_decision: Dict,
        validation_result: Dict,
        broadcast_fn=None,
        market_result: Optional[Dict] = None,
    ) -> Dict:
        """
        Execute an approved pricing decision.
        
        Args:
            product_data: Internal product data
            pricing_decision: Decision from Pricing Agent
            validation_result: Validation from Risk Agent
            broadcast_fn: Optional callback to broadcast status updates
        
        Returns:
            Execution result
        """
        try:
            product = product_data["product"]
            product_id = product["id"]
            pricing = pricing_decision["pricing"]
            validation = validation_result["validation"]

            # Check if approved
            if not validation["is_approved"]:
                log_agent_activity(
                    self.name,
                    "Execution skipped",
                    f"Price change rejected by Risk Agent: {validation.get('issues', [])}",
                    "completed",
                    product_id
                )
                return {
                    "success": False,
                    "reason": "Price change rejected by Risk Agent",
                    "issues": validation.get("issues", [])
                }

            # Skip if no change
            if pricing["decision"] == "no_change":
                log_agent_activity(
                    self.name,
                    "No action needed",
                    f"Price for {product['name']} is already optimal",
                    "completed",
                    product_id
                )
                return {"success": True, "action": "no_change"}

            log_agent_activity(
                self.name,
                "Executing price update",
                f"Updating {product['name']}: ₹{product['our_price']:,.0f} → ₹{pricing['optimal_price']:,.0f}",
                "running",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "running",
                    "step": "Executing price update",
                    "product_id": product_id
                })

            # Execute the price update (LangChain → SK → tools)
            update_result = await fetch_update_price(
                product_id=product_id,
                new_price=pricing["optimal_price"],
                reason=pricing.get("explanation", pricing.get("reason", "")),
                agent_name=self.name,
            )

            if not update_result["success"]:
                return update_result

            # Log the decision
            log_decision(
                product_id=product_id,
                product_name=product["name"],
                decision_type=pricing["decision"],
                old_price=product["our_price"],
                new_price=pricing["optimal_price"],
                competitor_price=pricing["competitor_price"],
                reason=pricing.get("explanation", ""),
                confidence=pricing.get("confidence", 0.8),
                profit_impact=pricing.get("profit_margin", 0),
                agent_chain=["Market Agent", "Data Agent", "Pricing Agent", "Risk Agent", "Execution Agent"]
            )

            # Send notification with detailed explainable email
            direction = "increased" if pricing["price_change"] > 0 else "decreased"
            try:
                short_msg, subject, plain_body, html_body = build_price_update_email(
                    product=product,
                    pricing=pricing,
                    validation=validation,
                    product_data=product_data,
                    market_result=market_result,
                    old_price=product["our_price"],
                    new_price=pricing["optimal_price"],
                )
                send_rich_notification(
                    product_id=product_id,
                    short_msg=short_msg,
                    subject=subject,
                    plain_body=plain_body,
                    html_body=html_body,
                    notification_type="success" if pricing["price_change"] > 0 else "info",
                )
            except Exception as email_err:
                logger.error(f"Rich email build/send failed, falling back: {email_err}")
                send_notification(
                    product_id=product_id,
                    title=f"Price {direction}: {product['name']}",
                    message=(
                        f"Price {direction} by {abs(pricing['change_percentage']):.1f}% "
                        f"(\u20b9{product['our_price']:,.0f} \u2192 \u20b9{pricing['optimal_price']:,.0f}). "
                        f"Reason: {pricing.get('reason', 'Market adjustment')}"
                    ),
                    notification_type="success" if pricing["price_change"] > 0 else "info",
                )

            log_agent_activity(
                self.name,
                "Price updated successfully",
                f"{product['name']}: ₹{product['our_price']:,.0f} → ₹{pricing['optimal_price']:,.0f}",
                "completed",
                product_id
            )

            if broadcast_fn:
                await broadcast_fn({
                    "type": "agent_status",
                    "agent": self.name,
                    "status": "completed",
                    "step": "Price updated successfully",
                    "product_id": product_id,
                    "result": update_result
                })

                # Send price update event
                await broadcast_fn({
                    "type": "price_update",
                    "product_id": product_id,
                    "product_name": product["name"],
                    "old_price": product["our_price"],
                    "new_price": pricing["optimal_price"],
                    "change_percentage": pricing["change_percentage"],
                    "reason": pricing.get("explanation", ""),
                    "decision_type": pricing["decision"]
                })

            return {
                "success": True,
                "action": "price_updated",
                "update": update_result
            }

        except Exception as e:
            logger.error(f"Execution Agent error: {e}")
            log_agent_activity(self.name, "Error", str(e), "error")
            return {"success": False, "error": str(e)}
