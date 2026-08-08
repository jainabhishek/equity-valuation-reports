"""Regenerate the social and per-company preview images from live model output.

These were previously hand-made and hardcoded the old valuations, so the landing
page and social cards published numbers that contradicted the memos. Generating
them from results.json means they cannot drift again.
"""
from __future__ import annotations

import json
from pathlib import Path

import cairosvg

import decision

DATA = Path(__file__).parent / "data"
ASSETS = Path(__file__).parent.parent / "assets"

NAVY = "#0b1739"
INK = "#142958"
BLUE = "#a8c4ff"
WHITE = "#ffffff"
MUTED = "#c3d3f2"
RED = "#ff8f9e"
PURPLE = "#c7b9ff"
FONT = "Inter,Aptos,Helvetica Neue,Arial,sans-serif"


def facts(ticker):
    if ticker == "GOOGL":
        pm = json.loads((DATA / "alphabet_pm.json").read_text())
        scen = {r["key"]: r["target"] for r in pm["scenarios"]["rows"]}
        ev = pm["scenarios"]["expected_value"]
        return {"spot": pm["inputs"]["spot"], "scen": scen,
                "rating": "WAIT FOR PROOF", "ev": ev,
                "ev_pct": ev / pm["inputs"]["spot"] - 1, "rr": 0.0, "size": 0.0}
    res = json.loads((DATA / "results.json").read_text())[ticker]
    scen = {k: res["scenarios"][k]["value_per_share"] for k in ("bear", "base", "bull")}
    meta = decision.RATING[ticker]
    direction = "SHORT" if meta["rating"] == "SHORT" else "LONG"
    sz = decision.size(ticker, scen, decision.PROBS[ticker], res["spot"], direction)
    return {
        "spot": res["spot"], "scen": scen, "rating": meta["rating"],
        "ev": sz["expected_value"], "ev_pct": sz["expected_value"] / res["spot"] - 1,
        "rr": sz["risk_reward"], "size": sz["position_size"],
    }


def scenario_bar(x, y, w, f, scale_lo=None, scale_hi=None):
    """Bear-base-bull range with spot and EV marked. The whole thesis in one strip."""
    lo = scale_lo if scale_lo is not None else min(f["scen"]["bear"], f["spot"]) * 0.9
    hi = scale_hi if scale_hi is not None else max(f["scen"]["bull"], f["spot"]) * 1.05
    def px(v):
        return x + (v - lo) / (hi - lo) * w
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="7" rx="3.5" fill="#ffffff" opacity="0.13"/>']
    o.append(f'<rect x="{px(f["scen"]["bear"]):.1f}" y="{y}" '
             f'width="{px(f["scen"]["bull"]) - px(f["scen"]["bear"]):.1f}" height="7" rx="3.5" '
             f'fill="{BLUE}" opacity="0.42"/>')
    # base case
    o.append(f'<circle cx="{px(f["scen"]["base"]):.1f}" cy="{y + 3.5}" r="6" fill="{WHITE}"/>')
    # expected value
    o.append(f'<circle cx="{px(f["ev"]):.1f}" cy="{y + 3.5}" r="5" fill="{PURPLE}"/>')
    # spot
    o.append(f'<rect x="{px(f["spot"]) - 1.5:.1f}" y="{y - 7}" width="3" height="21" rx="1.5" fill="{RED}"/>')
    return "".join(o)


def card(x, y, w, h, ticker, name, f):
    rating_fill = RED if f["rating"] == "SHORT" else PURPLE
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#ffffff" opacity="0.07"/>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="#ffffff" stroke-opacity="0.16"/>']
    o.append(f'<rect x="{x + 26}" y="{y + 26}" width="86" height="30" rx="15" fill="{WHITE}"/>')
    o.append(f'<text x="{x + 69}" y="{y + 46}" font-family="{FONT}" font-size="15" font-weight="800" '
             f'fill="{NAVY}" text-anchor="middle">{ticker}</text>')
    o.append(f'<text x="{x + 126}" y="{y + 47}" font-family="{FONT}" font-size="16" font-weight="700" '
             f'fill="{rating_fill}">{f["rating"]}</text>')
    o.append(f'<text x="{x + 26}" y="{y + 88}" font-family="{FONT}" font-size="25" font-weight="800" '
             f'fill="{WHITE}">{name}</text>')

    o.append(scenario_bar(x + 26, y + 112, w - 52, f))
    o.append(f'<text x="{x + 26}" y="{y + 148}" font-family="{FONT}" font-size="12" fill="{MUTED}">'
             f'bear ${f["scen"]["bear"]:,.0f}</text>')
    o.append(f'<text x="{x + w - 26}" y="{y + 148}" font-family="{FONT}" font-size="12" fill="{MUTED}" '
             f'text-anchor="end">bull ${f["scen"]["bull"]:,.0f}</text>')

    cols = [("Spot", f'${f["spot"]:,.2f}', MUTED),
            ("Expected value", f'${f["ev"]:,.2f}', WHITE),
            ("vs spot", f'{f["ev_pct"] * 100:+.1f}%', RED if f["ev_pct"] < 0 else PURPLE)]
    cw = (w - 52) / 3
    for i, (lab, val, col) in enumerate(cols):
        cx = x + 26 + i * cw
        o.append(f'<text x="{cx}" y="{y + 182}" font-family="{FONT}" font-size="11.5" '
                 f'fill="{MUTED}">{lab}</text>')
        o.append(f'<text x="{cx}" y="{y + 208}" font-family="{FONT}" font-size="21" font-weight="800" '
                 f'fill="{col}">{val}</text>')
    return "".join(o)


