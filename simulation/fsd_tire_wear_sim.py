#!/usr/bin/env python3
"""
Synthetic 1-year Texas Tesla fleet simulation: FSD vs manual tire wear.

Generates ~10,000 vehicles of realistic dummy data, computes the study KPIs,
and writes CSV + chart artifacts consumed by the HTML report builder.

THIS IS SYNTHETIC DATA — not sourced from Cortex, Tesla fleet logs, or field measurements.
Assumed FSD effects are scenario parameters for methodology demonstration only.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

RNG = np.random.default_rng(42)
N_VEHICLES = 10_000
YEAR = 2025
OUT = Path(__file__).resolve().parent / "output"
FIG = OUT / "figures"

# Assumed scenario effects (synthetic — for demo only)
FSD_NTWR_MULTIPLIER = 1.12          # +12% mean wear under FSD miles
FSD_REAR_BIAS = 1.08                # extra rear wear under FSD
FSD_WAI_SHIFT = 0.035               # higher inner/outer asymmetry
FSD_LSD_MULTIPLIER = 1.18           # more lateral dose
FSD_LAI_MULTIPLIER = 0.88           # smoother longitudinal (less lead-foot)
FSD_SSP_MULTIPLIER = 1.15
MANUAL_BASE_NTWR_MM_PER_1K = 0.185  # ~0.185 mm / 1k mi → ~35k mi life on ~6.5 mm usable

MODELS = {
    "Model Y": {"share": 0.45, "weight_kg": 2000, "tire_cost": 980, "usable_mm": 6.6},
    "Model 3": {"share": 0.35, "weight_kg": 1820, "tire_cost": 860, "usable_mm": 6.4},
    "Model S": {"share": 0.08, "weight_kg": 2270, "tire_cost": 1400, "usable_mm": 6.8},
    "Model X": {"share": 0.07, "weight_kg": 2450, "tire_cost": 1500, "usable_mm": 6.8},
    "Cybertruck": {"share": 0.05, "weight_kg": 3100, "tire_cost": 1800, "usable_mm": 7.2},
}

METROS = {
    "DFW": 0.32,
    "Houston": 0.28,
    "Austin": 0.18,
    "San Antonio": 0.12,
    "Other TX": 0.10,
}

# Road abrasiveness / heat proxies by metro (TX)
METRO_WEAR_FACTOR = {
    "DFW": 1.00,
    "Houston": 1.06,       # heat + humidity + stop-go
    "Austin": 0.98,
    "San Antonio": 1.02,
    "Other TX": 0.95,
}


def _choice(mapping: dict[str, float], n: int) -> np.ndarray:
    keys = list(mapping.keys())
    p = np.array(list(mapping.values()), dtype=float)
    p /= p.sum()
    return RNG.choice(keys, size=n, p=p)


def simulate_fleet(n: int = N_VEHICLES) -> pd.DataFrame:
    model = _choice({k: v["share"] for k, v in MODELS.items()}, n)
    metro = _choice(METROS, n)

    # Annual miles: Texas EV owners ~ lognormal around 13.5k
    annual_miles = np.clip(RNG.lognormal(mean=np.log(13500), sigma=0.35, size=n), 4_000, 40_000)

    # FSD capability / subscription (~62% of study fleet)
    has_fsd = RNG.random(n) < 0.62
    # Engagement among FSD cars: beta around ~40%; non-FSD ~0
    engagement = np.where(
        has_fsd,
        np.clip(RNG.beta(2.2, 3.3, size=n), 0.02, 0.95),
        0.0,
    )

    weight = np.array([MODELS[m]["weight_kg"] for m in model], dtype=float)
    tire_cost = np.array([MODELS[m]["tire_cost"] for m in model], dtype=float)
    usable_mm = np.array([MODELS[m]["usable_mm"] for m in model], dtype=float)
    metro_f = np.array([METRO_WEAR_FACTOR[m] for m in metro], dtype=float)

    # Driver aggression latent trait (also affects manual more)
    aggression = RNG.beta(2.0, 3.5, size=n)
    # Wheel size proxy (19–21") bumps wear
    wheel_inch = RNG.choice([18, 19, 20, 21], size=n, p=[0.15, 0.40, 0.30, 0.15])
    wheel_f = 1.0 + (wheel_inch - 18) * 0.035

    # Summer heat exposure share of miles (TX)
    heat_share = np.clip(RNG.normal(0.38, 0.08, size=n), 0.15, 0.60)
    heat_f = 1.0 + 0.22 * heat_share

    # Alignment quality (lower = worse → more asymmetry)
    alignment_quality = np.clip(RNG.normal(0.85, 0.12, size=n), 0.4, 1.0)

    # Baseline manual NTWR (mm / 1k mi)
    weight_f = 1.0 + (weight - 1900) / 1900 * 0.25
    aggression_f = 1.0 + 0.35 * aggression
    base_manual = (
        MANUAL_BASE_NTWR_MM_PER_1K
        * metro_f
        * wheel_f
        * heat_f
        * weight_f
        * aggression_f
        * RNG.lognormal(0, 0.08, size=n)
    )

    ntwr_manual = base_manual
    ntwr_fsd = base_manual * FSD_NTWR_MULTIPLIER * RNG.lognormal(0, 0.05, size=n)

    fsd_miles = annual_miles * engagement
    manual_miles = annual_miles - fsd_miles

    # Blended observed wear (what you'd measure on the car)
    ntwr_blended = np.where(
        annual_miles > 0,
        (ntwr_manual * manual_miles + ntwr_fsd * fsd_miles) / annual_miles,
        ntwr_manual,
    )

    # Axle-specific: FSD rear bias
    ntwr_front_manual = ntwr_manual * 0.97
    ntwr_rear_manual = ntwr_manual * 1.03
    ntwr_front_fsd = ntwr_fsd * 0.94
    ntwr_rear_fsd = ntwr_fsd * (1.06 * FSD_REAR_BIAS)

    # Wear asymmetry index (inner-outer); higher under FSD + poor alignment
    wai_manual = np.clip(
        0.04 + (1 - alignment_quality) * 0.12 + aggression * 0.03 + RNG.normal(0, 0.015, n),
        0.0,
        0.45,
    )
    wai_fsd = np.clip(
        wai_manual + FSD_WAI_SHIFT + RNG.normal(0, 0.01, n),
        0.0,
        0.50,
    )

    # Lateral severity dose: minutes per 100 mi with |ay| > 0.20g
    lsd_manual = np.clip(8 + 22 * aggression + RNG.normal(0, 2.5, n), 2, 60)
    lsd_fsd = np.clip(lsd_manual * FSD_LSD_MULTIPLIER + RNG.normal(0, 1.5, n), 2, 70)

    # Longitudinal aggression: hard events per 100 mi
    lai_manual = np.clip(6 + 28 * aggression + RNG.normal(0, 2.0, n), 1, 55)
    lai_fsd = np.clip(lai_manual * FSD_LAI_MULTIPLIER + RNG.normal(0, 1.2, n), 1, 50)

    # Steering-slip proxy (unitless index)
    ssp_manual = np.clip(1.0 + 0.8 * aggression + (1 - alignment_quality) + RNG.normal(0, 0.1, n), 0.4, 4.0)
    ssp_fsd = np.clip(ssp_manual * FSD_SSP_MULTIPLIER + RNG.normal(0, 0.08, n), 0.4, 4.5)

    # Thermal-pressure stress (hours/year above +3 psi over cold target, TX-weighted)
    tps = np.clip(
        180 + 420 * heat_share + RNG.normal(0, 40, n) + 30 * (metro == "Houston").astype(float),
        50,
        900,
    )

    # Mode-attributed annual tread loss
    loss_manual_mm = ntwr_manual * (manual_miles / 1000.0)
    loss_fsd_mm = ntwr_fsd * (fsd_miles / 1000.0)
    loss_total_mm = loss_manual_mm + loss_fsd_mm

    # RUL to 4/32" (~3.175 mm remaining from usable depth starting full)
    # Approximate: remaining usable after year / blended rate
    remaining_mm = np.clip(usable_mm - loss_total_mm, 0.2, None)
    rul_32_miles = remaining_mm / ntwr_blended * 1000.0  # miles from now to 4/32" proxy on usable stack
    # clearer: miles to consume remaining usable tread
    miles_to_replace = remaining_mm / np.maximum(ntwr_blended, 1e-6) * 1000.0

    # Counterfactual RULs if 100% manual vs 100% FSD from full tread
    life_manual = usable_mm / ntwr_manual * 1000.0
    life_fsd = usable_mm / ntwr_fsd * 1000.0

    # Tire cost intensity ($ / 1k mi) under each pure mode
    tci_manual = tire_cost / (life_manual / 1000.0)
    tci_fsd = tire_cost / (life_fsd / 1000.0)
    tci_blended = tire_cost / ((usable_mm / ntwr_blended))

    df = pd.DataFrame(
        {
            "vehicle_id": [f"TX-{i:05d}" for i in range(1, n + 1)],
            "model": model,
            "metro": metro,
            "has_fsd": has_fsd,
            "fsd_engagement": engagement,
            "annual_miles": annual_miles,
            "fsd_miles": fsd_miles,
            "manual_miles": manual_miles,
            "wheel_inch": wheel_inch,
            "aggression": aggression,
            "alignment_quality": alignment_quality,
            "heat_share": heat_share,
            "ntwr_manual_mm_per_1k": ntwr_manual,
            "ntwr_fsd_mm_per_1k": ntwr_fsd,
            "ntwr_blended_mm_per_1k": ntwr_blended,
            "ntwr_front_manual": ntwr_front_manual,
            "ntwr_rear_manual": ntwr_rear_manual,
            "ntwr_front_fsd": ntwr_front_fsd,
            "ntwr_rear_fsd": ntwr_rear_fsd,
            "wai_manual": wai_manual,
            "wai_fsd": wai_fsd,
            "lsd_manual_min_per_100mi": lsd_manual,
            "lsd_fsd_min_per_100mi": lsd_fsd,
            "lai_manual_events_per_100mi": lai_manual,
            "lai_fsd_events_per_100mi": lai_fsd,
            "ssp_manual": ssp_manual,
            "ssp_fsd": ssp_fsd,
            "tps_hours_overpressure": tps,
            "tread_loss_mm_year": loss_total_mm,
            "miles_to_replace": miles_to_replace,
            "life_if_100pct_manual": life_manual,
            "life_if_100pct_fsd": life_fsd,
            "tci_manual_usd_per_1k": tci_manual,
            "tci_fsd_usd_per_1k": tci_fsd,
            "tci_blended_usd_per_1k": tci_blended,
            "tire_set_cost_usd": tire_cost,
            "usable_tread_mm": usable_mm,
        }
    )
    return df


def simulate_monthly(fleet: pd.DataFrame) -> pd.DataFrame:
    """12 monthly measurement blocks per vehicle (800–1k mi style cadence)."""
    rows = []
    months = pd.date_range(f"{YEAR}-01-01", periods=12, freq="MS")
    # TX monthly heat index proxy (relative)
    month_heat = np.array([0.55, 0.60, 0.75, 0.90, 1.05, 1.20, 1.25, 1.22, 1.10, 0.90, 0.70, 0.58])

    for _, v in fleet.iterrows():
        miles_m = RNG.dirichlet(np.ones(12) * 3.0) * v.annual_miles
        eng = v.fsd_engagement
        for i, (m, mi) in enumerate(zip(months, miles_m)):
            heat = month_heat[i]
            fsd_mi = mi * eng
            man_mi = mi - fsd_mi
            ntwr_m = v.ntwr_manual_mm_per_1k * (0.92 + 0.16 * (heat - 0.55) / 0.70)
            ntwr_f = v.ntwr_fsd_mm_per_1k * (0.92 + 0.16 * (heat - 0.55) / 0.70)
            loss = ntwr_m * (man_mi / 1000) + ntwr_f * (fsd_mi / 1000)
            rows.append(
                {
                    "vehicle_id": v.vehicle_id,
                    "month": m.strftime("%Y-%m"),
                    "miles": mi,
                    "fsd_miles": fsd_mi,
                    "manual_miles": man_mi,
                    "heat_index": heat,
                    "tread_loss_mm": loss,
                    "ntwr_obs_mm_per_1k": loss / (mi / 1000) if mi > 1 else np.nan,
                }
            )
    return pd.DataFrame(rows)


def paired_mode_table(fleet: pd.DataFrame) -> pd.DataFrame:
    """Long-form: one row per vehicle×mode for vehicles with FSD miles."""
    fsd = fleet[fleet.fsd_miles > 100].copy()
    man = fsd.copy()
    rows_fsd = pd.DataFrame(
        {
            "vehicle_id": fsd.vehicle_id,
            "mode": "FSD",
            "miles": fsd.fsd_miles,
            "ntwr": fsd.ntwr_fsd_mm_per_1k,
            "wai": fsd.wai_fsd,
            "lsd": fsd.lsd_fsd_min_per_100mi,
            "lai": fsd.lai_fsd_events_per_100mi,
            "ssp": fsd.ssp_fsd,
            "life_miles": fsd.life_if_100pct_fsd,
            "tci": fsd.tci_fsd_usd_per_1k,
            "ntwr_front": fsd.ntwr_front_fsd,
            "ntwr_rear": fsd.ntwr_rear_fsd,
        }
    )
    rows_man = pd.DataFrame(
        {
            "vehicle_id": man.vehicle_id,
            "mode": "Manual",
            "miles": man.manual_miles,
            "ntwr": man.ntwr_manual_mm_per_1k,
            "wai": man.wai_manual,
            "lsd": man.lsd_manual_min_per_100mi,
            "lai": man.lai_manual_events_per_100mi,
            "ssp": man.ssp_manual,
            "life_miles": man.life_if_100pct_manual,
            "tci": man.tci_manual_usd_per_1k,
            "ntwr_front": man.ntwr_front_manual,
            "ntwr_rear": man.ntwr_rear_manual,
        }
    )
    return pd.concat([rows_man, rows_fsd], ignore_index=True)


def summarize(fleet: pd.DataFrame, paired: pd.DataFrame) -> dict:
    fsd_users = fleet[fleet.has_fsd]
    # Within-vehicle deltas for FSD-capable cars
    d = fsd_users.copy()
    d["d_ntwr"] = d.ntwr_fsd_mm_per_1k / d.ntwr_manual_mm_per_1k - 1
    d["d_wai"] = d.wai_fsd - d.wai_manual
    d["d_lsd"] = d.lsd_fsd_min_per_100mi / d.lsd_manual_min_per_100mi - 1
    d["d_lai"] = d.lai_fsd_events_per_100mi / d.lai_manual_events_per_100mi - 1
    d["d_ssp"] = d.ssp_fsd / d.ssp_manual - 1
    d["d_life"] = d.life_if_100pct_fsd / d.life_if_100pct_manual - 1
    d["d_tci"] = d.tci_fsd_usd_per_1k / d.tci_manual_usd_per_1k - 1
    d["rear_ratio_fsd"] = d.ntwr_rear_fsd / d.ntwr_front_fsd
    d["rear_ratio_manual"] = d.ntwr_rear_manual / d.ntwr_front_manual

    def mean_ci(x: pd.Series) -> tuple[float, float, float]:
        m = float(x.mean())
        se = float(x.std(ddof=1) / np.sqrt(len(x)))
        return m, m - 1.96 * se, m + 1.96 * se

    # Paired t-tests on within-vehicle mode contrasts
    tests = {}
    for name, a, b in [
        ("ntwr", d.ntwr_fsd_mm_per_1k, d.ntwr_manual_mm_per_1k),
        ("wai", d.wai_fsd, d.wai_manual),
        ("lsd", d.lsd_fsd_min_per_100mi, d.lsd_manual_min_per_100mi),
        ("lai", d.lai_fsd_events_per_100mi, d.lai_manual_events_per_100mi),
        ("ssp", d.ssp_fsd, d.ssp_manual),
    ]:
        t, p = stats.ttest_rel(a, b)
        tests[name] = {"t": float(t), "p": float(p)}

    m_ntwr, lo_ntwr, hi_ntwr = mean_ci(d.d_ntwr)
    summary = {
        "n_vehicles": int(len(fleet)),
        "n_fsd_capable": int(len(fsd_users)),
        "mean_annual_miles": float(fleet.annual_miles.mean()),
        "mean_fsd_engagement_among_capable": float(fsd_users.fsd_engagement.mean()),
        "total_miles": float(fleet.annual_miles.sum()),
        "total_fsd_miles": float(fleet.fsd_miles.sum()),
        "total_manual_miles": float(fleet.manual_miles.sum()),
        "kpi": {
            "ntwr_manual_mean": float(d.ntwr_manual_mm_per_1k.mean()),
            "ntwr_fsd_mean": float(d.ntwr_fsd_mm_per_1k.mean()),
            "ntwr_delta_pct_mean": m_ntwr * 100,
            "ntwr_delta_pct_ci95": [lo_ntwr * 100, hi_ntwr * 100],
            "rul_manual_mean_miles": float(d.life_if_100pct_manual.mean()),
            "rul_fsd_mean_miles": float(d.life_if_100pct_fsd.mean()),
            "rul_delta_pct_mean": float(d.d_life.mean() * 100),
            "wai_manual_mean": float(d.wai_manual.mean()),
            "wai_fsd_mean": float(d.wai_fsd.mean()),
            "wai_delta_mean": float(d.d_wai.mean()),
            "lsd_delta_pct_mean": float(d.d_lsd.mean() * 100),
            "lai_delta_pct_mean": float(d.d_lai.mean() * 100),
            "ssp_delta_pct_mean": float(d.d_ssp.mean() * 100),
            "tci_manual_mean": float(d.tci_manual_usd_per_1k.mean()),
            "tci_fsd_mean": float(d.tci_fsd_usd_per_1k.mean()),
            "tci_delta_pct_mean": float(d.d_tci.mean() * 100),
            "rear_front_ratio_manual": float(d.rear_ratio_manual.mean()),
            "rear_front_ratio_fsd": float(d.rear_ratio_fsd.mean()),
            "decision_rule_hit_15pct": bool(m_ntwr >= 0.15),
            "decision_rule_hit_10pct": bool(m_ntwr >= 0.10),
        },
        "tests": tests,
        "by_metro": fleet.groupby("metro")
        .agg(
            n=("vehicle_id", "count"),
            mean_ntwr_blended=("ntwr_blended_mm_per_1k", "mean"),
            mean_engagement=("fsd_engagement", "mean"),
            mean_tps=("tps_hours_overpressure", "mean"),
        )
        .reset_index()
        .to_dict(orient="records"),
        "by_model": fleet.groupby("model")
        .agg(
            n=("vehicle_id", "count"),
            mean_ntwr_blended=("ntwr_blended_mm_per_1k", "mean"),
            mean_life_manual=("life_if_100pct_manual", "mean"),
            mean_life_fsd=("life_if_100pct_fsd", "mean"),
        )
        .reset_index()
        .to_dict(orient="records"),
        "scenario_params": {
            "FSD_NTWR_MULTIPLIER": FSD_NTWR_MULTIPLIER,
            "FSD_REAR_BIAS": FSD_REAR_BIAS,
            "FSD_WAI_SHIFT": FSD_WAI_SHIFT,
            "FSD_LSD_MULTIPLIER": FSD_LSD_MULTIPLIER,
            "FSD_LAI_MULTIPLIER": FSD_LAI_MULTIPLIER,
            "note": "Synthetic assumed effects for methodology demo — not real Cortex/fleet data.",
        },
    }
    return summary


def style_axes(ax, title: str):
    ax.set_title(title, fontsize=12, pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.25)


def make_charts(fleet: pd.DataFrame, paired: pd.DataFrame, monthly: pd.DataFrame, summary: dict) -> list[str]:
    FIG.mkdir(parents=True, exist_ok=True)
    paths = []
    fsd_users = fleet[fleet.has_fsd]

    # 1. NTWR distributions
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.hist(fsd_users.ntwr_manual_mm_per_1k, bins=40, alpha=0.55, label="Manual", color="#1f4e79")
    ax.hist(fsd_users.ntwr_fsd_mm_per_1k, bins=40, alpha=0.55, label="FSD", color="#c45c26")
    ax.axvline(fsd_users.ntwr_manual_mm_per_1k.mean(), color="#1f4e79", ls="--", lw=1.5)
    ax.axvline(fsd_users.ntwr_fsd_mm_per_1k.mean(), color="#c45c26", ls="--", lw=1.5)
    ax.set_xlabel("NTWR (mm / 1,000 miles)")
    ax.set_ylabel("Vehicles")
    ax.legend()
    style_axes(ax, "KPI-1: Normalized tread wear rate — FSD vs Manual")
    p = FIG / "01_ntwr_dist.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p.name)

    # 2. Within-vehicle NTWR delta
    fig, ax = plt.subplots(figsize=(8, 4.8))
    delta = (fsd_users.ntwr_fsd_mm_per_1k / fsd_users.ntwr_manual_mm_per_1k - 1) * 100
    ax.hist(delta, bins=40, color="#2f6f4e", alpha=0.85)
    ax.axvline(delta.mean(), color="#111", ls="--", label=f"Mean {delta.mean():.1f}%")
    ax.axvline(15, color="#a33", ls=":", label="15% decision threshold")
    ax.set_xlabel("Within-vehicle ΔNTWR (FSD / Manual − 1), %")
    ax.set_ylabel("Vehicles")
    ax.legend()
    style_axes(ax, "Within-vehicle FSD wear premium")
    p = FIG / "02_ntwr_delta.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p.name)

    # 3. KPI bar chart
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    labels = ["NTWR", "RUL (inv)", "WAI", "LSD", "LAI", "SSP", "TCI"]
    # RUL shown as life reduction % (positive = worse under FSD)
    vals = [
        summary["kpi"]["ntwr_delta_pct_mean"],
        -summary["kpi"]["rul_delta_pct_mean"],
        summary["kpi"]["wai_delta_mean"] / max(summary["kpi"]["wai_manual_mean"], 1e-6) * 100,
        summary["kpi"]["lsd_delta_pct_mean"],
        summary["kpi"]["lai_delta_pct_mean"],
        summary["kpi"]["ssp_delta_pct_mean"],
        summary["kpi"]["tci_delta_pct_mean"],
    ]
    colors = ["#c45c26" if v > 0 else "#1f4e79" for v in vals]
    ax.bar(labels, vals, color=colors, alpha=0.9)
    ax.axhline(0, color="#333", lw=0.8)
    ax.set_ylabel("% change under FSD vs Manual (within vehicle)")
    style_axes(ax, "KPI scorecard — synthetic Texas fleet (FSD-capable)")
    p = FIG / "03_kpi_scorecard.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p.name)

    # 4. Front vs rear
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    modes = ["Manual\nFront", "Manual\nRear", "FSD\nFront", "FSD\nRear"]
    means = [
        fsd_users.ntwr_front_manual.mean(),
        fsd_users.ntwr_rear_manual.mean(),
        fsd_users.ntwr_front_fsd.mean(),
        fsd_users.ntwr_rear_fsd.mean(),
    ]
    ax.bar(modes, means, color=["#7aa0c4", "#1f4e79", "#e2a37a", "#c45c26"])
    ax.set_ylabel("NTWR (mm / 1,000 mi)")
    style_axes(ax, "Axle wear: rear bias under FSD (synthetic)")
    p = FIG / "04_axle_bias.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p.name)

    # 5. Monthly fleet tread loss
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    m = monthly.groupby("month").agg(loss=("tread_loss_mm", "sum"), miles=("miles", "sum"), heat=("heat_index", "mean"))
    ax2 = ax.twinx()
    ax.plot(m.index, m.loss, color="#1f4e79", marker="o", label="Fleet tread loss (mm)")
    ax2.plot(m.index, m.heat, color="#c45c26", ls="--", marker="s", label="TX heat index")
    ax.set_ylabel("Total tread loss (mm)")
    ax2.set_ylabel("Heat index")
    ax.tick_params(axis="x", rotation=45)
    style_axes(ax, "Seasonality: monthly fleet tread loss vs Texas heat")
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="upper left")
    p = FIG / "05_monthly_seasonality.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p.name)

    # 6. By metro
    fig, ax = plt.subplots(figsize=(8, 4.8))
    metro = fleet.groupby("metro")["ntwr_blended_mm_per_1k"].mean().sort_values(ascending=False)
    ax.bar(metro.index, metro.values, color="#2f6f4e", alpha=0.85)
    ax.set_ylabel("Blended NTWR (mm / 1k mi)")
    style_axes(ax, "Blended wear by Texas metro")
    p = FIG / "06_metro.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p.name)

    # 7. Engagement vs wear premium
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    sample = fsd_users.sample(n=min(2000, len(fsd_users)), random_state=42)
    premium = (sample.ntwr_blended_mm_per_1k / sample.ntwr_manual_mm_per_1k - 1) * 100
    ax.scatter(sample.fsd_engagement * 100, premium, s=10, alpha=0.25, color="#1f4e79")
    z = np.polyfit(sample.fsd_engagement * 100, premium, 1)
    xs = np.linspace(0, 100, 50)
    ax.plot(xs, np.polyval(z, xs), color="#c45c26", lw=2, label="Trend")
    ax.set_xlabel("FSD engagement (% of miles)")
    ax.set_ylabel("Blended wear premium vs pure-manual (%)")
    ax.legend()
    style_axes(ax, "Dose–response: more FSD miles → higher blended wear")
    p = FIG / "07_dose_response.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p.name)

    # 8. Model life comparison
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    models = sorted(fsd_users.model.unique())
    x = np.arange(len(models))
    w = 0.35
    man_life = [fsd_users.loc[fsd_users.model == m, "life_if_100pct_manual"].mean() / 1000 for m in models]
    fsd_life = [fsd_users.loc[fsd_users.model == m, "life_if_100pct_fsd"].mean() / 1000 for m in models]
    ax.bar(x - w / 2, man_life, w, label="100% Manual", color="#1f4e79")
    ax.bar(x + w / 2, fsd_life, w, label="100% FSD", color="#c45c26")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=15)
    ax.set_ylabel("Projected tire life (1,000 miles)")
    ax.legend()
    style_axes(ax, "KPI-2: Projected tire life by model (counterfactual)")
    p = FIG / "08_model_life.png"
    fig.tight_layout()
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths.append(p.name)

    return paths


def write_html(summary: dict, chart_names: list[str]) -> Path:
    k = summary["kpi"]
    tests = summary["tests"]

    def pct(x):
        return f"{x:+.1f}%"

    cards = [
        ("Vehicles", f"{summary['n_vehicles']:,}"),
        ("FSD-capable", f"{summary['n_fsd_capable']:,}"),
        ("Total miles", f"{summary['total_miles']/1e6:.1f}M"),
        ("ΔNTWR (FSD)", pct(k["ntwr_delta_pct_mean"])),
        ("Δ Tire life", pct(k["rul_delta_pct_mean"])),
        ("Δ Tire cost / 1k mi", pct(k["tci_delta_pct_mean"])),
    ]
    card_html = "\n".join(
        f'<div class="card"><div class="label">{lab}</div><div class="value">{val}</div></div>'
        for lab, val in cards
    )
    chart_html = "\n".join(
        f'<figure><img src="figures/{name}" alt="{name}"/><figcaption>{name.replace("_", " ").replace(".png", "")}</figcaption></figure>'
        for name in chart_names
    )

    metro_rows = "".join(
        f"<tr><td>{r['metro']}</td><td>{r['n']:,}</td><td>{r['mean_ntwr_blended']:.3f}</td>"
        f"<td>{r['mean_engagement']*100:.1f}%</td><td>{r['mean_tps']:.0f}</td></tr>"
        for r in sorted(summary["by_metro"], key=lambda x: -x["mean_ntwr_blended"])
    )
    model_rows = "".join(
        f"<tr><td>{r['model']}</td><td>{r['n']:,}</td><td>{r['mean_ntwr_blended']:.3f}</td>"
        f"<td>{r['mean_life_manual']/1000:.1f}k</td><td>{r['mean_life_fsd']/1000:.1f}k</td></tr>"
        for r in summary["by_model"]
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>FSD vs Manual Tire Wear — Synthetic Texas Fleet Report</title>
<style>
  :root {{
    --ink: #1a1f16;
    --muted: #5c6658;
    --paper: #f3efe6;
    --card: #fffdf8;
    --accent: #c45c26;
    --blue: #1f4e79;
    --line: #d9d2c5;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
    background:
      radial-gradient(1200px 600px at 10% -10%, #e7dfd0 0%, transparent 60%),
      radial-gradient(900px 500px at 100% 0%, #d9e2ea 0%, transparent 55%),
      var(--paper);
    color: var(--ink); line-height: 1.45;
  }}
  header {{
    padding: 48px 7vw 24px; border-bottom: 1px solid var(--line);
  }}
  header p.eyebrow {{
    text-transform: uppercase; letter-spacing: 0.14em; font-size: 12px;
    color: var(--accent); font-family: ui-sans-serif, system-ui, sans-serif; margin: 0 0 10px;
  }}
  h1 {{ font-size: clamp(28px, 4vw, 44px); margin: 0 0 12px; max-width: 18ch; }}
  .sub {{ color: var(--muted); max-width: 62ch; font-size: 17px; }}
  .warn {{
    margin-top: 18px; padding: 12px 14px; background: #fff4e8; border-left: 4px solid var(--accent);
    font-family: ui-sans-serif, system-ui, sans-serif; font-size: 14px; max-width: 80ch;
  }}
  main {{ padding: 28px 7vw 64px; }}
  .cards {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px; margin: 8px 0 28px;
  }}
  .card {{
    background: var(--card); border: 1px solid var(--line); padding: 14px 16px;
  }}
  .card .label {{
    font-family: ui-sans-serif, system-ui, sans-serif; font-size: 11px; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--muted);
  }}
  .card .value {{ font-size: 26px; margin-top: 6px; font-weight: 600; }}
  h2 {{ margin: 36px 0 10px; font-size: 24px; }}
  h3 {{ margin: 22px 0 8px; font-size: 18px; }}
  p, li {{ font-size: 15.5px; color: var(--ink); }}
  .grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px;
  }}
  figure {{
    margin: 0; background: var(--card); border: 1px solid var(--line); padding: 10px;
  }}
  img {{ width: 100%; height: auto; display: block; }}
  figcaption {{
    font-family: ui-sans-serif, system-ui, sans-serif; font-size: 12px; color: var(--muted);
    padding: 8px 4px 2px;
  }}
  table {{
    width: 100%; border-collapse: collapse; background: var(--card);
    font-family: ui-sans-serif, system-ui, sans-serif; font-size: 13.5px;
  }}
  th, td {{ border-bottom: 1px solid var(--line); padding: 10px 12px; text-align: left; }}
  th {{ color: var(--muted); font-weight: 600; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; }}
  .two {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 18px; }}
  footer {{
    padding: 20px 7vw 40px; color: var(--muted); font-family: ui-sans-serif, system-ui, sans-serif; font-size: 12px;
    border-top: 1px solid var(--line);
  }}
</style>
</head>
<body>
<header>
  <p class="eyebrow">Synthetic simulation · Texas Tesla fleet · 1 year</p>
  <h1>FSD vs Manual Tire Wear</h1>
  <p class="sub">
    Simulated study of {summary['n_vehicles']:,} on-road Teslas in Texas using the paired within-vehicle
    KPI framework (NTWR, RUL, WAI, LSD, LAI, SSP, TPS, TCI).
  </p>
  <div class="warn">
    <strong>Not real fleet data.</strong> All inputs are synthetic dummy data generated for methodology
    demonstration. No Cortex, Tesla telemetry, or field measurements were used.
    Assumed FSD NTWR multiplier = {summary['scenario_params']['FSD_NTWR_MULTIPLIER']:.2f}.
  </div>
</header>
<main>
  <div class="cards">{card_html}</div>

  <h2>Executive summary</h2>
  <p>
    Among {summary['n_fsd_capable']:,} FSD-capable vehicles, within-vehicle contrasts show FSD miles wearing
    tread <strong>{pct(k['ntwr_delta_pct_mean'])}</strong> faster than manual miles
    (95% CI {k['ntwr_delta_pct_ci95'][0]:+.1f}% to {k['ntwr_delta_pct_ci95'][1]:+.1f}%).
    Counterfactual tire life falls from
    <strong>{k['rul_manual_mean_miles']/1000:.1f}k</strong> to
    <strong>{k['rul_fsd_mean_miles']/1000:.1f}k</strong> miles ({pct(k['rul_delta_pct_mean'])}).
    Rear/front NTWR ratio rises from {k['rear_front_ratio_manual']:.3f} (manual) to
    {k['rear_front_ratio_fsd']:.3f} (FSD). Lateral dose and steering-slip proxies increase, while
    longitudinal aggression falls — consistent with smoother throttle but higher cornering scrub.
  </p>
  <p>
    Decision rule (≥15% NTWR premium):
    <strong>{"HIT" if k["decision_rule_hit_15pct"] else "NOT HIT"}</strong>
    at the mean; ≥10% threshold:
    <strong>{"HIT" if k["decision_rule_hit_10pct"] else "NOT HIT"}</strong>.
  </p>

  <h2>KPI results (FSD-capable, within-vehicle)</h2>
  <div class="two">
    <table>
      <thead><tr><th>KPI</th><th>Manual</th><th>FSD</th><th>Δ</th><th>p (paired t)</th></tr></thead>
      <tbody>
        <tr><td>1 NTWR (mm/1k mi)</td><td>{k['ntwr_manual_mean']:.3f}</td><td>{k['ntwr_fsd_mean']:.3f}</td><td>{pct(k['ntwr_delta_pct_mean'])}</td><td>{tests['ntwr']['p']:.2e}</td></tr>
        <tr><td>2 Tire life (mi)</td><td>{k['rul_manual_mean_miles']:,.0f}</td><td>{k['rul_fsd_mean_miles']:,.0f}</td><td>{pct(k['rul_delta_pct_mean'])}</td><td>—</td></tr>
        <tr><td>3 WAI</td><td>{k['wai_manual_mean']:.3f}</td><td>{k['wai_fsd_mean']:.3f}</td><td>{k['wai_delta_mean']:+.3f}</td><td>{tests['wai']['p']:.2e}</td></tr>
        <tr><td>4 LSD (min/100 mi)</td><td>—</td><td>—</td><td>{pct(k['lsd_delta_pct_mean'])}</td><td>{tests['lsd']['p']:.2e}</td></tr>
        <tr><td>5 LAI (events/100 mi)</td><td>—</td><td>—</td><td>{pct(k['lai_delta_pct_mean'])}</td><td>{tests['lai']['p']:.2e}</td></tr>
        <tr><td>6 SSP</td><td>—</td><td>—</td><td>{pct(k['ssp_delta_pct_mean'])}</td><td>{tests['ssp']['p']:.2e}</td></tr>
        <tr><td>8 TCI ($/1k mi)</td><td>${k['tci_manual_mean']:.2f}</td><td>${k['tci_fsd_mean']:.2f}</td><td>{pct(k['tci_delta_pct_mean'])}</td><td>—</td></tr>
      </tbody>
    </table>
    <div>
      <h3>Interpretation</h3>
      <ul>
        <li>Primary wear outcome (NTWR) is elevated under FSD in this synthetic scenario.</li>
        <li>Mechanism mix: ↑ LSD / SSP / WAI / rear bias; ↓ LAI (smoother long. control).</li>
        <li>Economics: tire cost intensity rises ~{k['tci_delta_pct_mean']:.1f}% under pure-FSD counterfactual.</li>
        <li>Texas heat (TPS) is modeled as a confounder shared across modes, stratified by metro/month.</li>
      </ul>
    </div>
  </div>

  <h2>Visuals</h2>
  <div class="grid">{chart_html}</div>

  <h2>By Texas metro</h2>
  <table>
    <thead><tr><th>Metro</th><th>N</th><th>Blended NTWR</th><th>Mean FSD engagement</th><th>TPS hours</th></tr></thead>
    <tbody>{metro_rows}</tbody>
  </table>

  <h2>By model</h2>
  <table>
    <thead><tr><th>Model</th><th>N</th><th>Blended NTWR</th><th>Life 100% Manual</th><th>Life 100% FSD</th></tr></thead>
    <tbody>{model_rows}</tbody>
  </table>
</main>
<footer>
  Generated by simulation/fsd_tire_wear_sim.py · seed=42 · year={YEAR} ·
  Scenario params: {json.dumps(summary['scenario_params'])}
</footer>
</body>
</html>
"""
    path = OUT / "report.html"
    path.write_text(html, encoding="utf-8")
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    print(f"Simulating {N_VEHICLES:,} vehicles…")
    fleet = simulate_fleet()
    print("Building monthly blocks…")
    # Monthly for a sample of 2,000 vehicles to keep runtime/artifact size reasonable,
    # plus full-fleet monthly aggregates via a lighter path for charts.
    monthly_sample = simulate_monthly(fleet.sample(n=2_000, random_state=7))
    # Lightweight full-fleet monthly aggregate (no per-vehicle expansion of all 10k)
    months = pd.date_range(f"{YEAR}-01-01", periods=12, freq="MS")
    month_heat = np.array([0.55, 0.60, 0.75, 0.90, 1.05, 1.20, 1.25, 1.22, 1.10, 0.90, 0.70, 0.58])
    agg_rows = []
    for i, m in enumerate(months):
        share = 1 / 12
        heat = month_heat[i]
        miles = fleet.annual_miles.sum() * share
        fsd_miles = (fleet.annual_miles * fleet.fsd_engagement).sum() * share
        man_miles = miles - fsd_miles
        # approximate fleet loss using mean rates scaled by heat
        ntwr_m = fleet.ntwr_manual_mm_per_1k.mean() * (0.92 + 0.16 * (heat - 0.55) / 0.70)
        ntwr_f = fleet.ntwr_fsd_mm_per_1k.mean() * (0.92 + 0.16 * (heat - 0.55) / 0.70)
        loss = ntwr_m * (man_miles / 1000) + ntwr_f * (fsd_miles / 1000)
        agg_rows.append(
            {
                "month": m.strftime("%Y-%m"),
                "miles": miles,
                "fsd_miles": fsd_miles,
                "manual_miles": man_miles,
                "heat_index": heat,
                "tread_loss_mm": loss,
            }
        )
    monthly_agg = pd.DataFrame(agg_rows)

    paired = paired_mode_table(fleet)
    summary = summarize(fleet, paired)

    fleet.to_csv(OUT / "fleet_year.csv", index=False)
    monthly_sample.to_csv(OUT / "monthly_sample_2000.csv", index=False)
    paired.to_csv(OUT / "paired_mode_kpis.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Rendering charts…")
    charts = make_charts(fleet, paired, monthly_agg, summary)
    report = write_html(summary, charts)
    print(f"Wrote {report}")
    print(json.dumps({k: summary[k] for k in ("n_vehicles", "n_fsd_capable", "kpi")}, indent=2))


if __name__ == "__main__":
    main()
