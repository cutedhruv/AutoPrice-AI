"""Plain + HTML bodies for explainable price-update emails."""
from __future__ import annotations

import html
from typing import Dict, Optional, Tuple


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_price_update_email(
    product: Dict,
    pricing: Dict,
    validation: Dict,
    product_data: Dict,
    market_result: Optional[Dict],
    old_price: float,
    new_price: float,
) -> Tuple[str, str, str, str]:
    """Returns (short_db_message, email_subject, plain_body, html_body)."""
    delta = round(new_price - old_price, 2)
    pct = pricing.get("change_percentage")
    if pct is None and old_price:
        pct = round((delta / old_price) * 100, 2)
    direction = "increased" if delta > 0 else "decreased" if delta < 0 else "unchanged"

    comp = (market_result or {}).get("competitor_data") or {}
    demand = (market_result or {}).get("demand_data") or {}
    competitors = comp.get("competitors") or []

    peer_lines = []
    for c in competitors[:5]:
        peer_lines.append(
            f"  \u2022 {_e(c.get('name', 'Peer'))}: \u20b9{float(c.get('price', 0) or 0):,.2f} "
            f"(in stock: {c.get('in_stock', True)})"
        )
    peer_block = "\n".join(peer_lines) if peer_lines else "  \u2022 (no simulated peer rows)"

    factors = pricing.get("factors") or {}
    trends = (market_result or {}).get("trends_data") or {}
    risk_issues = validation.get("issues") or []
    risk_warnings = validation.get("warnings") or []
    pricing_reason = pricing.get("reason") or pricing.get("explanation") or "Market-aligned adjustment"
    source = pricing.get("source", "unknown")
    confidence = pricing.get("confidence")
    anchor = float(pricing.get("competitor_price") or comp.get("lowest_competitor_price") or 0)

    lines = [
        "AGENT ANALYSIS (Explainable AI)",
        "",
        "1) Market Agent",
        f"   Anchor competitor price: \u20b9{anchor:,.2f}",
        f"   Avg simulated market: {comp.get('average_market_price', 'n/a')}",
        f"   Demand signal: {demand.get('demand_score', product_data.get('demand_score', 'n/a'))}",
        "   Simulated peers:",
        peer_block,
        "",
        "2) Data Agent",
        f"   Price trend: {product_data.get('price_trend', 'n/a')}",
        f"   Margin (before): {product_data.get('current_margin', product.get('profit_margin', 0)):.2f}%",
        f"   Stock: {product_data.get('stock_level', product.get('stock', 'n/a'))}",
        "",
        "3) Pricing Agent",
        f"   Decision: {pricing.get('decision', 'n/a')}",
        f"   New price: \u20b9{new_price:,.2f} (was \u20b9{old_price:,.2f})",
        f"   Change: \u20b9{delta:+,.2f}" + (f" ({pct:+.2f}%)" if pct is not None else ""),
        f"   Rationale: {pricing_reason}",
        f"   Engine: {'LLM (Groq)' if source == 'llm' else 'Rules' if source == 'rule_based' else source}",
    ]
    if confidence is not None:
        lines.append(f"   Confidence: {confidence}")
    lines += [
        "",
        "4) Risk Agent",
        f"   Approved: {validation.get('is_approved', False)}",
        f"   Risk level: {validation.get('risk_level', 'n/a')}",
    ]
    if risk_issues:
        lines.append("   Issues: " + "; ".join(str(i) for i in risk_issues))
    if risk_warnings:
        lines.append("   Warnings: " + "; ".join(str(w) for w in risk_warnings))
    if factors:
        lines += ["", "5) Factors"]
        for k, v in factors.items():
            lines.append(f"   \u2022 {k}: {v}")
    if trends.get("available"):
        lines += [
            "", "6) Google Trends",
            f"   Search interest (7d avg): {trends.get('avg_interest', 'N/A')}/100",
            f"   Trend direction: {trends.get('trend_direction', 'N/A')}",
            f"   Market signal: {trends.get('demand_signal', 'N/A')}",
        ]
        if trends.get("related_queries"):
            lines.append(f"   Related: {', '.join(trends['related_queries'][:3])}")
        if trends.get("rising_queries"):
            lines.append(f"   Rising: {', '.join(trends['rising_queries'][:3])}")

    plain_body = "\n".join(
        [
            f"AutoPrice AI \u2014 {direction} price for {product.get('name', 'Product')}",
            "",
            "SUMMARY",
            f"List price moved from \u20b9{old_price:,.2f} to \u20b9{new_price:,.2f} ({direction}).",
            f"Absolute change: \u20b9{delta:+,.2f}."
            + (f" Percent: {pct:+.2f}%." if pct is not None else ""),
            f"Projected margin: {pricing.get('profit_margin', 'n/a')}%",
            "",
            *lines,
            "",
            "Sent when the execution agent applied an approved pricing update.",
        ]
    )

    peer_html = "<ul style=\"margin:0;padding-left:18px;\">" + "".join(
        "<li style=\"margin:4px 0;color:#334155;\">{name}: \u20b9{p:,.2f} \u2014 in stock: {s}</li>".format(
            name=_e(c.get("name", "Peer")),
            p=float(c.get("price", 0) or 0),
            s=_e(str(c.get("in_stock", True))),
        )
        for c in competitors[:5]
    ) + "</ul>" if competitors else "<p style=\"color:#64748b;font-style:italic;\">No peer rows.</p>"

    factors_html = ""
    if factors:
        factors_html = (
            '<h3 style="margin:20px 0 10px;font-size:15px;color:#0f172a;">Key factors</h3>'
            '<ul style="margin:0;padding-left:18px;">'
            + "".join(
                f'<li style="margin:4px 0;color:#334155;">{_e(k)}: {_e(v)}</li>'
                for k, v in factors.items()
            )
            + "</ul>"
        )

    engine_label = "LLM (Groq)" if source == "llm" else "Rules"
    demand_s = _e(str(demand.get("demand_score", product_data.get("demand_score", "n/a"))))

    html_body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/></head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#f3f6fb;color:#0f172a;">
