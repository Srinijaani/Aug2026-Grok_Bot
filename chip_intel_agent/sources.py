"""Curated authentic sources for chip design and manufacturing intelligence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WebSource:
    name: str
    url: str
    kind: str  # rss | page
    topics: tuple[str, ...] = ()
    authentic: bool = True


@dataclass(frozen=True)
class YouTubeChannel:
    name: str
    channel_id: str
    handle: str
    focus: str
    authentic: bool = True

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/{self.handle}"

    @property
    def rss_url(self) -> str:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"


# Content source: exclusively Anastasi In Tech (per product requirement).
WEB_SOURCES: list[WebSource] = []


# Sole YouTube source for chip design & manufacturing briefings.
YOUTUBE_CHANNELS: list[YouTubeChannel] = [
    YouTubeChannel(
        name="Anastasi In Tech",
        channel_id="UCORX3Cl7ByidjEgzSCgv9Yw",
        handle="@AnastasiInTech",
        focus="Chip design, semiconductor manufacturing, AI hardware, and industry explainers",
    ),
]


COMPANIES = [
    {"name": "TSMC", "domain": "tsmc.com", "role": "Leading foundry (advanced nodes)", "color": "#1A3C6E"},
    {"name": "Intel", "domain": "intel.com", "role": "IDM + foundry services", "color": "#0071C5"},
    {"name": "Samsung", "domain": "samsung.com", "role": "Memory + foundry", "color": "#1428A0"},
    {"name": "ASML", "domain": "asml.com", "role": "EUV lithography monopoly", "color": "#0B5CAB"},
    {"name": "NVIDIA", "domain": "nvidia.com", "role": "AI accelerators / fabless", "color": "#76B900"},
    {"name": "AMD", "domain": "amd.com", "role": "CPU/GPU / fabless", "color": "#ED1C24"},
    {"name": "Broadcom", "domain": "broadcom.com", "role": "Networking / custom ASICs", "color": "#E31837"},
    {"name": "Qualcomm", "domain": "qualcomm.com", "role": "Mobile SoCs / modem IP", "color": "#3253DC"},
    {"name": "Arm", "domain": "arm.com", "role": "CPU ISA / IP licensing", "color": "#0091BD"},
    {"name": "GlobalFoundries", "domain": "globalfoundries.com", "role": "Specialty / mature nodes", "color": "#E35205"},
    {"name": "Applied Materials", "domain": "appliedmaterials.com", "role": "Process equipment", "color": "#1B4F72"},
    {"name": "Lam Research", "domain": "lamresearch.com", "role": "Etch / deposition tools", "color": "#003366"},
]


# Keywords used to classify scraped items into the three briefing themes.
TREND_KEYWORDS = (
    "euv", "high-na", "angstrom", "2nm", "3nm", "gate-all-around", "gaa", "nanosheet",
    "chiplet", "hbm", "advanced packaging", "cowoS", "hybrid bonding", "backside power",
    "ai chip", "gpu", "foundry", "yield", "process node", "finfet", "photonics",
    "silicon carbide", "sic", "gan", "eda", "design automation", "lithography",
)

GEO_KEYWORDS = (
    "chips act", "export control", "export controls", "sanction", "tariff", "geopolit",
    "taiwan", "china", "netherlands", "japan", "korea", "supply chain", "reshoring",
    "friendshoring", "national security", "entity list", "subsidy", "subsidies",
    "fab construction", "arizona", "dresden", "kumamoto", "national champion",
)

COMPANY_KEYWORDS = tuple(c["name"].lower() for c in COMPANIES) + (
    "sk hynix", "micron", "smic", "cxmt", "umc", "infineon", "nxp", "stmicro",
    "texas instruments", "synopsys", "cadence", "siemens eda", "kla", "tokyo electron",
)
