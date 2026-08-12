#!/usr/bin/env python3
"""
Global extrapolation: FSD tire-cost savings + environmental impact.

Takes the FSD-favorable synthetic KPI results and scales them to public
estimates of the worldwide Tesla on-road fleet / FSD subscriber base.

THIS IS AN ILLUSTRATIVE EXTRAPOLATION of synthetic scenario assumptions —
not Cortex data, not audited Tesla fleet economics, not measured LCA.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent / "output"
FIG = OUT / "figures_global"
SUMMARY_PATH = OUT / "summary.json"

# --- Public / literature anchors (documented in report) ---
GLOBAL_DELIVERIES_CUM = 9_700_000          # ~Q2 2026 cumulative deliveries (press)
ON_ROAD_RETENTION = 0.82                   # still-operational share assumption
FSD_ACTIVE_SUBS = 1_480_000                # Tesla Q2 2026 active FSD (incl. prepaid)
GLOBAL_MEAN_ANNUAL_MILES = 11_500          # blended US/EU/CN assumption
MEAN_ENGAGEMENT_FSD = None                 # filled from summary if present, else 0.40
AVG_TIRE_SET_USD = 1_050                   # global blended EV performance set

# Environmental factors (order-of-magnitude literature anchors)
KG_CO2E_PER_TIRE_CRADLE = 45.0             # materials + manufacturing (passenger PCR mid)
KG_RUBBER_PER_TIRE = 9.0                   # approx compound mass
KG_WEAR_MASS_PER_TIRE_LIFE = 1.25          # lifetime tread mass lost to environment
TWP_MG_PER_TONNE_KM = 57.1                 # EEA-style 4-tire factor per t·km
MEAN_VEHICLE_TONNES = 2.05                 # Tesla fleet blend
TREE_KG_CO2_PER_YEAR = 21.0                # rough sequestration equivalence
PASSENGER_CAR_KG_CO2E_PER_YEAR = 4_600     # rough ICE annual for comparison framing


def load_kpis() -> dict:
    summary = json.loads(SUMMARY_PATH.read_text())
    return summary


def extrapolate(summary: dict) -> dict:
    k = summary["kpi"]
    engagement = summary.get("mean_fsd_engagement_among_capable", 0.40)
    global MEAN_ENGAGEMENT_FSD
    MEAN_ENGAGEMENT_FSD = float(engagement)

    on_road = int(GLOBAL_DELIVERIES_CUM * ON_ROAD_RETENTION)
    fsd_cars = FSD_ACTIVE_SUBS
    non_fsd = max(on_road - fsd_cars, 0)

    ntwr_m = k["ntwr_manual_mean"]
    ntwr_f = k["ntwr_fsd_mean"]
    wear_reduction = (ntwr_m - ntwr_f) / ntwr_m  # ~0.119
    tci_m = k["tci_manual_mean"]
    tci_f = k["tci_fsd_mean"]
    tci_save_per_1k = tci_m - tci_f
    life_m = k["rul_manual_mean_miles"]
    life_f = k["rul_fsd_mean_miles"]

    # Annual miles on FSD among FSD-capable cars
    fsd_miles_yr = fsd_cars * GLOBAL_MEAN_ANNUAL_MILES * engagement
    manual_miles_on_fsd_cars = fsd_cars * GLOBAL_MEAN_ANNUAL_MILES * (1 - engagement)
    fleet_miles_yr = on_road * GLOBAL_MEAN_ANNUAL_MILES

    # Money: apply TCI delta only to FSD-attributed miles (vs counterfactual all-manual)
    annual_usd_saved = (fsd_miles_yr / 1000.0) * tci_save_per_1k
    per_fsd_owner_usd = annual_usd_saved / fsd_cars
    # Lifetime of ownership (~8 years remaining useful ownership horizon)
    ownership_years = 8.0
    lifetime_usd_saved = annual_usd_saved * ownership_years

    # Deferred tire sets: extra miles of life on FSD miles / life_manual * sets
    # Equivalent: rubber wear avoided / usable wear per set
    usable_mm = 6.6  # blend
    mm_saved = (fsd_miles_yr / 1000.0) * (ntwr_m - ntwr_f)
    # Convert mm of tread depth saved across 4 tires ≈ proportional to mass
    # usable ~6.6 mm corresponds to ~1.25 kg wear mass per tire * 4
    wear_mass_per_set_life = KG_WEAR_MASS_PER_TIRE_LIFE * 4
    fraction_life_saved = (mm_saved / usable_mm) / fsd_cars  # not used directly
    # Fleet-wide: depth-mm·vehicle saved / usable_mm = equivalent full-set lives deferred
    sets_deferred_yr = mm_saved / usable_mm
    tires_deferred_yr = sets_deferred_yr * 4
    usd_from_sets = sets_deferred_yr * AVG_TIRE_SET_USD  # alternate money view

    # Tire wear particles avoided (use-phase)
    # Baseline TWP on those miles if manual NTWR, scaled by wear rate ratio
    twp_g_per_km_manual = (TWP_MG_PER_TONNE_KM * MEAN_VEHICLE_TONNES) / 1000.0  # grams/km
    twp_avoided_tonnes = (
        fsd_miles_yr * 1.60934 * twp_g_per_km_manual * wear_reduction / 1e6
    )  # miles→km

    # Manufacturing CO2 avoided from deferred replacement sets
    co2e_per_set = KG_CO2E_PER_TIRE_CRADLE * 4
    co2e_avoided_tonnes = sets_deferred_yr * co2e_per_set / 1000.0
    rubber_avoided_tonnes = tires_deferred_yr * KG_RUBBER_PER_TIRE / 1000.0

    # What-if: entire on-road fleet adopts FSD at same engagement
    whatif_fsd_miles = on_road * GLOBAL_MEAN_ANNUAL_MILES * engagement
    whatif_usd = (whatif_fsd_miles / 1000.0) * tci_save_per_1k
    whatif_mm = (whatif_fsd_miles / 1000.0) * (ntwr_m - ntwr_f)
    whatif_sets = whatif_mm / usable_mm
    whatif_co2e = whatif_sets * co2e_per_set / 1000.0
    whatif_twp = whatif_fsd_miles * 1.60934 * twp_g_per_km_manual * wear_reduction / 1e6

    return {
        "assumptions": {
            "global_deliveries_cum": GLOBAL_DELIVERIES_CUM,
            "on_road_retention": ON_ROAD_RETENTION,
            "on_road_fleet": on_road,
            "fsd_active_subs": fsd_cars,
            "non_fsd_on_road": non_fsd,
            "global_mean_annual_miles": GLOBAL_MEAN_ANNUAL_MILES,
            "mean_fsd_engagement": engagement,
            "avg_tire_set_usd": AVG_TIRE_SET_USD,
            "ntwr_manual": ntwr_m,
            "ntwr_fsd": ntwr_f,
            "wear_reduction_on_fsd_miles": wear_reduction,
            "tci_save_usd_per_1k_mi": tci_save_per_1k,
            "life_manual_mi": life_m,
            "life_fsd_mi": life_f,
            "kg_co2e_per_tire_cradle": KG_CO2E_PER_TIRE_CRADLE,
            "scenario": summary.get("scenario_params", {}).get("scenario", "fsd_favorable"),
            "disclaimer": (
                "Illustrative extrapolation of synthetic FSD-favorable KPIs onto public fleet "
                "counts. Not real measured savings."
            ),
        },
        "annual": {
            "fsd_miles": fsd_miles_yr,
            "manual_miles_on_fsd_cars": manual_miles_on_fsd_cars,
            "fleet_miles": fleet_miles_yr,
            "usd_saved_tci_method": annual_usd_saved,
            "usd_saved_sets_method": usd_from_sets,
            "usd_per_fsd_owner": per_fsd_owner_usd,
            "sets_deferred": sets_deferred_yr,
            "tires_deferred": tires_deferred_yr,
            "twp_avoided_tonnes": twp_avoided_tonnes,
            "co2e_avoided_tonnes_mfg": co2e_avoided_tonnes,
            "rubber_compound_avoided_tonnes": rubber_avoided_tonnes,
            "tree_years_equiv": co2e_avoided_tonnes * 1000 / TREE_KG_CO2_PER_YEAR,
            "ice_car_years_equiv": co2e_avoided_tonnes * 1000 / PASSENGER_CAR_KG_CO2E_PER_YEAR,
        },
        "lifetime_8yr": {
            "usd_saved_tci_method": lifetime_usd_saved,
            "sets_deferred": sets_deferred_yr * ownership_years,
            "tires_deferred": tires_deferred_yr * ownership_years,
            "co2e_avoided_tonnes_mfg": co2e_avoided_tonnes * ownership_years,
            "twp_avoided_tonnes": twp_avoided_tonnes * ownership_years,
        },
        "what_if_full_fleet_same_engagement": {
            "fsd_miles": whatif_fsd_miles,
            "usd_saved_yr": whatif_usd,
            "sets_deferred_yr": whatif_sets,
            "co2e_avoided_tonnes_yr": whatif_co2e,
            "twp_avoided_tonnes_yr": whatif_twp,
        },
    }


def charts(impact: dict) -> list[str]:
    FIG.mkdir(parents=True, exist_ok=True)
    names = []
    a = impact["annual"]
    w = impact["what_if_full_fleet_same_engagement"]
    L = impact["lifetime_8yr"]

    def save(fig, name):
        p = FIG / name
        fig.tight_layout()
        fig.savefig(p, dpi=140)
        plt.close(fig)
        names.append(name)

    # 1. Money waterfall-ish bars
    fig, ax = plt.subplots(figsize=(8, 4.8))
    labels = ["Annual\n(FSD users)", "8-year\n(FSD users)", "Annual what-if\n(full fleet)"]
    vals = [
        a["usd_saved_tci_method"] / 1e6,
        L["usd_saved_tci_method"] / 1e6,
        w["usd_saved_yr"] / 1e6,
    ]
    bars = ax.bar(labels, vals, color=["#2f6f4e", "#1f4e79", "#c45c26"])
    ax.set_ylabel("USD saved (millions)")
    ax.set_title("Extrapolated tire-cost savings from lower FSD wear (synthetic)")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, f"${v:.1f}M", ha="center", va="bottom", fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    save(fig, "g01_money_saved.png")

    # 2. Tires deferred
    fig, ax = plt.subplots(figsize=(8, 4.8))
    labels = ["Tires deferred\n/ year", "Tires deferred\n/ 8 years", "What-if tires\n/ year"]
    vals = [a["tires_deferred"], L["tires_deferred"], w["sets_deferred_yr"] * 4]
    ax.bar(labels, vals, color="#1f4e79")
    ax.set_ylabel("Passenger tires")
    ax.set_title("Replacement tires avoided (extrapolated)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    save(fig, "g02_tires_deferred.png")

    # 3. Environment trio
    fig, ax = plt.subplots(figsize=(8, 4.8))
    labels = ["Mfg CO₂e\navoided (t/yr)", "TWP mass\navoided (t/yr)", "Rubber compound\navoided (t/yr)"]
    vals = [
        a["co2e_avoided_tonnes_mfg"],
        a["twp_avoided_tonnes"],
        a["rubber_compound_avoided_tonnes"],
    ]
    ax.bar(labels, vals, color=["#2f6f4e", "#c45c26", "#7aa0c4"])
    ax.set_ylabel("Tonnes / year")
    ax.set_title("Annual environmental co-benefits (order-of-magnitude)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    save(fig, "g03_environment.png")

    # 4. Per-owner savings distribution illustrative
    fig, ax = plt.subplots(figsize=(8, 4.8))
    rng = np.random.default_rng(7)
    # Spread engagement to show owner-level range
    eng = np.clip(rng.beta(2.2, 3.3, 5000), 0.05, 0.9)
    miles = rng.lognormal(np.log(GLOBAL_MEAN_ANNUAL_MILES), 0.35, 5000)
    save_i = (miles * eng / 1000.0) * impact["assumptions"]["tci_save_usd_per_1k_mi"]
    ax.hist(save_i, bins=40, color="#2f6f4e", alpha=0.85)
    ax.axvline(save_i.mean(), color="#111", ls="--", label=f"Mean ${save_i.mean():.0f}/yr")
    ax.set_xlabel("Annual tire $ saved per FSD owner")
    ax.set_ylabel("Owners (illustrative sample)")
    ax.legend()
    ax.set_title("Per-owner tire savings distribution (synthetic engagement mix)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    save(fig, "g04_per_owner.png")

    # 5. Fleet composition
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.pie(
        [impact["assumptions"]["fsd_active_subs"], impact["assumptions"]["non_fsd_on_road"]],
        labels=["FSD active", "On-road without FSD"],
        colors=["#c45c26", "#d9d2c5"],
        autopct="%1.1f%%",
        startangle=90,
    )
    ax.set_title("Global Tesla on-road fleet split (assumed)")
    save(fig, "g05_fleet_split.png")

    return names


def write_html(impact: dict, charts: list[str]) -> Path:
    A = impact["assumptions"]
    Y = impact["annual"]
    L = impact["lifetime_8yr"]
    W = impact["what_if_full_fleet_same_engagement"]

    def money(x):
        if abs(x) >= 1e9:
            return f"${x/1e9:.2f}B"
        if abs(x) >= 1e6:
            return f"${x/1e6:.1f}M"
        if abs(x) >= 1e3:
            return f"${x/1e3:.0f}K"
        return f"${x:.0f}"

    cards = [
        ("On-road Teslas", f"{A['on_road_fleet']/1e6:.1f}M"),
        ("FSD-active cars", f"{A['fsd_active_subs']/1e6:.2f}M"),
        ("Annual tire $ saved", money(Y["usd_saved_tci_method"])),
        ("$/FSD owner / yr", money(Y["usd_per_fsd_owner"])),
        ("Tires deferred / yr", f"{Y['tires_deferred']:,.0f}"),
        ("Mfg CO₂e avoided / yr", f"{Y['co2e_avoided_tonnes_mfg']:,.0f} t"),
    ]
    card_html = "\n".join(
        f'<div class="card"><div class="label">{l}</div><div class="value">{v}</div></div>'
        for l, v in cards
    )
    fig_html = "\n".join(
        f'<figure><img src="figures_global/{n}" alt="{n}"/><figcaption>{n}</figcaption></figure>'
        for n in charts
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Global FSD Tire Savings & Environmental Impact (Extrapolated)</title>
<style>
  :root {{
    --ink:#142017; --muted:#5a665c; --paper:#eef3ea; --card:#fbfef9;
    --line:#cfd9cc; --accent:#2f6f4e; --warm:#c45c26; --blue:#1f4e79;
  }}
  body {{
    margin:0; font-family:"Source Serif 4", "Iowan Old Style", Georgia, serif;
    color:var(--ink);
    background:
      radial-gradient(900px 500px at 0% 0%, #d7e8d7 0%, transparent 55%),
      radial-gradient(800px 480px at 100% 10%, #e8dfd2 0%, transparent 50%),
      var(--paper);
    line-height:1.45;
  }}
  header {{ padding:48px 7vw 22px; border-bottom:1px solid var(--line); }}
  .eyebrow {{
    font-family:ui-sans-serif,system-ui,sans-serif; text-transform:uppercase;
    letter-spacing:.14em; font-size:12px; color:var(--accent); margin:0 0 10px;
  }}
  h1 {{ font-size:clamp(28px,4vw,44px); margin:0 0 12px; max-width:18ch; }}
  .sub {{ max-width:70ch; color:var(--muted); font-size:17px; }}
  .warn {{
    margin-top:16px; max-width:85ch; padding:12px 14px; background:#fff6e8;
    border-left:4px solid var(--warm);
    font-family:ui-sans-serif,system-ui,sans-serif; font-size:13.5px;
  }}
  main {{ padding:28px 7vw 64px; }}
  .cards {{
    display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    gap:12px; margin-bottom:28px;
  }}
  .card {{ background:var(--card); border:1px solid var(--line); padding:14px 16px; }}
  .label {{
    font-family:ui-sans-serif,system-ui,sans-serif; font-size:11px; letter-spacing:.08em;
    text-transform:uppercase; color:var(--muted);
  }}
  .value {{ font-size:26px; margin-top:6px; font-weight:650; }}
  h2 {{ margin:34px 0 10px; font-size:24px; }}
  h3 {{ margin:20px 0 8px; font-size:18px; }}
  p,li {{ font-size:15.5px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:16px; }}
  figure {{ margin:0; background:var(--card); border:1px solid var(--line); padding:10px; }}
  img {{ width:100%; display:block; }}
  figcaption {{
    font-family:ui-sans-serif,system-ui,sans-serif; font-size:12px; color:var(--muted); padding-top:8px;
  }}
  table {{
    width:100%; border-collapse:collapse; background:var(--card);
    font-family:ui-sans-serif,system-ui,sans-serif; font-size:13.5px;
  }}
  th,td {{ border-bottom:1px solid var(--line); padding:10px 12px; text-align:left; }}
  th {{ font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); }}
  .two {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:18px; }}
  footer {{
    border-top:1px solid var(--line); padding:18px 7vw 40px; color:var(--muted);
    font-family:ui-sans-serif,system-ui,sans-serif; font-size:12px;
  }}
</style>
</head>
<body>
<header>
  <p class="eyebrow">Global extrapolation · FSD-favorable synthetic KPIs · 2026 anchors</p>
  <h1>How FSD could save Tesla drivers money on tires</h1>
  <p class="sub">
    Scaling the FSD-favorable tire-wear simulation to the worldwide on-road Tesla fleet —
    dollar savings for owners, deferred replacements, and environmental co-benefits.
  </p>
  <div class="warn">
    <strong>Illustrative only.</strong> Wear deltas come from a synthetic scenario
    (FSD NTWR −{A['wear_reduction_on_fsd_miles']*100:.1f}% on FSD miles), then multiplied by public
    fleet/FSD counts (~{A['on_road_fleet']/1e6:.1f}M on-road, {A['fsd_active_subs']/1e6:.2f}M FSD-active).
    This is <em>not</em> Cortex data, audited Tesla economics, or a measured LCA.
  </div>
</header>
<main>
  <div class="cards">{card_html}</div>

  <h2>Executive summary</h2>
  <p>
    If FSD miles wear tread {A['wear_reduction_on_fsd_miles']*100:.1f}% less than manual miles
    (synthetic assumption), today’s ~{A['fsd_active_subs']/1e6:.2f}M FSD-active Teslas —
    driving ~{Y['fsd_miles']/1e9:.2f}B FSD miles/year at {A['mean_fsd_engagement']*100:.0f}% engagement —
    would save owners about <strong>{money(Y['usd_saved_tci_method'])} per year</strong>
    (~<strong>{money(Y['usd_per_fsd_owner'])}</strong> per FSD owner), defer
    <strong>{Y['tires_deferred']:,.0f} tires</strong> of replacements, avoid roughly
    <strong>{Y['co2e_avoided_tonnes_mfg']:,.0f} tonnes CO₂e</strong> of tire manufacturing, and keep
    ~<strong>{Y['twp_avoided_tonnes']:,.0f} tonnes</strong> of tire-wear particles out of air/soil/water
    versus an all-manual counterfactual on those same miles.
  </p>
  <p>
    Over an 8-year ownership horizon that compounds to ~<strong>{money(L['usd_saved_tci_method'])}</strong>
    and ~<strong>{L['tires_deferred']:,.0f}</strong> tires deferred among current FSD users.
    If the entire ~{A['on_road_fleet']/1e6:.1f}M on-road fleet used FSD at the same engagement rate,
    annual savings scale to ~<strong>{money(W['usd_saved_yr'])}</strong>.
  </p>

  <h2>Money saved on tires</h2>
  <div class="two">
    <table>
      <thead><tr><th>Metric</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>TCI savings on FSD miles</td><td>${A['tci_save_usd_per_1k_mi']:.2f} / 1,000 mi</td></tr>
        <tr><td>Annual FSD miles (global)</td><td>{Y['fsd_miles']/1e9:.2f} billion</td></tr>
        <tr><td>Annual owner savings (TCI method)</td><td>{money(Y['usd_saved_tci_method'])}</td></tr>
        <tr><td>Cross-check via deferred sets × ${A['avg_tire_set_usd']:,.0f}</td><td>{money(Y['usd_saved_sets_method'])}</td></tr>
        <tr><td>Average per FSD owner / year</td><td>{money(Y['usd_per_fsd_owner'])}</td></tr>
        <tr><td>8-year cumulative (current FSD base)</td><td>{money(L['usd_saved_tci_method'])}</td></tr>
        <tr><td>What-if full on-road fleet / year</td><td>{money(W['usd_saved_yr'])}</td></tr>
      </tbody>
    </table>
    <div>
      <h3>How the dollars are counted</h3>
      <ul>
        <li>Only <em>FSD-attributed miles</em> get the wear discount (engagement ≈ {A['mean_fsd_engagement']*100:.0f}%).</li>
        <li>Savings = FSD miles × (manual TCI − FSD TCI) from the synthetic KPI run.</li>
        <li>Deferred-set cross-check converts avoided tread depth into equivalent full tire-set lives × ${A['avg_tire_set_usd']:,.0f}.</li>
        <li>Does <strong>not</strong> subtract FSD subscription cost — this is tire OPEX only.</li>
      </ul>
    </div>
  </div>

  <h2>Worldwide environmental impact</h2>
  <div class="two">
    <table>
      <thead><tr><th>Impact pathway</th><th>Annual (FSD users)</th><th>8-year</th></tr></thead>
      <tbody>
        <tr><td>Replacement tires deferred</td><td>{Y['tires_deferred']:,.0f}</td><td>{L['tires_deferred']:,.0f}</td></tr>
        <tr><td>Tire sets deferred</td><td>{Y['sets_deferred']:,.0f}</td><td>{L['sets_deferred']:,.0f}</td></tr>
        <tr><td>Manufacturing CO₂e avoided</td><td>{Y['co2e_avoided_tonnes_mfg']:,.0f} t</td><td>{L['co2e_avoided_tonnes_mfg']:,.0f} t</td></tr>
        <tr><td>Tire wear particles avoided</td><td>{Y['twp_avoided_tonnes']:,.0f} t</td><td>{L['twp_avoided_tonnes']:,.0f} t</td></tr>
        <tr><td>Rubber compound demand avoided</td><td>{Y['rubber_compound_avoided_tonnes']:,.0f} t</td><td>{Y['rubber_compound_avoided_tonnes']*8:,.0f} t</td></tr>
        <tr><td>Tree-year CO₂e equivalence (rough)</td><td>{Y['tree_years_equiv']:,.0f}</td><td>{Y['tree_years_equiv']*8:,.0f}</td></tr>
      </tbody>
    </table>
    <div>
      <h3>Why this matters environmentally</h3>
      <ul>
        <li><strong>Fewer replacements</strong> → less rubber, steel, carbon black, factory energy, and shipping.</li>
        <li><strong>Less tire-wear dust</strong> → fewer microplastics and zinc-bearing particles to roads, stormwater, and air.</li>
        <li><strong>Manufacturing CO₂e</strong> uses ~{A['kg_co2e_per_tire_cradle']:.0f} kg CO₂e/tire cradle-to-gate (order-of-magnitude LCA anchor).</li>
        <li>Use-phase rolling-resistance energy is <em>not</em> re-modeled here; this report isolates tire wear / replacement effects.</li>
      </ul>
    </div>
  </div>

  <h2>Visuals</h2>
  <div class="grid">{fig_html}</div>

  <h2>Assumptions & sources</h2>
  <table>
    <thead><tr><th>Input</th><th>Value</th><th>Role</th></tr></thead>
    <tbody>
      <tr><td>Cumulative Tesla deliveries</td><td>{A['global_deliveries_cum']:,}</td><td>Public ~Q2 2026 press/filings context</td></tr>
      <tr><td>On-road retention</td><td>{A['on_road_retention']*100:.0f}%</td><td>Assumption → {A['on_road_fleet']:,} on-road</td></tr>
      <tr><td>Active FSD subscriptions</td><td>{A['fsd_active_subs']:,}</td><td>Tesla Q2 2026 disclosed metric</td></tr>
      <tr><td>Mean annual miles</td><td>{A['global_mean_annual_miles']:,}</td><td>Global blend assumption</td></tr>
      <tr><td>FSD engagement</td><td>{A['mean_fsd_engagement']*100:.1f}%</td><td>From synthetic fleet summary</td></tr>
      <tr><td>NTWR manual → FSD</td><td>{A['ntwr_manual']:.3f} → {A['ntwr_fsd']:.3f} mm/1k</td><td>Synthetic FSD-favorable KPI</td></tr>
      <tr><td>Avg tire set price</td><td>${A['avg_tire_set_usd']:,.0f}</td><td>Blended EV performance set</td></tr>
      <tr><td>CO₂e / tire (cradle)</td><td>{A['kg_co2e_per_tire_cradle']:.0f} kg</td><td>LCA order-of-magnitude</td></tr>
    </tbody>
  </table>
</main>
<footer>
  Generated by simulation/global_fsd_tire_impact.py · reads simulation/output/summary.json ·
  {A['disclaimer']}
</footer>
</body>
</html>
"""
    path = OUT / "global_impact_report.html"
    path.write_text(html, encoding="utf-8")
    return path


def main():
    summary = load_kpis()
    impact = extrapolate(summary)
    (OUT / "global_impact.json").write_text(json.dumps(impact, indent=2), encoding="utf-8")
    names = charts(impact)
    report = write_html(impact, names)
    print(f"Wrote {report}")
    print(json.dumps({
        "annual_usd_m": impact["annual"]["usd_saved_tci_method"] / 1e6,
        "per_owner": impact["annual"]["usd_per_fsd_owner"],
        "tires_yr": impact["annual"]["tires_deferred"],
        "co2e_t_yr": impact["annual"]["co2e_avoided_tonnes_mfg"],
        "twp_t_yr": impact["annual"]["twp_avoided_tonnes"],
        "whatif_usd_m": impact["what_if_full_fleet_same_engagement"]["usd_saved_yr"] / 1e6,
    }, indent=2))


if __name__ == "__main__":
    main()
