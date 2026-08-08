"""Render the PM memo and evidence appendix to a self-contained HTML page."""
from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path

import cases
import decision

DATA = Path(__file__).parent / "data"
OUT = Path(__file__).parent.parent
AS_OF = "2026-08-07"

CSS = """
:root{--bg:#fbfaf8;--fg:#16181d;--muted:#5f6672;--line:#e2ded7;--card:#fff;
--pos:#0f7a52;--neg:#b3261e;--warn:#8a6100;--accent:#1a4fa0;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
@media(prefers-color-scheme:dark){:root{--bg:#12141a;--fg:#e9e6e1;--muted:#9aa3b0;--line:#282d38;
--card:#191c24;--pos:#4ec99a;--neg:#f2857c;--warn:#e0b062;--accent:#7aa7f0}}
:root[data-theme=dark]{--bg:#12141a;--fg:#e9e6e1;--muted:#9aa3b0;--line:#282d38;--card:#191c24;
--pos:#4ec99a;--neg:#f2857c;--warn:#e0b062;--accent:#7aa7f0}
:root[data-theme=light]{--bg:#fbfaf8;--fg:#16181d;--muted:#5f6672;--line:#e2ded7;--card:#fff;
--pos:#0f7a52;--neg:#b3261e;--warn:#8a6100;--accent:#1a4fa0}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 ui-serif,Georgia,'Times New Roman',serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:40px 28px 90px}
h1{font-size:31px;margin:.1em 0 .05em;letter-spacing:-.015em}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);
margin:38px 0 12px;font-family:system-ui,sans-serif;font-weight:600}
h3{font-size:16px;margin:20px 0 6px}
p{margin:.55em 0}
.sub{color:var(--muted);font-size:14px}
.eyebrow{font-family:system-ui,sans-serif;font-size:11px;letter-spacing:.16em;
text-transform:uppercase;color:var(--muted)}
.rule{height:1px;background:var(--line);margin:26px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:18px 20px}
.grid{display:grid;gap:14px}
.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}
.g4{grid-template-columns:repeat(4,1fr)}
.kpi{font-family:system-ui,sans-serif}
.kpi .lab{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
.kpi .val{font-size:25px;font-weight:600;letter-spacing:-.02em;margin-top:3px}
.kpi .note{font-size:12px;color:var(--muted);margin-top:2px}
.pos{color:var(--pos)}.neg{color:var(--neg)}.warn{color:var(--warn)}
.tag{display:inline-block;font-family:system-ui,sans-serif;font-size:11px;font-weight:600;
letter-spacing:.06em;padding:3px 9px;border-radius:999px;border:1px solid var(--line);
color:var(--muted);margin-right:6px}
.tag.big{font-size:13px;padding:5px 14px;color:var(--fg)}
table{border-collapse:collapse;width:100%;font-family:system-ui,sans-serif;font-size:13px;margin:8px 0}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:right}
th:first-child,td:first-child{text-align:left}
th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600}
tbody tr:hover{background:color-mix(in srgb,var(--accent) 6%,transparent)}
.scroll{overflow-x:auto;max-width:100%}
.num{font-variant-numeric:tabular-nums;font-family:var(--mono);font-size:12.5px}
ol,ul{padding-left:20px;margin:.5em 0}li{margin:.35em 0}
.thesis{counter-reset:t}
.thesis li{list-style:none;position:relative;padding-left:34px;margin:14px 0}
.thesis li:before{counter-increment:t;content:counter(t);position:absolute;left:0;top:1px;
width:22px;height:22px;border-radius:50%;background:var(--accent);color:#fff;
font:600 12px/22px system-ui,sans-serif;text-align:center}
.thesis .k{font-family:system-ui,sans-serif;font-size:11px;text-transform:uppercase;
letter-spacing:.08em;color:var(--muted);display:block}
.bar{height:26px;position:relative;background:color-mix(in srgb,var(--muted) 12%,transparent);
border-radius:3px;margin:3px 0}
.bar span{position:absolute;top:0;bottom:0;border-radius:3px}
.bridge td.b{padding:0;width:52%}
.callout{border-left:3px solid var(--accent);padding:10px 0 10px 16px;margin:16px 0}
.warnbox{border-left:3px solid var(--warn);padding:10px 0 10px 16px;margin:16px 0}
footer{margin-top:50px;padding-top:18px;border-top:1px solid var(--line);
color:var(--muted);font-size:12px;font-family:system-ui,sans-serif}
code{font-family:var(--mono);font-size:12px;background:color-mix(in srgb,var(--muted) 12%,transparent);
padding:1px 5px;border-radius:3px}
@media(max-width:800px){.g2,.g3,.g4{grid-template-columns:1fr}.wrap{padding:24px 16px 60px}h1{font-size:25px}}
@media print{body{background:#fff}.wrap{max-width:none}}
"""


def bn(x, dp=0):
    return f"{x / 1e9:,.{dp}f}"


def pct(x, dp=1, sign=False):
    s = f"{x * 100:+.{dp}f}%" if sign else f"{x * 100:.{dp}f}%"
    return s


def cls(x):
    return "pos" if x > 0 else ("neg" if x < 0 else "")


def esc(s):
    return html.escape(str(s))


