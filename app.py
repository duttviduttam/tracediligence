from __future__ import annotations

import os

import streamlit as st

from tracediligence.demo import load_demo_output, load_demo_sources
from tracediligence.file_ingest import extract_uploaded_files
from tracediligence.reporting import claims_dataframe, render_json, render_markdown_report
from tracediligence.research import run_diligence
from tracediligence.validation import calculate_audit_metrics, calculate_benchmark, validate_output


st.set_page_config(
    page_title="TraceDiligence",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --td-primary: #0a0a0a;
        --td-on-primary: #ffffff;
        --td-mint: #00d4a4;
        --td-mint-deep: #00b48a;
        --td-mint-soft: #e8fbf6;
        --td-canvas: #ffffff;
        --td-surface: #f7f7f7;
        --td-surface-soft: #fafafa;
        --td-hairline: #e5e5e5;
        --td-hairline-soft: #ededed;
        --td-ink: #0a0a0a;
        --td-slate: #3a3a3c;
        --td-steel: #5a5a5c;
        --td-muted: #888888;
        --td-error: #d45656;
        --td-warning: #c37d0d;
        --td-tag: #3772cf;
    }

    html, body, [class*="css"] {
        color: var(--td-ink);
    }

    .stApp {
        background: var(--td-canvas);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    section[data-testid="stSidebar"] {
        background: var(--td-surface-soft);
        border-right: 1px solid var(--td-hairline);
    }

    section[data-testid="stSidebar"] > div {
        background: var(--td-surface-soft);
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.1rem;
        border: 1px solid var(--td-hairline-soft);
        border-radius: 12px;
        margin-bottom: 1.4rem;
        background: linear-gradient(120deg, #f5e9d8 0%, #ffffff 46%, #dff8f1 100%);
        box-shadow: rgba(0, 0, 0, 0.04) 0 4px 12px;
    }

    .hero::after {
        content: "";
        position: absolute;
        width: 210px;
        height: 210px;
        right: -65px;
        top: -85px;
        border-radius: 9999px;
        background: rgba(0, 212, 164, 0.18);
        filter: blur(1px);
    }

    .hero h1 {
        position: relative;
        z-index: 1;
        margin: 0 0 .35rem 0;
        font-size: 2.45rem;
        font-weight: 600;
        letter-spacing: -0.04em;
        color: var(--td-ink);
    }

    .hero p {
        position: relative;
        z-index: 1;
        margin: 0;
        max-width: 880px;
        font-size: 1.02rem;
        line-height: 1.55;
        color: var(--td-steel);
    }

    .small-note {
        font-size: .85rem;
        color: var(--td-muted);
    }

    div[data-testid="stMetric"] {
        background: var(--td-canvas);
        border: 1px solid var(--td-hairline);
        padding: .9rem 1rem;
        border-radius: 12px;
        box-shadow: none;
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: var(--td-steel);
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--td-ink);
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    /* Primary actions: Mintlify-style black pills. */
    button[kind="primary"],
    div[data-testid="stFormSubmitButton"] button {
        background: var(--td-primary) !important;
        color: var(--td-on-primary) !important;
        border: 1px solid var(--td-primary) !important;
        border-radius: 9999px !important;
        min-height: 42px;
        font-weight: 500;
        box-shadow: none !important;
    }

    button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] button:hover {
        background: #1c1c1e !important;
        border-color: #1c1c1e !important;
    }

    button[kind="primary"]:focus,
    div[data-testid="stFormSubmitButton"] button:focus {
        box-shadow: 0 0 0 3px rgba(0, 212, 164, 0.22) !important;
    }

    /* Secondary and download actions. */
    div[data-testid="stDownloadButton"] button,
    .stButton > button:not([kind="primary"]) {
        background: var(--td-canvas) !important;
        color: var(--td-ink) !important;
        border: 1px solid var(--td-hairline) !important;
        border-radius: 9999px !important;
        min-height: 40px;
        font-weight: 500;
        box-shadow: none !important;
    }

    div[data-testid="stDownloadButton"] button:hover,
    .stButton > button:not([kind="primary"]):hover {
        border-color: var(--td-primary) !important;
        color: var(--td-primary) !important;
    }

    /* Inputs and selectors. */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] {
        background: var(--td-canvas) !important;
        border-color: var(--td-hairline) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }

    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--td-mint) !important;
        box-shadow: 0 0 0 1px var(--td-mint) !important;
    }

    span[data-baseweb="tag"] {
        background: var(--td-mint-soft) !important;
        color: var(--td-primary) !important;
        border-radius: 9999px !important;
    }

    div[data-testid="stFileUploaderDropzone"] {
        background: var(--td-surface-soft);
        border: 1px dashed var(--td-hairline);
        border-radius: 12px;
    }

    /* Tabs use a restrained black active underline. */
    div[data-baseweb="tab-list"] {
        gap: .25rem;
        border-bottom: 1px solid var(--td-hairline);
    }

    button[data-baseweb="tab"] {
        color: var(--td-steel) !important;
        font-weight: 500;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--td-ink) !important;
    }

    div[data-baseweb="tab-highlight"] {
        background-color: var(--td-ink) !important;
    }

    /* Expanders, data surfaces and code. */
    details[data-testid="stExpander"] {
        border: 1px solid var(--td-hairline) !important;
        border-radius: 12px !important;
        background: var(--td-canvas);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--td-hairline);
        border-radius: 12px;
        overflow: hidden;
    }

    code, pre, .stCodeBlock {
        border-radius: 8px !important;
    }

    /* Alerts use the same neutral palette with restrained semantic accents. */
    div[data-testid="stAlert"] {
        border-radius: 12px;
        border-width: 1px;
    }

    div[data-testid="stStatusWidget"] {
        border: 1px solid var(--td-hairline);
        border-radius: 12px;
    }

    div[role="progressbar"] > div {
        background-color: var(--td-mint) !important;
    }

    a {
        color: var(--td-mint-deep);
    }

    hr {
        border-color: var(--td-hairline-soft) !important;
    }

    @media (max-width: 768px) {
        .block-container {padding-top: 1rem;}
        .hero {padding: 1.4rem 1.25rem;}
        .hero h1 {font-size: 2rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>TraceDiligence</h1>
      <p>Source-grounded AI research with a claim-level evidence ledger, deterministic validation, and exportable diligence briefs.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

def _secret_or_env(name: str, default=""):
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return os.getenv(name, str(value) if value is not None else "")


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


enable_live_mode = _truthy(_secret_or_env("ENABLE_LIVE_MODE", "false"))
configured_access_code = _secret_or_env("APP_ACCESS_CODE", "").strip()

with st.sidebar:
    st.header("Run settings")
    available_modes = ["Demo"] + (["Live research"] if enable_live_mode else [])
    mode = st.radio(
        "Mode",
        available_modes,
        help=(
            "Demo uses fictional data. Live research appears only when ENABLE_LIVE_MODE is set "
            "and requires an OpenAI API key."
        ),
    )
    if not enable_live_mode:
        st.info("Public demo mode is enabled. Live research is disabled to protect API usage.")
    default_model = "gpt-5"
    model = st.text_input("OpenAI model", value=default_model, disabled=mode == "Demo")
    max_sources = st.slider("Target source count", 6, 20, 12, disabled=mode == "Demo")
    st.divider()
    st.caption(
        "This app does not replace analyst review. Verify every material claim against the original source before external use."
    )

with st.form("research_form"):
    col1, col2 = st.columns([1, 1])
    with col1:
        company = st.text_input(
            "Company",
            value="NeuroVista Health (fictional demo)" if mode == "Demo" else "",
            placeholder="Example: Adobe",
        )
    with col2:
        objective = st.text_input(
            "Research objective",
            value="Assess revenue quality, market position, and key risks." if mode == "Demo" else "",
            placeholder="Example: Evaluate revenue durability and acquisition risks",
        )

    categories = st.multiselect(
        "Diligence categories",
        [
            "Business model",
            "Financial performance",
            "Revenue quality",
            "Customers",
            "Market",
            "Competitive position",
            "Operations",
            "Strategic risks",
        ],
        default=[
            "Business model",
            "Financial performance",
            "Revenue quality",
            "Customers",
            "Market",
            "Competitive position",
            "Strategic risks",
        ],
    )
    uploaded_files = st.file_uploader(
        "Optional supporting documents",
        type=["pdf", "docx", "txt", "md", "csv"],
        accept_multiple_files=True,
        disabled=mode == "Demo",
        help="Text is extracted locally and included in the research prompt. Avoid confidential material in a public deployment.",
    )
    access_code = ""
    if mode == "Live research" and configured_access_code:
        access_code = st.text_input(
            "Live-mode access code",
            type="password",
            help="This prevents public visitors from consuming your API credits.",
        )
    submitted = st.form_submit_button("Run diligence", type="primary", use_container_width=True)

if submitted:
    if not company.strip() or not objective.strip() or not categories:
        st.error("Enter a company, objective, and at least one diligence category.")
    elif mode == "Demo":
        sources = load_demo_sources()
        result = validate_output(load_demo_output(company, objective), sources)
        st.session_state["result"] = result
        st.session_state["sources"] = sources
        st.session_state["research_text"] = "Fictional demonstration research record."
        st.success("Fictional demonstration analysis created.")
    else:
        api_key = _secret_or_env("OPENAI_API_KEY", "").strip()
        if configured_access_code and access_code != configured_access_code:
            st.error("The live-mode access code is incorrect.")
        elif not api_key:
            st.error("Add OPENAI_API_KEY to Streamlit secrets or your environment before running live research.")
        else:
            with st.status("Researching and validating sources...", expanded=True) as status:
                try:
                    st.write("Extracting uploaded documents")
                    uploaded_text, uploaded_sources = extract_uploaded_files(uploaded_files)
                    st.write("Collecting current public sources")
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
                    st.write("Applying claim-level validation rules")
                    st.session_state["result"] = result
                    st.session_state["sources"] = sources
                    st.session_state["research_text"] = research_text
                    status.update(label="Diligence analysis complete", state="complete", expanded=False)
                except Exception as exc:
                    status.update(label="Research failed", state="error", expanded=True)
                    st.exception(exc)

result = st.session_state.get("result")
sources = st.session_state.get("sources", [])

if result:
    metrics = calculate_audit_metrics(result)
    metric_cols = st.columns(5)
    metric_cols[0].metric("Claims", metrics["total_claims"])
    metric_cols[1].metric("Fully supported", metrics["supported_claims"])
    metric_cols[2].metric("Needs review", metrics["review_claims"])
    metric_cols[3].metric("Unique sources", metrics["unique_sources"])
    metric_cols[4].metric("Avg. confidence", f"{metrics['average_confidence']:.0%}")

    summary_tab, ledger_tab, sources_tab, export_tab, benchmark_tab = st.tabs(
        ["Executive brief", "Evidence ledger", "Source library", "Export", "Benchmark"]
    )

    with summary_tab:
        st.subheader(result.company)
        st.caption(result.objective)
        st.write(result.executive_summary)
        left, right = st.columns(2)
        with left:
            st.markdown("### Key risks")
            for risk in result.key_risks:
                st.markdown(f"- {risk}")
        with right:
            st.markdown("### Open diligence questions")
            for question in result.open_questions:
                st.markdown(f"- {question}")
        with st.expander("Methodology and limitations"):
            st.write(result.methodology_note)

    with ledger_tab:
        dataframe = claims_dataframe(result)
        status_filter = st.multiselect(
            "Filter by validation status",
            sorted(dataframe["Status"].unique().tolist()),
            default=sorted(dataframe["Status"].unique().tolist()),
        )
        filtered = dataframe[dataframe["Status"].isin(status_filter)] if status_filter else dataframe.iloc[0:0]
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn("URL", display_text="Open source"),
                "Confidence": st.column_config.ProgressColumn(
                    "Confidence", min_value=0.0, max_value=1.0, format="percent"
                ),
            },
        )
        st.caption("Claims not marked Supported should be reviewed, qualified, or removed before external use.")

    with sources_tab:
        if not sources:
            st.info("No source records were captured.")
        else:
            source_rows = [
                {
                    "Title": source.title,
                    "URL": source.url,
                    "Type": source.source_type,
                    "Publication date": source.publication_date or "",
                    "Reliability": source.reliability_score,
                }
                for source in sources
            ]
            import pandas as pd

            st.dataframe(
                pd.DataFrame(source_rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("URL", display_text="Open source"),
                    "Reliability": st.column_config.ProgressColumn(
                        "Reliability", min_value=0.0, max_value=1.0, format="percent"
                    ),
                },
            )

    with export_tab:
        markdown_report = render_markdown_report(result, sources)
        json_report = render_json(result, sources)
        csv_bytes = claims_dataframe(result).to_csv(index=False).encode("utf-8")
        file_stub = "".join(ch.lower() if ch.isalnum() else "-" for ch in result.company).strip("-") or "company"
        col_a, col_b, col_c = st.columns(3)
        col_a.download_button(
            "Download diligence brief",
            data=markdown_report,
            file_name=f"{file_stub}-diligence-report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        col_b.download_button(
            "Download evidence ledger",
            data=csv_bytes,
            file_name=f"{file_stub}-evidence-ledger.csv",
            mime="text/csv",
            use_container_width=True,
        )
        col_c.download_button(
            "Download full JSON",
            data=json_report,
            file_name=f"{file_stub}-full-output.json",
            mime="application/json",
            use_container_width=True,
        )
        st.markdown("### Report preview")
        st.code(markdown_report, language="markdown")

    with benchmark_tab:
        st.markdown("### Validate the resume impact claims")
        st.write(
            "Run the same assignment manually and through TraceDiligence, then record the actual results here."
        )
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
        st.warning(
            "Use these figures publicly only after you have preserved the test inputs, timing method, and reviewed outputs."
        )
else:
    st.info("Run the fictional demo to explore the full application without an API key.")
    with st.expander("Workflow architecture"):
        st.markdown(
            """
            1. **Research:** Collect current public sources and optional uploaded-document evidence.  
            2. **Structure:** Convert the research record into a consistent claim-level schema.  
            3. **Validate:** Check URL provenance, evidence length, confidence, and source reliability.  
            4. **Review:** Surface unsupported, conflicting, or inferred claims for human judgment.  
            5. **Export:** Produce an evidence ledger, Markdown brief, and structured JSON output.
            """
        )
