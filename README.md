# Cursor company dashboard

A static briefing dashboard for **Anysphere, Inc. (Cursor)** covering valuation, ARR, headcount, product releases, and the SpaceX merger share spread.

Open `index.html` in a browser. No build step.

## What’s on the page

| Panel | What’s shown |
| --- | --- |
| KPIs | $60B close value, $3.0B ARR, ~300 people, $3.37B raised, 391.0M SPCX shares issued |
| Valuation | Post-money from seed through the 14 Aug 2026 merger |
| ARR | Disclosed / reported run-rate, log scale |
| Headcount | Founding team through merger close |
| Revenue mix | Enterprise vs individual share of ARR |
| Share holding spread | SpaceX 8-K conversion of Cursor equity into SPCX Class A, RSUs, and options |
| Releases | Product, model, funding, and M&A timeline |
| Funding table | Round size, post-money, ARR, and revenue multiple |

Underlying series also live in `data/cursor-metrics.json`.

## How to read the share spread

At close (SpaceX Form 8-K, 14 August 2026):

- **389,289,254** SPCX Class A shares for outstanding Cursor common and preferred, at an implied **$60.0B** equity value
- **1,752,426** additional Class A shares for vested Cursor RSUs
- **29,128,326** unvested Cursor RSUs assumed as SpaceX RSUs
- **44,365,047** Cursor options assumed as SpaceX options

Implied 7-day VWAP = $60.0B ÷ 389,289,254 ≈ **$154.13**. The pre-close founder/investor mix tab is a reconstruction, not a filed cap table. Employee equity (16.2% fully diluted) is the one slice derived from the 8-K award conversions.

## Notes

- May 2026 ARR uses Bloomberg’s **$3.0B**. Sacra’s **$4.0B** estimate is footnoted, not plotted as the primary series.
- Headcount is assembled from press (The Verge, Series D coverage, Latka). Anysphere did not publish a formal census.
- Option dollar amounts are notional at deal VWAP; strikes were not disclosed.

Not an official Anysphere or SpaceX document.