def shell(w, h, inner, eyebrow, title, sub, chips):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
         f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
         f'<stop offset="0" stop-color="{NAVY}"/><stop offset="0.7" stop-color="{INK}"/>'
         f'<stop offset="1" stop-color="#183668"/></linearGradient></defs>',
         f'<rect width="{w}" height="{h}" fill="url(#g)"/>']
    o.append(f'<text x="80" y="70" font-family="{FONT}" font-size="15" font-weight="800" '
             f'letter-spacing="2.4" fill="{BLUE}">{eyebrow}</text>')
    o.append(f'<text x="80" y="136" font-family="{FONT}" font-size="52" font-weight="800" '
             f'letter-spacing="-1.6" fill="{WHITE}">{title}</text>')
    for i, line in enumerate(sub):
        o.append(f'<text x="80" y="{178 + i * 27}" font-family="{FONT}" font-size="19" '
                 f'fill="{MUTED}">{line}</text>')
    cx = 80
    for c in chips:
        cwid = 15 + len(c) * 7.4
        o.append(f'<rect x="{cx}" y="{178 + len(sub) * 27 + 4}" width="{cwid:.0f}" height="32" rx="16" '
                 f'fill="#ffffff" opacity="0.10"/>')
        o.append(f'<text x="{cx + cwid / 2:.0f}" y="{178 + len(sub) * 27 + 25}" font-family="{FONT}" '
                 f'font-size="13" font-weight="700" fill="{WHITE}" text-anchor="middle">{c}</text>')
        cx += cwid + 12
    o.append(inner)
    o.append(f'<text x="80" y="{h - 34}" font-family="{FONT}" font-size="13.5" fill="{BLUE}" '
             f'opacity="0.85">jainabhishek.github.io/equity-valuation-reports</text>')
    o.append("</svg>")
    return "".join(o)


def main():
    g, n = facts("GOOGL"), facts("NVDA")
    ASSETS.mkdir(exist_ok=True)

    # ---- social card, 1200x630
    inner = card(80, 340, 500, 235, "GOOGL", "Alphabet", g) + card(620, 340, 500, 235, "NVDA", "Nvidia", n)
    svg = shell(1200, 630, inner, "BUY-SIDE INVESTMENT MEMOS",
                "Equity Valuation Reports",
                ["Public-information research backed by live Excel models.",
                 "Point-in-time shares, implementation gates and source ledgers."],
                ["Alphabet and Nvidia", "Prepared Aug 8, 2026", "Market data Aug 7"])
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(ASSETS / "social-preview.png"),
                     output_width=1200, output_height=630)

    # ---- per-company cards, 1000x520
    for ticker, name, f, slug in (("GOOGL", "Alphabet", g, "alphabet"), ("NVDA", "Nvidia", n, "nvidia")):
        thesis = ("Wait for proof: D&amp;A must cause an unoffset EPS cut;" if ticker == "GOOGL"
                  else "Priced. Our range is $67&#8211;$437;")
        thesis2 = ("borrow, crowding, options and hedge gates remain open."
                   if ticker == "GOOGL" else "no defensible position size survives that spread.")
        inner = card(80, 250, 840, 225, ticker, name, f)
        svg = shell(1000, 520, inner, f"{ticker} &#183; INVESTMENT MEMO", name,
                    [thesis, thesis2],
                    (["No position", "Implementation gate open", "Dated FCFF cross-check"]
                     if ticker == "GOOGL" else
                     [f'R:R {f["rr"]:.2f}', f'Size {f["size"] * 100:.2f}% NAV', "6-yr FCFF DCF"]))
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(ASSETS / f"{slug}-preview.png"),
                         output_width=1000, output_height=520)

    for p in ("social-preview.png", "alphabet-preview.png", "nvidia-preview.png"):
        print("wrote", ASSETS / p)


if __name__ == "__main__":
    main()
