"""
LangGraph StateGraph for a single product — same steps as OrchestratorAgent.process_product.
Nodes call existing agent classes.
"""
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, TypedDict


def _ensure_langchain_root_shim():
    """Some LangGraph + langchain-core pairs expect attrs on top-level legacy ``langchain``."""
    try:
        import langchain as lc  # type: ignore[import-not-found]
    except ImportError:
        return
    if not hasattr(lc, "debug"):
        setattr(lc, "debug", False)
    if not hasattr(lc, "verbose"):
        setattr(lc, "verbose", False)


_ensure_langchain_root_shim()

from langgraph.graph import END, StateGraph

if TYPE_CHECKING:
    from agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)


class PricingGraphState(TypedDict, total=False):
    product_id: int
    broadcast_fn: Optional[Callable[..., Any]]
    pipeline_error: Optional[str]
    market_result: Dict[str, Any]
    data_result: Dict[str, Any]
    pricing_result: Dict[str, Any]
    risk_result: Dict[str, Any]
    exec_result: Dict[str, Any]
    final_output: Dict[str, Any]


def build_pricing_product_graph(orchestrator: "OrchestratorAgent"):
    """
    Build and compile a linear graph: Market → Data → Pricing → Risk → Execution → finalize.
    Early failures set ``pipeline_error``; later nodes no-op (mirrors legacy early returns).
    """

    async def node_market(state: PricingGraphState) -> Dict[str, Any]:
        pid = state["product_id"]
        bf = state.get("broadcast_fn")
        market_result = await orchestrator.market_agent.analyze(pid, bf)
        out: Dict[str, Any] = {"market_result": market_result}
        if not market_result.get("success"):
            out["pipeline_error"] = market_result.get("error", "Market analysis failed")
        return out

    async def node_data(state: PricingGraphState) -> Dict[str, Any]:
        if state.get("pipeline_error"):
            return {}
        pid = state["product_id"]
        bf = state.get("broadcast_fn")
        data_result = await orchestrator.data_agent.analyze(pid, bf)
        out: Dict[str, Any] = {"data_result": data_result}
        if not data_result.get("success"):
            out["pipeline_error"] = data_result.get("error", "Data analysis failed")
        return out

    async def node_pricing(state: PricingGraphState) -> Dict[str, Any]:
        if state.get("pipeline_error"):
            return {}
        bf = state.get("broadcast_fn")
        data_result = state["data_result"]
        market_result = state["market_result"]
        pricing_result = await orchestrator.pricing_agent.decide(data_result, market_result, bf)
        out: Dict[str, Any] = {"pricing_result": pricing_result}
        if not pricing_result.get("success"):
            out["pipeline_error"] = pricing_result.get("error", "Pricing decision failed")
        return out

    async def node_risk(state: PricingGraphState) -> Dict[str, Any]:
        if state.get("pipeline_error"):
            return {}
        bf = state.get("broadcast_fn")
        data_result = state["data_result"]
        pricing_result = state["pricing_result"]
        risk_result = await orchestrator.risk_agent.validate(data_result, pricing_result, bf)
        out: Dict[str, Any] = {"risk_result": risk_result}
        if not risk_result.get("success"):
            out["pipeline_error"] = risk_result.get("error", "Risk validation failed")
        return out

    async def node_execution(state: PricingGraphState) -> Dict[str, Any]:
        if state.get("pipeline_error"):
            return {}
        bf = state.get("broadcast_fn")
        data_result = state["data_result"]
        pricing_result = state["pricing_result"]
        risk_result = state["risk_result"]
        market_result = state["market_result"]
        exec_result = await orchestrator.execution_agent.execute(
            data_result,
            pricing_result,
            risk_result,
            bf,
            market_result=market_result,
        )
        return {"exec_result": exec_result}

    async def node_finalize(state: PricingGraphState) -> Dict[str, Any]:
        pid = state["product_id"]
        err = state.get("pipeline_error")
        if err:
            return {
                "final_output": {
                    "product_id": pid,
                    "action": "error",
                    "error": err,
                }
            }
        exec_result = state.get("exec_result") or {}
        return {
            "final_output": {
                "product_id": pid,
                "action": exec_result.get("action", "error"),
                "success": exec_result.get("success", False),
                "details": exec_result,
            }
        }

    graph = StateGraph(PricingGraphState)
    graph.add_node("market", node_market)
    graph.add_node("data", node_data)
    graph.add_node("pricing", node_pricing)
    graph.add_node("risk", node_risk)
    graph.add_node("execution", node_execution)
    graph.add_node("finalize", node_finalize)

    graph.set_entry_point("market")
    graph.add_edge("market", "data")
    graph.add_edge("data", "pricing")
    graph.add_edge("pricing", "risk")
    graph.add_edge("risk", "execution")
    graph.add_edge("execution", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()
