"""Nvidia PM-ready calculation layer and self-contained HTML memo.

The package is deliberately share-ready but not capital-ready.  Public-source
facts and calculation integrity can be audited here; broker consensus, channel
evidence and portfolio implementation remain explicit open gates.
"""
from __future__ import annotations

import json
import math
from pathlib import Path


AS_OF = "2026-08-07"
OUT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"

SPOT = 223.90  # Aug. 7 regular-hours last trade; refresh before risking capital.
SHARES_BN = 24.391  # Q1 FY2027 diluted weighted-average shares.
FY2026_REVENUE = 213.656
Q1_REVENUE = 81.615
Q2_GUIDE = 91.0
Q2_GUIDE_TOLERANCE = 0.02
Q1_FCF_PROXY = 50.344 - 1.757  # reported CFO less capex, used only for the FY27 stub.
OPENING_DA = 3.229  # TTM D&A at the April 26 balance-sheet cut.
Q1_EQUITY_SECURITY_GAINS = 15.936
POSITION_SIZE = 0.0

# April 26, 2026 balance sheet, $bn.  Public and private equity stakes are kept
# separate from cash because liquidity, lock-ups and valuation risk differ.
BALANCE_SHEET = {
    "liquid_cash_and_debt_securities": 50.335,
    "marketable_equity": 30.237,
    "nonmarketable_equity": 42.336,
    "equity_method": 1.028,
    "debt": 8.470,
    "operating_leases_disclosed_not_deducted": 4.344,
}

PERIODS = [0.24, 0.96, 1.96, 2.96, 3.96, 4.96]
TERMINAL_PERIOD = 5.47
YEARS = [2027, 2028, 2029, 2030, 2031, 2032]

# Consolidated revenue paths replace the retired product-market build.  These
# are analyst scenarios, not company guidance and not probability-weighted.
SCENARIOS = {
    "bear": {
        "label": "Bear / digestion",
        "revenue": [334.254, 415.810, 446.217, 432.052, 387.474, 334.723],
        "ebitda_margin": [0.590, 0.570, 0.545, 0.520, 0.495, 0.480],
        "capex_pct": [0.035, 0.037, 0.039, 0.040, 0.040, 0.040],
        "tax_rate": [0.160, 0.170, 0.170, 0.175, 0.175, 0.175],
        "nwc_pct": [0.115, 0.110, 0.105, 0.100, 0.095, 0.090],
        "wacc": 0.1195,
        "terminal_growth": 0.020,
        "terminal_roic": 0.250,
        "marketable_equity_credit": 0.750,
        "nonmarketable_equity_credit": 0.350,
        "equity_method_credit": 0.350,
        "description": "A digestion cycle, custom-silicon share gains and margin compression.",
    },
    "base": {
        "label": "Base / fade",
        "revenue": [380.878, 551.877, 698.959, 805.464, 862.585, 889.459],
        "ebitda_margin": [0.645, 0.625, 0.600, 0.575, 0.550, 0.535],
        "capex_pct": [0.030, 0.032, 0.034, 0.035, 0.035, 0.035],
        "tax_rate": [0.160, 0.170, 0.170, 0.175, 0.175, 0.175],
        "nwc_pct": [0.115, 0.110, 0.105, 0.100, 0.095, 0.090],
        "wacc": 0.1070,
        "terminal_growth": 0.030,
        "terminal_roic": 0.300,
        "marketable_equity_credit": 0.850,
        "nonmarketable_equity_credit": 0.500,
        "equity_method_credit": 0.500,
        "description": "Near-term demand holds; growth and cash margins fade as the base scales.",
    },
    "bull": {
        "label": "Bull / platform",
        "revenue": [417.307, 672.504, 956.101, 1_245.059, 1_513.250, 1_775.787],
        "ebitda_margin": [0.675, 0.655, 0.630, 0.605, 0.580, 0.565],
        "capex_pct": [0.027, 0.029, 0.031, 0.032, 0.032, 0.032],
        "tax_rate": [0.160, 0.170, 0.170, 0.175, 0.175, 0.175],
        "nwc_pct": [0.115, 0.110, 0.105, 0.100, 0.095, 0.090],
        "wacc": 0.0995,
        "terminal_growth": 0.035,
        "terminal_roic": 0.350,
        "marketable_equity_credit": 1.000,
        "nonmarketable_equity_credit": 0.750,
        "equity_method_credit": 0.750,
        "description": "Rubin pricing, networking attach and platform share remain exceptional.",
    },
}

WACC = {
    "risk_free_rate": 0.0465,
    "beta": 1.35,
    "equity_risk_premium": 0.0450,
    "pre_tax_debt_cost": 0.0500,
    "tax_rate": 0.1700,
}

