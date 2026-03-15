"""
ECHO Agents Package
All 21 autonomous agents.
"""
from .ceo import CEOAgent
from .ar import ARAgent
from .production import ProductionAgent
from .distribution import DistributionAgent
from .marketing import MarketingAgent
from .analytics import AnalyticsAgent
from .social import SocialAgent
from .finance import FinanceAgent
from .legal import LegalAgent
from .creative import CreativeAgent
from .sync import SyncAgent
from .artist_dev import ArtistDevAgent
from .pr import PRAgent
from .comms import CommsAgent
from .qc import QCAgent
from .infrastructure import InfrastructureAgent
from .intake import IntakeAgent
from .merch import MerchAgent
from .youtube import YouTubeAgent
from .hub import HubAgent
from .vault import VaultAgent

ALL_AGENTS = [
    CEOAgent,
    ARAgent,
    ProductionAgent,
    DistributionAgent,
    MarketingAgent,
    AnalyticsAgent,
    SocialAgent,
    FinanceAgent,
    LegalAgent,
    CreativeAgent,
    SyncAgent,
    ArtistDevAgent,
    PRAgent,
    CommsAgent,
    QCAgent,
    InfrastructureAgent,
    IntakeAgent,
    MerchAgent,
    YouTubeAgent,
    HubAgent,
    VaultAgent,
]

__all__ = [
    "CEOAgent", "ARAgent", "ProductionAgent", "DistributionAgent",
    "MarketingAgent", "AnalyticsAgent", "SocialAgent", "FinanceAgent",
    "LegalAgent", "CreativeAgent", "SyncAgent", "ArtistDevAgent",
    "PRAgent", "CommsAgent", "QCAgent", "InfrastructureAgent",
    "IntakeAgent", "MerchAgent", "YouTubeAgent", "HubAgent", "VaultAgent",
    "ALL_AGENTS",
]
