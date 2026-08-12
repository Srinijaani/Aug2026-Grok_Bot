"""Basic smoke tests for scrape → summarize → PDF pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from chip_intel_agent.pdf_builder import build_pdf
from chip_intel_agent.summarizer import summarize


def test_summarize_and_pdf(tmp_path: Path) -> None:
    sample = {
        "articles": [
            {
                "title": "TSMC ramps 2nm GAA production with High-NA EUV tools",
                "summary": "Advanced packaging and HBM demand continue to rise for AI accelerators.",
                "url": "https://example.com/a",
                "source": "Test Source",
                "published": "2026-08-01",
                "kind": "article",
                "tags": [],
            },
            {
                "title": "CHIPS Act funding accelerates U.S. fab construction amid export controls",
                "summary": "Geopolitical risk around Taiwan foundry capacity remains elevated.",
                "url": "https://example.com/b",
                "source": "Test Source",
                "published": "2026-08-02",
                "kind": "article",
                "tags": [],
            },
        ],
        "videos": [
            {
                "title": "How EUV lithography works",
                "summary": "ASML explains the process node roadmap.",
                "url": "https://youtube.com/watch?v=x",
                "source": "YouTube · Asianometry",
                "published": "2026-07-20",
                "kind": "youtube",
                "tags": [],
            }
        ],
    }
    briefing = summarize(sample)
    assert len(briefing.trends) >= 1
    assert len(briefing.geopolitics) >= 1
    assert len(briefing.companies) == 12

    pdf_path = tmp_path / "briefing.pdf"
    build_pdf(briefing, pdf_path, assets_dir=tmp_path / "assets")
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000

    # Ensure briefing serializes cleanly
    assert "generated_at" in json.loads(json.dumps(briefing.to_dict()))
