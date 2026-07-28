"""Semantic Kernel native plugins — same behavior as underlying tools/trends modules."""
import json
from typing import Annotated

from semantic_kernel.functions import kernel_function


class MarketIntelligencePlugin:
    """
    Market research plugin (Google Trends + competitor snapshot) for Semantic Kernel planners/agents.
    """

    @kernel_function(
        name="google_trends_research",
        description=(
            "Fetch Google Trends for a product or topic: 7-day interest, direction, related and rising queries, "
            "and a coarse demand_signal (high/medium/low). Uses cached pytrends calls."
        ),
    )
    def google_trends_research(
        self,
        product_name: Annotated[str, "Product name or search topic"],
        category: Annotated[str, "Optional category context"] = "",
        geo: Annotated[str, "Region code, e.g. IN, US, GB"] = "IN",
    ) -> str:
        from tools.trends_tools import get_google_trends

        data = get_google_trends(product_name, category=category or "", geo=geo or "IN")
        return json.dumps(data, default=str)

    @kernel_function(
        name="competitor_snapshot",
        description="Load simulated multi-retailer competitor prices for a product id from the internal database.",
    )
    def competitor_snapshot(
        self,
        product_id: Annotated[int, "Internal product id"],
    ) -> str:
        from tools.competitor_tools import get_competitor_price

        data = get_competitor_price(int(product_id))
        return json.dumps(data, default=str)

    @kernel_function(
        name="bulk_trends_research",
        description="Google Trends for up to five product keywords (summary map).",
    )
    def bulk_trends_research(
        self,
        keywords_json: Annotated[str, 'JSON array of strings, e.g. ["phone A","laptop B"]'],
    ) -> str:
        from tools.trends_tools import get_market_trends_summary

        try:
            keywords = json.loads(keywords_json)
            if not isinstance(keywords, list):
                return json.dumps({"error": "keywords_json must be a JSON array"})
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {e}"})
        return json.dumps(get_market_trends_summary([str(k) for k in keywords]), default=str)

    @kernel_function(
        name="simulate_market_demand",
        description="Simulated demand/stock snapshot for a product (read-only variance on DB demand).",
    )
    def simulate_market_demand(
        self,
        product_id: Annotated[int, "Internal product id"],
    ) -> str:
        from tools.competitor_tools import simulate_demand_change

        return json.dumps(simulate_demand_change(int(product_id)), default=str)


class PipelineAgentsPlugin:
    """Data, pricing rules, risk validation, execution, and memory reads for Semantic Kernel."""

    @kernel_function(
        name="internal_product_rows",
        description="Active product row(s) from SQLite for internal data analysis.",
    )
    def internal_product_rows(
        self,
        product_id: Annotated[int, "Internal product id"],
    ) -> str:
        from tools.product_tools import get_product_data

        return json.dumps(get_product_data(int(product_id)), default=str)

    @kernel_function(
        name="internal_price_history",
        description="Recent price history rows for a product.",
    )
    def internal_price_history(
        self,
        product_id: Annotated[int, "Internal product id"],
        limit: Annotated[int, "Max rows"] = 10,
    ) -> str:
        from tools.product_tools import get_price_history

        return json.dumps(get_price_history(int(product_id), limit=int(limit)), default=str)

    @kernel_function(
        name="rule_based_optimal_price",
        description="Deterministic optimal price from competitor, demand, stock, and margins.",
    )
    def rule_based_optimal_price(
        self,
        product_id: Annotated[int, "Internal product id"],
        competitor_price: Annotated[float, "Lowest competitor price"],
        demand_score: Annotated[float, "Demand 0-1"],
        stock: Annotated[int, "Stock units"],
        cost_price: Annotated[float, "Our cost"],
        current_price: Annotated[float, "Current selling price"],
    ) -> str:
        from tools.pricing_tools import calculate_optimal_price

        return json.dumps(
            calculate_optimal_price(
                product_id=int(product_id),
                competitor_price=float(competitor_price),
                demand_score=float(demand_score),
                stock=int(stock),
                cost_price=float(cost_price),
                current_price=float(current_price),
            ),
            default=str,
        )

    @kernel_function(
        name="validate_proposed_price",
        description="Validate a proposed price against margin, swing, and competitor rules.",
    )
    def validate_proposed_price(
        self,
        product_id: Annotated[int, "Internal product id"],
        proposed_price: Annotated[float, "Proposed new price"],
        cost_price: Annotated[float, "Cost price"],
        competitor_price: Annotated[float, "Competitor reference price"],
        current_price: Annotated[float, "Current price"],
    ) -> str:
        from tools.pricing_tools import validate_price

        return json.dumps(
            validate_price(
                product_id=int(product_id),
                proposed_price=float(proposed_price),
                cost_price=float(cost_price),
                competitor_price=float(competitor_price),
                current_price=float(current_price),
            ),
            default=str,
        )

    @kernel_function(
        name="execute_price_update",
        description="Persist new product price and append price history row.",
    )
    def execute_price_update(
        self,
        product_id: Annotated[int, "Internal product id"],
        new_price: Annotated[float, "New selling price"],
        reason: Annotated[str, "Reason for change"] = "",
        agent_name: Annotated[str, "Calling agent name"] = "Execution Agent",
    ) -> str:
        from tools.pricing_tools import update_price

        return json.dumps(
            update_price(
                product_id=int(product_id),
                new_price=float(new_price),
                reason=reason or "",
                agent_name=agent_name or "Execution Agent",
            ),
            default=str,
        )

    @kernel_function(
        name="recent_pricing_decisions",
        description="Recent structured pricing decisions for dashboard/memory.",
    )
    def recent_pricing_decisions(
        self,
        limit: Annotated[int, "Max decisions"] = 10,
    ) -> str:
        from tools.explanation_tools import get_recent_decisions

        return json.dumps(get_recent_decisions(int(limit)), default=str)

    @kernel_function(
        name="recent_agent_activity",
        description="Recent agent log lines for dashboard/memory.",
    )
    def recent_agent_activity(
        self,
        limit: Annotated[int, "Max log lines"] = 20,
    ) -> str:
        from tools.explanation_tools import get_agent_activity

        return json.dumps(get_agent_activity(int(limit)), default=str)
