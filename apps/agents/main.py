"""
ECHO Agent Orchestration Entry Point
Starts all 21 agents and the message bus.
"""

import asyncio
import logging
import os
import signal
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from bus import bus
from agents.ceo import CEOAgent
from agents.ar import ARAgent
from agents.production import ProductionAgent
from agents.distribution import DistributionAgent
from agents.marketing import MarketingAgent
from agents.social import SocialAgent
from agents.finance import FinanceAgent
from agents.legal import LegalAgent
from agents.analytics import AnalyticsAgent
from agents.creative import CreativeAgent
from agents.sync import SyncAgent
from agents.artist_dev import ArtistDevAgent
from agents.pr import PRAgent
from agents.comms import CommsAgent
from agents.qc import QCAgent
from agents.infrastructure import InfrastructureAgent
from agents.intake import IntakeAgent
from agents.merch import MerchAgent
from agents.youtube import YouTubeAgent
from agents.hub import HubAgent
from agents.vault import VaultAgent

ALL_AGENTS = [
    CEOAgent,
    ARAgent,
    ProductionAgent,
    DistributionAgent,
    MarketingAgent,
    SocialAgent,
    FinanceAgent,
    LegalAgent,
    AnalyticsAgent,
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


async def main():
    logger.info("ECHO Agent Network starting...")
    logger.info(f"Loading {len(ALL_AGENTS)} agents")

    await bus.connect()

    agent_instances = [AgentClass() for AgentClass in ALL_AGENTS]

    tasks = [asyncio.create_task(agent.start()) for agent in agent_instances]

    loop = asyncio.get_event_loop()

    def shutdown_handler():
        logger.info("Shutdown signal received")
        for task in tasks:
            task.cancel()

    loop.add_signal_handler(signal.SIGINT, shutdown_handler)
    loop.add_signal_handler(signal.SIGTERM, shutdown_handler)

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        for agent in agent_instances:
            await agent.stop()
        await bus.disconnect()
        logger.info("ECHO Agent Network stopped")


if __name__ == "__main__":
    asyncio.run(main())
