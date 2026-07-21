from __future__ import annotations

import html
import os
from collections import defaultdict
from typing import Iterable

import pandas as pd
import streamlit as st

from tracediligence.demo import load_demo_output, load_demo_sources
from tracediligence.file_ingest import extract_uploaded_files
from tracediligence.models import DiligenceOutput, EvidenceClaim, SourceRecord
from tracediligence.reporting import claims_dataframe, render_json, render_markdown_report
from tracediligence.research import run_diligence
from tracediligence.validation import calculate_audit_metrics, calculate_benchmark, validate_output


st.set_page_config(
    page_title="TraceDiligence",
    page_icon="TD",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# Visual system
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        color-scheme: light !important;
        --td-ink: #111827;
        --td-ink-soft: #1f2937;
        --td-muted: #475569;
        --td-subtle: #64748b;
        --td-border: #e2e8f0;
        --td-border-soft: #edf2f7;
        --td-surface: #ffffff;
        --td-canvas: #f8fafc;
        --td-surface-muted: #f1f5f9;
        --td-mint: #00b894;
        --td-mint-dark: #007f68;
        --td-mint-soft: #e7faf5;
        --td-amber: #b45309;
        --td-amber-soft: #fff7ed;
        --td-red: #b42318;
        --td-red-soft: #fff1f2;
        --td-blue: #2563eb;
        --td-blue-soft: #eff6ff;
        --td-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }

    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        background: var(--td-canvas) !important;
        color: var(--td-ink) !important;
    }

    html, body, input, textarea, button, select {
        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }

    [data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.92) !important;
        border-bottom: 1px solid rgba(226, 232, 240, 0.9) !important;
        backdrop-filter: blur(12px);
    }

    [data-testid="stToolbar"] button,
    [data-testid="stToolbar"] svg {
        color: var(--td-ink) !important;
        fill: currentColor !important;
    }

    .block-container {
        max-width: 1240px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    /* Force readable typography even when a viewer previously selected dark mode. */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp li, .stApp label, .stApp small,
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    [data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"],
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: var(--td-ink) !important;
        opacity: 1 !important;
    }

    [data-testid="stCaptionContainer"], .muted-copy, .muted-copy p {
        color: var(--td-subtle) !important;
    }

    .td-shell {
        background: var(--td-surface);
        border: 1px solid var(--td-border);
        border-radius: 18px;
        box-shadow: var(--td-shadow);
        overflow: hidden;
        margin-bottom: 1.2rem;
    }

    .td-hero {
        position: relative;
        overflow: hidden;
        padding: 2.35rem 2.5rem 2.2rem;
        background:
            radial-gradient(circle at 94% 10%, rgba(0,184,148,.17) 0 92px, transparent 93px),
            linear-gradient(120deg, #fff8ed 0%, #ffffff 48%, #eafbf7 100%);
        border-bottom: 1px solid var(--td-border-soft);
    }

    .td-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: .45rem;
        padding: .35rem .65rem;
        border-radius: 999px;
        background: rgba(255,255,255,.75);
        border: 1px solid var(--td-border);
        color: var(--td-ink-soft) !important;
        font-size: .76rem;
        font-weight: 700;
        letter-spacing: .055em;
        text-transform: uppercase;
    }

    .td-dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: var(--td-mint);
        box-shadow: 0 0 0 4px rgba(0,184,148,.12);
    }

    .td-hero h1 {
        margin: .9rem 0 .45rem;
        color: var(--td-ink) !important;
        font-size: clamp(2.25rem, 4.5vw, 3.65rem);
        line-height: 1.02;
        font-weight: 700;
        letter-spacing: -.055em;
    }

    .td-hero p {
        max-width: 790px;
        margin: 0;
        color: var(--td-muted) !important;
        font-size: 1.02rem;
        line-height: 1.65;
    }

    .td-how {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .8rem;
        padding: 1.1rem 1.2rem 1.25rem;
        background: var(--td-surface);
    }

    .td-how-card {
        padding: .95rem 1rem;
        border: 1px solid var(--td-border-soft);
        border-radius: 12px;
        background: #fff;
    }

    .td-how-number {
        display: inline-grid;
        place-items: center;
        width: 24px;
        height: 24px;
        margin-bottom: .55rem;
        border-radius: 999px;
        background: var(--td-ink);
        color: white !important;
        font-size: .72rem;
        font-weight: 700;
    }

    .td-how-card strong {
        display: block;
        color: var(--td-ink) !important;
        font-size: .91rem;
        margin-bottom: .22rem;
    }

    .td-how-card span {
        color: var(--td-subtle) !important;
        font-size: .8rem;
        line-height: 1.45;
    }

    .td-section-heading {
        margin: 1.5rem 0 .25rem;
        color: var(--td-ink) !important;
        font-size: 1.45rem;
        letter-spacing: -.025em;
    }

    .td-section-copy {
        color: var(--td-subtle) !important;
        margin: 0 0 .9rem;
        line-height: 1.55;
    }

    /* Native containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--td-surface) !important;
        border-color: var(--td-border) !important;
        border-radius: 15px !important;
        box-shadow: none !important;
    }

    /* Inputs */
    [data-testid="stWidgetLabel"] p {
        color: var(--td-ink-soft) !important;
        font-size: .86rem !important;
        font-weight: 650 !important;
    }

    input, textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea,
    [data-baseweb="select"] input,
    [data-baseweb="base-input"] input {
        background: #ffffff !important;
        color: var(--td-ink) !important;
        -webkit-text-fill-color: var(--td-ink) !important;
        caret-color: var(--td-ink) !important;
        opacity: 1 !important;
    }

    input::placeholder, textarea::placeholder {
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
        opacity: 1 !important;
    }

    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div,
    [data-baseweb="select"] > div,
    [data-baseweb="base-input"],
    div[role="combobox"] {
        background: #ffffff !important;
        color: var(--td-ink) !important;
        border-color: var(--td-border) !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }

    [data-baseweb="input"] > div:focus-within,
    [data-baseweb="textarea"] > div:focus-within,
    [data-baseweb="select"] > div:focus-within,
    [data-baseweb="base-input"]:focus-within {
        border-color: var(--td-mint) !important;
        box-shadow: 0 0 0 3px rgba(0,184,148,.13) !important;
    }

    [data-baseweb="select"] *, [data-baseweb="popover"] *,
    div[role="listbox"] *, div[role="option"] * {
        color: var(--td-ink) !important;
    }

    [data-baseweb="popover"], div[role="listbox"] {
        background: #fff !important;
        border-color: var(--td-border) !important;
    }

    span[data-baseweb="tag"] {
        background: var(--td-mint-soft) !important;
        color: var(--td-ink) !important;
        border: 1px solid #c9f2e7 !important;
        border-radius: 999px !important;
    }

    span[data-baseweb="tag"] * {
        color: var(--td-ink) !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: #ffffff !important;
        color: var(--td-ink) !important;
        border: 1px dashed #cbd5e1 !important;
        border-radius: 12px !important;
    }

    [data-testid="stFileUploaderDropzone"] *,
    [data-testid="stFileUploader"] small {
        color: var(--td-muted) !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background: #fff !important;
        color: var(--td-ink) !important;
        border-color: var(--td-border) !important;
    }

    /* Buttons */
    .stButton > button[kind="primary"],
    [data-testid="stFormSubmitButton"] button,
    button[kind="primary"] {
        min-height: 46px;
        border: 1px solid var(--td-ink) !important;
        border-radius: 999px !important;
        background: var(--td-ink) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 18px rgba(17,24,39,.12) !important;
    }

    .stButton > button[kind="primary"] *,
    [data-testid="stFormSubmitButton"] button *,
    button[kind="primary"] * {
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] button:hover,
    button[kind="primary"]:hover {
        background: #263244 !important;
        border-color: #263244 !important;
        transform: translateY(-1px);
    }

    .stButton > button:not([kind="primary"]),
    [data-testid="stDownloadButton"] button,
    [data-testid="stLinkButton"] a {
        min-height: 41px;
        border: 1px solid var(--td-border) !important;
        border-radius: 999px !important;
        background: #ffffff !important;
        color: var(--td-ink) !important;
        font-weight: 650 !important;
        box-shadow: none !important;
    }

    .stButton > button:not([kind="primary"]) *,
    [data-testid="stDownloadButton"] button *,
    [data-testid="stLinkButton"] a * {
        color: var(--td-ink) !important;
    }

    .stButton > button:not([kind="primary"]):hover,
    [data-testid="stDownloadButton"] button:hover,
    [data-testid="stLinkButton"] a:hover {
        border-color: var(--td-ink) !important;
        background: var(--td-surface-muted) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] > div {
        background: #ffffff !important;
        border-right: 1px solid var(--td-border) !important;
    }

    section[data-testid="stSidebar"] * {
        color: var(--td-ink) !important;
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        min-height: 112px;
        padding: 1rem 1.05rem;
        background: #ffffff !important;
        border: 1px solid var(--td-border) !important;
        border-radius: 14px;
        box-shadow: none;
    }

    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: var(--td-subtle) !important;
        font-size: .82rem !important;
        font-weight: 650 !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--td-ink) !important;
        font-size: 2rem !important;
        font-weight: 750 !important;
        letter-spacing: -.04em;
    }

    /* Tabs */
    [data-baseweb="tab-list"] {
        gap: 1.15rem;
        border-bottom: 1px solid var(--td-border) !important;
    }

    button[data-baseweb="tab"] {
        color: var(--td-subtle) !important;
        font-weight: 650 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    button[data-baseweb="tab"] * {
        color: inherit !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--td-ink) !important;
    }

    [data-baseweb="tab-highlight"] {
        background: var(--td-mint) !important;
        height: 3px !important;
    }

    /* Alerts/status */
    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border-width: 1px !important;
    }

    [data-testid="stAlert"] * {
        color: var(--td-ink-soft) !important;
    }

    [data-testid="stStatusWidget"] {
        background: #ffffff !important;
        border: 1px solid var(--td-border) !important;
        border-radius: 12px !important;
    }

    [role="progressbar"] > div {
        background: var(--td-mint) !important;
    }

    /* Data and expanders */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--td-border);
        border-radius: 12px;
        overflow: hidden;
        background: #fff !important;
    }

    details[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid var(--td-border) !important;
        border-radius: 12px !important;
    }

    details[data-testid="stExpander"] summary,
    details[data-testid="stExpander"] summary * {
        color: var(--td-ink) !important;
        font-weight: 650 !important;
    }

    /* Custom result cards */
    .td-summary-card {
        padding: 1.35rem 1.45rem;
        margin: .8rem 0 1rem;
        background: #ffffff;
        border: 1px solid var(--td-border);
        border-left: 4px solid var(--td-mint);
        border-radius: 14px;
    }

    .td-summary-card p {
        margin: 0;
        color: var(--td-ink-soft) !important;
        font-size: 1rem;
        line-height: 1.7;
    }

    .td-list-card {
        min-height: 100%;
        padding: 1.2rem 1.3rem;
        background: #ffffff;
        border: 1px solid var(--td-border);
        border-radius: 14px;
    }

    .td-list-card h3 {
        margin: 0 0 .7rem;
        color: var(--td-ink) !important;
        font-size: 1.05rem;
    }

    .td-list-card ul {
        margin: 0;
        padding-left: 1.15rem;
    }

    .td-list-card li {
        margin: 0 0 .7rem;
        color: var(--td-ink-soft) !important;
        font-size: .92rem;
        line-height: 1.5;
    }

    .td-status {
        display: inline-flex;
        align-items: center;
        padding: .28rem .58rem;
        border-radius: 999px;
        font-size: .72rem;
        font-weight: 750;
        letter-spacing: .01em;
    }

    .td-status-supported { background: var(--td-mint-soft); color: var(--td-mint-dark) !important; }
    .td-status-partial { background: var(--td-amber-soft); color: var(--td-amber) !important; }
    .td-status-conflict { background: var(--td-red-soft); color: var(--td-red) !important; }
    .td-status-other { background: var(--td-blue-soft); color: var(--td-blue) !important; }

    .td-claim-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: .45rem;
    }

    .td-claim-category {
        color: var(--td-subtle) !important;
        font-size: .76rem;
        font-weight: 700;
        letter-spacing: .04em;
        text-transform: uppercase;
    }

    .td-evidence-quote {
        margin: .65rem 0;
        padding: .8rem .95rem;
        border-left: 3px solid #cbd5e1;
        background: var(--td-surface-muted);
        border-radius: 0 9px 9px 0;
        color: var(--td-ink-soft) !important;
        font-size: .9rem;
        line-height: 1.55;
    }

    .td-run-banner {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: .85rem 1rem;
        margin: .2rem 0 1rem;
        border: 1px solid #bfe9de;
        border-radius: 12px;
        background: var(--td-mint-soft);
    }

    .td-run-banner strong { color: var(--td-mint-dark) !important; }
    .td-run-banner span { color: var(--td-muted) !important; font-size: .85rem; }

    .td-step-list {
        counter-reset: steps;
        margin: .25rem 0 0;
        padding: 0;
        list-style: none;
    }

    .td-step-list li {
        position: relative;
        padding: .75rem 0 .75rem 2.5rem;
        color: var(--td-ink-soft) !important;
        border-bottom: 1px solid var(--td-border-soft);
    }

    .td-step-list li:last-child { border-bottom: 0; }
    .td-step-list li::before {
        counter-increment: steps;
        content: counter(steps);
        position: absolute;
        left: 0;
        top: .62rem;
        display: grid;
        place-items: center;
        width: 1.7rem;
        height: 1.7rem;
        border-radius: 999px;
        background: var(--td-ink);
        color: white;
        font-size: .72rem;
        font-weight: 750;
    }

    a { color: var(--td-mint-dark) !important; }

    @media (max-width: 800px) {
        .block-container { padding: 1rem .85rem 3rem; }
        .td-hero { padding: 1.6rem 1.25rem; }
        .td-how { grid-template-columns: 1fr; }
        .td-run-banner { align-items: flex-start; flex-direction: column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _secret_or_env(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return os.getenv(name, str(value) if value is not None else "")


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _safe(value: object) -> str:
    return html.escape(str(value or ""))


def _status_class(status: str) -> str:
    if status == "Supported":
        return "td-status-supported"
    if status == "Partially supported":
        return "td-status-partial"
    if status == "Conflicting evidence":
        return "td-status-conflict"
    return "td-status-other"


def _render_list_card(title: str, items: Iterable[str]) -> None:
    lines = "".join(f"<li>{_safe(item)}</li>" for item in items)
    st.markdown(
        f'<div class="td-list-card"><h3>{_safe(title)}</h3><ul>{lines}</ul></div>',
        unsafe_allow_html=True,
    )


def _category_summary(result: DiligenceOutput) -> pd.DataFrame:
    grouped: dict[str, list[EvidenceClaim]] = defaultdict(list)
    for claim in result.claims:
        grouped[claim.category].append(claim)
    rows = []
    for category, claims in sorted(grouped.items()):
        count = len(claims)
        supported = sum(c.validation_status == "Supported" for c in claims)
        rows.append(
            {
                "Category": category,
                "Claims": count,
                "Supported": supported,
                "Support rate": supported / count if count else 0.0,
                "Avg. confidence": sum(c.confidence_score for c in claims) / count if count else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _render_claim_card(claim: EvidenceClaim, index: int) -> None:
    status_class = _status_class(claim.validation_status)
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="td-claim-head">
                <span class="td-claim-category">{_safe(claim.category)} · Claim {index}</span>
                <span class="td-status {status_class}">{_safe(claim.validation_status)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(f"#### {_safe(claim.claim)}", unsafe_allow_html=True)
        st.markdown(
            f'<div class="td-evidence-quote">“{_safe(claim.evidence_excerpt or "No evidence excerpt supplied.")}”</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([1.6, 1, 1])
        c1.markdown(f"**Source**  \n{_safe(claim.source_title or 'Not supplied')}")
        c2.markdown(f"**Confidence**  \n{claim.confidence_score:.0%}")
        c3.markdown(f"**Published**  \n{_safe(claim.publication_date or 'Not supplied')}")
        if claim.analyst_note:
            st.caption(f"Analyst note: {claim.analyst_note}")
        if claim.source_url and claim.source_url.startswith(("http://", "https://")):
            st.link_button("Open cited source", claim.source_url)


PRESETS = {
    "Acquisition screening": {
        "objective": "Assess revenue quality, market position, customer concentration, scalability, and key acquisition risks.",
        "categories": [
            "Business model",
            "Financial performance",
            "Revenue quality",
            "Customers",
            "Market",
            "Competitive position",
            "Strategic risks",
        ],
    },
    "Competitive intelligence": {
        "objective": "Evaluate the company's positioning, product differentiation, pricing, target customers, and competitive vulnerabilities.",
        "categories": ["Business model", "Customers", "Market", "Competitive position", "Operations", "Strategic risks"],
    },
    "Investment memo": {
        "objective": "Develop a source-grounded investment view covering growth, economics, market attractiveness, catalysts, and downside risks.",
        "categories": [
            "Business model",
            "Financial performance",
            "Revenue quality",
            "Customers",
            "Market",
            "Competitive position",
            "Strategic risks",
        ],
    },
    "Partnership assessment": {
        "objective": "Assess strategic fit, customer overlap, implementation requirements, commercial potential, and partnership risks.",
        "categories": ["Business model", "Customers", "Market", "Competitive position", "Operations", "Strategic risks"],
    },
    "Custom": {
        "objective": "",
        "categories": ["Business model", "Financial performance", "Market", "Strategic risks"],
    },
}

ALL_CATEGORIES = [
    "Business model",
    "Financial performance",
    "Revenue quality",
    "Customers",
    "Market",
    "Competitive position",
    "Operations",
    "Strategic risks",
]


# -----------------------------------------------------------------------------
# Header and onboarding
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="td-shell">
      <div class="td-hero">
        <span class="td-eyebrow"><span class="td-dot"></span> Source-grounded AI diligence</span>
        <h1>TraceDiligence</h1>
        <p>Turn a company, research objective, and optional documents into an auditable first-pass diligence brief with claim-level evidence, confidence scores, and a clear human-review queue.</p>
      </div>
      <div class="td-how">
        <div class="td-how-card"><span class="td-how-number">1</span><strong>Define the question</strong><span>Choose a research preset, company, objective, and the areas you want examined.</span></div>
        <div class="td-how-card"><span class="td-how-number">2</span><strong>Collect and validate</strong><span>The workflow gathers evidence, maps claims to sources, and flags weak or conflicting support.</span></div>
        <div class="td-how-card"><span class="td-how-number">3</span><strong>Review and export</strong><span>Inspect the evidence queue, resolve open questions, and download the brief and ledger.</span></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("How to use TraceDiligence", expanded=False):
    st.markdown(
        """
        <ol class="td-step-list">
          <li><strong>Start with Demo mode.</strong> It uses fictional data, costs nothing, and lets you inspect every output screen.</li>
          <li><strong>Choose a research preset.</strong> Acquisition screening is the best default for evaluating a company broadly.</li>
          <li><strong>Write a specific objective.</strong> State the decision you are trying to make and the risks that matter most.</li>
          <li><strong>Add documents only when authorized.</strong> Uploaded files supplement public research; do not place confidential data in a public app.</li>
          <li><strong>Review every non-green claim.</strong> “Partially supported,” “Conflicting evidence,” and “Insufficient evidence” require analyst judgment.</li>
          <li><strong>Export only after review.</strong> Download the brief, evidence ledger, or JSON after checking the cited source material.</li>
        </ol>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "TraceDiligence is a research accelerator, not legal, financial, tax, technical, or confirmatory diligence."
    )


# -----------------------------------------------------------------------------
# Run configuration
# -----------------------------------------------------------------------------
enable_live_mode = _truthy(_secret_or_env("ENABLE_LIVE_MODE", "false"))
configured_access_code = _secret_or_env("APP_ACCESS_CODE", "").strip()
available_modes = ["Demo"] + (["Live research"] if enable_live_mode else [])

if st.session_state.get("mode_selector") not in available_modes:
    st.session_state["mode_selector"] = "Demo"
if st.session_state.get("preset_selector") not in PRESETS:
    st.session_state["preset_selector"] = "Acquisition screening"


def _apply_mode_defaults() -> None:
    selected_mode = st.session_state.get("mode_selector", "Demo")
    selected_preset = st.session_state.get("preset_selector", "Acquisition screening")
    if selected_mode == "Demo":
        st.session_state["company_input"] = "NeuroVista Health (fictional)"
        st.session_state["objective_input"] = "Assess revenue quality, market position, and key risks."
    else:
        if st.session_state.get("company_input", "").startswith("NeuroVista Health"):
            st.session_state["company_input"] = ""
        st.session_state["objective_input"] = PRESETS[selected_preset]["objective"]
    st.session_state["categories_input"] = PRESETS[selected_preset]["categories"]


def _apply_preset() -> None:
    selected_preset = st.session_state.get("preset_selector", "Acquisition screening")
    if st.session_state.get("mode_selector", "Demo") == "Demo":
        st.session_state["objective_input"] = "Assess revenue quality, market position, and key risks."
    else:
        st.session_state["objective_input"] = PRESETS[selected_preset]["objective"]
    st.session_state["categories_input"] = PRESETS[selected_preset]["categories"]


if "company_input" not in st.session_state:
    st.session_state["company_input"] = "NeuroVista Health (fictional)"
if "objective_input" not in st.session_state:
    st.session_state["objective_input"] = "Assess revenue quality, market position, and key risks."
if "categories_input" not in st.session_state:
    st.session_state["categories_input"] = PRESETS["Acquisition screening"]["categories"]

st.markdown('<h2 class="td-section-heading">Start a diligence run</h2>', unsafe_allow_html=True)
st.markdown(
    '<p class="td-section-copy">Use the fictional demo first. Enable Live research only after adding protected API credentials in Streamlit secrets.</p>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    top1, top2 = st.columns([1, 1])
    with top1:
        st.segmented_control(
            "Research mode",
            available_modes,
            key="mode_selector",
            on_change=_apply_mode_defaults,
            help="Demo uses a fictional dataset. Live research uses your OpenAI API key and may incur API charges.",
        )
    with top2:
        st.selectbox(
            "Research preset",
            list(PRESETS),
            key="preset_selector",
            on_change=_apply_preset,
            help="Selecting a preset updates the objective and recommended diligence categories.",
        )

    mode = st.session_state["mode_selector"]
    preset = st.session_state["preset_selector"]

    if not enable_live_mode:
        st.caption("Live research is disabled in this public deployment to protect API usage.")

    with st.form("research_form", clear_on_submit=False):
        col1, col2 = st.columns([.8, 1.2])
        with col1:
            company = st.text_input(
                "Company name",
                key="company_input",
                placeholder="Example: Adobe",
                help="Use the legal or commonly recognized company name.",
            )
        with col2:
            objective = st.text_area(
                "Research objective",
                key="objective_input",
                placeholder="Example: Evaluate revenue durability, customer concentration, and acquisition risks.",
                height=96,
                help="Describe the decision you are supporting and the issues that matter most.",
            )

        categories = st.multiselect(
            "Diligence categories",
            ALL_CATEGORIES,
            key="categories_input",
            help="Select only the categories relevant to the decision. More categories usually produce a broader, less focused brief.",
        )

        uploaded_files = st.file_uploader(
            "Supporting documents (optional)",
            type=["pdf", "docx", "txt", "md", "csv"],
            accept_multiple_files=True,
            disabled=mode == "Demo",
            help="Text is extracted locally and added to the research context. Avoid confidential documents in public deployments.",
        )

        access_code = ""
        if mode == "Live research" and configured_access_code:
            access_code = st.text_input(
                "Live-mode access code",
                type="password",
                help="Required to prevent public visitors from using your API credits.",
            )

        submitted = st.form_submit_button("Run diligence", type="primary", width="stretch")

with st.sidebar:
    st.header("Advanced settings")
    st.caption("These controls apply only to Live research.")
    default_model = "gpt-5"
    model = st.text_input("OpenAI model", value=default_model, disabled=mode == "Demo")
    max_sources = st.slider("Target source count", 6, 20, 12, disabled=mode == "Demo")
    st.divider()
    st.markdown("**Recommended workflow**")
    st.caption("Demo → private live test → claim review → public export")


if submitted:
    if not company.strip() or not objective.strip() or not categories:
        st.error("Enter a company name, a research objective, and at least one diligence category.")
    elif mode == "Demo":
        sources = load_demo_sources()
        result = validate_output(load_demo_output(company.strip(), objective.strip()), sources)
        st.session_state["result"] = result
        st.session_state["sources"] = sources
        st.session_state["research_text"] = "Fictional demonstration research record."
        st.session_state["run_mode"] = "Demo"
        st.session_state["run_categories"] = categories
        st.toast("Demo diligence complete", icon="✅")
    else:
        api_key = _secret_or_env("OPENAI_API_KEY", "").strip()
        if configured_access_code and access_code != configured_access_code:
            st.error("The live-mode access code is incorrect.")
        elif not api_key:
            st.error("Add OPENAI_API_KEY to Streamlit secrets before running Live research.")
        else:
            with st.status("Running the diligence workflow...", expanded=True) as status:
                try:
                    st.write("1 of 3 · Extracting uploaded documents")
                    uploaded_text, uploaded_sources = extract_uploaded_files(uploaded_files)
                    st.write("2 of 3 · Collecting and structuring public evidence")
                    result, sources, research_text = run_diligence(
                        company=company.strip(),
                        objective=objective.strip(),
                        categories=categories,
                        api_key=api_key,
                        model=model.strip() or default_model,
                        max_sources=max_sources,
                        uploaded_text=uploaded_text,
                        uploaded_sources=uploaded_sources,
                    )
                    st.write("3 of 3 · Applying claim-level validation rules")
                    st.session_state["result"] = result
                    st.session_state["sources"] = sources
                    st.session_state["research_text"] = research_text
                    st.session_state["run_mode"] = "Live research"
                    st.session_state["run_categories"] = categories
                    status.update(label="Diligence analysis complete", state="complete", expanded=False)
                except Exception as exc:
                    status.update(label="Research failed", state="error", expanded=True)
                    st.exception(exc)


# -----------------------------------------------------------------------------
# Results workspace
# -----------------------------------------------------------------------------
result: DiligenceOutput | None = st.session_state.get("result")
sources: list[SourceRecord] = st.session_state.get("sources", [])
run_mode = st.session_state.get("run_mode", "")

if not result:
    st.info("Run the fictional demo above to explore the complete application without an API key.")
    st.stop()

metrics = calculate_audit_metrics(result)
banner_col, reset_col = st.columns([5, 1])
with banner_col:
    st.markdown(
        f"""
        <div class="td-run-banner">
          <div><strong>{_safe(run_mode)} results ready</strong><br><span>{'Fictional demonstration data — not real company research.' if run_mode == 'Demo' else 'Review every material claim before external use.'}</span></div>
          <span>{metrics['supported_claims']} of {metrics['total_claims']} claims fully supported</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with reset_col:
    if st.button("New analysis", width="stretch"):
        for key in ["result", "sources", "research_text", "run_mode", "run_categories"]:
            st.session_state.pop(key, None)
        st.rerun()

metric_cols = st.columns(5)
metric_cols[0].metric("Claims reviewed", metrics["total_claims"])
metric_cols[1].metric("Fully supported", metrics["supported_claims"])
metric_cols[2].metric("Needs review", metrics["review_claims"])
metric_cols[3].metric("Unique sources", metrics["unique_sources"])
metric_cols[4].metric("Avg. confidence", f"{metrics['average_confidence']:.0%}")

summary_tab, ledger_tab, sources_tab, methodology_tab, export_tab = st.tabs(
    ["Executive brief", "Evidence review", "Source library", "Methodology", "Export"]
)

with summary_tab:
    st.markdown(f"## {_safe(result.company)}", unsafe_allow_html=True)
    st.caption(result.objective)
    st.progress(metrics["support_rate"], text=f"Evidence support rate: {metrics['support_rate']:.0%}")
    st.markdown(
        f'<div class="td-summary-card"><p>{_safe(result.executive_summary)}</p></div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        _render_list_card("Key risks", result.key_risks)
    with right:
        _render_list_card("Open diligence questions", result.open_questions)

    st.markdown("### Coverage by category")
    category_df = _category_summary(result)
    st.dataframe(
        category_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Support rate": st.column_config.ProgressColumn(
                "Support rate", min_value=0.0, max_value=1.0, format="percent"
            ),
            "Avg. confidence": st.column_config.ProgressColumn(
                "Avg. confidence", min_value=0.0, max_value=1.0, format="percent"
            ),
        },
    )

    with st.expander("Recommended analyst review sequence", expanded=True):
        st.markdown(
            """
            1. Open every claim marked **Conflicting evidence** or **Insufficient evidence**.  
            2. Verify numerical claims against the original source and confirm period, currency, and unit.  
            3. Resolve the open diligence questions through management, data-room, or customer evidence.  
            4. Re-run or edit the final brief only after weak claims are qualified or removed.  
            5. Preserve the evidence ledger with the exported report for auditability.
            """
        )

with ledger_tab:
    dataframe = claims_dataframe(result)
    f1, f2, f3 = st.columns([1.1, 1.1, .7])
    with f1:
        status_options = sorted(dataframe["Status"].unique().tolist())
        status_filter = st.multiselect("Validation status", status_options, default=status_options)
    with f2:
        category_options = sorted(dataframe["Category"].unique().tolist())
        category_filter = st.multiselect("Category", category_options, default=category_options)
    with f3:
        view_mode = st.selectbox("View", ["Review cards", "Audit table"])

    filtered_claims = [
        claim
        for claim in result.claims
        if claim.validation_status in status_filter and claim.category in category_filter
    ]
    st.caption(f"Showing {len(filtered_claims)} of {len(result.claims)} claims.")

    if view_mode == "Review cards":
        if not filtered_claims:
            st.info("No claims match the selected filters.")
        for idx, claim in enumerate(filtered_claims, start=1):
            _render_claim_card(claim, idx)
    else:
        filtered = dataframe[
            dataframe["Status"].isin(status_filter) & dataframe["Category"].isin(category_filter)
        ]
        st.dataframe(
            filtered,
            width="stretch",
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn("URL", display_text="Open source"),
                "Confidence": st.column_config.ProgressColumn(
                    "Confidence", min_value=0.0, max_value=1.0, format="percent"
                ),
            },
        )
    st.warning("Any claim not marked Supported should be qualified, investigated, or removed before external use.")

with sources_tab:
    if not sources:
        st.info("No source records were captured.")
    else:
        st.markdown("### Source-quality overview")
        reliable = sum(source.reliability_score >= .75 for source in sources)
        s1, s2, s3 = st.columns(3)
        s1.metric("Sources captured", len(sources))
        s2.metric("High-reliability sources", reliable)
        s3.metric("Average reliability", f"{sum(s.reliability_score for s in sources) / len(sources):.0%}")
        for idx, source in enumerate(sources, start=1):
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"#### {idx}. {_safe(source.title)}", unsafe_allow_html=True)
                    st.caption(
                        f"Type: {source.source_type.replace('_', ' ').title()} · Published: {source.publication_date or 'Not supplied'}"
                    )
                with c2:
                    st.metric("Reliability", f"{source.reliability_score:.0%}")
                if source.url.startswith(("http://", "https://")):
                    st.link_button("Open source", source.url)

with methodology_tab:
    st.markdown("### What the workflow does")
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(
            """
            **Automated steps**
            - Collects public and uploaded-document evidence
            - Structures findings into claim-level records
            - Records source, excerpt, date, and confidence
            - Applies deterministic validation rules
            - Flags unsupported and contradictory claims
            """
        )
    with m2:
        st.markdown(
            """
            **Human responsibilities**
            - Confirm original-source accuracy
            - Reconcile numerical definitions and periods
            - Obtain private or missing diligence evidence
            - Decide whether a conclusion is material
            - Approve the final external report
            """
        )

    with st.expander("Methodology note and limitations", expanded=True):
        st.write(result.methodology_note)

    st.markdown("### Benchmark your actual efficiency")
    st.caption("Use a controlled manual-versus-assisted test before publishing performance claims on your resume.")
    c1, c2 = st.columns(2)
    with c1:
        manual_minutes = st.number_input("Manual review time (minutes)", min_value=0.0, value=100.0, step=5.0)
        manual_sources = st.number_input("Qualifying sources found manually", min_value=0, value=9, step=1)
        reviewed_claims = st.number_input("Claims manually checked", min_value=0, value=20, step=1)
    with c2:
        ai_minutes = st.number_input("AI-assisted review time (minutes)", min_value=0.0, value=65.0, step=5.0)
        ai_sources = st.number_input("Qualifying sources found with workflow", min_value=0, value=18, step=1)
        correct_citations = st.number_input("Correctly supported citations", min_value=0, value=18, step=1)
    benchmark = calculate_benchmark(
        manual_minutes,
        ai_minutes,
        int(manual_sources),
        int(ai_sources),
        int(reviewed_claims),
        int(correct_citations),
    )
    b1, b2, b3 = st.columns(3)
    b1.metric("Time reduction", f"{benchmark['time_reduction']:.1%}")
    b2.metric("Source coverage", f"{benchmark['coverage_multiplier']:.2f}×")
    b3.metric("Citation accuracy", f"{benchmark['citation_accuracy']:.1%}")
    st.info("Preserve the test inputs, timing method, reviewed outputs, and claim-level audit before using these results publicly.")

with export_tab:
    markdown_report = render_markdown_report(result, sources)
    json_report = render_json(result, sources)
    csv_bytes = claims_dataframe(result).to_csv(index=False).encode("utf-8")
    file_stub = "".join(ch.lower() if ch.isalnum() else "-" for ch in result.company).strip("-") or "company"

    st.markdown("### Download the reviewed work product")
    st.caption("Markdown is best for reading, CSV for claim review, and JSON for reuse in another workflow.")
    col_a, col_b, col_c = st.columns(3)
    col_a.download_button(
        "Download diligence brief",
        data=markdown_report,
        file_name=f"{file_stub}-diligence-report.md",
        mime="text/markdown",
        width="stretch",
    )
    col_b.download_button(
        "Download evidence ledger",
        data=csv_bytes,
        file_name=f"{file_stub}-evidence-ledger.csv",
        mime="text/csv",
        width="stretch",
    )
    col_c.download_button(
        "Download full JSON",
        data=json_report,
        file_name=f"{file_stub}-full-output.json",
        mime="application/json",
        width="stretch",
    )

    with st.expander("Preview the Markdown report"):
        st.code(markdown_report, language="markdown")
