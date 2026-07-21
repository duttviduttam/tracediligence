from __future__ import annotations

import json

import pandas as pd

from .models import DiligenceOutput, SourceRecord
from .validation import calculate_audit_metrics


def claims_dataframe(output: DiligenceOutput) -> pd.DataFrame:
    rows = [
        {
            "Category": c.category,
            "Claim": c.claim,
            "Evidence": c.evidence_excerpt,
            "Source": c.source_title,
            "URL": c.source_url,
            "Source type": c.source_type,
            "Published": c.publication_date or "",
            "Confidence": round(c.confidence_score, 2),
            "Status": c.validation_status,
            "Analyst note": c.analyst_note,
        }
        for c in output.claims
    ]
    return pd.DataFrame(rows)


def _escape(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown_report(output: DiligenceOutput, sources: list[SourceRecord]) -> str:
    metrics = calculate_audit_metrics(output)
    lines = [
        f"# TraceDiligence Report: {output.company}",
        "",
        f"**Objective:** {output.objective}",
        "",
        "## Executive Summary",
        "",
        output.executive_summary,
        "",
        "## Audit Snapshot",
        "",
        f"- Claims reviewed: {metrics['total_claims']}",
        f"- Fully supported: {metrics['supported_claims']}",
        f"- Requiring review: {metrics['review_claims']}",
        f"- Unique cited sources: {metrics['unique_sources']}",
        f"- Average confidence: {metrics['average_confidence']:.0%}",
        "",
        "## Key Risks",
        "",
    ]
    lines.extend(f"- {risk}" for risk in output.key_risks)
    lines.extend(
        [
            "",
            "## Evidence Ledger",
            "",
            "| Category | Claim | Evidence | Source | Confidence | Status |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for claim in output.claims:
        source = (
            f"[{_escape(claim.source_title)}]({claim.source_url})"
            if claim.source_url
            else _escape(claim.source_title)
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(claim.category),
                    _escape(claim.claim),
                    _escape(claim.evidence_excerpt),
                    source,
                    f"{claim.confidence_score:.0%}",
                    _escape(claim.validation_status),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Open Diligence Questions", ""])
    lines.extend(f"- {question}" for question in output.open_questions)
    lines.extend(["", "## Source Appendix", ""])
    for source in sources:
        lines.append(
            f"- [{source.title}]({source.url}) — {source.source_type}; "
            f"reliability {source.reliability_score:.0%}"
        )
    lines.extend(["", "## Methodology and Limitations", "", output.methodology_note, ""])
    return "\n".join(lines)


def render_json(output: DiligenceOutput, sources: list[SourceRecord]) -> str:
    payload = {
        "analysis": output.model_dump(mode="json"),
        "sources": [source.model_dump(mode="json") for source in sources],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
