"""
Market intelligence: LangChain tools are always attempted first for competitor + trends.
Semantic Kernel plugins are optional (USE_MARKET_SEMANTIC_KERNEL). Direct tools.* remain
as final fallbacks so the app keeps working if frameworks fail.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from config import USE_MARKET_SEMANTIC_KERNEL

logger = logging.getLogger(__name__)


def _parse_jsonish(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)
    return json.loads(str(raw))


def _sk_value_to_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return json.loads(str(value))


async def fetch_competitor_data(product_id: int) -> Dict[str, Any]:
    """
    Competitor snapshot: LangChain tool (required first step) → optional Semantic Kernel
    → direct get_competitor_price.
    """
    try:
        from agent_framework.langchain_tools import competitor_snapshot

        data = _parse_jsonish(competitor_snapshot.invoke({"product_id": int(product_id)}))
        if "error" not in data:
            logger.debug("Market competitor data via LangChain tool")
            return data
    except Exception as e:
        logger.debug("LangChain competitor_snapshot failed, trying next path: %s", e)

    if USE_MARKET_SEMANTIC_KERNEL:
        try:
            from agent_framework.kernel_factory import get_shared_kernel

            kernel = get_shared_kernel()
            result = await kernel.invoke(
                plugin_name="MarketIntelligence",
                function_name="competitor_snapshot",
                product_id=int(product_id),
            )
            if result is not None and getattr(result, "value", None) is not None:
                data = _sk_value_to_dict(result.value)
                if "error" not in data:
                    logger.debug("Market competitor data via Semantic Kernel")
                    return data
        except Exception as e:
            logger.debug("Semantic Kernel competitor_snapshot failed, trying direct tool: %s", e)

    from tools.competitor_tools import get_competitor_price

    logger.debug("Market competitor data via direct get_competitor_price")
    return get_competitor_price(product_id)


async def fetch_google_trends(product_name: str, category: str = "", geo: str = "IN") -> Dict[str, Any]:
    """
    Google Trends: LangChain tool (required first step) → optional Semantic Kernel
    → direct get_google_trends.
    """
    geo = (geo or "IN").strip() or "IN"

    try:
        from agent_framework.langchain_tools import google_trends_research

        data = _parse_jsonish(
            google_trends_research.invoke(
                {
                    "product_name": product_name,
                    "category": category or "",
                    "geo": geo,
                }
            )
        )
        if data:
            logger.debug("Market Google Trends via LangChain tool")
            return data
    except Exception as e:
        logger.debug("LangChain google_trends_research failed, trying next path: %s", e)

    if USE_MARKET_SEMANTIC_KERNEL:
        try:
            from agent_framework.kernel_factory import get_shared_kernel

            kernel = get_shared_kernel()
            result = await kernel.invoke(
                plugin_name="MarketIntelligence",
                function_name="google_trends_research",
                product_name=product_name,
                category=category or "",
                geo=geo,
            )
            if result is not None and getattr(result, "value", None) is not None:
                data = _sk_value_to_dict(result.value)
                if data:
                    logger.debug("Market Google Trends via Semantic Kernel")
                    return data
        except Exception as e:
            logger.debug("Semantic Kernel google_trends_research failed, trying direct tool: %s", e)

    from tools.trends_tools import get_google_trends

    logger.debug("Market Google Trends via direct get_google_trends")
    return get_google_trends(product_name, category=category or "", geo=geo)


async def fetch_simulated_demand(product_id: int) -> Dict[str, Any]:
    """
    Demand snapshot: LangChain tool → optional Semantic Kernel (MarketIntelligence)
    → direct simulate_demand_change.
    """
    try:
        from agent_framework.langchain_tools import simulate_market_demand

        data = _parse_jsonish(simulate_market_demand.invoke({"product_id": int(product_id)}))
        if isinstance(data, dict) and "error" not in data:
            logger.debug("Market demand via LangChain tool")
            return data
    except Exception as e:
        logger.debug("LangChain simulate_market_demand failed: %s", e)

    if USE_MARKET_SEMANTIC_KERNEL:
        try:
            from agent_framework.kernel_factory import get_shared_kernel

            kernel = get_shared_kernel()
            result = await kernel.invoke(
                plugin_name="MarketIntelligence",
                function_name="simulate_market_demand",
                product_id=int(product_id),
            )
            if result is not None and getattr(result, "value", None) is not None:
                data = _sk_value_to_dict(result.value)
                if isinstance(data, dict) and "error" not in data:
                    logger.debug("Market demand via Semantic Kernel")
                    return data
        except Exception as e:
            logger.debug("Semantic Kernel simulate_market_demand failed: %s", e)

    from tools.competitor_tools import simulate_demand_change

    return simulate_demand_change(int(product_id))
