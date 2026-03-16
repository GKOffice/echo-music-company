"""
Infrastructure Agent
Keeps the lights on — monitors all services, tracks agent heartbeats,
manages API keys, costs, and detects anomalies across the platform.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone

from base_agent import BaseAgent, AgentTask, AgentResult
from bus import bus

logger = logging.getLogger(__name__)

# Heartbeat thresholds
HEARTBEAT_WARNING_SECS = 15 * 60   # 15 min silent → WARNING
HEARTBEAT_CRITICAL_SECS = 30 * 60  # 30 min silent → CRITICAL

# All 21 agent IDs
ALL_AGENT_IDS = [
    "ceo", "ar", "production", "distribution", "marketing", "social",
    "finance", "legal", "analytics", "creative", "sync", "artist_dev",
    "pr", "comms", "qc", "infrastructure", "intake", "merch",
    "youtube", "hub", "vault",
]

# Per-service rate limit info (requests remaining / limit)
RATE_LIMIT_SERVICES = ["spotify", "apple_music", "youtube", "tiktok", "instagram", "anthropic"]


class InfrastructureAgent(BaseAgent):
    agent_id = "infrastructure"
    agent_name = "Infrastructure Agent"
    subscriptions = ["alert.critical", "system.health_check", "agent.status"]

    def __init__(self):
        super().__init__()
        # agent_id → {"last_seen": float (unix ts), "status": str}
        self._heartbeats: dict[str, dict] = {}
        self._rate_limits: dict[str, dict] = {}
        self._cost_log: list[dict] = []

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        # Start background heartbeat monitor
        asyncio.create_task(self._heartbeat_monitor_loop())
        logger.info("[Infrastructure] Online — monitoring all systems")

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        payload = message.get("payload", {})

        if topic == "agent.status":
            agent_id = payload.get("agent") or payload.get("agent_id")
            if agent_id:
                self._heartbeats[agent_id] = {
                    "last_seen": time.time(),
                    "status": payload.get("status", "online"),
                }

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "health_check": self._health_check,
            "rotate_api_key": self._rotate_api_key,
            "check_rate_limits": self._check_rate_limits,
            "backup_status": self._backup_status,
            "agent_heartbeat": self._agent_heartbeat,
            "cost_report": self._cost_report,
            "detect_anomaly": self._detect_anomaly,
            # Legacy
            "backup_db": self._backup_status,
            "cleanup_storage": self._cleanup_storage,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    # ----------------------------------------------------------------
    # health_check
    # ----------------------------------------------------------------

    async def _health_check(self, task: AgentTask) -> dict:
        services = {}
        response_times = {}
        issues = []

        # PostgreSQL
        t0 = time.time()
        if self._db_pool:
            try:
                await self._db_pool.fetchval("SELECT 1")
                services["postgres"] = "healthy"
                response_times["postgres_ms"] = int((time.time() - t0) * 1000)
            except Exception as e:
                services["postgres"] = "error"
                issues.append(f"PostgreSQL: {e}")
        else:
            services["postgres"] = "no_pool"
            issues.append("PostgreSQL pool not initialized")

        # Redis
        t0 = time.time()
        try:
            if bus._redis:
                await bus._redis.ping()
                services["redis"] = "healthy"
                response_times["redis_ms"] = int((time.time() - t0) * 1000)
            else:
                services["redis"] = "not_connected"
                issues.append("Redis not connected")
        except Exception as e:
            services["redis"] = "error"
            issues.append(f"Redis: {e}")

        # API self-check
        services["agents_running"] = len(self._heartbeats)

        healthy = len(issues) == 0
        return {
            "healthy": healthy,
            "services": services,
            "response_times": response_times,
            "issues": issues,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # rotate_api_key
    # ----------------------------------------------------------------

    async def _rotate_api_key(self, task: AgentTask) -> dict:
        service = task.payload.get("service", "unknown")
        reason = task.payload.get("reason", "scheduled rotation")

        logger.warning(f"[Infrastructure] API key rotation required for {service}: {reason}")
        await self.log_audit("api_key_rotation_reminder", "infrastructure", None, {
            "service": service,
            "reason": reason,
            "action_required": "manual key rotation in environment config",
        })

        # Alert CEO for immediate action
        await self.send_message("ceo", "infrastructure_alert", {
            "type": "api_key_rotation",
            "service": service,
            "reason": reason,
            "priority": "high",
        })

        return {
            "service": service,
            "rotation_logged": True,
            "action_required": "Update API key in environment config and redeploy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # check_rate_limits
    # ----------------------------------------------------------------

    async def _check_rate_limits(self, task: AgentTask) -> dict:
        service = task.payload.get("service")
        services_to_check = [service] if service else RATE_LIMIT_SERVICES

        report = {}
        warnings = []

        for svc in services_to_check:
            # Pull from stored rate limit data (populated by each service client)
            info = self._rate_limits.get(svc, {
                "requests_remaining": None,
                "requests_limit": None,
                "reset_at": None,
                "usage_pct": None,
            })
            report[svc] = info

            usage_pct = info.get("usage_pct")
            if usage_pct and usage_pct >= 90:
                warnings.append(f"{svc} rate limit at {usage_pct:.0f}% — throttling imminent")
            elif usage_pct and usage_pct >= 75:
                warnings.append(f"{svc} rate limit at {usage_pct:.0f}% — monitor closely")

        if warnings:
            await self.send_message("ceo", "infrastructure_alert", {
                "type": "rate_limit_warning",
                "warnings": warnings,
            })

        return {
            "services": report,
            "warnings": warnings,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # backup_status
    # ----------------------------------------------------------------

    async def _backup_status(self, task: AgentTask) -> dict:
        # Check last backup from audit log
        last_backup = await self.db_fetchrow(
            "SELECT created_at, details FROM audit_log WHERE action = 'db_backup' ORDER BY created_at DESC LIMIT 1"
        )

        if last_backup:
            last_at = last_backup.get("created_at")
            age_hours = (datetime.now(timezone.utc) - last_at).total_seconds() / 3600 if last_at else None
            status = "ok" if (age_hours and age_hours < 25) else "overdue"
            if status == "overdue":
                await self.send_message("ceo", "infrastructure_alert", {
                    "type": "backup_overdue",
                    "last_backup_hours_ago": age_hours,
                })
        else:
            status = "no_record"
            age_hours = None

        await self.log_audit("backup_status_check", "infrastructure", None, {"status": status})

        return {
            "status": status,
            "last_backup_at": last_backup.get("created_at").isoformat() if last_backup and last_backup.get("created_at") else None,
            "age_hours": round(age_hours, 1) if age_hours else None,
            "destination": "s3://echo-backups/postgres/",
        }

    # ----------------------------------------------------------------
    # agent_heartbeat
    # ----------------------------------------------------------------

    async def _agent_heartbeat(self, task: AgentTask) -> dict:
        agent_id = task.payload.get("agent_id") or task.payload.get("agent")
        if not agent_id:
            return {"error": "agent_id required"}

        self._heartbeats[agent_id] = {
            "last_seen": time.time(),
            "status": task.payload.get("status", "online"),
            "task_count": task.payload.get("task_count", 0),
            "error_count": task.payload.get("error_count", 0),
        }
        return {"agent_id": agent_id, "heartbeat_recorded": True}

    # ----------------------------------------------------------------
    # cost_report
    # ----------------------------------------------------------------

    async def _cost_report(self, task: AgentTask) -> dict:
        period = task.payload.get("period", "monthly")

        # Pull AI usage from audit log / tasks
        ai_tasks = await self.db_fetchrow(
            """
            SELECT
              COUNT(*) as total_tasks,
              COUNT(*) FILTER (WHERE status = 'completed') as completed,
              COUNT(*) FILTER (WHERE status = 'failed') as failed
            FROM agent_tasks
            WHERE created_at > NOW() - INTERVAL '30 days'
            """
        )

        # Estimate costs (Claude Haiku ~$0.25/1M input, $1.25/1M output)
        # Conservative estimate: 500 tokens per task avg
        total_tasks = int(ai_tasks.get("total_tasks") or 0) if ai_tasks else 0
        estimated_ai_cost = round(total_tasks * 0.001, 2)  # $0.001 per task estimate

        report = {
            "period": period,
            "ai_usage": {
                "total_tasks": total_tasks,
                "completed": int(ai_tasks.get("completed") or 0) if ai_tasks else 0,
                "failed": int(ai_tasks.get("failed") or 0) if ai_tasks else 0,
                "estimated_cost_usd": estimated_ai_cost,
            },
            "infrastructure": {
                "postgres": "managed — see cloud provider",
                "redis": "managed — see cloud provider",
                "storage": "see cloud provider",
            },
            "total_estimated_usd": estimated_ai_cost,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if estimated_ai_cost > 100:
            await self.send_message("ceo", "infrastructure_alert", {
                "type": "cost_spike",
                "estimated_ai_cost": estimated_ai_cost,
                "period": period,
            })

        return report

    # ----------------------------------------------------------------
    # detect_anomaly
    # ----------------------------------------------------------------

    async def _detect_anomaly(self, task: AgentTask) -> dict:
        anomalies = []

        # Check error rate
        error_stats = await self.db_fetchrow(
            """
            SELECT
              COUNT(*) FILTER (WHERE status = 'failed') as failed,
              COUNT(*) as total
            FROM agent_tasks
            WHERE created_at > NOW() - INTERVAL '1 hour'
            """
        )
        if error_stats:
            failed = int(error_stats.get("failed") or 0)
            total = int(error_stats.get("total") or 0)
            if total > 0:
                error_rate = failed / total
                if error_rate > 0.3:
                    anomalies.append({
                        "type": "high_error_rate",
                        "severity": "critical",
                        "detail": f"Error rate {error_rate:.0%} in last hour ({failed}/{total} tasks failed)",
                    })
                elif error_rate > 0.1:
                    anomalies.append({
                        "type": "elevated_error_rate",
                        "severity": "warning",
                        "detail": f"Error rate {error_rate:.0%} in last hour",
                    })

        # Check silent agents
        now = time.time()
        silent_agents = []
        for agent_id, hb in self._heartbeats.items():
            silent_secs = now - hb.get("last_seen", now)
            if silent_secs > HEARTBEAT_CRITICAL_SECS:
                silent_agents.append({"agent_id": agent_id, "silent_minutes": int(silent_secs / 60), "severity": "critical"})
            elif silent_secs > HEARTBEAT_WARNING_SECS:
                silent_agents.append({"agent_id": agent_id, "silent_minutes": int(silent_secs / 60), "severity": "warning"})

        if silent_agents:
            anomalies.append({
                "type": "silent_agents",
                "severity": "critical" if any(a["severity"] == "critical" for a in silent_agents) else "warning",
                "detail": f"{len(silent_agents)} agents not responding",
                "agents": silent_agents,
            })

        critical_anomalies = [a for a in anomalies if a.get("severity") == "critical"]
        if critical_anomalies:
            await self.send_message("ceo", "infrastructure_alert", {
                "type": "anomaly_detected",
                "anomalies": critical_anomalies,
            })

        return {
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "critical_count": len(critical_anomalies),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    async def _heartbeat_monitor_loop(self):
        """Check agent heartbeats every 10 minutes."""
        while self._running:
            try:
                await asyncio.sleep(600)  # 10 min
                if not self._running:
                    break

                now = time.time()
                for agent_id in ALL_AGENT_IDS:
                    hb = self._heartbeats.get(agent_id)
                    if not hb:
                        continue  # Never seen — may not have started yet

                    silent_secs = now - hb.get("last_seen", now)

                    if silent_secs > HEARTBEAT_CRITICAL_SECS:
                        logger.critical(f"[Infrastructure] Agent {agent_id} silent for {silent_secs/60:.0f} min — CRITICAL")
                        await self.send_message("ceo", "agent_down_alert", {
                            "agent_id": agent_id,
                            "silent_minutes": int(silent_secs / 60),
                            "severity": "critical",
                        })
                    elif silent_secs > HEARTBEAT_WARNING_SECS:
                        logger.warning(f"[Infrastructure] Agent {agent_id} silent for {silent_secs/60:.0f} min — WARNING")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Infrastructure] Heartbeat monitor error: {e}")

    async def _cleanup_storage(self, task: AgentTask) -> dict:
        dry_run = task.payload.get("dry_run", True)
        logger.info(f"[Infrastructure] Storage cleanup (dry_run={dry_run})")
        return {"dry_run": dry_run, "files_to_clean": 0, "space_recovered_mb": 0}
