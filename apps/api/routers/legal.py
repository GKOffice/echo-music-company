from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
import uuid
import re
import json
from datetime import datetime, timezone

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()

PROHIBITED_POINT_WORDS = [
    r"\binvest\b", r"\binvestment\b", r"\binvestments\b", r"\binvestor\b", r"\binvestors\b",
    r"\bROI\b", r"\breturn on investment\b", r"\breturns\b", r"\bfinancial returns\b",
    r"\bsecurities\b", r"\bsecurity\b", r"\bshares\b", r"\bequity\b", r"\bdividend\b",
]

ALLOWED_ALTERNATIVES = {
    "invest": "buy / purchase / own",
    "investment": "purchase / points",
    "ROI": "royalties earned",
    "returns": "royalties / earnings",
    "securities": "points",
    "equity": "master points",
}


# ----------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------

class ContractCreate(BaseModel):
    artist_id: str
    deal_type: str  # single|ep|album|producer|publishing_admin
    song_title: Optional[str] = None
    advance_amount: float = 0.0
    producer_name: Optional[str] = None
    producer_points: int = 0


class RegistrationCreate(BaseModel):
    track_id: Optional[str] = None
    release_id: Optional[str] = None
    society: str
    status: str = "pending"
    registration_number: Optional[str] = None
    notes: Optional[str] = None


class DMCACreate(BaseModel):
    track_id: Optional[str] = None
    claimant: str
    platform: str
    claim_type: str = "copyright"
    notes: Optional[str] = None


class ComplianceCheckRequest(BaseModel):
    content: str
    context: str = "general"  # general|points|marketing|contract
    source: Optional[str] = None


# ----------------------------------------------------------------
# Contracts
# ----------------------------------------------------------------

@router.get("/contracts")
async def list_contracts(
    artist_id: Optional[str] = Query(None),
    contract_type: Optional[str] = Query(None),
    contract_status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if artist_id:
        conditions.append("c.artist_id = :artist_id")
        params["artist_id"] = artist_id
    if contract_type:
        conditions.append("c.type = :type")
        params["type"] = contract_type
    if contract_status:
        conditions.append("c.status = :status")
        params["status"] = contract_status

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"""
            SELECT c.*, a.name AS artist_name, a.stage_name
            FROM contracts c
            LEFT JOIN artists a ON c.artist_id = a.id
            WHERE {where}
            ORDER BY c.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    rows = [dict(r) for r in result.mappings().all()]

    total_result = await db.execute(
        text(f"SELECT COUNT(*) FROM contracts c WHERE {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    total = total_result.scalar()

    return {"contracts": rows, "total": total, "limit": limit, "offset": offset}


@router.post("/contracts", status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_in: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    # Verify artist exists
    artist_result = await db.execute(
        text("SELECT id, name, stage_name FROM artists WHERE id = :id"),
        {"id": contract_in.artist_id},
    )
    artist = artist_result.mappings().fetchone()
    if not artist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")

    contract_id = str(uuid.uuid4())
    from datetime import date, timedelta
    today = datetime.now(timezone.utc).date()
    reversion_date = date(today.year + 5, today.month, today.day)

    terms = {
        "song_title": contract_in.song_title or "",
        "producer_name": contract_in.producer_name or "",
        "producer_points": contract_in.producer_points,
        "pre_recoup_split": "artist 40% / ECHO 60%",
        "post_recoup_split": "artist 60% / ECHO 40%",
        "reversion_override": "15% perpetual",
        "recoupable_costs": "advance + recording costs only",
    }

    await db.execute(
        text("""
            INSERT INTO contracts (id, artist_id, type, status, terms_json,
                royalty_split_artist, royalty_split_label, advance_amount,
                recoupment_balance, reversion_date, execution_date)
            VALUES (:id, :artist_id, :type, 'draft', :terms,
                40.0, 60.0, :advance, :advance, :reversion, :today)
        """),
        {
            "id": contract_id,
            "artist_id": contract_in.artist_id,
            "type": contract_in.deal_type,
            "terms": json.dumps(terms),
            "advance": contract_in.advance_amount,
            "reversion": reversion_date,
            "today": today,
        },
    )
    await db.commit()

    return {
        "id": contract_id,
        "artist_id": contract_in.artist_id,
        "artist_name": artist["stage_name"] or artist["name"],
        "deal_type": contract_in.deal_type,
        "status": "draft",
        "reversion_date": reversion_date.isoformat(),
        "advance_amount": contract_in.advance_amount,
        "splits": {"pre_recoup": "40/60", "post_recoup": "60/40"},
        "message": "Contract created in draft status",
    }


@router.get("/contracts/{contract_id}")
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text("""
            SELECT c.*, a.name AS artist_name, a.stage_name
            FROM contracts c
            LEFT JOIN artists a ON c.artist_id = a.id
            WHERE c.id = :id
        """),
        {"id": contract_id},
    )
    contract = result.mappings().fetchone()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return dict(contract)


# ----------------------------------------------------------------
# Copyright Registrations
# ----------------------------------------------------------------

@router.get("/registrations")
async def list_registrations(
    track_id: Optional[str] = Query(None),
    release_id: Optional[str] = Query(None),
    reg_status: Optional[str] = Query(None),
    society: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if track_id:
        conditions.append("track_id = :track_id")
        params["track_id"] = track_id
    if release_id:
        conditions.append("release_id = :release_id")
        params["release_id"] = release_id
    if reg_status:
        conditions.append("status = :status")
        params["status"] = reg_status
    if society:
        conditions.append("society = :society")
        params["society"] = society

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"SELECT * FROM copyright_registrations WHERE {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
        params,
    )
    rows = [dict(r) for r in result.mappings().all()]

    # Summary: overdue registrations (>30 days since track released and still pending)
    overdue_result = await db.execute(
        text("""
            SELECT COUNT(*) FROM copyright_registrations cr
            JOIN tracks t ON cr.track_id = t.id
            WHERE cr.status = 'pending'
              AND t.created_at < NOW() - INTERVAL '30 days'
        """)
    )
    overdue_count = overdue_result.scalar() or 0

    return {
        "registrations": rows,
        "total": len(rows),
        "overdue_count": int(overdue_count),
        "limit": limit,
        "offset": offset,
    }


@router.post("/registrations", status_code=status.HTTP_201_CREATED)
async def create_registration(
    reg_in: RegistrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    reg_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO copyright_registrations (id, track_id, release_id, society, status, registration_number, notes)
            VALUES (:id, :track_id, :release_id, :society, :status, :reg_num, :notes)
        """),
        {
            "id": reg_id,
            "track_id": reg_in.track_id,
            "release_id": reg_in.release_id,
            "society": reg_in.society,
            "status": reg_in.status,
            "reg_num": reg_in.registration_number,
            "notes": reg_in.notes,
        },
    )
    await db.commit()
    return {"id": reg_id, "society": reg_in.society, "status": reg_in.status, "message": "Registration record created"}


