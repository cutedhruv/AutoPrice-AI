"""LLM Client - Groq API integration for agentic pricing decisions"""
import json
import logging
import httpx
from typing import Dict, Optional
from config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def _apply_charm_pricing(price: float, min_price: float) -> float:
    """Apply Indian psychological charm pricing (₹X,990 / ₹X,999 / ₹X,490)."""
    if price < 500:
        return price  # Too small for charm pricing

    # Charm endings in preference order
    endings = [990, 999, 490, 750, 240]
    base = int(price) // 1000 * 1000  # e.g. 84000 for 84900

    candidates = []
    for end in endings:
        candidate = base + end
        if candidate < price + 500 and candidate >= min_price:
            candidates.append(candidate)
        # Also try one thousand lower
        lower = base - 1000 + end
        if lower >= min_price and lower < price:
            candidates.append(lower)

    if not candidates:
        return round(price, 2)

    # Pick the candidate closest to original price but not above it by much
    best = min(candidates, key=lambda c: abs(c - price))
    return float(best)


async def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Optional[str]:
    """
    Call Groq LLM API for intelligent decision making.
    
    Args:
        system_prompt: System role instructions
        user_prompt: User message with data context
        temperature: LLM temperature (lower = more deterministic)
    
    Returns:
        LLM response text, or None if failed
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set, LLM calls will fail")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1024
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GROQ_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content
    except httpx.HTTPStatusError as e:
        logger.error(f"Groq API HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return None


async def get_pricing_decision(
    product_name: str,
    our_price: float,
    cost_price: float,
    competitor_price: float,
    demand_score: float,
    stock: int,
    category: str,
    brand: str,
    trends_context: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Use LLM to analyze competitor pricing and decide optimal price.
    
    Returns:
        Dict with 'new_price', 'decision', 'reason', 'confidence'
    """
    system_prompt = """You are an elite autonomous pricing strategist AI for an Indian e-commerce platform. Your DUAL OBJECTIVE is to MAXIMIZE PROFIT while ALWAYS staying below the competitor price.

CORE PRICING PHILOSOPHY (Indian Market — Profit Maximization):
1. ALWAYS BELOW COMPETITOR: Our price MUST be below the competitor price. This is non-negotiable. Indian consumers compare on Amazon, Flipkart, Croma. Being even ₹1 cheaper wins.
2. MAXIMIZE MARGIN: Price as CLOSE to competitor as possible while still being cheaper. Don't undercut more than necessary. Every extra rupee below competitor is wasted profit.
3. DEMAND-BASED SPREAD:
   - High demand (>0.8): Price only 0.5-1% below competitor (consumers will buy anyway, maximize margin)
   - Medium demand (0.4-0.8): Price 1-1.5% below competitor (balanced)
   - Low demand (<0.4): Price 2-3% below competitor (need to attract buyers)
4. STOCK-BASED ADJUSTMENT:
   - Low stock (<20): Price closer to competitor (scarcity = less discount needed)
   - Normal stock: Standard competitive gap
   - Excess stock (>150): Deeper undercut to clear inventory faster
5. PSYCHOLOGICAL PRICING: Use Indian charm pricing — ₹X,990 / ₹X,999 / ₹X,490. Never round numbers.
6. MARGIN FLOOR: Never go below 5% profit margin.
7. PROFIT PRIORITY: Between two prices both below competitor, ALWAYS choose the higher one (more profit).
2. PSYCHOLOGICAL PRICING: Use Indian charm pricing — end prices at ₹990, ₹999, ₹490, ₹240 etc. Avoid round numbers. Indian shoppers perceive ₹14,990 as significantly cheaper than ₹15,000.
3. MARGIN PROTECTION: Never go below 5% profit margin (absolute floor). Target 8-15% margin for sustainability.
4. DEMAND-BASED PRICING: High demand (>0.8) lets you keep margin closer to competitor. Low demand (<0.4) needs aggressive undercut.
5. INVENTORY-AWARE: Low stock (<20 units) — hold price or slight premium. Excess stock (>150 units) — undercut competitor more.
6. PRICE ANCHORING: The competitor price is the anchor. Position 1-3% below it for best conversion.

DECISION RULES (Profit-First):
- If our price is ABOVE competitor → DECREASE to just below competitor (priority #1, use smallest undercut that wins)
- If our price is BELOW competitor by >3% → INCREASE to capture more margin (still stay below competitor)
- If our price is 0.5-2% below competitor → sweet spot, lean toward no_change
- High demand + low stock = closest to competitor (0.5% below, max profit)
- Low demand + high stock = larger gap (2-3% below to drive volume)
- Use charm pricing in final number (end in 990, 999, 490, 240, 750)

CONFIDENCE SCORING:
- 0.95+ : Clear competitive play, strong data signals
- 0.90-0.94 : Good decision with solid reasoning
- 0.85-0.89 : Moderate certainty, acceptable trade-offs
- Below 0.85 : Only when signals conflict

Your confidence should be 0.90+ for most straightforward competitive pricing decisions.

RESPOND ONLY in this EXACT JSON (no markdown, no commas in numbers):
{"new_price": <number>, "decision": "<price_increase|price_decrease|no_change>", "reason": "<detailed explanation covering: competitive position, margin impact, demand signal, Indian consumer insight>", "confidence": <0.0-1.0>}"""

    user_prompt = f"""PRODUCT ANALYSIS REQUEST:

Product: {product_name}
Brand: {brand}
Category: {category}

PRICING DATA:
  Our current price : ₹{our_price:,.2f}
  Cost price         : ₹{cost_price:,.2f}
  Competitor price   : ₹{competitor_price:,.2f}

MARKET SIGNALS:
  Demand score: {demand_score}/1.0 ({'🔥 High' if demand_score > 0.8 else '⚡ Medium' if demand_score > 0.4 else '❄️ Low'})
  Stock level : {stock} units ({'⚠️ Low' if stock < 20 else '✅ Normal' if stock < 150 else '📦 Excess'})

COMPUTED METRICS:
  Current margin           : {((our_price - cost_price) / our_price * 100):.1f}%
  Gap vs competitor        : {((our_price - competitor_price) / competitor_price * 100):+.1f}% ({'⚠️ We are MORE expensive' if our_price > competitor_price else '✅ We are cheaper'})
  Min price (5% margin)    : ₹{cost_price * 1.05:,.2f}
  Target price (1% below)  : ₹{competitor_price * 0.99:,.2f}
  Target price (2% below)  : ₹{competitor_price * 0.98:,.2f}

Decide the optimal price. Remember: Indian consumers always compare. Stay 1%+ below competitor. Use charm pricing (₹X,990 or ₹X,999 or ₹X,490).
Explain your reasoning covering competitive position, margin, demand, and consumer psychology."""

    # Append Google Trends context if available
    if trends_context and trends_context.get("available"):
        trends_section = f"""

GOOGLE TRENDS INTELLIGENCE:
  Search interest (7-day avg): {trends_context.get('avg_interest', 'N/A')}/100
  Peak interest: {trends_context.get('peak_interest', 'N/A')}/100
  Trend direction: {trends_context.get('trend_direction', 'N/A')}
  Market signal: {trends_context.get('demand_signal', 'N/A')}
  Related searches: {', '.join(trends_context.get('related_queries', [])[:3]) or 'N/A'}
  Rising searches: {', '.join(trends_context.get('rising_queries', [])[:3]) or 'N/A'}

Use this trends data: if interest is HIGH (>70), consumers are actively searching — you can price closer to competitor. If LOW (<30), product is cooling off — undercut more aggressively."""
        user_prompt += trends_section

    response = await call_llm(system_prompt, user_prompt)
    if not response:
        return None

    try:
        # Clean response - sometimes LLM wraps in markdown code blocks
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        # Fix common LLM JSON issues: numbers with commas like 152,500.00
        import re
        cleaned = re.sub(r'(?<=\d),(?=\d{3})', '', cleaned)

        result = json.loads(cleaned)

        # Validate response
        new_price = float(result.get("new_price", 0))
        min_price = cost_price * 1.05  # 5% margin floor

        if new_price < min_price:
            new_price = min_price
        if new_price < cost_price:
            new_price = min_price

        # ENFORCE: price must be below competitor (at least 0.5% below if margin allows)
        target_max = competitor_price * 0.995
        if new_price > target_max and target_max >= min_price:
            new_price = target_max

        # Apply Indian charm pricing (nearest ₹990, ₹999, ₹490, ₹240)
        new_price = _apply_charm_pricing(new_price, min_price)

        # HARD CEILING after charm pricing: must still be below competitor
        if new_price >= competitor_price and target_max >= min_price:
            new_price = target_max  # Fall back to 0.5% below

        # Determine decision type
        price_change = new_price - our_price
        change_pct = (price_change / our_price) * 100

        # Only no_change if already below competitor and change is tiny
        if abs(change_pct) < 0.3 and our_price < competitor_price:
            decision = "no_change"
            new_price = our_price
        elif abs(change_pct) < 0.3:
            # We're at or above competitor — force decrease
            new_price = target_max if target_max >= min_price else min_price
            price_change = new_price - our_price
            change_pct = (price_change / our_price) * 100
            decision = "price_decrease" if price_change < 0 else "no_change"
        elif price_change > 0:
            decision = "price_increase"
        else:
            decision = "price_decrease"

        # Confidence: boost if we are clearly below competitor
        raw_confidence = float(result.get("confidence", 0.9))
        if new_price < competitor_price and new_price > min_price:
            raw_confidence = max(raw_confidence, 0.91)

        return {
            "new_price": round(new_price, 2),
            "decision": decision,
            "reason": result.get("reason", "LLM competitive pricing decision"),
            "confidence": min(1.0, max(0.0, raw_confidence)),
            "change_percentage": round(change_pct, 2)
        }

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse LLM response: {e}. Response was: {response}")
        return None
