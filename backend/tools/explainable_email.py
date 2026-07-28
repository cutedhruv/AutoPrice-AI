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
            f"  • {_e(c.get('name', 'Peer'))}: ₹{float(c.get('price', 0) or 0):,.2f} "
            f"(in stock: {c.get('in_stock', True)})"
        )
    peer_block = "\n".join(peer_lines) if peer_lines else "  • (no simulated peer rows)"

    factors = pricing.get("factors") or {}
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
        f"   Anchor competitor price: ₹{anchor:,.2f}",
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
        f"   New price: ₹{new_price:,.2f} (was ₹{old_price:,.2f})",
        f"   Change: ₹{delta:+,.2f}" + (f" ({pct:+.2f}%)" if pct is not None else ""),
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
            lines.append(f"   • {k}: {v}")

    plain_body = "\n".join(
        [
            f"AutoPrice AI — {direction} price for {product.get('name', 'Product')}",
            "",
            "SUMMARY",
            f"List price moved from ₹{old_price:,.2f} to ₹{new_price:,.2f} ({direction}).",
            f"Absolute change: ₹{delta:+,.2f}."
            + (f" Percent: {pct:+.2f}%." if pct is not None else ""),
            f"Projected margin: {pricing.get('profit_margin', 'n/a')}%",
            "",
            *lines,
            "",
            "Sent when the execution agent applied an approved pricing update.",
        ]
    )

    peer_html = "<ul>" + "".join(
        "<li>{name}: ₹{p:,.2f} — in stock: {s}</li>".format(
            name=_e(c.get("name", "Peer")),
            p=float(c.get("price", 0) or 0),
            s=_e(c.get("in_stock", True)),
        )
        for c in competitors[:5]
    ) + "</ul>" if competitors else "<p><em>No peer rows.</em></p>"

    factors_html = ""
    if factors:
        factors_html = (
            '<h3 style="margin:16px 0 8px;">Key factors</h3><ul>'
            + "".join(f"<li>{_e(k)}: {_e(v)}</li>" for k, v in factors.items())
            + "</ul>"
        )

    engine_label = "LLM (Groq)" if source == "llm" else "Rules"
    demand_s = _e(demand.get("demand_score", product_data.get("demand_score", "n/a")))

    html_body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/></head>
<body style="font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#f3f6fb;color:#0f172a;padding:24px;">
<div style="max-width:700px;margin:0 auto;background:#ffffff;border-radius:16px;padding:24px;border:1px solid #e2e8f0;box-shadow:0 8px 24px rgba(15,23,42,0.08);">
  <p style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">AutoPrice AI</p>
  <h1 style="margin:8px 0 12px;font-size:24px;color:#0f172a;">Price {_e(direction.title())}</h1>
  <p style="margin:0 0 16px;color:#475569;font-size:14px;">{_e(product.get('name', 'Product'))}</p>
  <table style="width:100%;border-collapse:separate;border-spacing:0 8px;margin-bottom:12px;">
    <tr>
      <td style="padding:12px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;">
        <div style="font-size:11px;color:#64748b;">Previous</div>
        <div style="font-size:22px;font-weight:700;color:#1e293b;">₹{_e(f'{old_price:,.2f}')}</div>
      </td>
      <td style="width:32px;text-align:center;color:#94a3b8;">→</td>
      <td style="padding:12px;background:#ecfeff;border-radius:10px;border:1px solid #a5f3fc;">
        <div style="font-size:11px;color:#0e7490;">New</div>
        <div style="font-size:22px;font-weight:700;color:#0e7490;">₹{_e(f'{new_price:,.2f}')}</div>
      </td>
    </tr>
  </table>
  <p style="color:#334155;margin:6px 0;">Change: <strong>₹{_e(f'{delta:+,.2f}')}</strong>"""
    if pct is not None:
        html_body += f""" <span>({_e(f'{pct:+.2f}')}%)</span>"""
    html_body += f"""</p>
  <p style="color:#334155;margin:6px 0 0;">Projected margin: <strong>{_e(pricing.get('profit_margin', 'n/a'))}%</strong></p>
  <div style="margin-top:18px;padding:12px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;">
    <h2 style="font-size:15px;color:#0f172a;margin:0 0 6px;">Why this change</h2>
    <p style="line-height:1.6;color:#334155;margin:0;">{_e(pricing_reason)}</p>
  </div>
  <h2 style="font-size:15px;color:#0f172a;margin:20px 0 8px;">Agent analysis</h2>
  <ol style="line-height:1.6;color:#334155;padding-left:18px;margin:0;">
    <li><strong>Market</strong> — anchor ₹{_e(f'{anchor:,.2f}')}; demand {demand_s}.</li>
    <li><strong>Data</strong> — trend {_e(product_data.get('price_trend', 'n/a'))}; stock {_e(product_data.get('stock_level', product.get('stock', 'n/a')))}.</li>
    <li><strong>Pricing</strong> — {_e(engine_label)}; decision {_e(pricing.get('decision', 'n/a'))}.</li>
    <li><strong>Risk</strong> — {_e(validation.get('risk_level', 'n/a'))}; approved {_e(validation.get('is_approved', False))}.</li>
  </ol>
  <h3 style="margin:16px 0 8px;color:#0f172a;">Simulated peers</h3>
  {peer_html}
  {factors_html}
  <p style="margin-top:16px;color:#64748b;font-size:12px;">Sent automatically when the execution agent applied an approved update.</p>
</div></body></html>"""

    short_msg = (
        f"{product.get('name')}: ₹{old_price:,.0f} → ₹{new_price:,.0f} ({direction}"
        + (f", {pct:+.1f}%)" if pct is not None else ")")
        + f". {pricing_reason[:240]}"
    )
    subject = f"AutoPrice AI — {product.get('name', 'Product')}: ₹{old_price:,.0f} → ₹{new_price:,.0f}"
    return short_msg, subject, plain_body, html_body
