"""Fetch latest articles and YouTube uploads from curated authentic sources."""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import feedparser
import requests

from .sources import WEB_SOURCES, YOUTUBE_CHANNELS, WebSource, YouTubeChannel

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class ScrapedItem:
    title: str
    summary: str
    url: str
    source: str
    published: str | None = None
    kind: str = "article"  # article | youtube
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: str | None, limit: int = 600) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _normalize_date(entry: dict[str, Any]) -> str | None:
    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
        except (TypeError, ValueError, IndexError, OverflowError):
            pass
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d")
            except (TypeError, ValueError):
                pass
    return None


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_rss(source_name: str, url: str, kind: str = "article", limit: int = 12) -> list[ScrapedItem]:
    session = _session()
    try:
        response = session.get(url, timeout=25)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s (%s): %s", source_name, url, exc)
        return []

    feed = feedparser.parse(response.content)
    items: list[ScrapedItem] = []
    for entry in feed.entries[:limit]:
        title = _clean_text(entry.get("title"), 200)
        if not title:
            continue
        link = entry.get("link") or ""
        summary = _clean_text(entry.get("summary") or entry.get("description"), 500)
        items.append(
            ScrapedItem(
                title=title,
                summary=summary,
                url=link,
                source=source_name,
                published=_normalize_date(entry),
                kind=kind,
                tags=[t.term for t in entry.get("tags", []) if getattr(t, "term", None)][:8],
            )
        )
    return items


def scrape_web_sources(sources: list[WebSource] | None = None, per_source: int = 10) -> list[ScrapedItem]:
    sources = sources or WEB_SOURCES
    collected: list[ScrapedItem] = []
    for source in sources:
        if source.kind != "rss":
            continue
        items = fetch_rss(source.name, source.url, kind="article", limit=per_source)
        logger.info("Fetched %d items from %s", len(items), source.name)
        collected.extend(items)
    return _dedupe(collected)


def scrape_youtube_channels(
    channels: list[YouTubeChannel] | None = None, per_channel: int = 5
) -> list[ScrapedItem]:
    channels = channels or YOUTUBE_CHANNELS
    collected: list[ScrapedItem] = []
    for channel in channels:
        items = fetch_rss(f"YouTube · {channel.name}", channel.rss_url, kind="youtube", limit=per_channel)
        for item in items:
            item.tags = list(dict.fromkeys([*item.tags, channel.focus.split(",")[0].strip()]))
        logger.info("Fetched %d videos from %s", len(items), channel.name)
        collected.extend(items)
    return _dedupe(collected)


def _dedupe(items: list[ScrapedItem]) -> list[ScrapedItem]:
    seen: set[str] = set()
    unique: list[ScrapedItem] = []
    for item in items:
        key = (item.url or item.title).strip().lower()
        # Google News wraps destination URLs; also dedupe by normalized title.
        title_key = re.sub(r"[^a-z0-9]+", "", item.title.lower())
        fingerprint = f"{urlparse(key).netloc}:{title_key[:80]}" if item.url else title_key
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append(item)
    return unique


def scrape_all() -> dict[str, Any]:
    articles = scrape_web_sources()
    videos = scrape_youtube_channels()
    return {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(articles),
        "video_count": len(videos),
        "articles": [a.to_dict() for a in articles],
        "videos": [v.to_dict() for v in videos],
        "youtube_channels": [
            {
                "name": c.name,
                "url": c.url,
                "focus": c.focus,
                "authentic": c.authentic,
            }
            for c in YOUTUBE_CHANNELS
        ],
        "web_sources": [
            {"name": s.name, "url": s.url, "topics": list(s.topics), "authentic": s.authentic}
            for s in WEB_SOURCES
        ],
    }
