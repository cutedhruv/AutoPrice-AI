"""Google Trends integration — cached, non-blocking, graceful fallback."""
import logging
import time
import threading
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# In-memory cache: { "keyword|GEO": { "data": {...}, "ts": timestamp } }
_cache: Dict[str, dict] = {}
_CACHE_TTL = 600  # 10 minutes — Google Trends data doesn't change fast
_lock = threading.Lock()


def _fetch_trends_sync(keyword: str, geo: str = "IN") -> dict:
    """Synchronous fetch from Google Trends (runs in thread)."""
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-IN", tz=330, timeout=(10, 25))
        pytrends.build_payload([keyword], cat=0, timeframe="now 7-d", geo=geo)

        # Interest over time
        interest_df = pytrends.interest_over_time()
        if interest_df.empty:
            return {"keyword": keyword, "available": False, "reason": "No data"}

        values = interest_df[keyword].tolist()
        avg_interest = round(sum(values) / len(values), 1) if values else 0
        peak = max(values) if values else 0
        latest = values[-1] if values else 0
        trend_dir = "rising" if len(values) >= 2 and values[-1] > values[-2] else "falling" if len(values) >= 2 and values[-1] < values[-2] else "stable"

        # Related queries
        related = {}
        try:
            related_df = pytrends.related_queries()
            if keyword in related_df and related_df[keyword].get("top") is not None:
                top_queries = related_df[keyword]["top"].head(5)
                related = {
                    "top_queries": top_queries["query"].tolist() if "query" in top_queries.columns else [],
                }
            if keyword in related_df and related_df[keyword].get("rising") is not None:
                rising_df = related_df[keyword]["rising"].head(5)
                related["rising_queries"] = rising_df["query"].tolist() if "query" in rising_df.columns else []
        except Exception:
            pass

        return {
            "keyword": keyword,
            "available": True,
            "geo": geo,
            "timeframe": "7 days",
            "avg_interest": avg_interest,
            "peak_interest": peak,
            "latest_interest": latest,
            "trend_direction": trend_dir,
            "interest_values": values[-7:],  # Last 7 data points
            "related_queries": related.get("top_queries", []),
            "rising_queries": related.get("rising_queries", []),
            "demand_signal": "high" if avg_interest > 70 else "medium" if avg_interest > 40 else "low",
        }
    except Exception as e:
        logger.warning(f"Google Trends fetch failed for '{keyword}': {e}")
        return {"keyword": keyword, "available": False, "reason": str(e)}


def get_google_trends(product_name: str, category: str = "", geo: str = "IN") -> dict:
    """
    Get Google Trends data for a product. Uses cache to avoid rate limits.
    Non-blocking: returns cached data instantly, refreshes in background.
    
    Args:
        product_name: Product name to search
        category: Product category for fallback search
        geo: Google Trends region code (e.g. IN, US, GB)
    
    Returns:
        Trends data dict
    """
    # Simplify keyword — use brand + category for better results
    keyword = _simplify_keyword(product_name)
    cache_key = f"{keyword}|{geo.upper().strip() or 'IN'}"
    
    with _lock:
        cached = _cache.get(cache_key)
        if cached and (time.time() - cached["ts"]) < _CACHE_TTL:
            return cached["data"]

    # Try to fetch (with timeout protection)
    try:
        result = _fetch_trends_sync(keyword, geo=geo)
        with _lock:
            _cache[cache_key] = {"data": result, "ts": time.time()}
        return result
    except Exception as e:
        logger.warning(f"Trends lookup failed for '{keyword}': {e}")
        return {
            "keyword": keyword,
            "available": False,
            "reason": str(e),
            "demand_signal": "unknown",
        }


def _simplify_keyword(product_name: str) -> str:
    """Simplify product name to a better Google Trends keyword."""
    # Remove common filler words, keep brand + product type
    replacements = {
        "Apple ": "", "Samsung ": "", "Sony ": "", "Dell ": "",
        "LG ": "", "Canon ": "", "Nike ": "", "Dyson ": "",
        "(5th Gen)": "", "Mark II": "Mark 2",
    }
    kw = product_name
    for old, new in replacements.items():
        kw = kw.replace(old, new)
    kw = kw.strip()
    # Keep it short — Google Trends works best with 2-4 words
    words = kw.split()
    if len(words) > 4:
        kw = " ".join(words[:4])
    return kw


def get_market_trends_summary(products_keywords: list) -> dict:
    """Get trends for multiple products at once."""
    results = {}
    for kw in products_keywords[:5]:  # Limit to 5 to avoid rate limits
        results[kw] = get_google_trends(kw)
    return results