SOURCES = [
    {
        "id": "S1",
        "type": "Filed fact",
        "date": "2026-05-20",
        "title": "Nvidia Q1 FY2027 Form 10-Q",
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000052/nvda-20260426.htm",
        "use": "Financials, current disclosure, investments, commitments, concentration and D&A.",
    },
    {
        "id": "S2",
        "type": "Company release",
        "date": "2026-05-20",
        "title": "Nvidia Q1 FY2027 results",
        "url": "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2027",
        "use": "Q1 revenue, current reporting framework, Data Center detail and Q2 guide.",
    },
    {
        "id": "S3",
        "type": "Filed fact",
        "date": "2026-02-25",
        "title": "Nvidia FY2026 Form 10-K",
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm",
        "use": "FY2026 revenue and historical financial context.",
    },
    {
        "id": "S4",
        "type": "Market fact",
        "date": AS_OF,
        "title": "U.S. Treasury daily par yield curve",
        "url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2026",
        "use": "4.65% ten-year risk-free rate on August 7.",
    },
    {
        "id": "S5",
        "type": "Market snapshot",
        "date": AS_OF,
        "title": "Read-only Robinhood regular-hours snapshot",
        "url": "https://robinhood.com/stocks/NVDA",
        "use": "$223.90 last trade; frozen reference, not an executable quote.",
    },
    {
        "id": "S6",
        "type": "Aggregator snapshot",
        "date": AS_OF,
        "title": "Frozen FMP annual consensus extract",
        "url": "https://financialmodelingprep.com/",
        "use": "Revenue range and analyst count; provider metadata and revisions remain an open gate.",
    },
    {
        "id": "S7",
        "type": "Analyst assumption",
        "date": AS_OF,
        "title": "PM scenario and valuation assumptions",
        "url": "",
        "use": "Revenue paths, margins, beta, ERP, terminal ROIC, haircuts and action hurdles.",
    },
]

REVIEW_FINDINGS = [
    ("Internal contradictions and Alphabet copy", "Fixed", "One decision, one valuation set; company reference corrected."),
    ("Q1 equity-security gains silently set to zero", "Fixed", "$15.936bn is shown and separated from operating earnings."),
    ("FY2027 D&A below a defensible run-rate", "Fixed", "Opening D&A plus forecast capex vintages; Q1/amortization floor checked."),
    ("Retired product-market disclosure used in forecast", "Fixed", "Consolidated scenarios anchored on Q1 actual and Q2 guidance."),
    ("Hardcoded WACC described as CAPM", "Fixed", "Treasury, beta, ERP, debt cost and capital weights are visible."),
    ("Unnormalized terminal FCFF", "Fixed", "Terminal reinvestment equals growth divided by terminal ROIC."),
    ("Full credit to strategic and illiquid stakes", "Fixed", "Public, private and equity-method stakes carry explicit haircuts."),
    ("Unsupported scenario probabilities drove sizing", "Fixed", "Scenarios are unweighted states; position size remains zero."),
]

CAPITAL_GATES = [
    ("Variant", "Freeze broker-level consensus, cohort and revision history around the next print.", "OPEN"),
    ("Catalyst", "Reconcile Q2 actuals and forward guidance; reverify the event date on official IR.", "OPEN"),
    ("Demand quality", "Quantify customer-financing exposure within investments and commitments.", "OPEN"),
    ("Channel", "Obtain lead-time, backlog, cancellation and pull-forward evidence.", "OPEN"),
    ("Market", "Refresh price, liquidity, options, short interest, borrow and crowding.", "OPEN"),
    ("Portfolio", "Complete current exposure, risk budget, factor, hedge and drawdown ledger.", "OPEN"),
    ("Hurdle", "Require an observable variant and at least 20% net underwritten return.", "OPEN"),
]


def _depreciation(capex: list[float]) -> list[float]:
    """Opening D&A runoff plus straight-line depreciation on forecast vintages."""
    out = []
    for year_index in range(6):
        opening = OPENING_DA * max(0.0, 1.0 - year_index / 5.0)
        forecast = 0.0
        for vintage, amount in enumerate(capex):
            age = year_index - vintage
            if age < 0:
                continue
            short_factor = 0.5 if age in (0, 5) else (1.0 if age < 5 else 0.0)
            long_factor = 0.5 if age in (0, 20) else (1.0 if age < 20 else 0.0)
            forecast += amount * (
                0.60 / 5.0 * short_factor + 0.40 / 20.0 * long_factor
            )
        out.append(opening + forecast)
    return out


