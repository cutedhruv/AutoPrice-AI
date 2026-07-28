"""
Data / Pricing / Risk / Execution / Memory operations:
LangChain tools first → optional Semantic Kernel (USE_AGENT_SEMANTIC_KERNEL) → direct tools.*.

Async LLM pricing uses LangChain async tool then direct get_pricing_decision (no SK; SK plugins are sync).
Memory dashboard reads use sync LangChain → tools (see fetch_*_sync) to avoid nested event loops.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from config import USE_AGENT_SEMANTIC_KERNEL

logger = logging.getLogger(__name__)


def _parse_jsonish(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)
    return json.loads(str(raw))


def _sk_value_to_any(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "value") and value.value is not None:
        inner = value.value
    else:
        inner = value
    if isinstance(inner, (dict, list)):
        return inner
    if isinstance(inner, str):
        return json.loads(inner)
    return json.loads(str(inner))


async def fetch_internal_product_rows(product_id: int) -> List[Dict[str, Any]]:
    """Active product rows for one id (Data Agent)."""
    pid = int(product_id)
    try:
        from agent_framework.langchain_tools import internal_product_rows

        data = _parse_jsonish(internal_product_rows.invoke({"product_id": pid}))
        if isinstance(data, list) and len(data) > 0:
            logger.debug("internal_product_rows via LangChain")
            return data
    except Exception as e:
        logger.debug("LangChain internal_product_rows failed: %s", e)

    if USE_AGENT_SEMANTIC_KERNEL:
        try:
            from agent_framework.kernel_factory import get_shared_kernel

            kernel = get_shared_kernel()
            result = await kernel.invoke(
                plugin_name="PipelineAgents",
                function_name="internal_product_rows",
                product_id=pid,
            )
            if result is not None and getattr(result, "value", None) is not None:
                data = _sk_value_to_any(result.value)
                if isinstance(data, list) and len(data) > 0:
                    logger.debug("internal_product_rows via Semantic Kernel")
                    return data
        except Exception as e:
            logger.debug("Semantic Kernel internal_product_rows failed: %s", e)

    from tools.product_tools import get_product_data

    return get_product_data(pid)


async def fetch_internal_price_history(product_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    pid = int(product_id)
    lim = int(limit)
    try:
        from agent_framework.langchain_tools import internal_price_history

        data = _parse_jsonish(internal_price_history.invoke({"product_id": pid, "limit": lim}))
        if isinstance(data, list):
            logger.debug("internal_price_history via LangChain")
            return data
    except Exception as e:
        logger.debug("LangChain internal_price_history failed: %s", e)

    if USE_AGENT_SEMANTIC_KERNEL:
        try:
            from agent_framework.kernel_factory import get_shared_kernel

            kernel = get_shared_kernel()
            result = await kernel.invoke(
                plugin_name="PipelineAgents",
                function_name="internal_price_history",
                product_id=pid,
                limit=lim,
            )
            if result is not None and getattr(result, "value", None) is not None:
                data = _sk_value_to_any(result.value)
                if isinstance(data, list):
                    logger.debug("internal_price_history via Semantic Kernel")
                    return data
        except Exception as e:
            logger.debug("Semantic Kernel internal_price_history failed: %s", e)

    from tools.product_tools import get_price_history

    return get_price_history(pid, limit=lim)


async def fetch_llm_pricing_decision(
    *,
    product_name: str,
    our_price: float,
    cost_price: float,
    competitor_price: float,
    demand_score: float,
    stock: int,
    category: str,
    brand: str,
    trends_context: Optional[Dict],
) -> Optional[Dict[str, Any]]:
    """Groq-backed decision dict or None (Pricing Agent). SK skipped (async)."""
    trends_json = json.dumps(trends_context or {})
    try:
        from agent_framework.langchain_tools import pricing_llm_decide

        raw = await pricing_llm_decide.ainvoke(
            {
                "product_name": product_name,
                "our_price": float(our_price),
                "cost_price": float(cost_price),
                "competitor_price": float(competitor_price),
                "demand_score": float(demand_score),
                "stock": int(stock),
                "category": category or "General",
                "brand": brand or "Unknown",
                "trends_json": trends_json,
            }
        )
        if raw and raw != "null":
            data = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(data, dict) and data:
                logger.debug("get_pricing_decision via LangChain tool")
                return data
    except Exception as e:
        logger.debug("LangChain pricing_llm_decide failed: %s", e)

    from tools.llm_client import get_pricing_decision

    return await get_pricing_decision(
        product_name=product_name,
        our_price=float(our_price),
        cost_price=float(cost_price),
        competitor_price=float(competitor_price),
        demand_score=float(demand_score),
        stock=int(stock),
        category=category or "General",
        brand=brand or "Unknown",
        trends_context=trends_context,
    )


async def fetch_optimal_price_rule_based(
    *,
    product_id: int,
    competitor_price: float,
    demand_score: float,
    stock: int,
    cost_price: float,
    current_price: float,
) -> Dict[str, Any]:
    try:
        from agent_framework.langchain_tools import rule_based_optimal_price

        data = _parse_jsonish(
            rule_based_optimal_price.invoke(
                {
                    "product_id": int(product_id),
                    "competitor_price": float(competitor_price),
                    "demand_score": float(demand_score),
                    "stock": int(stock),
                    "cost_price": float(cost_price),
                    "current_price": float(current_price),
                }
            )
        )
        if isinstance(data, dict) and data.get("product_id") is not None:
            logger.debug("calculate_optimal_price via LangChain")
            return data
    except Exception as e:
        logger.debug("LangChain rule_based_optimal_price failed: %s", e)

    if USE_AGENT_SEMANTIC_KERNEL:
        try:
            from agent_framework.kernel_factory import get_shared_kernel

            kernel = get_shared_kernel()
            result = await kernel.invoke(
                plugin_name="PipelineAgents",
                function_name="rule_based_optimal_price",
                product_id=int(product_id),
                competitor_price=float(competitor_price),
                demand_score=float(demand_score),
                stock=int(stock),
                cost_price=float(cost_price),
                current_price=float(current_price),
            )
            if result is not None and getattr(result, "value", None) is not None:
                data = _sk_value_to_any(result.value)
                if isinstance(data, dict) and data.get("product_id") is not None:
                    logger.debug("calculate_optimal_price via Semantic Kernel")
                    return data
        except Exception as e:
            logger.debug("Semantic Kernel rule_based_optimal_price failed: %s", e)

    from tools.pricing_tools import calculate_optimal_price

    return calculate_optimal_price(
        product_id=int(product_id),
        competitor_price=float(competitor_price),
        demand_score=float(demand_score),
        stock=int(stock),
        cost_price=float(cost_price),
        current_price=float(current_price),
    )


async def fetch_validate_price(
    *,
    product_id: int,
    proposed_price: float,
    cost_price: float,
    competitor_price: float,
    current_price: float,
) -> Dict[str, Any]:
    try:
        from agent_framework.langchain_tools import validate_proposed_price_tool

        data = _parse_jsonish(
            validate_proposed_price_tool.invoke(
                {
                    "product_id": int(product_id),
                    "proposed_price": float(proposed_price),
                    "cost_price": float(cost_price),
                    "competitor_price": float(competitor_price),
                    "current_price": float(current_price),
                }
            )
        )
        if isinstance(data, dict) and "is_approved" in data:
            logger.debug("validate_price via LangChain")
            return data
    except Exception as e:
        logger.debug("LangChain validate_proposed_price_tool failed: %s", e)

    if USE_AGENT_SEMANTIC_KERNEL:
        try:
            from agent_framework.kernel_factory import get_shared_kernel

            kernel = get_shared_kernel()
            result = await kernel.invoke(
                plugin_name="PipelineAgents",
                function_name="validate_proposed_price",
                product_id=int(product_id),
                proposed_price=float(proposed_price),
                cost_price=float(cost_price),
                competitor_price=float(competitor_price),
                current_price=float(current_price),
            )
            if result is not None and getattr(result, "value", None) is not None:
                data = _sk_value_to_any(result.value)
                if isinstance(data, dict) and "is_approved" in data:
                    logger.debug("validate_price via Semantic Kernel")
                    return data
        except Exception as e:
            logger.debug("Semantic Kernel validate_proposed_price failed: %s", e)

    from tools.pricing_tools import validate_price

    return validate_price(
        product_id=int(product_id),
        proposed_price=float(proposed_price),
        cost_price=float(cost_price),
        competitor_price=float(competitor_price),
        current_price=float(current_price),
    )


async def fetch_update_price(
    *,
    product_id: int,
    new_price: float,
    reason: str,
    agent_name: str,
) -> Dict[str, Any]:
    try:
        from agent_framework.langchain_tools import execute_price_update_tool

        data = _parse_jsonish(
            execute_price_update_tool.invoke(
                {
                    "product_id": int(product_id),
                    "new_price": float(new_price),
                    "reason": reason or "",
                    "agent_name": agent_name or "Execution Agent",
                }
            )
        )
        if isinstance(data, dict) and "success" in data:
            logger.debug("update_price via LangChain")
            return data
    except Exception as e:
        logger.debug("LangChain execute_price_update_tool failed: %s", e)

    if USE_AGENT_SEMANTIC_KERNEL:
        try:
            from agent_framework.kernel_factory import get_shared_kernel

            kernel = get_shared_kernel()
            result = await kernel.invoke(
                plugin_name="PipelineAgents",
                function_name="execute_price_update",
                product_id=int(product_id),
                new_price=float(new_price),
                reason=reason or "",
                agent_name=agent_name or "Execution Agent",
            )
            if result is not None and getattr(result, "value", None) is not None:
                data = _sk_value_to_any(result.value)
                if isinstance(data, dict) and "success" in data:
                    logger.debug("update_price via Semantic Kernel")
                    return data
        except Exception as e:
            logger.debug("Semantic Kernel execute_price_update failed: %s", e)

    from tools.pricing_tools import update_price

    return update_price(
        product_id=int(product_id),
        new_price=float(new_price),
        reason=reason or "",
        agent_name=agent_name or "Execution Agent",
    )


def fetch_recent_decisions_sync(limit: int = 10) -> List[Dict[str, Any]]:
    """Sync path for MemoryAgent.get_system_stats (LangChain → tools; no SK)."""
    lim = int(limit)
    try:
        from agent_framework.langchain_tools import recent_pricing_decisions

        data = _parse_jsonish(recent_pricing_decisions.invoke({"limit": lim}))
        if isinstance(data, list):
            logger.debug("get_recent_decisions via LangChain (sync)")
            return data
    except Exception as e:
        logger.debug("LangChain recent_pricing_decisions sync failed: %s", e)

    from tools.explanation_tools import get_recent_decisions

    return get_recent_decisions(lim)


def fetch_agent_activity_sync(limit: int = 20) -> List[Dict[str, Any]]:
    lim = int(limit)
    try:
        from agent_framework.langchain_tools import recent_agent_activity

        data = _parse_jsonish(recent_agent_activity.invoke({"limit": lim}))
        if isinstance(data, list):
            logger.debug("get_agent_activity via LangChain (sync)")
            return data
    except Exception as e:
        logger.debug("LangChain recent_agent_activity sync failed: %s", e)

    from tools.explanation_tools import get_agent_activity

    return get_agent_activity(lim)
