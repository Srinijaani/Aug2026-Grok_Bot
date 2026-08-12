"""Build a 3-slide landscape PDF briefing: Trends, Company logos, Geopolitics."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from .summarizer import Briefing, Bullet

logger = logging.getLogger(__name__)

PAGE = landscape(letter)  # 792 x 612
WIDTH, HEIGHT = PAGE

NAVY = HexColor("#0B1F33")
TEAL = HexColor("#1F6F8B")
SLATE = HexColor("#243B53")
MUTED = HexColor("#486581")
LIGHT = HexColor("#F0F4F8")
ACCENT = HexColor("#D97706")
LINE = HexColor("#D9E2EC")


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _fetch_icon(domain: str, size: int = 128) -> Image.Image | None:
    urls = [
        f"https://www.google.com/s2/favicons?sz={size}&domain_url=https://{domain}",
        f"https://www.google.com/s2/favicons?domain={domain}&sz={size}",
        f"https://icons.duckduckgo.com/ip3/{domain}.ico",
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=12, headers={"User-Agent": "ChipIntelAgent/1.0"})
            if response.status_code != 200 or len(response.content) < 200:
                continue
            image = Image.open(BytesIO(response.content)).convert("RGBA")
            if image.width < 16 or image.height < 16:
                continue
            return image
        except Exception as exc:  # noqa: BLE001
            logger.debug("Icon fetch failed for %s via %s: %s", domain, url, exc)
    return None


def _make_logo_tile(name: str, domain: str, color: str, out_path: Path, size: int = 220) -> Path:
    """Create a branded logo tile PNG (icon + name)."""
    bg = _rgb(color)
    # Slightly lighten for readability.
    canvas_img = Image.new("RGBA", (size, size), (*bg, 255))
    draw = ImageDraw.Draw(canvas_img)

    # Soft inner panel
    margin = 14
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=22,
        fill=(255, 255, 255, 235),
    )

    icon = _fetch_icon(domain, size=128)
    if icon is not None:
        icon = icon.resize((72, 72), Image.Resampling.LANCZOS)
        canvas_img.paste(icon, ((size - 72) // 2, 42), icon)
        text_y = 130
    else:
        # Monogram fallback
        monogram = "".join(part[0] for part in name.split()[:2]).upper()
        try:
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        except OSError:
            font_big = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), monogram, font=font_big)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size - tw) / 2, 55), monogram, fill=bg + (255,), font=font_big)
        text_y = 130

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except OSError:
        font = ImageFont.load_default()

    display = {
        "Applied Materials": "Applied Mat.",
        "GlobalFoundries": "GlobalFoundries",
        "Lam Research": "Lam Research",
    }.get(name, name)
    bbox = draw.textbbox((0, 0), display, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((size - tw) / 2, text_y), display, fill=(20, 40, 60, 255), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas_img.convert("RGB").save(out_path, format="PNG")
    return out_path


def _draw_background(c: canvas.Canvas) -> None:
    c.setFillColor(LIGHT)
    c.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    # Atmospheric top band
    c.setFillColor(NAVY)
    c.rect(0, HEIGHT - 78, WIDTH, 78, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, HEIGHT - 82, WIDTH, 4, fill=1, stroke=0)


def _draw_footer(c: canvas.Canvas, page_no: int, generated_at: str) -> None:
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(0.55 * inch, 0.35 * inch, f"Chip Design & Manufacturing Briefing  ·  {generated_at}")
    c.drawRightString(WIDTH - 0.55 * inch, 0.35 * inch, f"{page_no} / 3")


def _header(c: canvas.Canvas, title: str, subtitle: str) -> None:
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(0.6 * inch, HEIGHT - 42, title)
    c.setFont("Helvetica", 10)
    c.drawString(0.6 * inch, HEIGHT - 60, subtitle)


def _wrap(c: canvas.Canvas, text: str, font: str, size: int, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if c.stringWidth(trial, font, size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def _draw_bullets(c: canvas.Canvas, bullets: list[Bullet], y_start: float, max_width: float) -> None:
    y = y_start
    for bullet in bullets:
        c.setFillColor(ACCENT)
        c.circle(0.75 * inch, y + 4, 3.2, fill=1, stroke=0)
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 11)
        lines = _wrap(c, bullet.text, "Helvetica", 11, max_width)
        for i, line in enumerate(lines[:3]):
            c.drawString(0.95 * inch, y - (i * 14), line)
        used = min(len(lines), 3)
        if bullet.source:
            c.setFillColor(MUTED)
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(0.95 * inch, y - used * 14 - 2, bullet.source)
            y -= used * 14 + 22
        else:
            y -= used * 14 + 16
        if y < 0.7 * inch:
            break


def _slide_trends(c: canvas.Canvas, briefing: Briefing) -> None:
    _draw_background(c)
    _header(
        c,
        "1. Trends",
        "Latest signals in chip design, process technology, and manufacturing",
    )
    # Left accent panel with stats
    c.setFillColor(HexColor("#E6F0F5"))
    c.roundRect(0.55 * inch, 0.7 * inch, 2.1 * inch, 4.35 * inch, 12, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.75 * inch, 4.7 * inch, "THIS BRIEFING")
    stats = [
        (str(briefing.stats.get("articles", 0)), "Articles"),
        (str(briefing.stats.get("videos", 0)), "YouTube videos"),
        (str(briefing.stats.get("sources", 0)), "Sources"),
    ]
    y = 4.2 * inch
    for value, label in stats:
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(0.75 * inch, y, value)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(0.75 * inch, y - 14, label)
        y -= 0.7 * inch

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    note = "Sourced exclusively from YouTube: Anastasi In Tech (@AnastasiInTech)."
    for i, line in enumerate(_wrap(c, note, "Helvetica", 8, 1.8 * inch)):
        c.drawString(0.75 * inch, 1.15 * inch - i * 11, line)

    _draw_bullets(c, briefing.trends[:6], y_start=4.85 * inch, max_width=5.9 * inch)
    _draw_footer(c, 1, briefing.generated_at)


def _slide_logos(c: canvas.Canvas, briefing: Briefing, logo_dir: Path) -> None:
    _draw_background(c)
    _header(
        c,
        "2. Company Logos",
        "Key design, foundry, equipment, and IP leaders shaping the ecosystem",
    )

    companies = briefing.companies[:12]
    cols, rows = 6, 2
    tile = 1.05 * inch
    gap_x = 0.22 * inch
    gap_y = 0.55 * inch
    grid_width = cols * tile + (cols - 1) * gap_x
    start_x = (WIDTH - grid_width) / 2
    start_y = HEIGHT - 2.05 * inch

    for idx, company in enumerate(companies):
        row, col = divmod(idx, cols)
        if row >= rows:
            break
        x = start_x + col * (tile + gap_x)
        y = start_y - row * (tile + gap_y)
        logo_path = logo_dir / f"{company['domain'].replace('.', '_')}.png"
        if not logo_path.exists():
            _make_logo_tile(company["name"], company["domain"], company["color"], logo_path)
        try:
            c.drawImage(
                str(logo_path),
                x,
                y - tile,
                width=tile,
                height=tile,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:  # noqa: BLE001
            c.setFillColor(HexColor(company["color"]))
            c.roundRect(x, y - tile, tile, tile, 10, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(x + tile / 2, y - tile / 2, company["name"][:12])

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7)
        role = company.get("role", "")
        for i, line in enumerate(_wrap(c, role, "Helvetica", 7, tile + 0.05 * inch)[:2]):
            c.drawCentredString(x + tile / 2, y - tile - 12 - i * 9, line)

    # Highlight strip
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(0.6 * inch, 1.55 * inch, WIDTH - 0.6 * inch, 1.55 * inch)
    c.setFillColor(SLATE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(0.6 * inch, 1.3 * inch, "Recent coverage highlights")
    c.setFont("Helvetica", 8)
    c.setFillColor(MUTED)
    highlights = briefing.company_highlights[:2]
    y = 1.1 * inch
    for bullet in highlights:
        for line in _wrap(c, f"• {bullet.text}", "Helvetica", 8, WIDTH - 1.3 * inch)[:2]:
            c.drawString(0.6 * inch, y, line)
            y -= 11

    _draw_footer(c, 2, briefing.generated_at)


def _slide_geopolitics(c: canvas.Canvas, briefing: Briefing) -> None:
    _draw_background(c)
    _header(
        c,
        "3. Geopolitical Impact",
        "Policy, export controls, and supply-chain geography shaping semiconductor capability",
    )

    # Map-ish region chips
    regions = [
        ("United States", "CHIPS Act fabs & AI export rules"),
        ("Taiwan", "Advanced foundry concentration"),
        ("Netherlands / Japan", "Lithography & tool controls"),
        ("South Korea", "Memory & foundry capacity"),
        ("China", "Domestic node catch-up pressure"),
        ("EU / India", "Incentive-led diversification"),
    ]
    chip_w, chip_h = 2.25 * inch, 0.55 * inch
    start_x = 0.6 * inch
    y = 4.85 * inch
    for i, (region, blurb) in enumerate(regions):
        col = i % 3
        row = i // 3
        x = start_x + col * (chip_w + 0.25 * inch)
        yy = y - row * (chip_h + 0.18 * inch)
        c.setFillColor(HexColor("#E6F0F5") if row == 0 else HexColor("#EDF2F7"))
        c.roundRect(x, yy - chip_h, chip_w, chip_h, 8, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 10, yy - 18, region)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(x + 10, yy - 34, blurb)

    _draw_bullets(c, briefing.geopolitics[:5], y_start=3.35 * inch, max_width=6.8 * inch)

    # Trusted channels footnote
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 7.5)
    channel = briefing.youtube_channels[0] if briefing.youtube_channels else {"name": "Anastasi In Tech", "url": "https://www.youtube.com/@AnastasiInTech"}
    c.drawString(
        0.6 * inch,
        0.55 * inch,
        f"Sole source: {channel.get('name', 'Anastasi In Tech')} — {channel.get('url', 'https://www.youtube.com/@AnastasiInTech')}",
    )
    _draw_footer(c, 3, briefing.generated_at)


def build_pdf(briefing: Briefing, output_path: Path, assets_dir: Path | None = None) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = Path(assets_dir or output_path.parent / "assets")
    logo_dir = assets_dir / "logos"
    logo_dir.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=PAGE)
    _slide_trends(c, briefing)
    c.showPage()
    _slide_logos(c, briefing, logo_dir)
    c.showPage()
    _slide_geopolitics(c, briefing)
    c.save()
    logger.info("Wrote PDF to %s", output_path)
    return output_path
