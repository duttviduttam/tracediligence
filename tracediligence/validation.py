from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import DiligenceOutput, EvidenceClaim, SourceRecord


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("uploaded://"):
        return url.lower()
    if not url:
        return ""
    try:
        parts = urlsplit(url)
        query = urlencode(
            [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
        )
        path = parts.path.rstrip("/") or "/"
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))
    except ValueError:
        return url.rstrip("/").lower()


def infer_source_type(url: str, title: str = "") -> str:
    haystack = f"{url} {title}".lower()
    if "sec.gov" in haystack or "annual report" in haystack or "10-k" in haystack or "10-q" in haystack:
        return "regulatory_filing"
    if any(domain in haystack for domain in [".gov", "who.int", "oecd.org", "worldbank.org"]):
        return "government"
    if "investor" in haystack or "earnings" in haystack:
        return "investor_relations"
    if url.startswith("uploaded://"):
        return "uploaded_document"
    if any(term in haystack for term in ["press release", "newsroom", "company blog"]):
        return "company_statement"
    return "web_source"


def reliability_for_source_type(source_type: str) -> float:
    scores = {
        "regulatory_filing": 1.00,
        "annual_report": 0.95,
        "government": 0.95,
        "audited_financials": 0.95,
        "uploaded_document": 0.80,
        "investor_relations": 0.80,
        "investor_presentation": 0.80,
        "industry_research": 0.75,
        "reputable_news": 0.72,
        "company_statement": 0.65,
        "company_marketing": 0.50,
        "web_source": 0.55,
        "other": 0.45,
    }
    return scores.get(source_type, 0.50)


def validate_claim(claim: EvidenceClaim, known_sources: dict[str, SourceRecord]) -> EvidenceClaim:
    normalized = normalize_url(claim.source_url)
    known = known_sources.get(normalized)
    status = claim.validation_status
    note_parts = [claim.analyst_note.strip()] if claim.analyst_note.strip() else []

    if not normalized:
        status = "Insufficient evidence"
        note_parts.append("No source URL was supplied.")
    elif known is None:
        status = "Insufficient evidence"
        note_parts.append("The cited URL was not found in the collected source set.")
    else:
        source_type = claim.source_type if claim.source_type != "other" else known.source_type
        claim = claim.model_copy(
            update={
                "source_title": claim.source_title or known.title,
                "source_type": source_type,
            }
        )

        if len(claim.evidence_excerpt.strip()) < 18:
            status = "Partially supported"
            note_parts.append("Evidence excerpt is too short for a strong claim-level audit.")
        elif claim.confidence_score < 0.55:
            status = "Insufficient evidence"
            note_parts.append("Confidence score is below the minimum review threshold.")
        elif status == "Supported" and claim.confidence_score < 0.75:
            status = "Partially supported"
            note_parts.append("Supported status was downgraded because confidence is below 75%.")

        if reliability_for_source_type(source_type) < 0.60 and status == "Supported":
            status = "Partially supported"
            note_parts.append("The source type has limited independent reliability.")

    return claim.model_copy(
        update={
            "validation_status": status,
            "analyst_note": " ".join(part for part in note_parts if part).strip(),
        }
    )


def validate_output(output: DiligenceOutput, sources: list[SourceRecord]) -> DiligenceOutput:
    source_map = {normalize_url(source.url): source for source in sources}
    validated = [validate_claim(claim, source_map) for claim in output.claims]
    return output.model_copy(update={"claims": validated})


def calculate_audit_metrics(output: DiligenceOutput) -> dict[str, float | int]:
    claims = output.claims
    total = len(claims)
    supported = sum(c.validation_status == "Supported" for c in claims)
    review = total - supported
    avg_confidence = sum(c.confidence_score for c in claims) / total if total else 0.0
    unique_sources = len({normalize_url(c.source_url) for c in claims if c.source_url})
    return {
        "total_claims": total,
        "supported_claims": supported,
        "review_claims": review,
        "support_rate": supported / total if total else 0.0,
        "average_confidence": avg_confidence,
        "unique_sources": unique_sources,
    }


def calculate_benchmark(
    manual_minutes: float,
    ai_minutes: float,
    manual_sources: int,
    ai_sources: int,
    reviewed_claims: int = 0,
    correct_citations: int = 0,
) -> dict[str, float]:
    time_reduction = (manual_minutes - ai_minutes) / manual_minutes if manual_minutes > 0 else 0.0
    coverage_multiplier = ai_sources / manual_sources if manual_sources > 0 else 0.0
    citation_accuracy = correct_citations / reviewed_claims if reviewed_claims > 0 else 0.0
    return {
        "time_reduction": time_reduction,
        "coverage_multiplier": coverage_multiplier,
        "citation_accuracy": citation_accuracy,
    }
