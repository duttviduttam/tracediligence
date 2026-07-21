from __future__ import annotations

import json
from typing import Any

from .models import DiligenceOutput, SourceRecord
from .validation import infer_source_type, normalize_url, reliability_for_source_type, validate_output


RESEARCH_SYSTEM = """You are a commercial due-diligence research analyst.
Research the requested company using current public sources and any supplied document text.
Prioritize primary sources: regulatory filings, audited financial statements, government records,
company investor-relations materials, and then reputable independent reporting.

Your work must be source-grounded. Separate reported facts from analytical inference. Capture
specific figures, time periods, definitions, contradictions, risks, and missing information.
Do not fabricate quotations, metrics, URLs, publication dates, or source titles.
"""


EXTRACTION_SYSTEM = """You convert a research record into a claim-level diligence ledger.
Use only the research text and allowed source list provided by the user. Every material claim must
cite exactly one URL from the allowed source list. Uploaded files use uploaded:// URLs and are valid.

Validation rules:
- 'Supported' means the evidence excerpt directly supports the claim.
- 'Partially supported' means the evidence supports only part of the claim or requires qualification.
- 'Conflicting evidence' means the evidence conflicts with another source or management assertion.
- 'Insufficient evidence' means there is not enough direct support.
- 'Outdated source' means a newer source is needed.
- 'Model inference' means the conclusion is analytical rather than directly stated.

Keep evidence excerpts concise. Do not invent verbatim wording. Confidence is a number from 0 to 1.
The executive summary may use only claims represented in the claims list.
"""


def _walk_for_sources(node: Any, collected: list[dict]) -> None:
    if isinstance(node, dict):
        url = node.get("url")
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            collected.append(
                {
                    "url": url,
                    "title": node.get("title") or node.get("name") or node.get("source") or url,
                    "publication_date": node.get("publication_date") or node.get("published_at"),
                }
            )
        for value in node.values():
            _walk_for_sources(value, collected)
    elif isinstance(node, list):
        for item in node:
            _walk_for_sources(item, collected)


def extract_sources_from_response(response: Any) -> list[SourceRecord]:
    try:
        payload = response.model_dump(mode="json")
    except Exception:
        try:
            payload = json.loads(response.model_dump_json())
        except Exception:
            return []

    raw: list[dict] = []
    _walk_for_sources(payload, raw)
    deduped: dict[str, SourceRecord] = {}
    for item in raw:
        normalized = normalize_url(item["url"])
        if not normalized or normalized in deduped:
            continue
        source_type = infer_source_type(item["url"], item.get("title", ""))
        deduped[normalized] = SourceRecord(
            title=item.get("title") or item["url"],
            url=item["url"],
            source_type=source_type,
            publication_date=item.get("publication_date"),
            reliability_score=reliability_for_source_type(source_type),
        )
    return list(deduped.values())


def run_diligence(
    *,
    company: str,
    objective: str,
    categories: list[str],
    api_key: str,
    model: str = "gpt-5",
    max_sources: int = 12,
    uploaded_text: str = "",
    uploaded_sources: list[dict] | None = None,
) -> tuple[DiligenceOutput, list[SourceRecord], str]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    category_text = ", ".join(categories)
    prompt = f"""Company: {company}
Research objective: {objective}
Diligence categories: {category_text}
Target source count: approximately {max_sources}

Prepare a rigorous research record. For each important fact, identify the source and explain any
qualification needed. Specifically look for financial and operating performance, business model,
customer and revenue quality, market and competition, strategic risks, contradictions, and open
questions. Avoid unsupported market-leadership language.

Uploaded document text, if any:
{uploaded_text or '[None supplied]'}
"""

    research_response = client.responses.create(
        model=model,
        tools=[{"type": "web_search", "search_context_size": "medium"}],
        tool_choice="auto",
        include=["web_search_call.action.sources"],
        input=[
            {"role": "system", "content": RESEARCH_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    research_text = research_response.output_text
    web_sources = extract_sources_from_response(research_response)
    local_sources = [SourceRecord.model_validate(source) for source in (uploaded_sources or [])]

    combined_map: dict[str, SourceRecord] = {}
    for source in [*web_sources, *local_sources]:
        combined_map[normalize_url(source.url)] = source
    sources = list(combined_map.values())[: max_sources + len(local_sources)]

    allowed_sources = [
        {
            "title": source.title,
            "url": source.url,
            "source_type": source.source_type,
            "publication_date": source.publication_date,
        }
        for source in sources
    ]
    extraction_prompt = f"""Company: {company}
Objective: {objective}
Requested categories: {category_text}

ALLOWED SOURCES:
{json.dumps(allowed_sources, indent=2)}

RESEARCH RECORD:
{research_text}

Create a diligence output with a concise executive summary, 8-18 material claims where evidence
permits, key risks, and open diligence questions. Cite only URLs in ALLOWED SOURCES. If evidence is
weak, preserve the claim but assign the appropriate non-supported status.
"""

    structured_response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": extraction_prompt},
        ],
        text_format=DiligenceOutput,
    )
    output = structured_response.output_parsed
    if output is None:
        raise RuntimeError("The model did not return a structured diligence output.")

    output = output.model_copy(update={"company": company, "objective": objective})
    return validate_output(output, sources), sources, research_text