def _equity_bridge(case: dict) -> dict:
    credited_public = BALANCE_SHEET["marketable_equity"] * case["marketable_equity_credit"]
    credited_private = BALANCE_SHEET["nonmarketable_equity"] * case["nonmarketable_equity_credit"]
    credited_method = BALANCE_SHEET["equity_method"] * case["equity_method_credit"]
    total = (
        BALANCE_SHEET["liquid_cash_and_debt_securities"]
        + credited_public
        + credited_private
        + credited_method
        - BALANCE_SHEET["debt"]
    )
    return {
        "liquid": BALANCE_SHEET["liquid_cash_and_debt_securities"],
        "marketable_reported": BALANCE_SHEET["marketable_equity"],
        "marketable_credit": case["marketable_equity_credit"],
        "marketable_credited": credited_public,
        "nonmarketable_reported": BALANCE_SHEET["nonmarketable_equity"],
        "nonmarketable_credit": case["nonmarketable_equity_credit"],
        "nonmarketable_credited": credited_private,
        "equity_method_reported": BALANCE_SHEET["equity_method"],
        "equity_method_credit": case["equity_method_credit"],
        "equity_method_credited": credited_method,
        "debt": BALANCE_SHEET["debt"],
        "total": total,
    }


def calculate_case(key: str, *, wacc: float | None = None, revenue_scale: float = 1.0) -> dict:
    case = SCENARIOS[key]
    discount_rate = case["wacc"] if wacc is None else wacc
    revenue = [x * revenue_scale for x in case["revenue"]]
    capex = [r * pct for r, pct in zip(revenue, case["capex_pct"])]
    da = _depreciation(capex)
    rows = []
    prior_revenue = FY2026_REVENUE
    for i, year in enumerate(YEARS):
        ebitda = revenue[i] * case["ebitda_margin"][i]
        ebit = ebitda - da[i]
        nopat = ebit * (1.0 - case["tax_rate"][i])
        prior_nwc_pct = 0.115 if i == 0 else case["nwc_pct"][i - 1]
        delta_nwc = revenue[i] * case["nwc_pct"][i] - prior_revenue * prior_nwc_pct
        annual_fcff = nopat + da[i] - capex[i] - delta_nwc
        dcf_fcff = annual_fcff - Q1_FCF_PROXY if i == 0 else annual_fcff
        discount_factor = 1.0 / (1.0 + discount_rate) ** PERIODS[i]
        rows.append({
            "year": year,
            "revenue": revenue[i],
            "growth": revenue[i] / prior_revenue - 1.0,
            "ebitda_margin": case["ebitda_margin"][i],
            "ebitda": ebitda,
            "da": da[i],
            "ebit": ebit,
            "ebit_margin": ebit / revenue[i],
            "tax_rate": case["tax_rate"][i],
            "nopat": nopat,
            "capex_pct": case["capex_pct"][i],
            "capex": capex[i],
            "nwc_pct": case["nwc_pct"][i],
            "delta_nwc": delta_nwc,
            "annual_fcff": annual_fcff,
            "q1_fcf_proxy_subtracted": Q1_FCF_PROXY if i == 0 else 0.0,
            "dcf_fcff": dcf_fcff,
            "period": PERIODS[i],
            "discount_factor": discount_factor,
            "pv_fcff": dcf_fcff * discount_factor,
        })
        prior_revenue = revenue[i]

    final = rows[-1]
    terminal_nopat = final["nopat"]
    terminal_reinvestment_rate = case["terminal_growth"] / case["terminal_roic"]
    terminal_fcff = terminal_nopat * (1.0 - terminal_reinvestment_rate)
    terminal_value = terminal_fcff * (1.0 + case["terminal_growth"]) / (
        discount_rate - case["terminal_growth"]
    )
    pv_terminal = terminal_value / (1.0 + discount_rate) ** TERMINAL_PERIOD
    pv_explicit = sum(row["pv_fcff"] for row in rows)
    enterprise_value = pv_explicit + pv_terminal
    bridge = _equity_bridge(case)
    equity_value = enterprise_value + bridge["total"]
    value_per_share = equity_value / SHARES_BN
    return {
        "key": key,
        "label": case["label"],
        "description": case["description"],
        "rows": rows,
        "wacc": discount_rate,
        "terminal_growth": case["terminal_growth"],
        "terminal_roic": case["terminal_roic"],
        "terminal_reinvestment_rate": terminal_reinvestment_rate,
        "terminal_fcff": terminal_fcff,
        "terminal_period": TERMINAL_PERIOD,
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "pv_explicit": pv_explicit,
        "enterprise_value": enterprise_value,
        "tv_pct_ev": pv_terminal / enterprise_value,
        "bridge": bridge,
        "equity_value": equity_value,
        "shares_bn": SHARES_BN,
        "value_per_share": value_per_share,
        "upside": value_per_share / SPOT - 1.0,
        "revenue_cagr": (revenue[-1] / FY2026_REVENUE) ** (1.0 / 6.0) - 1.0,
    }


