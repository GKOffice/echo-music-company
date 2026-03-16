from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, Any
import uuid
import json

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()

VALID_AGENTS = {
    "ceo", "ar", "production", "distribution", "marketing", "social",
    "finance", "legal", "analytics", "creative", "sync", "artist_dev",
    "pr", "comms", "qc", "infrastructure", "intake", "merch",
    "youtube", "hub", "vault",
}


class TaskCreate(BaseModel):
    agent_id: str
    task_type: str
    payload: dict = {}
    priority: str = "normal"
    release_id: Optional[str] = None
    artist_id: Optional[str] = None


class MessagePublish(BaseModel):
    from_agent: str
    to_agent: Optional[str] = None
    topic: str
    payload: dict = {}
    priority: str = "normal"


class CEODecision(BaseModel):
    approval_index: int
    approved: bool
    reason: str = ""
    deal_type: Optional[str] = None


# ----------------------------------------------------------------
# Tasks
# ----------------------------------------------------------------

@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if task_in.agent_id not in VALID_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown agent: {task_in.agent_id}",
        )

    task_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO agent_tasks (id, agent_id, task_type, priority, payload_json,
              release_id, artist_id)
            VALUES (:id, :agent_id, :task_type, :priority, :payload_json,
              :release_id, :artist_id)
            """
        ),
        {
            "id": task_id,
            "agent_id": task_in.agent_id,
            "task_type": task_in.task_type,
            "priority": task_in.priority,
            "payload_json": json.dumps(task_in.payload),
            "release_id": task_in.release_id,
            "artist_id": task_in.artist_id,
        },
    )
    await db.commit()

    # Enqueue to agent's Redis Stream (matches bus.enqueue_task key format)
    try:
        stream_data = {
            "task_id": task_id,
            "task_type": task_in.task_type,
            "priority": task_in.priority,
            "payload": json.dumps(task_in.payload),
        }
        if task_in.release_id:
            stream_data["release_id"] = task_in.release_id
        if task_in.artist_id:
            stream_data["artist_id"] = task_in.artist_id

        await request.app.state.redis.xadd(
            f"agent:tasks:{task_in.agent_id}",
            stream_data,
            maxlen=10000,
        )
    except Exception:
        pass  # DB record committed; stream delivery best-effort

    return {"id": task_id, "message": "Task created"}


@router.get("/tasks")
async def list_tasks(
    agent_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    conditions = ["1=1"]
    params: dict = {"limit": limit}

    if agent_id:
        conditions.append("agent_id = :agent_id")
        params["agent_id"] = agent_id
    if status:
        conditions.append("status = :status")
        params["status"] = status

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"SELECT * FROM agent_tasks WHERE {where} ORDER BY assigned_at DESC LIMIT :limit"),
        params,
    )
    tasks = result.mappings().all()
    return {"tasks": [dict(t) for t in tasks]}


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM agent_tasks WHERE id = :id"),
        {"id": task_id},
    )
    task = result.mappings().fetchone()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return dict(task)


@router.patch("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    new_status: str,
    result_data: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    valid_statuses = {"pending", "running", "completed", "failed", "cancelled"}
    if new_status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    timestamp_field = ""
    if new_status == "running":
        timestamp_field = ", started_at = NOW()"
    elif new_status in {"completed", "failed"}:
        timestamp_field = ", completed_at = NOW()"

    await db.execute(
        text(
            f"""
            UPDATE agent_tasks
            SET status = :status, result_json = :result_json {timestamp_field}
            WHERE id = :id
            """
        ),
        {
            "id": task_id,
            "status": new_status,
            "result_json": json.dumps(result_data) if result_data else None,
        },
    )
    await db.commit()
    return {"message": "Task status updated"}


# ----------------------------------------------------------------
# Messages
# ----------------------------------------------------------------

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def publish_message(
    msg: MessagePublish,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    message_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO agent_messages (id, from_agent, to_agent, topic, priority, payload_json)
            VALUES (:id, :from_agent, :to_agent, :topic, :priority, :payload_json)
            """
        ),
        {
            "id": message_id,
            "from_agent": msg.from_agent,
            "to_agent": msg.to_agent,
            "topic": msg.topic,
            "priority": msg.priority,
            "payload_json": json.dumps(msg.payload),
        },
    )
    await db.commit()

    try:
        await request.app.state.redis.publish(
            f"echo:{msg.topic}",
            json.dumps({
                "topic": msg.topic,
                "payload": {
                    "id": message_id,
                    "from_agent": msg.from_agent,
                    "to_agent": msg.to_agent,
                    **msg.payload,
                },
            }),
        )
    except Exception:
        pass

    return {"id": message_id, "message": "Message published"}


