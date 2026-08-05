"""Company cases: named drivers, and the depreciation engine that drives the thesis.

Key model choice, and the reason this differs from both the published report and
the consensus feed: we forecast EBITDA margin (a cash margin, driven by mix,
pricing and opex) and DERIVE EBIT by subtracting a depreciation schedule built
from the capex program. Forecasting EBIT margin directly -- which both the
published report and the consensus feed do -- hides the depreciation assumption
inside a single number.
"""
from __future__ import annotations

FIRST_YEAR = {"GOOGL": 2026, "NVDA": 2027}  # first forecast year (NVDA fiscal)

# Historical capex by fiscal year, $bn, from SEC XBRL (see depreciation.py).
HIST_CAPEX = {
    "GOOGL": {2021: 24.6, 2022: 31.5, 2023: 32.3, 2024: 52.5, 2025: 91.4},
    "NVDA": {2023: 1.1, 2024: 1.1, 2025: 3.2, 2026: 5.0},
}

# Asset-life mix. Alphabet's fleet is a blend of long-lived shells (data-centre
# buildings, 25-40yr) and short-lived equipment (servers and network gear, which
# Alphabet extended to a 6-year life effective 2023). A single life does not fit
# reported D&A; the two-bucket split does.
ASSET_MIX = {
    "GOOGL": {"short_share": 0.72, "short_life": 6.0, "long_life": 25.0},
    "NVDA": {"short_share": 0.60, "short_life": 5.0, "long_life": 20.0},
}


def depreciation_path(ticker, capex_forecast, first_year, years):
    """D&A per forecast year from straight-line depreciation of every vintage.

    Half-year convention in the year an asset is placed in service.
    """
    mix = ASSET_MIX[ticker]
    vintages = dict(HIST_CAPEX[ticker])
    for i, c in enumerate(capex_forecast):
        vintages[first_year + i] = c

    out = []
    for i in range(years):
        y = first_year + i
        d = 0.0
        for v, cap in vintages.items():
            if v > y:
                continue
            short, long = cap * mix["short_share"], cap * (1 - mix["short_share"])
            if y < v + mix["short_life"]:
                d += short / mix["short_life"] * (0.5 if v == y else 1.0)
            if y < v + mix["long_life"]:
                d += long / mix["long_life"] * (0.5 if v == y else 1.0)
        out.append(d)
    return out


# --------------------------------------------------------------------------
# Alphabet
# --------------------------------------------------------------------------
# Base = FY2025 reported segments ($m). Sum ties to consolidated FY2025 revenue
# of $402.8bn within 0.2%.
GOOGL_BASE_SEGMENTS = {
    "search": 224_532e6,
    "youtube_ads": 40_367e6,
    "network": 29_792e6,
    "subs_devices": 48_030e6,
    "cloud": 58_705e6,
    "other_bets": 1_537e6,
}

GOOGL_DRIVERS = {
    "base": {
        "segments": {
            # Search = queries x ad coverage x price per click.
            # Coverage is the AI Overviews question: AI answers consume SERP real
            # estate that used to carry ads. Falsifiable quarterly against
            # disclosed paid-click growth.
            "search": {
                "queries": [0.065, 0.055, 0.05, 0.045, 0.04, 0.035],
                "ad_coverage": [-0.010, -0.015, -0.015, -0.010, -0.005, 0.0],
                "price_per_click": [0.130, 0.080, 0.062, 0.050, 0.045, 0.040],
            },
            # YouTube = watch hours x ad load x CPM
            "youtube_ads": {
                "watch_hours": [0.05, 0.045, 0.04, 0.035, 0.03, 0.03],
                "ad_load": [0.02, 0.015, 0.010, 0.005, 0.0, 0.0],
                "cpm": [0.075, 0.050, 0.040, 0.035, 0.030, 0.025],
            },
            # Structurally declining: third-party ad network disintermediated by
            # direct demand and by AI-native surfaces.
            "network": {"runoff": [-0.03, -0.04, -0.04, -0.05, -0.05, -0.05]},
            # Subscriptions (One, YouTube Premium/TV) x ARPU, plus devices
            "subs_devices": {
                "subscribers": [0.14, 0.12, 0.10, 0.09, 0.08, 0.07],
                "arpu": [0.03, 0.03, 0.025, 0.025, 0.02, 0.02],
            },
            # Cloud is supply-constrained, not demand-constrained: growth is set
            # by deliverable capacity, which is a function of the capex program.
            "cloud": {"capacity": [0.55, 0.34, 0.28, 0.23, 0.19, 0.15]},
            "other_bets": {"growth": [0.10, 0.15, 0.20, 0.20, 0.20, 0.20]},
        },
        # EBITDA margin: cash margin before depreciation. Rises modestly on
        # Cloud scale and Search opex leverage, offset by AI serving costs.
        "ebitda_margin": [0.385, 0.392, 0.398, 0.402, 0.405, 0.407],
        "capex_pct_revenue": [0.295, 0.270, 0.240, 0.210, 0.185, 0.170],
        "tax_rate": [0.185, 0.19, 0.19, 0.19, 0.19, 0.19],
        "nwc_pct_revenue": [0.020, 0.020, 0.020, 0.020, 0.020, 0.020],
        "terminal_growth": 0.030,
        "wacc": 0.0875,
    },
    "bear": {
        "search_coverage_delta": -0.015,   # AI Overviews bite harder
        "search_cpc_delta": -0.020,
        "cloud_capacity_delta": -0.06,
        "ebitda_margin_delta": -0.025,
        "capex_delta": 0.02,               # spend more, get less
        "terminal_growth": 0.025,
        "wacc": 0.0950,
    },
    "bull": {
        "search_coverage_delta": 0.012,    # AI Mode monetises better than Search
        "search_cpc_delta": 0.015,
        "cloud_capacity_delta": 0.06,
        "ebitda_margin_delta": 0.020,
        "capex_delta": -0.025,             # AI capex proves front-loaded, not permanent
        "terminal_growth": 0.038,
        # The reverse DCF says the market is discounting Alphabet at ~6.0%. That
        # is below any CAPM build we would defend, but the equity risk premium
        # is not observable and mega-cap terminal-value duration is genuinely
        # long. A bull case that cannot reach the market price is not a bull
        # case, it is an assertion that the market has no chance of being right.
        "wacc": 0.0725,
    },
}

