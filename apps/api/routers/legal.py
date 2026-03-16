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
    # EU / international securities terms
    r"\bWertpapier\b", r"\bValeurs mobilières\b",
    # Crypto / token investment context
    r"\btoken\b", r"\bcrypto\b",
    # Additional high-risk financial terms
    r"\bguaranteed returns\b", r"\bcapital gain\b", r"\bappreciation\b",
]

ALLOWED_ALTERNATIVES = {
    "invest": "buy / purchase / own",
    "investment": "purchase / points",
    "ROI": "royalties earned",
    "returns": "royalties / earnings",
    "securities": "points",
    "equity": "master points",
    "wertpapier": "Punkte (points)",
    "valeurs mobilières": "points de redevance",
    "token": "points / credits",
    "crypto": "digital points",
    "guaranteed returns": "potential royalty earnings",
    "capital gain": "royalty earnings",
    "appreciation": "royalty growth",
}

COPYRIGHT_SOCIETIES = [
    # United States
    "ascap", "bmi", "sesac", "mlc", "soundexchange", "songtrust",
    "copyright_office", "content_id",
    # United Kingdom
    "prs_for_music", "ppl_uk",
    # Germany
    "gema", "gvl",
    # France
    "sacem", "scpp", "sppf",
    # Italy
    "siae",
    # Spain
    "sgae",
    # Netherlands
    "buma_stemra",
    # Scandinavia
    "stim", "koda", "tono", "teosto",
    # Australia / New Zealand
    "apra_amcos",
    # Japan
    "jasrac",
    # Canada
    "socan", "re_sound",
    # Brazil
    "ecad",
    # Mexico
    "sacm",
    # South Africa
    "samro",
    # International umbrella
    "cisac", "wipo",
]

SUPPORTED_JURISDICTIONS = [
    {"id": "california_us", "name": "California, USA", "body": "AAA Commercial Arbitration, Los Angeles"},
    {"id": "england_wales", "name": "England and Wales", "body": "LCIA Arbitration, London"},
    {"id": "germany", "name": "Germany", "body": "DIS Arbitration, Frankfurt"},
    {"id": "france", "name": "France", "body": "ICC Arbitration, Paris"},
    {"id": "australia", "name": "New South Wales, Australia", "body": "ACICA Arbitration, Sydney"},
    {"id": "international_icc", "name": "International (ICC)", "body": "ICC International Court of Arbitration, Geneva"},
]

TAKEDOWN_REGIMES = {
    "dmca_us": {
        "name": "DMCA (US)",
        "law": "Digital Millennium Copyright Act 17 U.S.C. § 512",
        "response_window": "10 business days",
        "response_days": 10,
    },
    "dsa_eu": {
        "name": "DSA (EU)",
        "law": "Digital Services Act (EU) 2022/2065, Article 16",
        "response_window": "24–72 hours for illegal content; 7 days general",
        "response_days": 1,
    },
    "osa_uk": {
        "name": "Online Safety Act (UK)",
        "law": "Online Safety Act 2023 (UK)",
        "response_window": "7 days",
        "response_days": 7,
    },
    "osa_au": {
        "name": "Online Safety Act (Australia)",
        "law": "Online Safety Act 2021 (Cth)",
        "response_window": "48 hours for class 1 material; 7 days general",
        "response_days": 2,
    },
    "nnr_ca": {
        "name": "Notice-and-Notice (Canada)",
        "law": "Copyright Act (Canada) R.S.C. 1985, c. C-42, s. 41.25",
        "response_window": "Forward notice within a reasonable time",
        "response_days": 5,
    },
    "plla_jp": {
        "name": "Provider Liability Limitation Act (Japan)",
        "law": "Provider Liability Limitation Act (Japan) Act No. 137 of 2001",
        "response_window": "7 days",
        "response_days": 7,
    },
}

FATF_HIGH_RISK_COUNTRIES = [
    "IR", "KP", "MM", "SY", "YE", "IQ", "LY", "SD", "SO",
    "AF", "VU", "PK", "HT",
]

