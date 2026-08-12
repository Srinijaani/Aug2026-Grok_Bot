# FSD vs Manual Tire Wear — Synthetic Texas Simulation

Simulates **10,000 Tesla vehicles** over **1 year** in Texas and estimates tire wear under FSD vs manual miles using the study KPI framework.

> **Synthetic data only.** Not from Cortex, Tesla fleet logs, or field measurements. Assumed FSD effects are scenario parameters for methodology demo.

## Quick start

```bash
pip install -r simulation/requirements.txt
python simulation/fsd_tire_wear_sim.py
python simulation/global_fsd_tire_impact.py
```

Open:
- `simulation/output/report.html` — Texas fleet KPI report
- `simulation/output/global_impact_report.html` — global money + environment extrapolation

## Outputs

| File | Description |
| ---- | ----------- |
| `output/report.html` | Visual Texas KPI report |
| `output/global_impact_report.html` | Global tire $ savings + environmental impact |
| `output/summary.json` / `output/global_impact.json` | Machine-readable results |
| `output/fleet_year.csv` | 10,000 vehicle-year records |
| `output/figures/*.png` / `output/figures_global/*.png` | Charts |

## Scenario knobs (in `fsd_tire_wear_sim.py`)

Current run is an **FSD-favorable** inversion:

- `FSD_NTWR_MULTIPLIER = 0.88` (−12% mean wear on FSD miles)
- Lower rear scrub, WAI / LSD / SSP; lower LAI (smoother longitudinal)

## KPIs

1. NTWR — mm tread / 1,000 mode-attributed miles  
2. RUL / tire life — projected miles to replacement  
3. WAI — wear asymmetry index  
4. LSD — lateral severity dose  
5. LAI — longitudinal aggression index  
6. SSP — steering–slip proxy  
7. TPS — thermal–pressure stress (Texas heat confounder)  
8. TCI — tire cost intensity ($ / 1,000 mi)
