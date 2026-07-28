"""LangChain tools wrapping agent operations (market, data, pricing, risk, execution, memory)."""
import json
from typing import List

from langchain_core.tools import tool


@tool
def google_trends_research(product_name: str, category: str = "", geo: str = "IN") -> str:
    """Google Trends: 7-day search interest, trend direction, related/rising queries, demand_signal. Cached."""
    from tools.trends_tools import get_google_trends

    payload = get_google_trends(product_name, category=category or "", geo=geo or "IN")
    return json.dumps(payload, default=str)


@tool
def competitor_snapshot(product_id: int) -> str:
    """Competitor price landscape for a product id (Amazon/Flipkart-style simulated rows)."""
    from tools.competitor_tools import get_competitor_price

    return json.dumps(get_competitor_price(int(product_id)), default=str)


@tool
def bulk_google_trends(keywords_csv: str) -> str:
    """Comma-separated product names/keywords (max 5) for batched Google Trends lookups."""
    from tools.trends_tools import get_market_trends_summary

    parts = [p.strip() for p in keywords_csv.split(",") if p.strip()]
    return json.dumps(get_market_trends_summary(parts[:5]), default=str)


@tool
def simulate_market_demand(product_id: int) -> str:
    """Simulated demand/stock snapshot for a product (same as Market Agent demand step)."""
    from tools.competitor_tools import simulate_demand_change

    return json.dumps(simulate_demand_change(int(product_id)), default=str)


@tool
def internal_product_rows(product_id: int) -> str:
    """Active product row(s) from SQLite for Data Agent."""
    from tools.product_tools import get_product_data

    return json.dumps(get_product_data(int(product_id)), default=str)


@tool
def internal_price_history(product_id: int, limit: int = 10) -> str:
    """Recent price history rows for Data Agent."""
    from tools.product_tools import get_price_history

    return json.dumps(get_price_history(int(product_id), limit=int(limit)), default=str)


@tool
async def pricing_llm_decide(
    product_name: str,
    our_price: float,
    cost_price: float,
    competitor_price: float,
    demand_score: float,
    stock: int,
    category: str,
    brand: str,
    trends_json: str = "{}",
) -> str:
    """Groq-backed pricing decision (async). Returns JSON object or literal null if LLM unavailable."""
    from tools.llm_client import get_pricing_decision

    try:
        ctx = json.loads(trends_json) if trends_json else None
        if not isinstance(ctx, dict):
            ctx = None
    except json.JSONDecodeError:
        ctx = None
    r = await get_pricing_decision(
        product_name=product_name,
        our_price=float(our_price),
        cost_price=float(cost_price),
        competitor_price=float(competitor_price),
        demand_score=float(demand_score),
        stock=int(stock),
        category=category or "General",
        brand=brand or "Unknown",
        trends_context=ctx,
    )
    return json.dumps(r, default=str) if r else "null"


@tool
def rule_based_optimal_price(
    product_id: int,
    competitor_price: float,
    demand_score: float,
    stock: int,
    cost_price: float,
    current_price: float,
) -> str:
    """Deterministic pricing engine (Pricing Agent fallback)."""
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


@tool
def validate_proposed_price_tool(
    product_id: int,
    proposed_price: float,
    cost_price: float,
    competitor_price: float,
    current_price: float,
) -> str:
    """Risk Agent: validate a proposed price against business rules."""
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


@tool
def execute_price_update_tool(product_id: int, new_price: float, reason: str, agent_name: str) -> str:
    """Execution Agent: persist new price and append price history."""
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


@tool
def recent_pricing_decisions(limit: int = 10) -> str:
    """Memory / dashboard: recent structured decisions."""
    from tools.explanation_tools import get_recent_decisions

    return json.dumps(get_recent_decisions(int(limit)), default=str)


@tool
def recent_agent_activity(limit: int = 20) -> str:
    """Memory / dashboard: recent agent log lines."""
    from tools.explanation_tools import get_agent_activity

    return json.dumps(get_agent_activity(int(limit)), default=str)


def list_market_intelligence_tools() -> List:
    """Tools list for LangGraph / LangChain agents."""
    return [google_trends_research, competitor_snapshot, bulk_google_trends]


def list_pipeline_agent_tools() -> List:
    """All non-market LangChain tools used by agent_operations_bridge."""
    return [
        simulate_market_demand,
        internal_product_rows,
        internal_price_history,
        pricing_llm_decide,
        rule_based_optimal_price,
        validate_proposed_price_tool,
        execute_price_update_tool,
        recent_pricing_decisions,
        recent_agent_activity,
    ]
