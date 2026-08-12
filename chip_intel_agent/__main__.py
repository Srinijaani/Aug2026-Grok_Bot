#!/usr/bin/env python3
"""CLI entrypoint for the Chip Intel briefing agent."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs):  # type: ignore[misc]
        return False

from chip_intel_agent.emailer import send_pdf
from chip_intel_agent.pdf_builder import build_pdf
from chip_intel_agent.scraper import scrape_all
from chip_intel_agent.summarizer import summarize

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "output" / "chip_briefing.pdf"


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scrape authentic chip design/manufacturing sources and YouTube channels, "
            "summarize into a 3-slide PDF (Trends, Company Logos, Geopolitical Impact), "
            "and optionally email it."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"PDF output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=ROOT / "output",
        help="Directory for intermediate JSON artifacts",
    )
    parser.add_argument(
        "--skip-email",
        action="store_true",
        help="Generate the PDF only; do not send email",
    )
    parser.add_argument(
        "--email-only",
        action="store_true",
        help="Email an existing PDF from --output without re-scraping",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    configure_logging(args.verbose)
    log = logging.getLogger("chip_intel")

    args.data_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.email_only:
        if not args.output.exists():
            log.error("PDF not found at %s", args.output)
            return 1
        briefing_meta = {}
        meta_path = args.data_dir / "briefing.json"
        if meta_path.exists():
            briefing_meta = json.loads(meta_path.read_text())
        recipient = send_pdf(
            args.output,
            generated_at=briefing_meta.get("generated_at", "latest"),
            stats=briefing_meta.get("stats"),
        )
        log.info("Emailed existing PDF to %s", recipient)
        return 0

    log.info("Scraping authentic web and YouTube sources…")
    scrape_payload = scrape_all()
    scrape_path = args.data_dir / "scrape.json"
    scrape_path.write_text(json.dumps(scrape_payload, indent=2))
    log.info(
        "Scraped %s articles and %s videos → %s",
        scrape_payload["article_count"],
        scrape_payload["video_count"],
        scrape_path,
    )

    log.info("Summarizing into Trends / Companies / Geopolitics…")
    briefing = summarize(scrape_payload)
    briefing_path = args.data_dir / "briefing.json"
    briefing_path.write_text(json.dumps(briefing.to_dict(), indent=2))

    log.info("Building 3-slide PDF…")
    pdf_path = build_pdf(briefing, args.output, assets_dir=args.data_dir / "assets")
    log.info("PDF ready: %s", pdf_path)

    if args.skip_email:
        log.info("Skipping email (--skip-email).")
        return 0

    try:
        recipient = send_pdf(pdf_path, generated_at=briefing.generated_at, stats=briefing.stats)
    except RuntimeError as exc:
        log.error("%s", exc)
        log.error("PDF was still written to %s", pdf_path)
        return 2
    except Exception as exc:  # noqa: BLE001
        log.exception("Failed to send email: %s", exc)
        log.error("PDF was still written to %s", pdf_path)
        return 3

    log.info("Briefing emailed to %s", recipient)
    return 0


if __name__ == "__main__":
    sys.exit(run())