<div style="max-width:700px;margin:32px auto;background:#ffffff;border-radius:16px;padding:0;border:1px solid #e2e8f0;box-shadow:0 8px 24px rgba(15,23,42,0.08);overflow:hidden;">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1e1b4b,#312e81);padding:28px 32px;">
    <p style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(199,210,254,0.7);">AutoPrice AI</p>
  </div>

  <div style="padding:28px 32px;">
    <!-- Title -->
    <h1 style="margin:0 0 4px;font-size:24px;font-weight:700;color:#0f172a;">Price {_e(direction.title())}</h1>
    <!-- Product Name -->
    <p style="margin:0 0 20px;color:#475569;font-size:16px;font-weight:600;">{_e(product.get('name', 'Product'))}</p>

    <!-- Price Comparison Table -->
    <table style="width:100%;border-collapse:separate;border-spacing:0;margin-bottom:16px;">
      <tr>
        <td style="padding:16px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;width:42%;">
          <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;">Previous</div>
          <div style="font-size:24px;font-weight:700;color:#64748b;margin-top:4px;">\u20b9{_e(f'{old_price:,.2f}')}</div>
        </td>
        <td style="width:16%;text-align:center;color:#94a3b8;font-size:20px;vertical-align:middle;">\u2192</td>
        <td style="padding:16px;background:#ecfeff;border-radius:12px;border:1px solid #a5f3fc;width:42%;">
          <div style="font-size:11px;color:#0e7490;text-transform:uppercase;letter-spacing:0.05em;">New</div>
          <div style="font-size:24px;font-weight:700;color:#0e7490;margin-top:4px;">\u20b9{_e(f'{new_price:,.2f}')}</div>
        </td>
      </tr>
    </table>

    <!-- Change & Margin -->
    <p style="color:#334155;margin:8px 0;font-size:14px;">Change: <strong>\u20b9{_e(f'{delta:+,.2f}')}</strong>"""
    if pct is not None:
        html_body += f""" <span style="color:#64748b;">({_e(f'{pct:+.2f}')}%)</span>"""
    html_body += f"""</p>
    <p style="color:#334155;margin:4px 0 0;font-size:14px;">Projected margin: <strong>{_e(str(pricing.get('profit_margin', 'n/a')))}%</strong></p>

    <!-- Why this change -->
    <div style="margin-top:24px;padding:16px 18px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;">
      <h2 style="font-size:15px;color:#0f172a;margin:0 0 8px;font-weight:600;">Why this change</h2>
      <p style="line-height:1.65;color:#475569;margin:0;font-size:14px;">{_e(pricing_reason)}</p>
    </div>

    <!-- Agent Analysis -->
    <h2 style="font-size:15px;color:#0f172a;margin:24px 0 12px;font-weight:600;">Agent analysis</h2>
    <ol style="line-height:1.7;color:#334155;padding-left:18px;margin:0;font-size:14px;">
      <li style="margin:6px 0;"><strong>Market</strong> \u2014 anchor \u20b9{_e(f'{anchor:,.2f}')}; demand {demand_s}.</li>
      <li style="margin:6px 0;"><strong>Data</strong> \u2014 trend {_e(str(product_data.get('price_trend', 'n/a')))}; stock {_e(str(product_data.get('stock_level', product.get('stock', 'n/a'))))}.</li>
      <li style="margin:6px 0;"><strong>Pricing</strong> \u2014 {_e(engine_label)}; decision {_e(str(pricing.get('decision', 'n/a')))}.</li>
      <li style="margin:6px 0;"><strong>Risk</strong> \u2014 {_e(str(validation.get('risk_level', 'n/a')))}; approved {_e(str(validation.get('is_approved', False)))}.</li>
    </ol>

    <!-- Simulated Peers -->
    <h3 style="margin:20px 0 10px;font-size:15px;color:#0f172a;">Simulated peers</h3>
    {peer_html}

    <!-- Key Factors -->
    {factors_html}

    <!-- Google Trends -->"""
    if trends.get("available"):
        html_body += f"""
    <h3 style="margin:20px 0 10px;font-size:15px;color:#0f172a;">Google Trends</h3>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;">
      <div style="display:flex;gap:16px;margin-bottom:8px;">
        <div><span style="color:#94a3b8;font-size:11px;">Interest (7d)</span><br/><strong style="font-size:18px;color:#0f172a;">{_e(str(trends.get('avg_interest', 'N/A')))}</strong><span style="color:#94a3b8;font-size:11px;">/100</span></div>
        <div><span style="color:#94a3b8;font-size:11px;">Trend</span><br/><strong style="font-size:14px;color:#0f172a;">{_e(str(trends.get('trend_direction', 'N/A')))}</strong></div>
        <div><span style="color:#94a3b8;font-size:11px;">Signal</span><br/><strong style="font-size:14px;color:{'#10b981' if trends.get('demand_signal') == 'high' else '#f59e0b' if trends.get('demand_signal') == 'medium' else '#64748b'};">{_e(str(trends.get('demand_signal', 'N/A')))}</strong></div>
      </div>"""
        if trends.get("related_queries"):
            html_body += f'<p style="color:#475569;font-size:12px;margin:4px 0;">Related: {_e(", ".join(trends["related_queries"][:3]))}</p>'
        if trends.get("rising_queries"):
            html_body += f'<p style="color:#475569;font-size:12px;margin:4px 0;">Rising: {_e(", ".join(trends["rising_queries"][:3]))}</p>'
        html_body += "</div>"

    html_body += """

    <!-- Footer -->
    <p style="margin-top:28px;padding-top:16px;border-top:1px solid #f1f5f9;color:#94a3b8;font-size:12px;">
      Sent automatically when the execution agent applied an approved update.
    </p>
  </div>
</div>
</body></html>"""

    short_msg = (
        f"{product.get('name')}: \u20b9{old_price:,.0f} \u2192 \u20b9{new_price:,.0f} ({direction}"
        + (f", {pct:+.1f}%)" if pct is not None else ")")
        + f". {pricing_reason[:240]}"
    )
    subject = f"AutoPrice AI \u2014 {product.get('name', 'Product')}: \u20b9{old_price:,.0f} \u2192 \u20b9{new_price:,.0f}"
    return short_msg, subject, plain_body, html_body
