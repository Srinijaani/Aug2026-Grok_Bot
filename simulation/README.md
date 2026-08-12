# FSD vs Manual Tire Wear — Synthetic Texas Simulation

Simulates **10,000 Tesla vehicles** over **1 year** in Texas and estimates tire wear under FSD vs manual miles using the study KPI framework.

> **Synthetic data only.** Not from Cortex, Tesla fleet logs, or field measurements. Assumed FSD effects are scenario parameters for methodology demo.

## Quick start

```bash
pip install -r simulation/requirements.txt
python simulation/fsd_tire_wear_sim.py
```

Open `simulation/output/report.html` in a browser.

## Outputs

| File | Description |
| ---- | ----------- |
| `output/report.html` | Visual report + KPI tables |
| `output/summary.json` | Machine-readable results |
| `output/fleet_year.csv` | 10,000 vehicle-year records |
| `output/paired_mode_kpis.csv` | Within-vehicle Manual vs FSD rows |
| `output/monthly_sample_2000.csv` | Monthly blocks for 2,000-vehicle sample |
| `output/figures/*.png` | Charts |

## Scenario knobs (in `fsd_tire_wear_sim.py`)

- `FSD_NTWR_MULTIPLIER = 1.12` (+12% mean wear on FSD miles)
- Rear bias, higher WAI / LSD / SSP, lower LAI (smoother longitudinal)

## KPIs

1. NTWR — mm tread / 1,000 mode-attributed miles  
2. RUL / tire life — projected miles to replacement  
3. WAI — wear asymmetry index  
4. LSD — lateral severity dose  
5. LAI — longitudinal aggression index  
6. SSP — steering–slip proxy  
7. TPS — thermal–pressure stress (Texas heat confounder)  
8. TCI — tire cost intensity ($ / 1,000 mi)
