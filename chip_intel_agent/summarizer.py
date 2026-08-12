"""Summarize scraped semiconductor intelligence into three briefing themes."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .sources import (
    COMPANIES,
    COMPANY_KEYWORDS,
    GEO_KEYWORDS,
    TREND_KEYWORDS,
    YOUTUBE_CHANNELS,
)


@dataclass
class Bullet:
    text: str
    source: str | None = None
    url: str | None = None


@dataclass
class Briefing:
    generated_at: str
    trends: list[Bullet] = field(default_factory=list)
    companies: list[dict[str, str]] = field(default_factory=list)
    company_highlights: list[Bullet] = field(default_factory=list)
    geopolitics: list[Bullet] = field(default_factory=list)
    youtube_channels: list[dict[str, str]] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "trends": [asdict(b) for b in self.trends],
            "companies": self.companies,
            "company_highlights": [asdict(b) for b in self.company_highlights],
            "geopolitics": [asdict(b) for b in self.geopolitics],
            "youtube_channels": self.youtube_channels,
            "sources_used": self.sources_used,
            "stats": self.stats,
        }


def _blob(item: dict[str, Any]) -> str:
    return f"{item.get('title', '')} {item.get('summary', '')}".lower()


def _score(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for kw in keywords if kw in text)


def _shorten(title: str, summary: str, max_len: int = 160) -> str:
    base = title.strip()
    extra = summary.strip()
    sponsor_markers = (
        "subscribe and watch",
        "check out plaud",
        "go to https://",
        "go to http://",
        "use code ",
        "using my code",
        "get an exclusive",
        "sponsored by",
    )
    if extra and any(m in extra.lower() for m in sponsor_markers):
        extra = ""
    if extra and extra.lower() not in base.lower():
        # Prefer a concise clause from the summary when title is terse.
        clause = re.split(r"(?<=[.!?])\s+", extra)[0]
        if 40 < len(clause) < 220 and clause.lower() != base.lower():
            if not any(m in clause.lower() for m in sponsor_markers):
                candidate = f"{base} — {clause}"
                if len(candidate) <= max_len + 40:
                    base = candidate
    base = re.sub(r"\s+", " ", base).strip()
    if len(base) > max_len:
        return base[: max_len - 1].rstrip() + "…"
    return base


def _pick_top(
    items: list[dict[str, Any]],
    keywords: tuple[str, ...],
    limit: int,
    require_any: tuple[str, ...] | None = None,
) -> list[Bullet]:
    ranked: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        text = _blob(item)
        if require_any and not any(token in text for token in require_any):
            continue
        score = _score(text, keywords)
        # Mild recency boost if published date present (ISO-ish YYYY-MM-DD).
        published = item.get("published") or ""
        if published.startswith("202"):
            score += 1
        if score <= 0 and keywords is TREND_KEYWORDS:
            # Keep some general semiconductor headlines for trends.
            if any(w in text for w in ("chip", "semiconductor", "foundry", "wafer", "transistor")):
                score = 1
        if score > 0:
            ranked.append((score, item))
    ranked.sort(key=lambda pair: (-pair[0], pair[1].get("published") or "", pair[1].get("title") or ""))
    bullets: list[Bullet] = []
    seen_titles: set[str] = set()
    for _, item in ranked:
        key = re.sub(r"[^a-z0-9]+", "", (item.get("title") or "").lower())[:70]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        bullets.append(
            Bullet(
                text=_shorten(item.get("title", ""), item.get("summary", "")),
                source=item.get("source"),
                url=item.get("url"),
            )
        )
        if len(bullets) >= limit:
            break
    return bullets


def _company_mentions(items: list[dict[str, Any]]) -> Counter:
    counts: Counter = Counter()
    for item in items:
        text = _blob(item)
        for company in COMPANIES:
            name = company["name"].lower()
            if name == "arm":
                # Avoid matching common English word "arm" loosely.
                if re.search(r"\barm\b", text) or "arm holdings" in text:
                    counts[company["name"]] += 1
            elif name in text:
                counts[company["name"]] += 1
        for alias in COMPANY_KEYWORDS:
            if alias not in {c["name"].lower() for c in COMPANIES} and alias in text:
                counts[alias.title()] += 1
    return counts


def _fallback_trends() -> list[Bullet]:
    return [
        Bullet("Advanced logic moves toward angstrom-class nodes with Gate-All-Around (nanosheet) transistors."),
        Bullet("AI accelerators continue to drive HBM demand and advanced 2.5D/3D packaging capacity."),
        Bullet("High-NA EUV adoption is the next lithography bottleneck for leading-edge foundries."),
        Bullet("Chiplet architectures and UCIe-style interconnects reshape SoC design economics."),
        Bullet("Specialty nodes (SiC/GaN, mature CMOS) expand as automotive and power electronics grow."),
    ]


def _fallback_geo() -> list[Bullet]:
    return [
        Bullet("CHIPS Act incentives accelerate U.S. and allied fab construction, with multi-year ramp risk."),
        Bullet("Export controls on advanced tools and AI accelerators remain central to U.S.–China tech rivalry."),
        Bullet("Taiwan’s foundry concentration keeps geopolitical risk elevated for global supply chains."),
        Bullet("Netherlands/Japan tool controls around EUV and deposition equipment shape China’s node roadmap."),
        Bullet("Friendshoring (Japan, Europe, India, Middle East) diversifies but raises cost and time-to-yield."),
    ]


def summarize(scrape_payload: dict[str, Any]) -> Briefing:
    articles = scrape_payload.get("articles") or []
    videos = scrape_payload.get("videos") or []
    combined = [*articles, *videos]

    trends = _pick_top(combined, TREND_KEYWORDS, limit=6)
    chip_context = (
        "chip",
        "semiconductor",
        "foundry",
        "wafer",
        "tsmc",
        "intel",
        "samsung",
        "asml",
        "hbm",
        "euv",
        "fab",
        "gpu",
        "ai accelerator",
        "chips act",
        "lithography",
        "memory",
        "dram",
        "transistor",
    )
    geopolitics = _pick_top(combined, GEO_KEYWORDS, limit=6, require_any=chip_context)
    company_highlights = _pick_top(combined, COMPANY_KEYWORDS, limit=6)

    if len(trends) < 4:
        trends = (trends + _fallback_trends())[:6]
    if len(geopolitics) < 4:
        geopolitics = (geopolitics + _fallback_geo())[:6]

    mentions = _company_mentions(combined)
    companies = []
    for company in COMPANIES:
        companies.append(
            {
                **company,
                "mentions": str(mentions.get(company["name"], 0)),
            }
        )
    # Sort logo slide order by recent mention volume while keeping all curated firms.
    companies.sort(key=lambda c: (-int(c["mentions"]), c["name"]))

    sources_used = sorted({item.get("source") for item in combined if item.get("source")})
    youtube = [
        {"name": c.name, "url": c.url, "focus": c.focus}
        for c in YOUTUBE_CHANNELS
    ]

    return Briefing(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        trends=trends,
        companies=companies,
        company_highlights=company_highlights,
        geopolitics=geopolitics,
        youtube_channels=youtube,
        sources_used=sources_used,
        stats={
            "articles": len(articles),
            "videos": len(videos),
            "sources": len(sources_used),
        },
    )