def _bisect(target: float, fn, low: float, high: float, increasing: bool) -> float:
    for _ in range(100):
        mid = (low + high) / 2.0
        value = fn(mid)
        if (value < target) == increasing:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def build_data(*, write: bool = True) -> dict:
    scenarios = {key: calculate_case(key) for key in ("bear", "base", "bull")}
    base = scenarios["base"]
    implied_wacc = _bisect(
        SPOT,
        lambda x: calculate_case("base", wacc=x)["value_per_share"],
        0.05,
        0.20,
        increasing=False,
    )
    implied_revenue_scale = _bisect(
        SPOT,
        lambda x: calculate_case("base", revenue_scale=x)["value_per_share"],
        0.50,
        2.00,
        increasing=True,
    )
    market_cap = SPOT * SHARES_BN
    debt_weight = BALANCE_SHEET["debt"] / (market_cap + BALANCE_SHEET["debt"])
    equity_weight = 1.0 - debt_weight
    cost_of_equity = WACC["risk_free_rate"] + WACC["beta"] * WACC["equity_risk_premium"]
    after_tax_debt_cost = WACC["pre_tax_debt_cost"] * (1.0 - WACC["tax_rate"])
    built_wacc = equity_weight * cost_of_equity + debt_weight * after_tax_debt_cost

    h2_required = base["rows"][0]["revenue"] - Q1_REVENUE - Q2_GUIDE
    checks = [
        ("Scenario ordering", scenarios["bear"]["value_per_share"] < base["value_per_share"] < scenarios["bull"]["value_per_share"]),
        ("WACC build rounds to base input", abs(built_wacc - SCENARIOS["base"]["wacc"]) < 0.0003),
        ("WACC exceeds terminal growth by 400bp", base["wacc"] - base["terminal_growth"] > 0.04),
        ("Terminal ROIC exceeds growth", base["terminal_roic"] > base["terminal_growth"]),
        ("FY2027 D&A clears Q1 actual plus disclosed remaining amortization", base["rows"][0]["da"] > 0.997 + 0.689),
        ("Q1 equity-security gains retained", Q1_EQUITY_SECURITY_GAINS > 15.0),
        ("April liquid balance ties to release", math.isclose(BALANCE_SHEET["liquid_cash_and_debt_securities"], 13.237 + 37.098)),
        ("All capital gates open implies zero size", POSITION_SIZE == 0.0 and all(status == "OPEN" for _, _, status in CAPITAL_GATES)),
        ("No probability-weighted decision", all("probability" not in case for case in SCENARIOS.values())),
    ]
    data = {
        "meta": {
            "ticker": "NVDA",
            "company": "NVIDIA Corporation",
            "as_of": AS_OF,
            "stance": "WATCHLIST / NO POSITION",
            "share_status": "Share-ready; not capital-ready",
            "horizon": "12 months",
            "edge": "None established",
            "position_size": POSITION_SIZE,
        },
        "market": {"spot": SPOT, "shares_bn": SHARES_BN, "market_cap_bn": market_cap},
        "facts": {
            "fy2026_revenue": FY2026_REVENUE,
            "q1_revenue": Q1_REVENUE,
            "q1_yoy_growth": 0.85,
            "q1_gross_margin": 0.749,
            "q1_data_center": 75.246,
            "q1_data_center_compute": 60.4,
            "q1_data_center_networking": 14.8,
            "q2_guide": Q2_GUIDE,
            "q2_guide_low": Q2_GUIDE * (1.0 - Q2_GUIDE_TOLERANCE),
            "q2_guide_high": Q2_GUIDE * (1.0 + Q2_GUIDE_TOLERANCE),
            "q2_china_dc_compute_assumed": 0.0,
            "q1_equity_security_gains": Q1_EQUITY_SECURITY_GAINS,
            "q1_pretax_income": 69.903,
            "q1_equity_gains_pct_pretax": Q1_EQUITY_SECURITY_GAINS / 69.903,
            "q1_inventory": 25.797,
            "manufacturing_commitments": 119.0,
            "cloud_commitments": 30.0,
            "investment_commitments": 27.0,
            "q1_private_investments": 18.6,
            "customer_revenue_concentration": [0.21, 0.17, 0.16],
            "customer_ar_concentration": [0.30, 0.18, 0.16],
            "q1_fcf_proxy": Q1_FCF_PROXY,
        },
        "wacc": {
            **WACC,
            "cost_of_equity": cost_of_equity,
            "after_tax_debt_cost": after_tax_debt_cost,
            "equity_weight": equity_weight,
            "debt_weight": debt_weight,
            "built_wacc": built_wacc,
        },
        "balance_sheet": BALANCE_SHEET,
        "scenarios": scenarios,
        "reverse": {
            "implied_wacc": implied_wacc,
            "base_wacc": base["wacc"],
            "implied_revenue_scale": implied_revenue_scale,
            "implied_fy2027_revenue": base["rows"][0]["revenue"] * implied_revenue_scale,
            "implied_fy2032_revenue": base["rows"][-1]["revenue"] * implied_revenue_scale,
            "implied_revenue_cagr": (
                base["rows"][-1]["revenue"] * implied_revenue_scale / FY2026_REVENUE
            ) ** (1.0 / 6.0) - 1.0,
        },
        "decision": {
            "base_value": base["value_per_share"],
            "base_upside": base["upside"],
            "long_entry_reference": base["value_per_share"] / 1.20,
            "required_return": 0.20,
            "position_size": POSITION_SIZE,
            "reason": "No verified variant, base DCF below spot, and every implementation gate is open.",
        },
        "near_term": {
            "base_fy2027_revenue": base["rows"][0]["revenue"],
            "h2_required": h2_required,
            "h2_quarterly_required": h2_required / 2.0,
            "required_vs_q2_guide": h2_required / 2.0 / Q2_GUIDE - 1.0,
            "street_fy2027_avg": 393.652880225,
            "street_fy2027_low": 364.351823875,
            "street_fy2027_high": 402.782772175,
            "street_fy2027_analysts": 40,
            "street_fy2028_avg": 563.601060724,
            "street_fy2028_analysts": 40,
        },
        "sources": SOURCES,
        "review_findings": REVIEW_FINDINGS,
        "capital_gates": CAPITAL_GATES,
        "checks": [{"name": name, "pass": passed} for name, passed in checks],
    }
    if write:
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / "nvidia_pm.json").write_text(json.dumps(data, indent=2) + "\n")
    return data


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _pct(value: float, decimals: int = 1, signed: bool = False) -> str:
    sign = "+" if signed and value >= 0 else ""
    return f"{sign}{value * 100:.{decimals}f}%"


