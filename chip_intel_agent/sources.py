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


# Industry / technical news RSS feeds that consistently publish semiconductor coverage.
WEB_SOURCES: list[WebSource] = [
    WebSource(
        name="Semiconductor Engineering",
        url="https://semiengineering.com/feed/",
        kind="rss",
        topics=("process", "design", "manufacturing", "EDA"),
    ),
    WebSource(
        name="Electronics Weekly",
        url="https://www.electronicsweekly.com/feed/",
        kind="rss",
        topics=("semiconductors", "manufacturing"),
    ),
    WebSource(
        name="EE Times",
        url="https://www.eetimes.com/feed/",
        kind="rss",
        topics=("semiconductors", "design", "systems"),
    ),
    WebSource(
        name="IEEE Spectrum",
        url="https://spectrum.ieee.org/feeds/topic/semiconductors.rss",
        kind="rss",
        topics=("research", "devices", "manufacturing"),
    ),
    WebSource(
        name="Google News — Chip Design & Manufacturing",
        url=(
            "https://news.google.com/rss/search?"
            "q=semiconductor+manufacturing+OR+%22chip+design%22+OR+foundry+OR+EUV"
            "&hl=en-US&gl=US&ceid=US:en"
        ),
        kind="rss",
        topics=("latest", "industry"),
    ),
    WebSource(
        name="Google News — Foundry Leaders",
        url=(
            "https://news.google.com/rss/search?"
            "q=TSMC+OR+Intel+OR+Samsung+OR+ASML+OR+GlobalFoundries+foundry"
            "&hl=en-US&gl=US&ceid=US:en"
        ),
        kind="rss",
        topics=("companies", "capacity"),
    ),
    WebSource(
        name="Google News — Geopolitics & Policy",
        url=(
            "https://news.google.com/rss/search?"
            "q=%22CHIPS+Act%22+OR+%22export+controls%22+OR+semiconductor+geopolitics"
            "+OR+%22tech+restrictions%22"
            "&hl=en-US&gl=US&ceid=US:en"
        ),
        kind="rss",
        topics=("geopolitics", "policy", "trade"),
    ),
]


# High-signal YouTube channels covering semiconductor tech with factual depth.
# Channel IDs verified against each channel's canonical / externalId.
YOUTUBE_CHANNELS: list[YouTubeChannel] = [
    YouTubeChannel(
        name="Asianometry",
        channel_id="UC1LpsuAUaKoMzzJSEt5WImw",
        handle="@Asianometry",
        focus="Semiconductor history, manufacturing economics, supply chains",
    ),
    YouTubeChannel(
        name="High Yield",
        channel_id="UCmMwHbw2j8LfvTKVh3O7Vdw",
        handle="@HighYield",
        focus="Process nodes, packaging, yield engineering explainers",
    ),
    YouTubeChannel(
        name="Branch Education",
        channel_id="UCdp4_l1vPmpN-gDbUwhaRUQ",
        handle="@BranchEducation",
        focus="Deep visual explainers of chip fabrication and transistors",
    ),
    YouTubeChannel(
        name="TechTechPotato",
        channel_id="UC1r0DG-KEPyqOeW6o79PByw",
        handle="@TechTechPotato",
        focus="CPU/GPU microarchitecture and process analysis",
    ),
    YouTubeChannel(
        name="ColdFusion",
        channel_id="UC4QZ_LsYcvcq7qOsOhpAX4A",
        handle="@ColdFusion",
        focus="Industry documentaries including semiconductor geopolitics",
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