def ordinal_suffix(n):
    """st/nd/rd/th for an integer, with the 11-13 exception."""
    if 11 <= n % 100 <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def render(ticker, res, base_year):
    spec = cases.SPEC[ticker]
    r = res[ticker]
    by = base_year[ticker]
    d, t = by["derived"], by["ttm"]
    spot = r["spot"]
    fy0 = r["first_year"]
    scen = {k: r["scenarios"][k]["value_per_share"] for k in ("bear", "base", "bull")}
    probs = decision.PROBS[ticker]
    meta = decision.RATING[ticker]
    direction = "SHORT" if meta["rating"] == "SHORT" else "LONG"
    sz = decision.size(ticker, scen, probs, spot, direction)
    ev = sz["expected_value"]
    be = decision.breakeven_bull(scen, probs, spot)
    pt = r["consensus_price_target"]
    rev = r["reverse"]
    br = r["bridge"]
    base = r["scenarios"]["base"]

    o = []
    A = o.append
    A(f'<div class="wrap"><div class="eyebrow">Equity research &middot; internal memorandum &middot; {AS_OF}</div>')
    A(f'<h1>{esc(spec["name"])} <span class="sub">({ticker})</span></h1>')
    A(f'<p class="sub">Six-year segment-driver model with a vintage depreciation schedule. '
      f'Base year TTM to {by["as_of"]}, all statement inputs from SEC XBRL.</p>')

    rat_cls = "neg" if meta["rating"] == "SHORT" else ("pos" if meta["rating"] == "LONG" else "warn")
    A(f'<p style="margin-top:14px"><span class="tag big {rat_cls}"><b>{meta["rating"]}</b></span>'
      f'<span class="tag">Conviction {meta["conviction"]}/3</span>'
      f'<span class="tag">{meta["horizon_months"]}-month horizon</span>'
      f'<span class="tag">Edge: {meta["edge_type"]}</span></p>')

    # ---- headline metrics
    A('<div class="grid g4" style="margin-top:20px">')
    for lab, val, note in [
        ("Spot", f"${spot:,.2f}", f"as of {AS_OF}"),
        ("Expected value", f"${ev:,.2f}", f'<span class="{cls(ev / spot - 1)}">{pct(ev / spot - 1, 1, True)}</span> vs spot'),
        ("Risk / reward", f"{sz['risk_reward']:.2f} : 1", f"{direction.lower()} framing"),
        ("Breakeven p(bull)", pct(be, 0), f"vs {probs['bull']['bp'] / 100:.0f}% assumed"),
    ]:
        A(f'<div class="card kpi"><div class="lab">{lab}</div><div class="val">{val}</div>'
          f'<div class="note">{note}</div></div>')
    A('</div>')

    # ---- thesis
    A('<h2>Thesis</h2><ol class="thesis">')
    for b in meta["thesis"]:
        A(f'<li><span class="k">{esc(b["kind"])}</span>{esc(b["text"])}</li>')
    A('</ol>')
    A(f'<div class="callout"><b>Edge type: {meta["edge_type"]}.</b> {esc(meta["edge_statement"])}</div>')

    # ---- the variant
    A('<h2>The variant &mdash; where we differ from consensus</h2>')
    v = r["variant"]
    A('<div class="scroll"><table><thead><tr><th>Fiscal year</th><th>Our revenue</th>'
      '<th>Street avg</th><th>Street low&ndash;high</th><th>&Delta;</th><th>Percentile</th>'
      '<th>Analysts</th><th>Our EBIT mgn</th><th>Street EBIT mgn</th></tr></thead><tbody>')
    for row in v:
        inr = "" if row["inside_range"] else ' <span class="warn">outside</span>'
        p = row["position_in_range"]
        if p is None:
            ptxt = "&mdash;"
        elif p < 0:
            ptxt = '<span class="warn">below low</span>'
        elif p > 1:
            ptxt = '<span class="warn">above high</span>'
        else:
            ptxt = f"{p * 100:.0f}{ordinal_suffix(round(p * 100))}"
        A(f'<tr><td>{row["fy"]}</td><td class="num">${bn(row["ours"])}bn</td>'
          f'<td class="num">${bn(row["street_avg"])}bn</td>'
          f'<td class="num">{bn(row["street_low"])}&ndash;{bn(row["street_high"])}</td>'
          f'<td class="num {cls(row["delta_pct"])}">{pct(row["delta_pct"], 1, True)}{inr}</td>'
          f'<td class="num">{ptxt}</td>'
          f'<td class="num">{row["n_analysts"]}</td>'
          f'<td class="num">{pct(row["our_margin"])}</td>'
          f'<td class="num">{pct(row["street_margin"])}</td></tr>')
    A('</tbody></table></div>')

    epsv = r.get("eps_variant")
    if epsv and epsv["rows"]:
        A('<h3>Stated in EPS, because EPS is what analysts actually publish</h3>')
        if epsv["feed_margin_is_constant"]:
            m = epsv["rows"][0]
            A(f'<div class="warnbox"><b>The Street EBIT margin column above is not an analyst '
              f'forecast.</b> It is <b>{pct(m["street_ebit_margin"], 2)}</b> in every single '
              f'forecast year, and the D&amp;A it implies is <b>{pct(m["street_da_pct"], 2)}</b> in '
              f'every single forecast year, to four significant figures. EBIT growth equals revenue '
              f'growth to a decimal place in all of them. No panel of forty analysts produces that: '
              f'it is a vendor holding a margin constant against a revenue consensus. Saying we '
              f'disagree with it is not saying we disagree with anybody, and earlier editions of '
              f'this memo leaned on that comparison harder than it can bear.</div>')
        corr, hd = epsv["corroboration"], epsv["headline"]
        A(f'<p>The EPS line in the same feed is different in kind. It moves independently from year '
          f'to year, it carries the largest analyst cohort of any field &mdash; '
          f'<b>{max(x["n_eps"] or 0 for x in epsv["rows"])}</b> estimates at the peak &mdash; and '
          f'the <b>${hd["street_eps"]:,.2f}</b> it carries for {corr["fiscal_year"]} is bracketed by '
          f'independently reported Street consensus of '
          f'<b>${corr["reported_low"]:,.2f}&ndash;${corr["reported_high"]:,.2f}</b>. That is a real '
          f'forecast by real people. So this is the variant, in their units: take the Street\'s own '
          f'revenue and EBITDA, substitute our depreciation schedule for theirs, and read off the '
          f'EPS. The build refuses to state it this way if that corroboration ever stops holding.</p>')
        A('<div class="scroll"><table><thead><tr><th>Fiscal year</th><th>Street EPS</th>'
          '<th>Analysts</th><th>Street EBIT mgn</th><th>Restated on our D&amp;A</th>'
          '<th>EPS restated</th><th>&Delta;</th></tr></thead><tbody>')
        for row in epsv["rows"]:
            A(f'<tr><td>{row["fy"]}</td><td class="num">${row["street_eps"]:,.2f}</td>'
              f'<td class="num">{row["n_eps"]}</td>'
              f'<td class="num">{pct(row["street_ebit_margin"], 2)}</td>'
              f'<td class="num">{pct(row["restated_ebit_margin"], 2)}</td>'
              f'<td class="num"><b>${row["restated_eps"]:,.2f}</b></td>'
              f'<td class="num {cls(row["eps_delta_pct"])}">'
              f'{pct(row["eps_delta_pct"], 1, True)}</td></tr>')
        A('</tbody></table></div>')
        A(f'<p class="sub">If we are right about depreciation and the Street is right about '
          f'everything else, {hd["fy"]} EPS is <b>${hd["restated_eps"]:,.2f}</b> against a '
          f'published <b>${hd["street_eps"]:,.2f}</b>. That is the whole disagreement in one '
          f'number, and unlike a D&amp;A ratio nobody publishes, it is checked against a printed '
          f'figure four times a year. Note that {epsv["rows"][0]["fy"]} Street EPS is inflated by '
          f'non-operating equity-securities gains and is not comparable to the years after it '
          f'&mdash; see the quality-of-earnings appendix. Corroboration: {esc(corr["source"])}.</p>')

    # ---- depreciation exhibit (the analytical core for GOOGL)
    A('<h2>Why the margins differ: the depreciation schedule</h2>')
    A(f'<p>We forecast EBITDA margin &mdash; a cash margin driven by mix, pricing and opex &mdash; '
      f'and <em>derive</em> EBIT by subtracting depreciation built from the capex programme, '
      f'vintage by vintage. Forecasting EBIT margin directly, which both the published consensus '
      f'feed and most sell-side models do, hides the depreciation assumption inside a single number.</p>')
    A(f'<div class="warnbox">The consensus feed carries D&amp;A at a flat '
      f'<b>{pct(0.046 if ticker == "GOOGL" else 0.031)} of revenue in every year</b> and EBIT margin '
      f'flat to one decimal place. {esc(spec["name"])} spent <b>{pct(d["capex_pct_revenue"])} of '
      f'revenue</b> on capex in the last twelve months and depreciated '
      f'<b>{pct(d["da_pct_revenue"])}</b> &mdash; a ratio of '
      f'<b>{t["capex"] / t["da"]:.1f}&times;</b>. Those cannot both persist.</div>')
    A('<div class="scroll"><table><thead><tr><th>Year</th><th>Revenue</th><th>Growth</th>'
      '<th>EBITDA mgn</th><th>Capex</th><th>Capex %rev</th><th>D&amp;A</th><th>D&amp;A %rev</th>'
      '<th>EBIT mgn</th><th>FCFF</th></tr></thead><tbody>')
    for i, row in enumerate(base["rows"]):
        A(f'<tr><td>{fy0 + i}E</td><td class="num">${bn(row["revenue"])}bn</td>'
          f'<td class="num">{pct(row["growth"])}</td>'
          f'<td class="num">{pct(base["ebitda_margin"][i])}</td>'
          f'<td class="num">${bn(row["capex"])}bn</td>'
          f'<td class="num">{pct(row["capex"] / row["revenue"])}</td>'
          f'<td class="num">${base["da_abs_bn"][i]:,.0f}bn</td>'
          f'<td class="num">{pct(row["da"] / row["revenue"])}</td>'
          f'<td class="num">{pct(row["ebit_margin"])}</td>'
          f'<td class="num">${bn(row["fcff"])}bn</td></tr>')
    A('</tbody></table></div>')

    # ---- how year-1 capex is anchored, and the arithmetic the thesis rests on
    ytd, anch = r["ytd"], r["capex_anchor"]["base"]
    cum_capex = sum(q["capex"] for q in base["rows"])
    cum_da = sum(q["da"] for q in base["rows"])
    cum_street_da = sum(v * q["revenue"] for v, q in
                        zip(r["street_case"]["da_pct_revenue_path"], base["rows"]))
    last = base["rows"][-1]
    street_last = r["street_case"]["da_pct_revenue_path"][-1]
    A(f'<h3>How year 1 is anchored</h3>')
    A(f'<p>Forecast year {fy0} is part history. <b>${bn(ytd["capex"]["val"], 1)}bn</b> of capex through '
      f'Q{ytd["quarters_elapsed"]} is a filed fact, not an estimate.</p>')
    if anch.get("guided"):
        cg = r["capex_guidance"]
        A(f'<p>The rest of the year is not an estimate either: management guided full-year capex to '
          f'<b>${bn(anch["guidance_low"], 0)}&ndash;{bn(anch["guidance_high"], 0)}bn</b> on '
          f'{cg["as_of"]}, up from ${bn(cg["prior_low"], 0)}&ndash;{bn(cg["prior_high"], 0)}bn. '
          f'The base case takes the midpoint, <b>${bn(anch["year_one_capex"], 1)}bn</b>. That implies '
          f'<b>${bn(anch["implied_remaining_quarterly"], 1)}bn</b> in each remaining quarter, '
          f'{pct(anch["vs_exit_quarter"], 0, True)} on the ${bn(anch["exit_quarter"], 1)}bn just '
          f'reported. Bear and bull are allowed to disagree with guidance and land at '
          f'${bn(r["capex_anchor"]["bear"]["year_one_capex"], 0)}bn and '
          f'${bn(r["capex_anchor"]["bull"]["year_one_capex"], 0)}bn; the base case is not, and the '
          f'build fails if it drifts outside the range.</p>')
        A(f'<div class="callout"><b>What this replaced.</b> The previous edition of this memo held '
          f'the exit quarter flat and carried <b>${bn(anch["exit_rate_alternative"], 1)}bn</b> for '
          f'{fy0} &mdash; ${bn(anch["guidance_low"] - anch["exit_rate_alternative"], 0)}bn below the '
          f'bottom of a range management had already published two weeks before that edition went '
          f'out. Freezing a quarterly figure that has risen for seven consecutive quarters is a '
          f'reasonable way to forecast a stub when nobody has guided. It is not a reasonable way to '
          f'forecast one when somebody has. Nothing in the build looked at guidance, so nothing '
          f'caught it; a check now fails the build instead.</div>')
        A(f'<p class="sub">Source: {esc(cg["source"])}. &ldquo;{esc(cg["quote"])}&rdquo; On the year '
          f'after: &ldquo;{esc(cg["forward"])}&rdquo; &mdash; our {fy0 + 1} path carries '
          f'${bn(base["rows"][1]["capex"], 0)}bn, only '
          f'{pct(base["rows"][1]["capex"] / base["rows"][0]["capex"] - 1, 0, True)} on {fy0}, so if '
          f'&ldquo;significantly&rdquo; means what it usually means this path is still too low.</p>')
    else:
        A(f'<p>The remaining '
          f'{ytd["quarters_remaining"]} quarter{"s" if ytd["quarters_remaining"] != 1 else ""} are held at '
          f'the last observed quarterly rate of <b>${bn(ytd["exit_quarter_capex"]["val"], 1)}bn</b> '
          f'({ytd["exit_quarter_capex"]["period_end"]}), giving <b>${bn(anch["year_one_capex"], 1)}bn</b> '
          f'for the full year. This company does not guide capex, so the exit rate is the best '
          f'available anchor; where management does guide, guidance outranks it.</p>')
    ranch = r["revenue_anchor"]["base"]
    if ranch:
        A(f'<p>Revenue in year 1 is anchored the same way, one level down. '
          f'<b>${bn(ranch["reported"], 1)}bn</b> is reported for Q{ranch["reported_quarters"]} and '
          f'Q{ranch["guided_quarter"]} is guided to <b>${bn(ranch["guided_mid"], 1)}bn</b> '
          f'(&plusmn;{pct(ranch["guided_high"] / ranch["guided_mid"] - 1, 0)}), so '
          f'<b>{pct(ranch["covered"])}</b> of the year is fixed before our segment build says '
          f'anything. Our ${bn(ranch["year_one_revenue"], 0)}bn leaves '
          f'<b>${bn(ranch["stub_per_quarter"], 1)}bn</b> a quarter for the remaining '
          f'{ranch["stub_quarters"]}, {pct(ranch["stub_vs_guided_quarter"], 1, True)} on the guided '
          f'quarter. Note the guide {esc(ranch["caveat"])}.</p>')
        A(f'<p class="sub">Source: {esc(ranch["source"])}. This does not set the forecast &mdash; one '
          f'guided quarter is not a year &mdash; but a year-1 figure below reported plus guided is '
          f'arithmetic that has already been falsified, and the build refuses it.</p>')

    sanch = r.get("segment_anchor", {}).get("base")
    if sanch:
        A('<h3>Every segment against its own reported quarters</h3>')
        A(f'<p>A consolidated total can be right for the wrong reasons. Each segment is therefore '
          f'checked against what it has actually printed: year-1 revenue less the '
          f'{sanch["reported_quarters"]} reported quarters, divided by the '
          f'{sanch["remaining_quarters"]} remaining, against the exit quarter. A stub more than '
          f'{pct(sanch["tolerance"], 0)} below the exit quarter fails the build unless somebody '
          f'records why.</p>')
        A('<div class="scroll"><table><thead><tr><th>Segment</th>'
          f'<th>Reported through Q{sanch["reported_quarters"]} $bn</th><th>Exit quarter $bn</th>'
          f'<th>Year {fy0} $bn</th><th>Implied per remaining quarter $bn</th>'
          '<th>vs exit quarter</th></tr></thead><tbody>')
        for row in sanch["rows"]:
            v = row["vs_exit_quarter"]
            vcls = "warn" if v is not None and v < 0 else "pos"
            A(f'<tr><td>{esc(cases.SPEC[ticker]["segment_labels"][row["segment"]])}</td>'
              f'<td class="num">{bn(row["reported"], 1)}</td>'
              f'<td class="num">{bn(row["exit_quarter"], 2)}</td>'
              f'<td class="num">{bn(row["year_one"], 1)}</td>'
              f'<td class="num">{bn(row["implied_per_quarter"], 2)}</td>'
              f'<td class="num {vcls}">{pct(v, 1, True)}</td></tr>')
        A('</tbody></table></div>')
        src = ", ".join(f'{s["form"]} {s["accn"]} ({s["period_end"]})' for s in sanch["sources"])
        A(f'<div class="callout"><b>What this replaced.</b> The previous edition forecast '
          f'{fy0} Cloud revenue of <b>$91.0bn</b> against <b>$44.8bn</b> already reported, which '
          f'implied <b>$23.1bn</b> in each remaining quarter &mdash; below the <b>$24.8bn</b> the '
          f'June quarter had just printed. A sequential decline, forecast into the one segment '
          f'growing 82% year over year, with a backlog that had just added $54bn in three months to '
          f'reach $514bn. Consolidated revenue looked entirely reasonable throughout, because other '
          f'segments were forecast above their own exit rates and absorbed it: the error lived in '
          f'the mix, where nothing consolidated could see it. Cloud now carries '
          f'<b>${bn(dict((x["segment"], x["year_one"]) for x in sanch["rows"])["cloud"], 1)}bn</b>, '
          f'and every segment is checked separately.</div>')
        A(f'<p class="sub">Segment revenue is not in XBRL &mdash; <code>companyfacts</code> flattens '
          f'dimensioned facts &mdash; so the reported quarters are keyed from the earnings releases: '
          f'{esc(src)}. Their sum ties to the consolidated fiscal-year-to-date revenue taken '
          f'independently from XBRL, and the build fails if it does not.</p>')

    if ticker == "GOOGL":
        A(f'<div class="warnbox"><b>The arithmetic the thesis rests on.</b> Over {fy0}&ndash;'
          f'{fy0 + 5} this capex path spends <b>${bn(cum_capex, 0)}bn</b>. Our vintage schedule '
          f'depreciates <b>${bn(cum_da, 0)}bn</b> of it. The consensus feed, held at '
          f'{pct(street_last)} of revenue, depreciates <b>${bn(cum_street_da, 0)}bn</b> &mdash; a '
          f'<b>${bn(cum_da - cum_street_da, 0)}bn</b> gap. By {fy0 + 5} that is '
          f'<b>${bn(last["da"] - street_last * last["revenue"], 0)}bn</b> a year of depreciation the '
          f'consensus EBIT margin never charges, roughly '
          f'<b>${(last["da"] - street_last * last["revenue"]) * (1 - 0.185) / r["diluted_shares"]:,.2f}'
          f'</b> per share of annual earnings. An asset base that produces the consensus D&amp;A '
          f'figure cannot also absorb the capex the cash flow statement reports.</div>')
        A(f'<p class="sub">Note this is a claim about reported earnings, not primarily about '
          f'discounted value: in an FCFF model depreciation is added back, so a higher charge is '
          f'close to value-neutral and shows up in the bridge below as a small tax effect. The cash '
          f'that leaves is capex, and that is anchored on filings above. The depreciation gap matters '
          f'because it is what the multiple is applied to, and because it is observable every ninety '
          f'days.</p>')

    # ---- value bridge
    A('<h2>Price-to-value bridge</h2>')
    A(f'<p>Contributions are exact Shapley values over all '
      f'2<sup>{len(br["contributions"])}</sup> = {br["coalitions_evaluated"]} driver coalitions, so they sum to the total '
      f'without residual (residual ${br["residual"]:+.4f}). One-at-a-time sensitivity would not, '
      f'because DCF driver interactions are large.</p>')
    contribs = sorted(br["contributions"].items(), key=lambda kv: -abs(kv[1]))
    mx = max([abs(x) for _, x in contribs] + [1e-9])
    A('<div class="scroll"><table class="bridge"><thead><tr><th>Step</th><th>$/share</th>'
      '<th class="b"></th></tr></thead><tbody>')
    A(f'<tr><td><b>Street-calibrated value</b></td><td class="num">${br["start_value"]:,.2f}</td><td class="b"></td></tr>')
    for k, val in contribs:
        if abs(val) < 0.01:
            continue
        w = abs(val) / mx * 100
        col = "var(--pos)" if val > 0 else "var(--neg)"
        left = 50 if val > 0 else 50 - w / 2
        A(f'<tr><td>{esc(k.replace("_", " "))}</td><td class="num {cls(val)}">{val:+,.2f}</td>'
          f'<td class="b"><div class="bar"><span style="left:{left}%;width:{w / 2}%;background:{col}"></span></div></td></tr>')
    A(f'<tr><td><b>Our base case</b></td><td class="num"><b>${br["end_value"]:,.2f}</b></td><td class="b"></td></tr>')
    A(f'<tr><td>Market price</td><td class="num">${spot:,.2f}</td><td class="b"></td></tr>')
    A('</tbody></table></div>')
    A(f'<p class="sub">The gap from our base case to the market price is not decomposed into drivers, '
      f'because it is not a forecast disagreement &mdash; it is the discount rate and terminal '
      f'assumptions the market is applying. That is stated below rather than disguised as precision.</p>')

    # ---- reverse DCF
    A('<h2>What the market is paying for</h2>')
    A(f'<p>At <b>${spot:,.2f}</b>, holding everything else at our base case, the market is paying for '
      f'<em>either</em>&hellip;</p>')
    A('<div class="grid g3">')
    for lab, val, note in [
        ("Revenue CAGR", pct(rev["implied_revenue_cagr"]),
         f'vs our {pct((base["revenue_path"][-1] / r["base_revenue"]) ** (1 / 6) - 1)} base'),
        ("Terminal EBIT margin", pct(rev["implied_terminal_ebit_margin"]),
         f'vs our {pct(base["rows"][-1]["ebit_margin"])} terminal'),
        ("Discount rate (WACC)", pct(rev["implied_wacc"], 2),
         f'vs our {pct(base["wacc"], 2)} build'),
    ]:
        A(f'<div class="card kpi"><div class="lab">{lab}</div><div class="val">{val}</div>'
          f'<div class="note">{note}</div></div>')
    A('</div>')

    # ---- discount-rate sensitivity
    ws = r.get("wacc_sensitivity")
    if ws:
        A('<h3>What the discount rate is worth</h3>')
        A(f'<p>Terminal value is <b>{pct(ws["tv_pct_ev"])}</b> of enterprise value, so the discount '
          f'rate is not one assumption among many &mdash; it is most of the answer. Our '
          f'<b>{pct(ws["base_wacc"], 2)}</b> is a CAPM build. Widely published third-party estimates '
          f'of Alphabet\'s WACC cluster near <b>7.5%</b>. The reverse DCF above says the market is '
          f'discounting at <b>{pct(ws["market_implied_wacc"], 2)}</b>. Those are large differences '
          f'and the reader should see what each is worth rather than take ours on trust.</p>')
        A('<div class="scroll"><table><thead><tr><th>WACC</th><th>Value/share</th>'
          '<th>vs our base</th><th>vs spot</th><th>TV % of EV</th><th></th></tr></thead><tbody>')
        for g in ws["grid"]:
            mark = ' style="background:#f7faff"' if g["is_base"] else ""
            A(f'<tr{mark}><td class="num">{pct(g["wacc"], 2)}</td>'
              f'<td class="num"><b>${g["value_per_share"]:,.2f}</b></td>'
              f'<td class="num">{pct(g["vs_base"], 1, True)}</td>'
              f'<td class="num {cls(g["vs_spot"])}">{pct(g["vs_spot"], 1, True)}</td>'
              f'<td class="num">{pct(g["tv_pct_ev"])}</td>'
              f'<td class="sub">{esc(g["note"] or "")}</td></tr>')
        A('</tbody></table></div>')
        A(f'<p class="sub">This is disclosure, not a change of view: '
          f'{pct(ws["base_wacc"], 2)} remains the base case, and the depreciation work is '
          f'independent of it. But a reader who prefers 7.5% is not disagreeing with the thesis '
          f'&mdash; they are disagreeing with one input, and on our own numbers that input is worth '
          f'more than the entire depreciation argument. Saying so is the honest way to publish a '
          f'valuation this far below the market.</p>')

    # ---- scenarios
    A('<h2>Scenarios and expected value</h2>')
    A('<div class="scroll"><table><thead><tr><th>Case</th><th>Value/share</th><th>vs spot</th>'
      '<th>Probability</th><th>WACC</th><th>Terminal g</th><th>TV % of EV</th><th>Anchor</th>'
      '</tr></thead><tbody>')
    for k in ("bear", "base", "bull"):
        s = r["scenarios"][k]
        vps = s["value_per_share"]
        A(f'<tr><td><b>{k.title()}</b></td><td class="num">${vps:,.2f}</td>'
          f'<td class="num {cls(vps / spot - 1)}">{pct(vps / spot - 1, 1, True)}</td>'
          f'<td class="num">{probs[k]["bp"] / 100:.0f}%</td>'
          f'<td class="num">{pct(s["wacc"], 2)}</td><td class="num">{pct(s["terminal_growth"])}</td>'
          f'<td class="num">{pct(s["tv_pct_ev"], 0)}</td>'
          f'<td>{esc(probs[k]["anchor"].replace("_", " "))}</td></tr>')
    A(f'<tr><td><b>Expected value</b></td><td class="num"><b>${ev:,.2f}</b></td>'
      f'<td class="num {cls(ev / spot - 1)}"><b>{pct(ev / spot - 1, 1, True)}</b></td>'
      f'<td class="num">100%</td><td colspan="4"></td></tr>')
    A(f'<tr><td>Street-calibrated (their revenue, EBIT and D&amp;A; our capex, our engine)</td>'
      f'<td class="num">${r["street_case"]["value_per_share"]:,.2f}</td>'
      f'<td class="num {cls(r["street_case"]["value_per_share"] / spot - 1)}">'
      f'{pct(r["street_case"]["value_per_share"] / spot - 1, 1, True)}</td><td colspan="5"></td></tr>')
    A(f'<tr><td>Street published price target (median {pt["median"]:,.0f}, range {pt["low"]:,.0f}&ndash;{pt["high"]:,.0f})</td>'
      f'<td class="num">${pt["consensus"]:,.2f}</td>'
      f'<td class="num {cls(pt["consensus"] / spot - 1)}">{pct(pt["consensus"] / spot - 1, 1, True)}</td>'
      f'<td colspan="5"></td></tr>')
    A('</tbody></table></div>')
    A('<div class="grid g3" style="margin-top:6px">')
    for k in ("bear", "base", "bull"):
        A(f'<div class="card"><b>{k.title()} &middot; {probs[k]["bp"] / 100:.0f}%</b>'
          f'<p class="sub" style="margin-top:6px">{esc(probs[k]["justification"])}</p></div>')
    A('</div>')

    # ---- sizing
    A('<h2>Position sizing</h2>')
    A(f'<p>Computed through a constraint cascade, not chosen. Basis: {sz["nav_basis"]}.</p>')
    A('<div class="scroll"><table><thead><tr><th>Term</th><th>Value</th><th>Note</th></tr></thead><tbody>')
    for lab, val, note in [
        ("Payoff ratio b", f"{sz['b']:.2f}", "reward &divide; risk"),
        ("p(win)", pct(sz["p_win"], 0), "probability mass favouring the position"),
        ("Kelly f", pct(sz["kelly_f"], 1), "full Kelly fraction"),
        ("Quarter-Kelly", pct(sz["size_raw"], 2), "0.25 &times; Kelly"),
        ("Liquidity cap", pct(sz["size_liquidity"], 2), "20% of ADV over 5 days"),
        ("Risk-budget cap", pct(sz["size_risk_budget"], 2), "1.5% of NAV at risk to the adverse case"),
        ("Concentration cap", pct(sz["size_concentration"], 2), "single-name hard limit"),
    ]:
        A(f'<tr><td>{lab}</td><td class="num">{val}</td><td class="sub">{note}</td></tr>')
    A(f'<tr><td><b>Position size</b></td><td class="num"><b>{pct(sz["position_size"], 2)} of NAV</b></td>'
      f'<td class="sub">binding constraint: <b>{sz["binding_constraint"]}</b></td></tr>')
    A('</tbody></table></div>')

    # ---- kill criteria
    A('<h2>Kill criteria</h2>')
    A('<div class="scroll"><table><thead><tr><th>#</th><th>If this happens</th><th>Observable</th>'
      '<th>Threshold</th><th>By</th><th>Action</th></tr></thead><tbody>')
    for k in meta["kill_criteria"]:
        A(f'<tr><td>{k["id"]}</td><td><b>{esc(k["statement"])}</b><br>'
          f'<span class="sub">{esc(k["note"])}</span></td>'
          f'<td class="sub">{esc(k["observable"])}</td><td class="num">{esc(k["threshold"])}</td>'
          f'<td class="num">{k["check_date"]}</td><td><b>{esc(k["action"])}</b></td></tr>')
    A('</tbody></table></div>')

    # ---- catalysts
    A('<h2>Catalyst path</h2>')
    A('<div class="scroll"><table><thead><tr><th>Date</th><th>Event</th><th>What we learn</th>'
      '<th>Tests</th></tr></thead><tbody>')
    for c in meta["catalysts"]:
        conf = "" if c["confirmed"] else ' <span class="sub">(tentative)</span>'
        A(f'<tr><td class="num">{c["date"]}{conf}</td><td><b>{esc(c["event"])}</b></td>'
          f'<td class="sub">{esc(c["learn"])}</td><td class="num">{esc(c["tests"])}</td></tr>')
    A('</tbody></table></div>')

    # ---- falsification
    A('<h2>What would make us wrong</h2>')
    for f in meta["falsification"]:
        A(f'<p>{esc(f)}</p>')
    A(f'<h3>Pre-mortem</h3><p>{esc(meta["pre_mortem"])}</p>')

    # ================= APPENDIX =================
    A('<div class="rule"></div><h2>Appendix A &mdash; quality of earnings</h2>')
    A('<div class="scroll"><table><thead><tr><th>TTM to ' + by["as_of"] + '</th><th>$bn</th>'
      '<th>Comment</th></tr></thead><tbody>')
    qoe = [
        ("Revenue", bn(t["revenue"], 1), ""),
        ("Operating income (EBIT)", bn(t["operating_income"], 1), f'{pct(d["ebit_margin"])} margin'),
        ("Non-operating income", bn(t["nonoperating"], 1),
         f'{pct(d["nonoperating_share_of_pretax"])} of pretax income'),
        ("&nbsp;&nbsp;of which equity-securities gains", bn(d["equity_sec_gains"], 1),
         "non-cash marks on investment stakes"),
        ("Reported net income", bn(d["reported_net_income"], 1), "includes the marks above"),
        ("NOPAT (EBIT after tax)", bn(d["nopat"], 1), f'at {pct(d["effective_tax_rate"])} effective rate'),
    ]
    for a, b, c in qoe:
        A(f'<tr><td>{a}</td><td class="num">{b}</td><td class="sub">{c}</td></tr>')
    A('</tbody></table></div>')
    A('<div class="grid g4" style="margin-top:10px">')
    for lab, val, note in [
        ("Reported diluted EPS", f"${d['reported_eps']:,.2f}", "as filed"),
        ("Economic EPS", f"${d['economic_eps']:,.2f}", "NOPAT basis"),
        ("Reported P/E", f"{d['reported_pe']:,.1f}x", "what screens show"),
        ("Economic P/E", f"{d['economic_pe']:,.1f}x", "what you actually pay"),
    ]:
        A(f'<div class="card kpi"><div class="lab">{lab}</div><div class="val">{val}</div>'
          f'<div class="note">{note}</div></div>')
    A('</div>')

    A('<h2>Appendix B &mdash; segment build</h2>')
    A('<p>Every revenue line is the product of named quantities, not a growth rate. '
      'Each driver can be disagreed with individually and checked against disclosure.</p>')
    dv = spec["drivers"]["base"]["segments"]
    A('<div class="scroll"><table><thead><tr><th>Segment / driver</th>'
      + "".join(f'<th>{fy0 + i}E</th>' for i in range(6)) + '</tr></thead><tbody>')
    for seg, paths in base["segment_paths"].items():
        A(f'<tr><td><b>{esc(spec["segment_labels"][seg])}</b> ($bn)</td>'
          + "".join(f'<td class="num"><b>{bn(p)}</b></td>' for p in paths) + '</tr>')
        for drv, vec in dv.get(seg, {}).items():
            A(f'<tr><td class="sub">&nbsp;&nbsp;{esc(drv.replace("_", " "))}</td>'
              + "".join(f'<td class="num sub">{pct(x, 1, True)}</td>' for x in vec) + '</tr>')
    A(f'<tr><td><b>Total revenue</b> ($bn)</td>'
      + "".join(f'<td class="num"><b>{bn(x)}</b></td>' for x in base["revenue_path"]) + '</tr>')
    A('</tbody></table></div>')

    A('<h2>Appendix C &mdash; equity bridge and balance sheet</h2>')
    bi = r["bridge_inputs"]
    A('<div class="scroll"><table><thead><tr><th>Item</th><th>$bn</th><th>Note</th></tr></thead><tbody>')
    A(f'<tr><td>Enterprise value (base case)</td><td class="num">{bn(base["enterprise_value"], 0)}</td><td class="sub"></td></tr>')
    A(f'<tr><td>+ Cash &amp; marketable securities</td><td class="num">{bn(bi["cash_and_marketable"], 1)}</td><td class="sub"></td></tr>')
    A(f'<tr><td>+ Equity investments (stakes)</td><td class="num">{bn(bi["equity_investments"], 1)}</td>'
      f'<td class="sub">{pct(d["equity_investments_pct_revenue"])} of revenue &mdash; '
      f'${d["equity_investments_per_share"]:,.2f}/share. Omitted from the published report\'s bridge.</td></tr>')
    A(f'<tr><td>&minus; Debt</td><td class="num">{bn(bi["debt"], 1)}</td><td class="sub"></td></tr>')
    A(f'<tr><td>&minus; Operating leases</td><td class="num">{bn(bi["leases"], 1)}</td><td class="sub"></td></tr>')
    if bi.get("preferred"):
        A(f'<tr><td>&minus; Preferred stock</td><td class="num">{bn(bi["preferred"], 1)}</td>'
          f'<td class="sub">6.25% mandatory convertible issued June 2026, carrying value. '
          f'Liquidation preference is $19.0bn. Deducted here rather than converted into the share '
          f'count; the diluted count already carries ~8m if-converted shares, so the two overlap '
          f'by well under 0.1%.</td></tr>')
    A(f'<tr><td><b>Equity value</b></td><td class="num"><b>{bn(base["equity_value"], 0)}</b></td>'
      f'<td class="sub">&divide; {r["diluted_shares"] / 1e6:,.0f}m diluted shares</td></tr>')
    A(f'<tr><td><b>Value per share</b></td><td class="num"><b>${scen["base"]:,.2f}</b></td><td class="sub"></td></tr>')
    A('</tbody></table></div>')

    post = by.get("post_balance_sheet") or []
    if post:
        filed = by["balance_sheet_as_filed"]
        A('<h3>Financing between the balance-sheet date and the valuation date</h3>')
        A(f'<p>The bridge above is not the {by["as_of"]} balance sheet unchanged. A filing goes '
          f'stale, and the reader is pricing the company as it stands today, so priced financing '
          f'completed after the balance-sheet date is rolled in and itemised here.</p>')
        A('<div class="scroll"><table><thead><tr><th>Event</th><th>Priced</th><th>Debt $bn</th>'
          '<th>Cash $bn</th><th>Filing</th></tr></thead><tbody>')
        for it in post:
            A(f'<tr><td>{esc(it["event"])}</td><td class="num">{esc(it["priced"])}</td>'
              f'<td class="num">{bn(it.get("debt", 0.0), 1)}</td>'
              f'<td class="num">{bn(it.get("cash_and_marketable", 0.0), 1)}</td>'
              f'<td class="sub">{esc(it["form"])} {esc(it["accn"])}</td></tr>')
        net = sum(it.get("cash_and_marketable", 0.0) - it.get("debt", 0.0) for it in post)
        A(f'<tr><td><b>Net effect on equity value</b></td><td></td><td></td>'
          f'<td class="num"><b>{bn(net, 1)}</b></td>'
          f'<td class="sub"><b>${net / r["diluted_shares"]:,.2f}</b> per share</td></tr>')
        A('</tbody></table></div>')
        A(f'<p class="sub">Debt as filed at {by["as_of"]} was ${bn(filed["debt"], 1)}bn; the bridge '
          f'carries ${bn(bi["debt"], 1)}bn. Cash as filed was ${bn(filed["cash_and_marketable"], 1)}bn '
          f'against ${bn(bi["cash_and_marketable"], 1)}bn. Both legs are carried, so what survives is '
          f'the underwriting spread. The number is small; the reason to know it is small is that it '
          f'went through the bridge rather than being waved off.</p>')

    undrawn = by.get("authorised_undrawn") or []
    if undrawn:
        A('<h3>Authorised but undrawn &mdash; and deliberately not in the share count</h3>')
        for it in undrawn:
            sh = it["capacity"] / spot
            shares_after = r["diluted_shares"] + sh
            vps_after = (scen["base"] * r["diluted_shares"] + it["capacity"]) / shares_after
            direction = "accretive to" if vps_after > scen["base"] else "dilutive to"
            A(f'<div class="warnbox"><b>{esc(it["event"])}.</b> Established {esc(it["established"])}, '
              f'managers expanded {esc(it["amended"])}. Drawn as of {esc(it["drawn_as_of"])}: '
              f'<b>${bn(it["drawn"], 1)}bn</b>. Nothing has been issued, so nothing is in the '
              f'{r["diluted_shares"] / 1e6:,.0f}m share count &mdash; putting unissued shares into a '
              f'share count is inventing a fact. Drawn in full at ${spot:,.2f} it would be roughly '
              f'<b>{sh / 1e6:,.0f}m shares</b>, <b>{pct(sh / r["diluted_shares"])}</b> more stock. '
              f'The share count is not the interesting part: because those shares would be sold at '
              f'${spot:,.2f} against our estimate of ${scen["base"]:,.2f} of intrinsic value, a full '
              f'draw is <b>{direction}</b> value per share, taking the base case to '
              f'<b>${vps_after:,.2f}</b>. Selling stock the seller thinks is expensive is a transfer '
              f'from the buyer, and on our numbers that is what this programme is. '
              f'{esc(it["purpose"]).capitalize()}.<br>'
              f'<span class="sub">{esc(it["source"])}</span></div>')

    ss = base.get("steady_state") or {}
    if ss:
        ok = "pos" if ss.get("consistent") else "warn"
        A(f'<p class="sub">Terminal steady state: reinvestment rate '
          f'<b>{pct(ss["reinvestment_rate"], 0)}</b> of NOPAT against '
          f'<b>{pct(ss["implied_reinvestment_rate"], 0)}</b> implied by g &divide; ROIC '
          f'(<span class="{ok}">{"consistent" if ss.get("consistent") else "review"}</span>). '
          f'A DCF that fails this check is capitalising a terminal cash flow computed at '
          f'peak underinvestment.</p>')

    A('<h2>Appendix D &mdash; sources and method</h2>')
    A('<ul>')
    A(f'<li><b>Financial statements:</b> SEC XBRL <code>companyconcept</code> API, CIK '
      f'{"0001652044" if ticker == "GOOGL" else "0001045810"}. Quarterly series are reconstructed '
      f'from filed facts, with Q4 derived as fiscal year minus the nine-month cumulative and '
      f'cash-flow items unwound from year-to-date cumulatives.</li>')
    A('<li><b>Consensus estimates and price targets:</b> FMP <code>analyst/financial-estimates</code> '
      'and <code>analyst/price-target-consensus</code>.</li>')
    A('<li><b>Segment revenue:</b> FMP <code>statements/revenue-product-segmentation</code>. No SEC '
      'fallback exists &mdash; <code>companyfacts</code> flattens dimensioned facts &mdash; so the '
      'only control is reconciling the segment sum to consolidated revenue.</li>')
    A('<li><b>Earnings dates and surprise history:</b> Robinhood <code>get_earnings_results</code>. '
      'Prices and average dollar volume from Robinhood <code>get_equity_quotes</code> and '
      '<code>get_equity_historicals</code>.</li>')
    A('<li><b>Management guidance:</b> quoted from the earnings call it was given on, and recorded in '
      '<code>build/cases.py</code> with the date and speaker, so that the figure the model anchors on '
      'and the sentence management said are the same object. Guidance is management\'s own statement, '
      'not a third party\'s conclusion, and it outranks any extrapolation we would build for a period '
      'they have already guided.</li>')
    A('<li><b>Financing after the balance-sheet date:</b> SEC prospectus filings (424B2/424B5/FWP), '
      'itemised in Appendix C with accession numbers rather than folded silently into the bridge.</li>')
    A('<li><b>Not used:</b> third-party model outputs (vendor DCFs, quantitative scores, aggregated '
      'ratings). They are other people\'s conclusions, not evidence.</li>')
    A('</ul>')
    A('<h3>Known limitations</h3><ul>')
    A('<li>We have no channel checks, expert calls, or alternative data. The edge claimed here is '
      'analytical, derived entirely from public filings.</li>')
    A('<li>The asset-life split driving the depreciation schedule (short-lived equipment versus '
      'long-lived shells) is a stated assumption calibrated to reported D&amp;A, not a disclosed '
      'figure. It is the single most load-bearing assumption in the model and kill criterion k1 '
      'exists to monitor it.</li>')
    A('<li>The consensus feed holds D&amp;A at a constant share of revenue in every year, which may '
      'be an artefact of the aggregator rather than what individual analysts model. The comparison '
      'is to the feed we can observe, and is labelled as such.</li>')
    A(f'<li>Segment sum reconciles to consolidated revenue within '
      f'{"0.2" if ticker == "GOOGL" else "1.0"}%.</li>')
    A('</ul>')

    A(f'<footer>Prepared {AS_OF}. Base year TTM to {by["as_of"]}; market data as of the '
      f'2026-08-07 session. Analytical research on public information; not investment advice, '
      f'not a recommendation to any person, and not a solicitation. Position sizing is illustrative '
      f'against a notional $1bn book. The author may hold positions in the securities discussed.'
      f'</footer></div>')
    return "\n".join(o)


def page(title, body):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><style>{CSS}</style></head><body>{body}</body></html>')


def main():
    res = json.loads((DATA / "results.json").read_text())
    by = json.loads((DATA / "base_year.json").read_text())
    for ticker, slug in (("GOOGL", "alphabet"), ("NVDA", "nvidia")):
        body = render(ticker, res, by)
        title = f'{cases.SPEC[ticker]["name"]} ({ticker}) — investment memo'
        p = OUT / slug / "memo.html"
        p.parent.mkdir(exist_ok=True)
        p.write_text(page(title, body))
        print("wrote", p)


if __name__ == "__main__":
    main()
