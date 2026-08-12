# Chip Intel Briefing Agent

Automated agent that scrapes **authentic websites** and **YouTube channels** for the latest chip design and manufacturing intelligence, summarizes it, and produces a **3-slide PDF**:

1. **Trends** — process nodes, packaging, AI silicon, equipment
2. **Company Logos** — key foundry / fabless / equipment / IP leaders
3. **Geopolitical Impact** — CHIPS Act, export controls, supply-chain geography

The PDF is emailed to `sriniwas.gattani@gmail.com` (configurable).

## Quick start

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env   # then set SMTP_USER / SMTP_PASSWORD
python3 run_briefing.py
```

Generate PDF without sending email:

```bash
python3 run_briefing.py --skip-email
```

Email an already-generated PDF:

```bash
python3 run_briefing.py --email-only
```

## Email setup (Gmail)

1. Enable 2-Step Verification on the sender Google account.
2. Create an [App Password](https://myaccount.google.com/apppasswords).
3. Set environment variables (or `.env`):

| Variable | Required | Default |
|---|---|---|
| `SMTP_USER` | yes | — |
| `SMTP_PASSWORD` | yes | — |
| `SMTP_HOST` | no | `smtp.gmail.com` |
| `SMTP_PORT` | no | `587` |
| `EMAIL_FROM` | no | `SMTP_USER` |
| `EMAIL_TO` | no | `sriniwas.gattani@gmail.com` |

## Sources

Curated authentic feeds include Semiconductor Engineering, Electronics Weekly, EE Times, IEEE Spectrum, Google News semiconductor queries, plus YouTube channels such as Asianometry, High Yield, Branch Education, TechTechPotato, and ColdFusion.

## Outputs

- `output/scrape.json` — raw scraped articles/videos
- `output/briefing.json` — structured summary
- `output/chip_briefing.pdf` — 3-slide presentation
- `output/assets/logos/` — generated company logo tiles