# ----------------------------------------------------------------
# Compliance Check
# ----------------------------------------------------------------

@router.post("/compliance/check")
async def compliance_check(
    body: ComplianceCheckRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """Scan text for compliance issues — prohibited investment language, missing disclosures."""
    issues = []
    warnings = []

    # Check for prohibited point/investment language
    for pattern in PROHIBITED_POINT_WORDS:
        matches = re.findall(pattern, body.content, re.IGNORECASE)
        for match in matches:
            suggestion = ALLOWED_ALTERNATIVES.get(match.lower(), "Use approved ECHO Points terminology")
            issues.append({
                "type": "prohibited_language",
                "severity": "critical",
                "match": match,
                "suggestion": suggestion,
                "rule": "No investment terminology in ECHO Points context",
            })

    # Context-specific checks
    if body.context in ("points", "marketing"):
        required_disclosures = [
            "past earnings do not guarantee",
            "points are not securities",
        ]
        for phrase in required_disclosures:
            if phrase.lower() not in body.content.lower():
                warnings.append({
                    "type": "missing_disclosure",
                    "severity": "warning",
                    "message": f'Consider adding disclosure: "{phrase}"',
                })

    if body.context == "contract":
        for keyword, msg in [
            ("reversion", "Contract should reference master reversion rights"),
            ("recoup", "Contract should define recoupable costs"),
            ("arbitration", "Contract should specify dispute resolution"),
        ]:
            if keyword not in body.content.lower():
                warnings.append({"type": "missing_clause", "severity": "warning", "message": msg})

    return {
        "compliant": len(issues) == 0,
        "context": body.context,
        "issues": issues,
        "warnings": warnings,
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "policy_summary": "Never use: invest, investment, ROI, returns, securities, equity. Use: buy, purchase, own, earn, points, royalties.",
    }


# ----------------------------------------------------------------
# DMCA
# ----------------------------------------------------------------

@router.post("/dmca", status_code=status.HTTP_201_CREATED)
async def create_dmca(
    dmca_in: DMCACreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    dmca_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO dmca_requests (id, track_id, claimant, platform, claim_type, status, notes)
            VALUES (:id, :track_id, :claimant, :platform, :claim_type, 'received', :notes)
        """),
        {
            "id": dmca_id,
            "track_id": dmca_in.track_id,
            "claimant": dmca_in.claimant,
            "platform": dmca_in.platform,
            "claim_type": dmca_in.claim_type,
            "notes": dmca_in.notes,
        },
    )
    await db.commit()

    return {
        "id": dmca_id,
        "status": "received",
        "claimant": dmca_in.claimant,
        "platform": dmca_in.platform,
        "next_steps": [
            "Verify ECHO's ownership rights for this track",
            "Respond to claimant within 10 business days",
            "If counter-notice warranted, file within 14 days",
        ],
        "message": "DMCA request logged",
    }


@router.get("/dmca")
async def list_dmca(
    track_id: Optional[str] = Query(None),
    dmca_status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if track_id:
        conditions.append("track_id = :track_id")
        params["track_id"] = track_id
    if dmca_status:
        conditions.append("status = :status")
        params["status"] = dmca_status
    if platform:
        conditions.append("platform = :platform")
        params["platform"] = platform

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"SELECT * FROM dmca_requests WHERE {where} ORDER BY received_at DESC LIMIT :limit OFFSET :offset"),
        params,
    )
    rows = [dict(r) for r in result.mappings().all()]

    open_result = await db.execute(
        text("SELECT COUNT(*) FROM dmca_requests WHERE status IN ('received', 'in_review')")
    )
    open_count = open_result.scalar() or 0

    return {
        "dmca_requests": rows,
        "total": len(rows),
        "open_count": int(open_count),
        "limit": limit,
        "offset": offset,
    }