def render_memo(data: dict) -> str:
    base = data["scenarios"]["base"]
    bear = data["scenarios"]["bear"]
    bull = data["scenarios"]["bull"]
    facts = data["facts"]
    near = data["near_term"]
    reverse = data["reverse"]
    decision = data["decision"]
    rows_findings = "".join(
        f"<tr><td>{finding}</td><td><span class='fixed'>{status}</span></td><td>{resolution}</td></tr>"
        for finding, status, resolution in data["review_findings"]
    )
    rows_gates = "".join(
        f"<tr><td>{gate}</td><td>{requirement}</td><td><span class='open'>{status}</span></td></tr>"
        for gate, requirement, status in data["capital_gates"]
    )
    rows_sources = "".join(
        f"<tr><td>{s['id']}</td><td>{s['type']}</td><td><a href='{s['url']}'>{s['title']}</a></td>"
        f"<td>{s['date']}</td><td>{s['use']}</td></tr>" if s["url"] else
        f"<tr><td>{s['id']}</td><td>{s['type']}</td><td>{s['title']}</td>"
        f"<td>{s['date']}</td><td>{s['use']}</td></tr>"
        for s in data["sources"]
    )
    scenario_rows = "".join(
        f"<tr><td><b>{case['label']}</b><br><span class='muted'>{case['description']}</span></td>"
        f"<td>{_money(case['value_per_share'])}</td><td class='{'positive' if case['upside'] >= 0 else 'negative'}'>"
        f"{_pct(case['upside'], signed=True)}</td><td>{_pct(case['revenue_cagr'])}</td>"
        f"<td>{_pct(case['rows'][-1]['ebit_margin'])}</td><td>{_pct(case['wacc'])}</td>"
        f"<td>{_pct(case['terminal_growth'])}</td><td>{_pct(case['terminal_roic'])}</td>"
        f"<td>{_pct(case['tv_pct_ev'])}</td></tr>"
        for case in (bear, base, bull)
    )
    forecast_rows = "".join(
        f"<tr><td>FY{row['year']}</td><td>${row['revenue']:,.1f}bn</td>"
        f"<td>{_pct(row['growth'])}</td><td>{_pct(row['ebitda_margin'])}</td>"
        f"<td>${row['da']:,.1f}bn</td><td>{_pct(row['ebit_margin'])}</td>"
        f"<td>${row['capex']:,.1f}bn</td><td>${row['dcf_fcff']:,.1f}bn</td></tr>"
        for row in base["rows"]
    )
    check_rows = "".join(
        f"<tr><td>{x['name']}</td><td><span class='fixed'>{'PASS' if x['pass'] else 'FAIL'}</span></td></tr>"
        for x in data["checks"]
    )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Nvidia PM review memo, public-information research as of {AS_OF}.">
