from tracediligence.demo import load_demo_output, load_demo_sources
from tracediligence.models import EvidenceClaim
from tracediligence.reporting import render_markdown_report
from tracediligence.validation import (
    calculate_benchmark,
    normalize_url,
    validate_claim,
    validate_output,
)


def test_normalize_url_removes_tracking_and_fragment():
    url = "https://Example.com/report/?utm_source=test&a=1#page=2"
    assert normalize_url(url) == "https://example.com/report?a=1"


def test_unknown_source_is_downgraded():
    claim = EvidenceClaim(
        claim="Revenue grew 20%.",
        category="Financial performance",
        evidence_excerpt="Revenue grew 20% during the year.",
        source_title="Unknown",
        source_url="https://unknown.example/report",
        confidence_score=0.90,
        validation_status="Supported",
    )
    validated = validate_claim(claim, {})
    assert validated.validation_status == "Insufficient evidence"


def test_demo_output_validates_and_renders():
    sources = load_demo_sources()
    output = validate_output(load_demo_output("Demo Co", "Test objective"), sources)
    assert len(output.claims) >= 8
    report = render_markdown_report(output, sources)
    assert "# TraceDiligence Report: Demo Co" in report
    assert "## Evidence Ledger" in report


def test_benchmark_calculation():
    result = calculate_benchmark(100, 65, 9, 18, 20, 18)
    assert round(result["time_reduction"], 2) == 0.35
    assert result["coverage_multiplier"] == 2.0
    assert result["citation_accuracy"] == 0.9