# --------------------------------------------------------------------------
# Nvidia
# --------------------------------------------------------------------------
# Base = FY2026 reported segments ($m); sum $215.9bn vs consolidated $213.7bn.
NVDA_BASE_SEGMENTS = {
    "data_center": 193_737e6,
    "gaming": 16_042e6,
    "proviz": 3_191e6,
    "automotive": 2_349e6,
    "oem_other": 619e6,
}

NVDA_DRIVERS = {
    "base": {
        "segments": {
            # Data Center = systems shipped x ASP per system. Rubin lifts ASP;
            # unit growth decelerates as hyperscaler capex growth normalises and
            # custom silicon takes share of incremental sockets.
            "data_center": {
                "units": [0.52, 0.30, 0.18, 0.10, 0.05, 0.02],
                "asp": [0.16, 0.10, 0.06, 0.03, 0.01, 0.0],
                "attach_networking": [0.04, 0.03, 0.02, 0.02, 0.01, 0.01],
            },
            "gaming": {"growth": [0.12, 0.08, 0.06, 0.05, 0.04, 0.03]},
            "proviz": {"growth": [0.20, 0.15, 0.12, 0.10, 0.08, 0.06]},
            "automotive": {"growth": [0.35, 0.30, 0.25, 0.20, 0.15, 0.12]},
            "oem_other": {"growth": [0.05, 0.05, 0.05, 0.05, 0.05, 0.05]},
        },
        # Gross margin compresses as HBM/CoWoS cost inflates and as the mix
        # shifts toward full systems (lower margin than merchant silicon).
        "ebitda_margin": [0.645, 0.625, 0.600, 0.575, 0.550, 0.535],
        "capex_pct_revenue": [0.030, 0.032, 0.034, 0.035, 0.035, 0.035],
        "tax_rate": [0.16, 0.17, 0.17, 0.175, 0.175, 0.175],
        "nwc_pct_revenue": [0.115, 0.110, 0.105, 0.100, 0.095, 0.090],
        "terminal_growth": 0.030,
        "wacc": 0.0975,
    },
    "bear": {
        "dc_units_delta": -0.14,       # digestion year; custom ASIC share gain
        "dc_asp_delta": -0.05,
        "ebitda_margin_delta": -0.055,
        "capex_delta": 0.005,
        "terminal_growth": 0.020,
        "wacc": 0.1100,
    },
    "bull": {
        "dc_units_delta": 0.10,
        "dc_asp_delta": 0.04,
        "ebitda_margin_delta": 0.030,
        "capex_delta": -0.003,
        "terminal_growth": 0.035,
        "wacc": 0.0925,
    },
}

SPEC = {
    "GOOGL": {
        "name": "Alphabet Inc.",
        "base_segments": GOOGL_BASE_SEGMENTS,
        "drivers": GOOGL_DRIVERS,
        "segment_labels": {
            "search": "Google Search & other",
            "youtube_ads": "YouTube ads",
            "network": "Google Network",
            "subs_devices": "Subscriptions, platforms & devices",
            "cloud": "Google Cloud",
            "other_bets": "Other Bets",
        },
        "scenario_deltas": {
            "search": ("ad_coverage", "search_coverage_delta", "price_per_click", "search_cpc_delta"),
            "cloud": ("capacity", "cloud_capacity_delta"),
        },
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "base_segments": NVDA_BASE_SEGMENTS,
        "drivers": NVDA_DRIVERS,
        "segment_labels": {
            "data_center": "Data Center",
            "gaming": "Gaming",
            "proviz": "Professional Visualization",
            "automotive": "Automotive",
            "oem_other": "OEM & other",
        },
        "scenario_deltas": {
            "data_center": ("units", "dc_units_delta", "asp", "dc_asp_delta"),
        },
    },
}