GDPR_REQUIRED_FIELDS = [
    "data_controller", "lawful_basis", "retention_period", "data_subject_rights",
]

PERSONAL_DATA_CATEGORIES = [
    "name", "email", "address", "payment", "credit card", "bank",
    "biometric", "photo", "location", "ip address", "device id",
    "date of birth", "phone", "national id", "passport",
]


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
    territory: str = "worldwide"
    governing_law: str = "california_us"


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
    context: str = "general"  # general|points|marketing|contract|platform|financial
    source: Optional[str] = None
    territory: Optional[str] = ""


class KYCCheckRequest(BaseModel):
    user_id: str
    country_code: str
    purchase_amount: float = 0.0
    annual_royalties: float = 0.0
    is_us_person: bool = False


class GDPRCheckRequest(BaseModel):
    content: str
    context: str = "general"


class TakedownRequest(BaseModel):
    track_id: Optional[str] = None
    claimant: str
    platform: str
    claim_type: str = "copyright"
    takedown_regime: str = "dmca_us"
    notes: Optional[str] = None


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

    governing_law = contract_in.governing_law
    if governing_law not in {j["id"] for j in SUPPORTED_JURISDICTIONS}:
        governing_law = "california_us"

    territory_lower = contract_in.territory.lower()
    gdpr_addendum = any(t in territory_lower for t in ["eu", "eea", "uk", "europe", "worldwide"])

    contract_id = str(uuid.uuid4())
    from datetime import date
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
        "territory": contract_in.territory,
        "governing_law": governing_law,
        "gdpr_addendum": gdpr_addendum,
        "kyc_verified": False,
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
        "territory": contract_in.territory,
        "governing_law": governing_law,
        "gdpr_addendum": gdpr_addendum,
        "splits": {"pre_recoup": "40/60", "post_recoup": "60/40"},
        "message": "Contract created in draft status",
        "disclaimer": "TEMPLATE ONLY — Not legal advice. Review with qualified counsel in each jurisdiction.",
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
    """Scan text for compliance issues — prohibited language, GDPR, DSA, MiFID II."""
    issues = []
    warnings = []

    # Prohibited point/investment language
    for pattern in PROHIBITED_POINT_WORDS:
        matches = re.findall(pattern, body.content, re.IGNORECASE)
        for match in matches:
            suggestion = ALLOWED_ALTERNATIVES.get(match.lower(), "Use approved ECHO Points terminology")
            issues.append({
                "type": "prohibited_language",
                "severity": "critical",
                "match": match,
                "suggestion": suggestion,
                "rule": "No investment terminology in ECHO Points context (global)",
            })

    # Points / marketing disclosures
    if body.context in ("points", "marketing"):
        for phrase in ["past earnings do not guarantee", "points are not securities"]:
            if phrase.lower() not in body.content.lower():
                warnings.append({
                    "type": "missing_disclosure",
                    "severity": "warning",
                    "message": f'Consider adding disclosure: "{phrase}"',
                })

    # Contract checks
    if body.context == "contract":
        for keyword, msg in [
            ("reversion", "Contract should reference master reversion rights"),
            ("recoup", "Contract should define recoupable costs"),
            ("arbitration", "Contract should specify dispute resolution"),
            ("berne", "Contract should reference Berne Convention for international protection"),
        ]:
            if keyword not in body.content.lower():
                warnings.append({"type": "missing_clause", "severity": "warning", "message": msg})

    # GDPR checks
    territory_lower = (body.territory or "").lower()
    is_eu = any(t in territory_lower for t in ["eu", "eea", "uk", "europe", "worldwide"])
    if is_eu or body.context in ("contract", "platform", "artist_portal"):
        for field in GDPR_REQUIRED_FIELDS:
            if field.replace("_", " ") not in body.content.lower():
                warnings.append({
                    "type": "gdpr_missing_field",
                    "severity": "warning",
                    "message": f"GDPR: Consider disclosing '{field.replace('_', ' ')}' per GDPR Art. 13/14",
                })

    # DSA checks
    if body.context in ("platform", "marketing"):
        for keyword, msg in [
            ("transparency", "DSA Art. 26: Advertising transparency disclosure required"),
            ("recommender", "DSA Art. 27: Algorithmic recommendation system disclosure"),
            ("contact", "DSA Art. 12: Accessible contact point for authorities required"),
        ]:
            if keyword not in body.content.lower():
                warnings.append({"type": "dsa_missing", "severity": "warning", "message": msg})

    # Financial context — MiFID II / FCA / ASIC
    if body.context == "financial":
        for phrase, msg in [
            ("risk warning", "FCA/ASIC/MiFID II: Prominent risk warning required"),
            ("not financial advice", "Disclaimer: 'Not financial advice' required"),
            ("past performance", "Required: past performance disclaimer"),
        ]:
            if phrase not in body.content.lower():
                warnings.append({"type": "financial_warning_missing", "severity": "warning", "message": msg})

    return {
        "compliant": len(issues) == 0,
        "context": body.context,
        "territory": body.territory,
        "eu_territory": is_eu,
        "issues": issues,
        "warnings": warnings,
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "policy_summary": "Never use: invest, investment, ROI, returns, securities, equity, token, crypto. Use: buy, purchase, own, earn, points, royalties.",
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


# ----------------------------------------------------------------
# KYC Check
# ----------------------------------------------------------------

@router.post("/kyc/check")
async def kyc_check(
    body: KYCCheckRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """KYC/AML tier determination per FATF recommendations."""
    country_code = body.country_code.upper()
    sanctions_flagged = country_code in FATF_HIGH_RISK_COUNTRIES
    fatf_high_risk = country_code in FATF_HIGH_RISK_COUNTRIES

    if body.purchase_amount < 500:
        kyc_tier = 1
        verification_required = ["email", "phone"]
        tier_description = "Tier 1: Email + phone verification"
    elif body.purchase_amount <= 5000:
        kyc_tier = 2
        verification_required = ["email", "phone", "government_id"]
        tier_description = "Tier 2: Government ID required (Persona API)"
    else:
        kyc_tier = 3
        verification_required = [
            "email", "phone", "government_id",
            "source_of_funds", "enhanced_due_diligence",
        ]
        tier_description = "Tier 3: Enhanced due diligence + source of funds"

    tax_form_required = None
    if body.is_us_person and body.annual_royalties > 600:
        tax_form_required = "W-9"
    elif not body.is_us_person and body.annual_royalties > 0:
        tax_form_required = "W-8BEN"

    return {
        "user_id": body.user_id,
        "country_code": country_code,
        "purchase_amount": body.purchase_amount,
        "kyc_tier": kyc_tier,
        "tier_description": tier_description,
        "verification_required": verification_required,
        "tax_form_required": tax_form_required,
        "sanctions_flagged": sanctions_flagged,
        "fatf_high_risk": fatf_high_risk,
        "ofac_check_required": True,
        "aml_note": (
            "ECHO applies AML/KYC per FATF recommendations. "
            "Identity verification required for point purchases > $500."
        ),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


# ----------------------------------------------------------------
# GDPR Check
# ----------------------------------------------------------------

@router.post("/gdpr/check")
async def gdpr_check(
    body: GDPRCheckRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """GDPR compliance scan for content or document."""
    content_lower = body.content.lower()
    issues = []
    recommendations = []

    detected_personal_data = [cat for cat in PERSONAL_DATA_CATEGORIES if cat in content_lower]

    article_map = {
        "data_controller": "GDPR Art. 13(1)(a)",
        "lawful_basis": "GDPR Art. 13(1)(c)",
        "retention_period": "GDPR Art. 13(2)(a)",
        "data_subject_rights": "GDPR Art. 13(2)(b)",
    }
    missing_fields = []
    for field in GDPR_REQUIRED_FIELDS:
        if field.replace("_", " ") not in content_lower:
            missing_fields.append(field)
            issues.append({
                "field": field,
                "message": f"Missing required GDPR disclosure: {field.replace('_', ' ')}",
                "article": article_map.get(field, "GDPR Art. 13/14"),
            })

    if "purpose" not in content_lower and detected_personal_data:
        issues.append({
            "field": "processing_purpose",
            "message": "Data processing purpose not stated (GDPR Art. 5(1)(b) — purpose limitation)",
            "article": "GDPR Art. 5(1)(b)",
        })

    lawful_bases = [
        "consent", "contract", "legitimate interest",
        "legal obligation", "vital interests", "public task",
    ]
    has_lawful_basis = any(basis in content_lower for basis in lawful_bases)
    if not has_lawful_basis and detected_personal_data:
        issues.append({
            "field": "lawful_basis",
            "message": (
                "No valid GDPR lawful basis identified (Art. 6). "
                "Must state: consent / contract / legitimate interest / legal obligation."
            ),
            "article": "GDPR Art. 6",
        })

    if detected_personal_data:
        recommendations.append(
            f"Personal data detected: {', '.join(detected_personal_data)}. "
            "Ensure Article 30 processing record is maintained."
        )
    if "transfer" in content_lower or "third party" in content_lower:
        recommendations.append(
            "International data transfers: Ensure SCCs / adequacy decision in place (GDPR Art. 46)."
        )
    recommendations.append(
        "Appoint a Data Protection Officer if processing large-scale special category data (GDPR Art. 37)."
    )
    recommendations.append(
        "Conduct DPIA for high-risk processing activities (GDPR Art. 35)."
    )

    return {
        "gdpr_compliant": len(issues) == 0,
        "context": body.context,
        "detected_personal_data": detected_personal_data,
        "missing_fields": missing_fields,
        "issues": issues,
        "recommendations": recommendations,
        "issue_count": len(issues),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "TEMPLATE ONLY — Not legal advice. Review with qualified GDPR counsel.",
    }


# ----------------------------------------------------------------
# Jurisdictions
# ----------------------------------------------------------------

@router.get("/jurisdictions")
async def list_jurisdictions(
    current_user: TokenData = Depends(get_current_user),
):
    """List all supported governing law jurisdictions."""
    return {
        "jurisdictions": SUPPORTED_JURISDICTIONS,
        "count": len(SUPPORTED_JURISDICTIONS),
        "default": "california_us",
        "note": "TEMPLATE ONLY — Not legal advice. Select jurisdiction with qualified counsel.",
    }


# ----------------------------------------------------------------
# Unified Global Takedown
# ----------------------------------------------------------------

@router.post("/takedown", status_code=status.HTTP_201_CREATED)
async def create_takedown(
    body: TakedownRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Submit a global takedown request under the specified legal regime."""
    regime = body.takedown_regime
    if regime not in TAKEDOWN_REGIMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown takedown_regime. Supported: {list(TAKEDOWN_REGIMES.keys())}",
        )

    regime_info = TAKEDOWN_REGIMES[regime]
    takedown_id = str(uuid.uuid4())

    await db.execute(
        text("""
            INSERT INTO dmca_requests (id, track_id, claimant, platform, claim_type, status, notes)
            VALUES (:id, :track_id, :claimant, :platform, :claim_type, 'received', :notes)
        """),
        {
            "id": takedown_id,
            "track_id": body.track_id,
            "claimant": body.claimant,
            "platform": body.platform,
            "claim_type": body.claim_type,
            "notes": f"[{regime.upper()}] {body.notes or ''}".strip(),
        },
    )
    await db.commit()

    return {
        "id": takedown_id,
        "status": "received",
        "takedown_regime": regime,
        "regime": regime_info,
        "claimant": body.claimant,
        "platform": body.platform,
        "track_id": body.track_id,
        "next_steps": [
            f"Review under {regime_info['name']}: {regime_info['law']}",
            f"Respond within: {regime_info['response_window']}",
            "Verify ECHO's ownership rights",
            "If counter-notice warranted, file within 14 days",
        ],
        "received_at": datetime.now(timezone.utc).isoformat(),
        "message": "Takedown request logged",
    }


# ----------------------------------------------------------------
# Royalty Collection Societies
# ----------------------------------------------------------------

@router.get("/societies")
async def list_societies(
    current_user: TokenData = Depends(get_current_user),
):
    """List all supported royalty collection societies."""
    society_details = [
        {"id": "ascap", "name": "ASCAP", "region": "US", "type": "PRO"},
        {"id": "bmi", "name": "BMI", "region": "US", "type": "PRO"},
        {"id": "sesac", "name": "SESAC", "region": "US", "type": "PRO"},
        {"id": "mlc", "name": "MLC (Mechanical Licensing Collective)", "region": "US", "type": "Mechanical"},
        {"id": "soundexchange", "name": "SoundExchange", "region": "US", "type": "Neighboring Rights"},
        {"id": "songtrust", "name": "Songtrust", "region": "US/Global", "type": "Publishing Admin"},
        {"id": "copyright_office", "name": "US Copyright Office", "region": "US", "type": "Registration"},
        {"id": "content_id", "name": "YouTube Content ID", "region": "Global", "type": "Digital"},
        {"id": "prs_for_music", "name": "PRS for Music", "region": "UK", "type": "PRO"},
        {"id": "ppl_uk", "name": "PPL UK", "region": "UK", "type": "Neighboring Rights"},
        {"id": "gema", "name": "GEMA", "region": "Germany", "type": "PRO"},
        {"id": "gvl", "name": "GVL", "region": "Germany", "type": "Neighboring Rights"},
        {"id": "sacem", "name": "SACEM", "region": "France", "type": "PRO"},
        {"id": "scpp", "name": "SCPP", "region": "France", "type": "Neighboring Rights"},
        {"id": "sppf", "name": "SPPF", "region": "France", "type": "Neighboring Rights"},
        {"id": "siae", "name": "SIAE", "region": "Italy", "type": "PRO"},
        {"id": "sgae", "name": "SGAE", "region": "Spain", "type": "PRO"},
        {"id": "buma_stemra", "name": "BUMA/STEMRA", "region": "Netherlands", "type": "PRO"},
        {"id": "stim", "name": "STIM", "region": "Sweden", "type": "PRO"},
        {"id": "koda", "name": "KODA", "region": "Denmark", "type": "PRO"},
        {"id": "tono", "name": "TONO", "region": "Norway", "type": "PRO"},
        {"id": "teosto", "name": "TEOSTO", "region": "Finland", "type": "PRO"},
        {"id": "apra_amcos", "name": "APRA AMCOS", "region": "Australia/NZ", "type": "PRO"},
        {"id": "jasrac", "name": "JASRAC", "region": "Japan", "type": "PRO"},
        {"id": "socan", "name": "SOCAN", "region": "Canada", "type": "PRO"},
        {"id": "re_sound", "name": "Re:Sound", "region": "Canada", "type": "Neighboring Rights"},
        {"id": "ecad", "name": "ECAD", "region": "Brazil", "type": "PRO"},
        {"id": "sacm", "name": "SACM", "region": "Mexico", "type": "PRO"},
        {"id": "samro", "name": "SAMRO", "region": "South Africa", "type": "PRO"},
        {"id": "cisac", "name": "CISAC", "region": "International", "type": "Umbrella"},
        {"id": "wipo", "name": "WIPO", "region": "International", "type": "Treaty Body"},
    ]
    return {
        "societies": society_details,
        "count": len(society_details),
        "berne_convention": (
            "Copyright protections under Berne Convention (1886, as amended) "
            "across all 181 signatory nations."
        ),
    }