# ----------------------------------------------------------------
# Agent registry & status
# ----------------------------------------------------------------

@router.get("/agents")
async def list_agents(current_user: TokenData = Depends(get_current_user)):
    return {"agents": sorted(list(VALID_AGENTS))}


@router.get("/agents/status")
async def get_all_agent_statuses(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
):
    """Return live status for all agents from Redis."""
    statuses = {}
    for agent_id in VALID_AGENTS:
        try:
            raw = await request.app.state.redis.hgetall(f"agent:state:{agent_id}")
            if raw:
                statuses[agent_id] = {k: _try_parse(v) for k, v in raw.items()}
            else:
                statuses[agent_id] = {"status": "unknown"}
        except Exception:
            statuses[agent_id] = {"status": "unreachable"}
    return {"statuses": statuses}


@router.get("/agents/{agent_id}/status")
async def get_agent_status(
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if agent_id not in VALID_AGENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown agent")

    # Live state from Redis
    redis_state: dict[str, Any] = {}
    try:
        raw = await request.app.state.redis.hgetall(f"agent:state:{agent_id}")
        redis_state = {k: _try_parse(v) for k, v in raw.items()}
    except Exception:
        pass

    # Recent task stats from DB
    result = await db.execute(
        text(
            """
            SELECT status, COUNT(*) AS count
            FROM agent_tasks
            WHERE agent_id = :agent_id
            GROUP BY status
            """
        ),
        {"agent_id": agent_id},
    )
    task_stats = {row["status"]: row["count"] for row in result.mappings().all()}

    return {
        "agent_id": agent_id,
        "live": redis_state,
        "task_stats": task_stats,
    }


# ----------------------------------------------------------------
# CEO approvals
# ----------------------------------------------------------------

@router.get("/ceo/approvals")
async def get_ceo_approvals(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Return the CEO's pending approval queue from Redis.
    The CEO agent stores this under agent:state:ceo as 'pending_approvals'.
    """
    try:
        raw = await request.app.state.redis.hget("agent:state:ceo", "pending_approvals")
        approvals = json.loads(raw) if raw else []
    except Exception:
        approvals = []
    return {"pending_approvals": approvals, "count": len(approvals)}


@router.post("/ceo/decide", status_code=status.HTTP_200_OK)
async def ceo_decide(
    decision: CEODecision,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Submit a manual CEO decision for a pending approval.
    Publishes the decision onto the CEO agent's task stream.
    """
    task_id = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "approval_index": decision.approval_index,
        "approved": decision.approved,
        "reason": decision.reason,
    }
    if decision.deal_type:
        payload["deal_type"] = decision.deal_type

    await db.execute(
        text(
            """
            INSERT INTO agent_tasks (id, agent_id, task_type, priority, payload_json)
            VALUES (:id, 'ceo', 'process_approval', 'high', :payload_json)
            """
        ),
        {"id": task_id, "payload_json": json.dumps(payload)},
    )
    await db.commit()

    try:
        await request.app.state.redis.xadd(
            "agent:tasks:ceo",
            {
                "task_id": task_id,
                "task_type": "process_approval",
                "priority": "high",
                "payload": json.dumps(payload),
            },
            maxlen=10000,
        )
    except Exception:
        pass

    return {"task_id": task_id, "message": "Decision submitted to CEO agent"}


# ----------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------

def _try_parse(value: str) -> Any:
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value
