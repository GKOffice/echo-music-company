"""
ECHO Agent Orchestrator
Boots all 23 agents and manages the full autonomous operation.
"""

import asyncio
import logging
import signal
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

from bus import bus

# Import all 21 agents
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
from agents.deal_room import DealRoomAgent
from agents.fan_intelligence import FanIntelligenceAgent

ALL_AGENTS = [
    CEOAgent, ARAgent, ProductionAgent, DistributionAgent, MarketingAgent,
    SocialAgent, FinanceAgent, LegalAgent, AnalyticsAgent, CreativeAgent,
    SyncAgent, ArtistDevAgent, PRAgent, CommsAgent, QCAgent,
    InfrastructureAgent, IntakeAgent, MerchAgent, YouTubeAgent, HubAgent,
    VaultAgent, DealRoomAgent, FanIntelligenceAgent,
]


async def main():
    logger.info("=" * 60)
    logger.info("  Melodio — AI Music Company")
    logger.info("  Booting all 23 agents...")
    logger.info("=" * 60)

    await bus.connect()
    logger.info("Message bus connected")

    agents = []
    tasks = []

    for AgentClass in ALL_AGENTS:
        agent = AgentClass()
        agents.append(agent)

    # Start all agents
    for agent in agents:
        task = asyncio.create_task(agent.start(), name=agent.agent_id)
        tasks.append(task)
        logger.info(f"  {agent.agent_name} starting...")

    logger.info(f"\nAll {len(agents)} agents booted. Melodio is operational.\n")

    # Handle graceful shutdown via event
    shutdown_event = asyncio.Event()

    def handle_shutdown():
        logger.info("\nShutdown signal received...")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_shutdown)

    await shutdown_event.wait()

    # Graceful shutdown — stop agents, then cancel tasks
    logger.info("Stopping all agents...")
    for agent in agents:
        await agent.stop()

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    await bus.disconnect()
    logger.info("ECHO shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
