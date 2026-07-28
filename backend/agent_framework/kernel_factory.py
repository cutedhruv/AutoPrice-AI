"""Shared Semantic Kernel instance with market plugins and optional Groq chat service."""
import logging
from typing import Optional

from semantic_kernel import Kernel

from agent_framework.semantic_plugins import MarketIntelligencePlugin, PipelineAgentsPlugin
from config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL, SEMANTIC_KERNEL_CHAT_ENABLED

logger = logging.getLogger(__name__)

_shared_kernel: Optional[Kernel] = None


def get_shared_kernel() -> Kernel:
    """Singleton kernel: native research plugins always; Groq chat only if enabled in config."""
    global _shared_kernel
    if _shared_kernel is not None:
        return _shared_kernel

    kernel = Kernel()
    kernel.add_plugin(MarketIntelligencePlugin(), plugin_name="MarketIntelligence")
    kernel.add_plugin(PipelineAgentsPlugin(), plugin_name="PipelineAgents")

    if SEMANTIC_KERNEL_CHAT_ENABLED and GROQ_API_KEY:
        try:
            from openai import AsyncOpenAI
            from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

            base = GROQ_BASE_URL.rstrip("/")
            client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=base)
            chat = OpenAIChatCompletion(
                ai_model_id=GROQ_MODEL,
                async_client=client,
                service_id="groq_chat",
            )
            kernel.add_service(chat)
            logger.info("Semantic Kernel: Groq chat service registered (model=%s)", GROQ_MODEL)
        except Exception as e:
            logger.warning("Semantic Kernel: Skipping Groq chat registration: %s", e)

    _shared_kernel = kernel
    return _shared_kernel
