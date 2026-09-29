"""Typed contracts passed between ADK 2.x graph nodes."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class NeedCategory(str, Enum):
    FOOD_SUPPORT = "food_support"
    EDUCATION_SUPPORT = "education_support"
    YOUTH_PROGRAMS = "youth_programs"
    EMPLOYMENT_SUPPORT = "employment_support"
    HEALTH_WELLNESS = "health_wellness"
    HOUSING_NAVIGATION = "housing_navigation"
    LEGAL_INFORMATION = "legal_information"
    NEWCOMER_SUPPORT = "newcomer_support"
    TRANSPORTATION_SUPPORT = "transportation_support"
    DIGITAL_ACCESS = "digital_access"
    FAMILY_SUPPORT = "family_support"
    DISABILITY_SUPPORT = "disability_support"
    OTHER = "other"


class Urgency(str, Enum):
    IMMEDIATE = "immediate"
    TODAY = "today"
    THIS_WEEK = "this_week"
    ONGOING = "ongoing"
    UNKNOWN = "unknown"


class AgeBand(str, Enum):
    UNDER_13 = "under_13"
    AGE_13_17 = "13_17"
    AGE_18_24 = "18_24"
    ADULT_25_PLUS = "25_plus"
    UNKNOWN = "unknown"


class BarrierType(str, Enum):
    TRANSPORTATION = "transportation"
    DOCUMENTS = "documents"
    COST = "cost"
    SCHEDULE = "schedule"
    LANGUAGE = "language"
    ACCESSIBILITY = "accessibility"
    DIGITAL_ACCESS = "digital_access"
    CHILDCARE = "childcare"
    CONTACT_ANXIETY = "contact_anxiety"
    SAFETY = "safety"
    OTHER = "other"


class RequestEnvelope(BaseModel):
    message: str
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    clarification_round: int = 0


class NeedItem(BaseModel):
    category: NeedCategory
    statement: str
    urgency: Urgency = Urgency.UNKNOWN
    priority: int = Field(default=3, ge=1, le=5)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    keywords: list[str] = Field(default_factory=list)


class UserBarrier(BaseModel):
    barrier: BarrierType
    statement: str
    severity: int = Field(default=3, ge=1, le=5)


class SupportPreferences(BaseModel):
    languages: list[str] = Field(default_factory=lambda: ["English"])
    delivery_modes: list[Literal["in_person", "online", "phone", "delivery"]] = Field(
        default_factory=list
    )
    free_only: bool = True
    online_only: bool = False
    preferred_times: list[str] = Field(default_factory=list)
    accessibility_needs: list[str] = Field(default_factory=list)
    travel_radius_km: float = Field(default=10.0, ge=0.5, le=100.0)


class SupportProfile(BaseModel):
    safe_summary: str
    location_text: str | None = None
    age_band: AgeBand = AgeBand.UNKNOWN
    needs: list[NeedItem] = Field(default_factory=list)
    barriers: list[UserBarrier] = Field(default_factory=list)
    preferences: SupportPreferences = Field(default_factory=SupportPreferences)
    strengths: list[str] = Field(default_factory=list)
    missing_required_fields: list[str] = Field(default_factory=list)
    clarifying_questions: list[str] = Field(default_factory=list)
    privacy_notes: list[str] = Field(default_factory=list)
    clarification_round: int = 0


class ResourceContact(BaseModel):
    phone: str | None = None
    email: str | None = None
    website: str | None = None


class ResourceRecord(BaseModel):
    resource_id: str
    name: str
    description: str
    categories: list[NeedCategory]
    keywords: list[str] = Field(default_factory=list)
    service_areas: list[str] = Field(default_factory=list)
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    delivery_modes: list[Literal["in_person", "online", "phone", "delivery"]]
    cost: Literal["free", "low_cost", "paid", "unknown"] = "unknown"
    min_age: int | None = None
    max_age: int | None = None
    eligibility_rules: list[str] = Field(default_factory=list)
    documents_required: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["English"])
    accessibility: list[str] = Field(default_factory=list)
    hours: dict[str, list[str]] = Field(default_factory=dict)
    contact: ResourceContact = Field(default_factory=ResourceContact)
    source_url: str
    source_kind: Literal["official", "directory", "community", "demo"] = "demo"
    last_verified: date
    capacity_status: Literal["available", "limited", "waitlist", "unknown"] = "unknown"
    is_demo: bool = True


class ResourceCandidate(BaseModel):
    resource: ResourceRecord
    base_match_score: float = Field(ge=0.0, le=1.0)
    match_reasons: list[str] = Field(default_factory=list)
    hard_filter_notes: list[str] = Field(default_factory=list)


class CandidateBundle(BaseModel):
    profile: SupportProfile
    candidates: list[ResourceCandidate]
    search_trace: list[str] = Field(default_factory=list)
    normalized_location: str | None = None
    origin_latitude: float | None = None
    origin_longitude: float | None = None
    demo_data: bool = True


class EligibilityAssessment(BaseModel):
    resource_id: str
    label: Literal["likely", "possible", "uncertain", "unlikely"]
    reasons: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    disclaimer: str = "The organization makes the final eligibility decision."


class EligibilityReport(BaseModel):
    assessments: list[EligibilityAssessment]
    global_notes: list[str] = Field(default_factory=list)


class BarrierMatch(BaseModel):
    resource_id: str
    fit_score: float = Field(ge=0.0, le=1.0)
    barriers_addressed: list[str] = Field(default_factory=list)
    remaining_barriers: list[str] = Field(default_factory=list)
    practical_workarounds: list[str] = Field(default_factory=list)


class BarrierReport(BaseModel):
    matches: list[BarrierMatch]
    global_barriers: list[str] = Field(default_factory=list)
    user_strengths_to_use: list[str] = Field(default_factory=list)


class TrustAssessment(BaseModel):
    resource_id: str
    confidence: Literal["high", "medium", "low"]
    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    verify_before_visiting: bool = False


class TrustReport(BaseModel):
    assessments: list[TrustAssessment]


class AccessAssessment(BaseModel):
    resource_id: str
    score: float = Field(ge=0.0, le=1.0)
    distance_km: float | None = None
    mode_fit: list[str] = Field(default_factory=list)
    schedule_notes: list[str] = Field(default_factory=list)


class AccessReport(BaseModel):
    assessments: list[AccessAssessment]


class EvidenceBundle(BaseModel):
    candidates: CandidateBundle
    eligibility: EligibilityReport
    barriers: BarrierReport
    trust: TrustReport
    access: AccessReport


class RankedResource(BaseModel):
    resource: ResourceRecord
    total_score: float = Field(ge=0.0, le=1.0)
    score_breakdown: dict[str, float]
    why_match: list[str] = Field(default_factory=list)
    watch_outs: list[str] = Field(default_factory=list)
    eligibility_label: Literal["likely", "possible", "uncertain", "unlikely"]
    confidence_label: Literal["high", "medium", "low"]


class RankingResult(BaseModel):
    profile: SupportProfile
    ranked_resources: list[RankedResource]
    unmet_needs: list[NeedCategory] = Field(default_factory=list)
    ranking_trace: list[str] = Field(default_factory=list)
    demo_data: bool = True


class ActionStep(BaseModel):
    order: int = Field(ge=1)
    action: str
    reason: str
    resource_id: str | None = None
    timing: str = "Next"


class ContactDraft(BaseModel):
    resource_id: str
    channel: Literal["email", "text", "phone_script"]
    subject: str | None = None
    body: str


class PlanOption(BaseModel):
    title: str
    purpose: str
    resource_ids: list[str]
    steps: list[ActionStep]
    use_when: str


class SupportPlan(BaseModel):
    headline: str
    requested_needs: list[NeedCategory] = Field(default_factory=list)
    barrier_types: list[BarrierType] = Field(default_factory=list)
    best_first_step: ActionStep
    selected_resources: list[RankedResource]
    plan_a: PlanOption
    plan_b: PlanOption
    document_backpack: list[str] = Field(default_factory=list)
    contact_drafts: list[ContactDraft] = Field(default_factory=list)
    confidence_notes: list[str] = Field(default_factory=list)
    shareable_summary: str
    unmet_needs: list[NeedCategory] = Field(default_factory=list)
    revision_count: int = Field(default=0, ge=0, le=5)
    demo_data_notice: str = "This project ships with synthetic demonstration resources."


class PlanCritique(BaseModel):
    verdict: Literal["READY", "REVISE"]
    quality_score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)
    required_changes: list[str] = Field(default_factory=list)
    hallucination_risks: list[str] = Field(default_factory=list)


class PlanReviewBundle(BaseModel):
    plan: SupportPlan
    critique: PlanCritique


class UserRevisionRequest(BaseModel):
    plan: SupportPlan
    feedback: str


class GapEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    need_categories: list[NeedCategory]
    barrier_types: list[BarrierType]
    unmet_needs: list[NeedCategory]
    resource_ids_offered: list[str]
    demo_data: bool


class AidCompassState(BaseModel):
    model_config = ConfigDict(extra="allow")

    clarification_count: int = 0
    pending_profile: dict[str, Any] | None = None
    latest_ranking: dict[str, Any] | None = None
    latest_plan: dict[str, Any] | None = None
    pending_plan: dict[str, Any] | None = None
    pending_critique: dict[str, Any] | None = None
    final_plan: dict[str, Any] | None = None