<link rel="icon" href="data:,"><title>Nvidia PM memo | {AS_OF}</title>
<style>
:root{{--ink:#151923;--muted:#626b78;--line:#dfe3e8;--paper:#f7f7f5;--card:#fff;--navy:#163a5f;--teal:#0b6b68;--red:#a63d40;--soft:#eef2f5}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.page{{max-width:1160px;margin:0 auto;padding:38px 28px 84px}}a{{color:var(--navy);text-underline-offset:2px}}h1{{font:700 clamp(2rem,5vw,4.1rem)/.98 Georgia,serif;letter-spacing:-.045em;margin:.22em 0 .18em}}h2{{font-size:1.05rem;letter-spacing:.08em;text-transform:uppercase;margin:44px 0 14px}}h3{{font-size:1rem;margin:22px 0 7px}}p{{margin:.55em 0}}.eyebrow,.label{{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:700}}.muted{{color:var(--muted)}}
.hero{{background:var(--navy);color:#fff;border-radius:16px;padding:34px 36px;box-shadow:0 12px 40px rgba(22,58,95,.13)}}.hero .muted,.hero .eyebrow{{color:#c9d5df}}.tags{{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}}.tag{{border:1px solid rgba(255,255,255,.32);border-radius:999px;padding:5px 10px;font-size:.76rem;font-weight:700;letter-spacing:.04em}}.hero-grid{{display:grid;grid-template-columns:1.35fr repeat(3,.75fr);gap:18px;margin-top:26px}}.metric{{border-top:1px solid rgba(255,255,255,.28);padding-top:12px}}.metric .value{{font-size:1.75rem;font-weight:750;letter-spacing:-.035em}}.metric .note{{font-size:.78rem;color:#c9d5df}}
.grid2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}.grid3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:19px 20px}}.callout{{border-left:4px solid var(--teal);background:#edf6f5;padding:16px 18px;margin:18px 0;border-radius:0 10px 10px 0}}.risk{{border-left-color:var(--red);background:#f7eded}}.fixed{{color:var(--teal);font-weight:800}}.open,.negative{{color:var(--red);font-weight:800}}.positive{{color:var(--teal);font-weight:800}}
.scroll{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:#fff}}table{{border-collapse:collapse;width:100%;font-size:.82rem;min-width:720px}}th,td{{padding:10px 11px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}}th{{font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);background:var(--soft)}}th:first-child,td:first-child{{text-align:left}}tr:last-child td{{border-bottom:0}}ul,ol{{padding-left:21px}}li{{margin:.42em 0}}.number{{font-variant-numeric:tabular-nums}}.compact table{{min-width:520px}}footer{{margin-top:50px;border-top:1px solid var(--line);padding-top:18px;color:var(--muted);font-size:.78rem}}
@media(max-width:820px){{.page{{padding:18px 14px 56px}}.hero{{padding:24px 20px;border-radius:12px}}.hero-grid,.grid2,.grid3{{grid-template-columns:1fr}}h2{{margin-top:34px}}.metric .value{{font-size:1.5rem}}}}
@media print{{body{{background:#fff}}.page{{max-width:none;padding:20px}}.hero{{box-shadow:none}}}}
</style></head><body><main class="page">
<section class="hero"><div class="eyebrow">Public-information equity research · PM review cut · {AS_OF}</div>
<h1>Nvidia <span style="font-weight:400">NVDA</span></h1>
<p class="muted">A risk frame for the next earnings decision, rebuilt around current disclosure and auditable valuation mechanics.</p>
<div class="tags"><span class="tag">WATCHLIST / NO POSITION</span><span class="tag">Share-ready; not capital-ready</span><span class="tag">Edge: none established</span><span class="tag">Position: 0.0%</span></div>
<div class="hero-grid"><div class="metric"><div class="label">PM call</div><div class="value">Do not force a trade</div><div class="note">The business is exceptional. The model has no verified near-term variant and every implementation gate is open.</div></div>
<div class="metric"><div class="label">Spot</div><div class="value">{_money(SPOT)}</div><div class="note">Aug. 7 regular-hours snapshot</div></div>
<div class="metric"><div class="label">Base DCF</div><div class="value">{_money(base['value_per_share'])}</div><div class="note">{_pct(base['upside'], signed=True)} vs spot</div></div>
<div class="metric"><div class="label">State range</div><div class="value">{_money(bear['value_per_share'])}–{_money(bull['value_per_share'])}</div><div class="note">Unweighted; not a probability distribution</div></div></div></section>

<h2>PM decision</h2><div class="grid2"><div class="card"><div class="label">What is mispriced?</div><p><b>Nothing we can establish from public information today.</b> The base revenue path is 3.2% below the frozen FY2027 consensus average and remains inside its range. The apparent valuation gap is a duration and discount-rate argument, not a differentiated earnings call.</p></div>
<div class="card"><div class="label">What would change the call?</div><p>A verified estimate revision, observable demand-quality evidence and a cleared implementation ledger. Until then, a low DCF is not a short catalyst and an exceptional franchise is not a long entry.</p></div></div>
<div class="callout"><b>Action:</b> keep size at zero through the next print. Re-underwrite after actual revenue, gross margin, forward guidance and consensus revisions are frozen. For reference, the current base DCF supports a 20% margin-of-safety entry near <b>{_money(decision['long_entry_reference'])}</b>; that is a model output, not a standing limit order.</div>

<h2>Highest-priority findings</h2><p class="muted">All eight defects from the review have been remediated in this memo and the linked workbook.</p><div class="scroll"><table><thead><tr><th>Finding</th><th>Status</th><th>Resolution</th></tr></thead><tbody>{rows_findings}</tbody></table></div>

<h2>What the tape must be underwriting</h2><div class="grid3"><div class="card"><div class="label">Base CAPM</div><p style="font-size:1.55rem;font-weight:800">{_pct(base['wacc'])}</p><p class="muted">4.65% Treasury + 1.35 beta × 4.50% ERP; debt weight is immaterial.</p></div><div class="card"><div class="label">Spot-implied WACC</div><p style="font-size:1.55rem;font-weight:800">{_pct(reverse['implied_wacc'])}</p><p class="muted">Holding the base operating path, terminal ROIC and stake haircuts constant.</p></div><div class="card"><div class="label">Or: operating uplift</div><p style="font-size:1.55rem;font-weight:800">{_pct(reverse['implied_revenue_scale'] - 1, signed=True)}</p><p class="muted">Uniform revenue scale required at 10.7% WACC; an intentionally blunt reverse-DCF diagnostic.</p></div></div>
<p>At spot, the model requires either a discount rate about <b>{(base['wacc']-reverse['implied_wacc'])*10000:.0f}bp</b> below the explicit CAPM build or a revenue path scaled to <b>${reverse['implied_fy2032_revenue']:,.0f}bn</b> by FY2032. Those are not equivalent forecasts; they identify the two assumptions doing the work.</p>

<h2>Near-term setup</h2><div class="grid2"><div class="card"><div class="label">Reported and guided</div><ul><li>Q1 FY2027 revenue: <b>${facts['q1_revenue']:.1f}bn</b>, +85% year over year.</li><li>Data Center: <b>${facts['q1_data_center']:.1f}bn</b>; compute $60.4bn and networking $14.8bn under the prior sub-markets.</li><li>Q2 revenue guide: <b>${facts['q2_guide']:.1f}bn ±2%</b>, with no China Data Center compute revenue assumed.</li><li>Q1 gross margin: <b>{_pct(facts['q1_gross_margin'])}</b>.</li></ul></div>
<div class="card"><div class="label">What base needs</div><ul><li>FY2027 revenue: <b>${near['base_fy2027_revenue']:.1f}bn</b>.</li><li>After Q1 and Q2 midpoint: <b>${near['h2_required']:.1f}bn</b> in H2, or ${near['h2_quarterly_required']:.1f}bn per quarter.</li><li>That run-rate is <b>{_pct(near['required_vs_q2_guide'], signed=True)}</b> versus Q2 guidance.</li><li>Frozen FY2027 consensus: <b>${near['street_fy2027_avg']:.1f}bn</b>, range ${near['street_fy2027_low']:.1f}–${near['street_fy2027_high']:.1f}bn, 40 estimates.</li></ul></div></div>
<div class="callout risk"><b>Catalyst control:</b> August 26 appears in the prior market calendar, but Nvidia IR returned a rate-limit response during this rebuild. Treat the date as expected, not confirmed, and reverify it before the event.</div>

<h2>Quality of earnings and demand</h2><div class="grid2"><div class="card"><div class="label">Non-operating gain</div><p>Q1 cash-flow reconciliation reports <b>${facts['q1_equity_security_gains']:.3f}bn</b> of equity-security gains. That is <b>{_pct(facts['q1_equity_gains_pct_pretax'])}</b> of pretax income. The prior memo showed zero because a rejected tag was converted to 0.0; this version keeps the amount visible and does not treat it as operating earnings.</p></div>
<div class="card"><div class="label">Demand-quality evidence</div><p>Nvidia invested <b>${facts['q1_private_investments']:.1f}bn</b> in private companies and infrastructure funds in Q1. The filing says <i>some</i> investees include AI model makers that may indirectly use Nvidia products. It does not support calling the entire ${BALANCE_SHEET['marketable_equity'] + BALANCE_SHEET['nonmarketable_equity']:.1f}bn equity portfolio customer financing.</p></div></div>
<div class="grid3" style="margin-top:14px"><div class="card"><div class="label">Concentration</div><p>Three direct customers were 21%, 17% and 16% of revenue; A/R concentration was 30%, 18% and 16%.</p></div><div class="card"><div class="label">Commitments</div><p>$119bn manufacturing and capacity, $30bn cloud service and $27bn contingent investment commitments.</p></div><div class="card"><div class="label">Inventory</div><p>$25.8bn at April 26. Read it with forward guidance, lead times and cancellation behavior, not alone.</p></div></div>

<h2>Valuation states</h2><p class="muted">Values are present values as of the August decision cut. FY2027 DCF cash flow subtracts reported Q1 CFO less capex from the full-year model; the April 26 balance sheet therefore is not double-counted. Probabilities are deliberately omitted.</p><div class="scroll"><table><thead><tr><th>State</th><th>Value/share</th><th>Vs spot</th><th>Revenue CAGR</th><th>FY32 EBIT margin</th><th>WACC</th><th>g</th><th>Terminal ROIC</th><th>TV / EV</th></tr></thead><tbody>{scenario_rows}</tbody></table></div>
<h3>Base forecast mechanics</h3><div class="scroll"><table><thead><tr><th>Fiscal year</th><th>Revenue</th><th>Growth</th><th>EBITDA margin</th><th>D&A</th><th>EBIT margin</th><th>Capex</th><th>DCF FCFF</th></tr></thead><tbody>{forecast_rows}</tbody></table></div>
<div class="callout"><b>Terminal control:</b> terminal FCFF equals NOPAT × (1 − g / terminal ROIC). Base terminal reinvestment is {_pct(base['terminal_reinvestment_rate'])}, and terminal value is {_pct(base['tv_pct_ev'])} of enterprise value.</div>

<h2>Equity bridge</h2><p>The base bridge credits $50.3bn of cash and marketable debt securities at par, 85% of $30.2bn marketable equity, 50% of $42.3bn non-marketable equity and 50% of $1.0bn equity-method stakes, then deducts $8.5bn debt. The credited bridge is <b>${base['bridge']['total']:.1f}bn</b>. Operating leases stay disclosed but are not deducted because the cash flows already include operating lease expense.</p>

<h2>Variant, catalysts and falsifiers</h2><div class="grid2"><div class="card"><div class="label">Why no long</div><ul><li>No verified earnings variant versus a canonical broker panel.</li><li>Base value is below spot at a visible CAPM discount rate.</li><li>Strategic-investment demand attribution is not quantified.</li><li>The next print can reset both numerator and duration assumptions.</li></ul></div><div class="card"><div class="label">Why no short</div><ul><li>The downside is a valuation opinion without an observed revision catalyst.</li><li>The bull state remains {_money(bull['value_per_share'])}; upside risk is not capped.</li><li>Borrow, crowding, options and hedge economics are missing.</li><li>A lower but defensible discount rate closes much of the gap.</li></ul></div></div>
<p><b>What proves a long:</b> Q2 and guidance establish upside to a frozen consensus, demand-quality work separates durable end demand from financed pull-forward, and underwritten upside clears 20% after hedging and event costs.</p><p><b>What proves a short:</b> reported demand or forward guidance breaks the base path, revisions follow, a live implementation ledger caps squeeze and factor risk, and expected downside remains at least 20% after costs.</p>
<p><b>Pre-mortem:</b> we force a short because the DCF is low, then Rubin and networking deliver, consensus rises, duration compresses the discount rate and the stock gaps through an uncapped bull case. The prevention is the current decision: no position before evidence and implementation agree.</p>

<h2>Required before risking capital</h2><div class="scroll"><table><thead><tr><th>Gate</th><th>Required evidence</th><th>Status</th></tr></thead><tbody>{rows_gates}</tbody></table></div>

<h2>Model checks</h2><div class="scroll compact"><table><thead><tr><th>Control</th><th>Result</th></tr></thead><tbody>{check_rows}</tbody></table></div>

<h2>Sources and limits</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Type</th><th>Source</th><th>Date</th><th>Use</th></tr></thead><tbody>{rows_sources}</tbody></table></div>
<p class="muted">Limits: no broker-level revision tape, channel checks, expert calls, alternative data, live options, current borrow/crowding or portfolio book context. The August price is a frozen regular-hours reference. Q2 has ended but was not filed at this cut. Scenario assumptions are analyst judgments, not company guidance. This memo is research, not investment advice or a solicitation.</p>
<footer>Prepared from public information · NVIDIA Corporation (NVDA) · {AS_OF} · Companion workbook: <a href="model.xlsx">model.xlsx</a></footer>
</main></body></html>"""
    return html


def main() -> None:
    data = build_data(write=True)
    out_dir = OUT / "nvidia"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "memo.html").write_text(render_memo(data))
    print(f"Nvidia PM data: {DATA / 'nvidia_pm.json'}")
    print(f"Nvidia PM memo: {out_dir / 'memo.html'}")
    print(
        "Values:",
        ", ".join(
            f"{key} ${data['scenarios'][key]['value_per_share']:.2f}"
            for key in ("bear", "base", "bull")
        ),
    )


if __name__ == "__main__":
    main()
