# Summary: TeraFab — New Chip Factory That Terrifies TSMC

| Field | Value |
| --- | --- |
| **Video** | [TeraFab — New Chip Factory That Terrifies TSMC](https://www.youtube.com/watch?v=FQhoQ4bRbe8) |
| **Channel** | [Anastasi In Tech](https://www.youtube.com/@AnastasiInTech) |
| **Video ID** | `FQhoQ4bRbe8` |
| **Topic** | Why Tesla/SpaceX/xAI’s Terafab is either genius vertical integration or a capital trap |

Full cleaned transcript: [`transcript.md`](./transcript.md)

---

## One-line verdict

Terafab aims to produce **1 TW/year of AI compute** at **2 nm GAA** in Texas by owning the full stack (logic, memory, packaging, test) — motivated by sold-out foundry capacity and huge silicon demand from cars, robots, and especially **space** — but tool scarcity, yield learning, and fab utilization make it extremely risky.

---

## Core thesis

1. **Leading-edge fabs are scarce.** Only ~2–3 companies (TSMC, Intel, Samsung) still make advanced nodes; capacity is booked years out.
2. **Chips are now the product** for Tesla/SpaceX (autonomy, AI, Starlink, rockets) — depending on foundries means paying margins, waiting for wafers, and slowing iteration.
3. **Terafab’s bet:** vertical integration at extreme scale, in Texas, possibly with Intel as manufacturing partner to de-risk the learning curve.
4. **Open question:** genius control of supply — or an Intel-style utilization/capital trap.

---

## Key numbers cited in the video

### Scale & tools

| Metric | Figure |
| --- | --- |
| Target AI compute output | **1 TW / year** |
| Process target | **2 nm**, gate-all-around (GAA) |
| Leading-edge players today | **2–3** (was ~12 in 2007) |
| EUV tool cost | **~$150M** each |
| EUVs per advanced fab | **~15–20** |
| Assumed fab throughput | **30,000 wafers/month** @ **85% yield** |
| Implied compute per “normal” advanced fab | **~40 GW / year** |
| Fabs-equivalent to hit 1 TW | **~25 fabs in one site** |
| EUVs needed at Terafab scale | **>300** |
| ASML EUV production | **~50 / year** globally |
| Proposed facility size | **~100M sq ft** (~**30×** TSMC Arizona-scale) |
| Stated starting capital | **~$25B** (called a “starting ticket”; long-run cost could be far higher) |
| Tool lead times (non-EUV) | **12–24 months**, then months to install/calibrate |

### Demand & economics (cars / robots)

| Metric | Figure |
| --- | --- |
| TSMC 3 nm / upcoming nodes | Booked **~3 years** ahead |
| AI demand vs supply (estimate) | Demand **≥3×** supply |
| Tesla Model 3 silicon | Up to **~3,000 chips**, **~$2,000** BOM |
| Typical non-AI chip supplier margin | **30–50%** |
| AI inference silicon (AI4/AI5) | **~$200 / car** |
| Potential in-house savings | Up to **~$1,000 / car** (~**12%** margin lift) |
| Robotaxi scenario (10M cars/yr) | Up to **~$5B / year** saved |
| Robot chip market upside | Volume could be **10–100×** automotive; capturing **10–20%** = multi-billion impact |

### Space & Starlink (claimed majority of wafers)

| Metric | Figure |
| --- | --- |
| Share of Terafab wafers for space | Potentially **up to ~80%** |
| Typical rad-hard chip price | **~$5,000** |
| Deep-space / fully rad-hard | **Tens of thousands** per chip (up to **~$10k+**) |
| Target cost if stack redesigned in-house | **~$300–$500** per chip |
| Preferred space nodes | Often **1–2 nodes behind** leading edge (reliability > perf) |
| Starlink terminal silicon | **~500 chips / terminal**, **~$150** silicon |
| Current Starlink chip manufacturing | Designed by Starlink, made by **STMicroelectronics** (Europe) |
| Advanced chips made in Asia today | **>90%** |

### Process / cleanroom claims

| Metric | Figure |
| --- | --- |
| Wafer time outside FOUP | **~70%** (exposed during process steps) |
| SOI equipment cost uplift | **~20%** (wafer-level cost uplift: single digits %) |
| TSMC Arizona path to GAA | **~5–6 years** (ramp via mature FinFET first) |
| Intel partnership (post-recording note) | Intel brings **18A** experience + packaging |

---

## Argument map

### Why try Terafab

- Foundry capacity is effectively sold out; waiting kills product roadmaps.
- Vertical integration captures supplier margins and shortens the design→silicon loop.
- Demand stack is huge: vehicles, Optimus-class robots, Starlink terminals, satellites, rad-hard space compute.
- Texas already has Samsung Taylor, TI presence, Gigafactory adjacency, incentives / CHIPS Act support.
- Pre-IPO / valuation angle: owning silicon manufacturing changes how investors price SpaceX/Tesla-like vertical stacks.
- Later addendum: **Intel partnership** raises odds by supplying process know-how and packaging.

### Why it may fail

- Needs years of global ASML EUV output alone; equipment is scarce and pre-ordered by incumbents.
- Co-locating logic + HBM memory + packaging + rad-hard flows risks cross-contamination and yield collapse.
- GAA at 2 nm from a greenfield fab is far harder than copying a mature recipe (TSMC’s cautious Arizona ramp).
- “Dirty fab” / relaxed cleanroom ideas collide with physics: particles at 2 nm destroy yield; FOUPs don’t protect wafers during process.
- Biggest economic risk: **utilization** — a city-scale fab must stay full 24/7 or depreciation crushes margins (Intel’s historical trap vs fabless NVIDIA/Apple).

---

## Strategic takeaways

1. **Terafab is not one factory** — it’s many factories (2 nm logic, space/SOI or older-node rad-hard, memory, packaging/test) compressed into one megasite.
2. **Space, not AI GPUs, may dominate wafer mix** in the narrator’s framing — shifting priorities from bleeding-edge performance to reliability and cost.
3. **The scarce resources are EUVs, skilled process control, and yield learning** — not just capital.
4. **Partnership (Intel) is the pragmatic de-risk** versus pure greenfield Musk-style fab ownership.
5. **Outcome frame:** control of supply chain and margins vs. irreversible capital intensity and utilization risk — “genius or expensive trap.”

---

## Notable entities mentioned

Tesla, SpaceX, xAI, Terafab, TSMC, Intel (18A), Samsung, ASML, SK Hynix, NVIDIA, Apple, AMD, Broadcom, STMicroelectronics, Infineon, NXP, Bosch, Texas Instruments, Siemens EDA (Tessent sponsor), Starlink, AI4/AI5, SpaceX D3, FOUP, GAA, FinFET, SOI, CHIPS Act, Texas / Giga Texas region.
