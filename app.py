import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
    * { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Syne', sans-serif !important; }
    .block-container { padding: 2rem 3rem; max-width: 1200px; }

    .hero {
        background: linear-gradient(135deg, #0a0f1a 0%, #0f1525 50%, #0a1520 100%);
        border: 1px solid #1a2a3e;
        border-radius: 16px;
        padding: 2.5rem;
        margin-bottom: 2rem;
    }
    .hero-title { font-family: 'Syne', sans-serif !important; font-size: 2.4rem; font-weight: 800; color: #f0f0f8; margin: 0 0 0.5rem 0; }
    .hero-sub { font-size: 1rem; color: #6688aa; margin: 0; font-weight: 300; }

    .agent-pipeline {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 1.5rem 0;
        flex-wrap: wrap;
    }
    .agent-node {
        background: #0f1a2a;
        border: 1px solid #1a3a5a;
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 500;
        color: #4488cc;
    }
    .agent-arrow { color: #2a4a6a; font-size: 16px; }
    .agent-parallel {
        background: #0a2a0a;
        border: 1px solid #1a5a1a;
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 500;
        color: #44cc88;
    }

    .result-section { background: #0a0f1a; border: 1px solid #1a2a3e; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
    .result-title { font-family: 'Syne', sans-serif; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem; color: #4488cc; }

    .subtopic-card {
        background: #0a1520;
        border: 1px solid #1a3a5a;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
    }
    .subtopic-title { font-family: 'Syne', sans-serif; font-weight: 600; font-size: 14px; color: #88bbdd; margin-bottom: 0.5rem; }
    .subtopic-content { font-size: 13px; color: #8899aa; line-height: 1.6; }

    .score-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 14px;
    }

    .hitl-box { background: #0a1a0a; border: 1px solid #1a5a2a; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; }
    .hitl-title { font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700; color: #44ee88; margin-bottom: 0.5rem; }
    .hitl-sub { font-size: 0.85rem; color: #446644; margin-bottom: 1rem; }

    .report-box { background: #080c14; border: 1px solid #1a2a3e; border-radius: 10px; padding: 1.5rem; font-size: 0.9rem; line-height: 1.8; color: #c0ccd8; }

    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #1a4a8a, #1a7a5a);
        color: white; border: none; border-radius: 8px;
        font-family: 'Syne', sans-serif; font-weight: 600;
        padding: 0.6rem 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Hero 

st.markdown("""
<div class="hero">
    <div class="hero-title">🔬 Multi-Agent Research Assistant</div>
    <p class="hero-sub">Enter any topic · Parallel agents research simultaneously · Review findings · Get a structured report</p>
    <div class="agent-pipeline">
        <div class="agent-node">📋 Planner</div>
        <div class="agent-arrow">→</div>
        <div class="agent-parallel">⚡ Search Agent 1</div>
        <div class="agent-parallel">⚡ Search Agent 2</div>
        <div class="agent-parallel">⚡ Search Agent 3</div>
        <div class="agent-arrow">→</div>
        <div class="agent-node">🔬 Critic</div>
        <div class="agent-arrow">→</div>
        <div class="agent-node">✋ You Review</div>
        <div class="agent-arrow">→</div>
        <div class="agent-node">✍️ Writer</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Step 1: Input 

if "pending_session" not in st.session_state and "final_result" not in st.session_state:

    st.markdown("#### 🔍 What do you want to research?")
    topic = st.text_input(
        "Research topic",
        placeholder="e.g. The future of AI agents, Climate change solutions, Quantum computing...",
        label_visibility="collapsed"
    )

    examples = [
        "The future of AI agents in 2026",
        "How LangGraph is changing AI development",
        "Best practices for RAG systems",
        "Remote work trends in tech industry"
    ]

    st.markdown("**💡 Example topics:**")
    cols = st.columns(4)
    for i, (col, example) in enumerate(zip(cols, examples)):
        with col:
            if st.button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state["example_topic"] = example
                st.rerun()

    # Handle example topic selection
    if "example_topic" in st.session_state:
        topic = st.session_state.pop("example_topic")

    st.markdown("<br>", unsafe_allow_html=True)
    research_btn = st.button("🚀 Start Research", use_container_width=True)

    if research_btn:
        if not topic or not topic.strip():
            st.error("Please enter a research topic")
        else:
            with st.spinner("🤖 Running parallel research agents... (this takes 30-60 seconds)"):
                try:
                    response = requests.post(
                        f"{API_URL}/research",
                        json={"topic": topic},
                        timeout=180
                    )
                    if response.status_code == 200:
                        st.session_state["pending_session"] = response.json()
                        st.rerun()
                    else:
                        st.error(f"Error: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Run: `uvicorn api:app --reload`")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Step 2: Human in the loop review

elif "pending_session" in st.session_state:
    session = st.session_state["pending_session"]

    st.markdown(f"### Research: **{session['topic']}**")

    # Quality score
    score = session.get("quality_score", 0)
    score_color = "#44ee88" if score >= 8 else "#ccaa44" if score >= 6 else "#cc4444"

    col_score, col_info = st.columns([1, 4])
    with col_score:
        st.markdown(f"""
        <div style="text-align:center;background:#0a1a0a;border:1px solid #1a5a2a;border-radius:12px;padding:1.5rem">
            <div style="font-family:Syne,sans-serif;font-size:3rem;font-weight:800;color:{score_color}">{score}/10</div>
            <div style="font-size:11px;color:#446644;text-transform:uppercase;letter-spacing:.1em">Quality Score</div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown('<div class="result-section">', unsafe_allow_html=True)
        st.markdown('<div class="result-title">🔬 Critic\'s Assessment</div>', unsafe_allow_html=True)
        st.markdown(session.get("critique", ""))
        st.markdown('</div>', unsafe_allow_html=True)

    # Subtopics researched
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.markdown('<div class="result-title">⚡ Research by Parallel Agents</div>', unsafe_allow_html=True)

    for result in session.get("research_results", []):
        with st.expander(f"📄 {result['subtopic']}", expanded=False):
            st.markdown(result["summary"])
            if result.get("sources"):
                st.markdown("**Sources:**")
                for src in result["sources"][:3]:
                    st.markdown(f"- {src}")
    st.markdown('</div>', unsafe_allow_html=True)

    # HITL box
    st.markdown("""
    <div class="hitl-box">
        <div class="hitl-title">✋ Your Turn — Guide the Report</div>
        <div class="hitl-sub">Review the research above. Add any instructions before the writer generates the final report.</div>
    </div>
    """, unsafe_allow_html=True)

    human_feedback = st.text_area(
        "Instructions for the report (optional)",
        placeholder='e.g. "Focus more on practical applications", "Add a section on risks", "Keep it concise"...',
        height=100,
        label_visibility="collapsed"
    )

    col_approve, col_restart = st.columns([3, 1])

    with col_approve:
        approve_btn = st.button("✅ Generate Report", use_container_width=True)
    with col_restart:
        if st.button("🔄 Start Over", use_container_width=True):
            del st.session_state["pending_session"]
            st.rerun()

    if approve_btn:
        with st.spinner("✍️ Writing your research report..."):
            try:
                response = requests.post(
                    f"{API_URL}/approve",
                    json={
                        "thread_id": session["thread_id"],
                        "human_feedback": human_feedback
                    },
                    timeout=120
                )
                if response.status_code == 200:
                    st.session_state["final_result"] = response.json()
                    del st.session_state["pending_session"]
                    st.rerun()
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Step 3: Final report

elif "final_result" in st.session_state:
    result = st.session_state["final_result"]

    st.markdown(f"### ✅ Research Report: **{result['topic']}**")

    # Subtopics covered
    if result.get("subtopics"):
        st.markdown("**Topics covered:** " + " · ".join(f"`{s}`" for s in result["subtopics"]))

    st.markdown("<br>", unsafe_allow_html=True)

    # Report
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.markdown('<div class="result-title">📄 Full Research Report</div>', unsafe_allow_html=True)
    st.markdown(result["report"])
    st.markdown('</div>', unsafe_allow_html=True)

    col_dl, col_new = st.columns([1, 1])
    with col_dl:
        st.download_button(
            "⬇️ Download Report",
            data=result["report"],
            file_name=f"research_{result['topic'][:30].lower().replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with col_new:
        if st.button("🔍 New Research", use_container_width=True):
            del st.session_state["final_result"]
            st.rerun()
