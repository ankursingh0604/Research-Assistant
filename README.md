# 🔬 Multi-Agent Research Assistant

A LangGraph multi-agent system that researches any topic using parallel search agents, critiques the findings, and synthesizes a structured report — all with human review before the final output.

Built with LangGraph's Send API for true parallel execution, Human in the Loop review, and LangSmith tracing.

🚀 [Live Demo](https://research-assistant-ybkpacxvhyqduzam2mparf.streamlit.app/) &nbsp;|&nbsp; 🔌 [API](https://research-assistant-production-d815.up.railway.app)

---

## What it does

Enter any research topic and the system:

1. **Plans** — breaks topic into 3 focused subtopics for comprehensive coverage
2. **Researches in parallel** — 3 search agents run simultaneously using LangGraph Send API, each independently searching and synthesizing their subtopic
3. **Critiques** — evaluates research quality, identifies gaps, scores out of 10
4. **Pauses for human review** — shows all findings before writing anything ← Human in the Loop
5. **Takes your instructions** — you guide the final report before it's written
6. **Writes** — synthesizes everything into a structured markdown report with sources

---

## Architecture

```
User Topic
    ↓
Planner Node — breaks into 3 subtopics
    ↓
Send API — dispatches parallel agents simultaneously
    ├── Search Agent 1 → researches subtopic 1
    ├── Search Agent 2 → researches subtopic 2
    └── Search Agent 3 → researches subtopic 3
    ↓ (all results collected via reducer)
Critic Node — evaluates quality, scores 1-10
    ↓
PAUSE ← Human reviews findings + adds instructions
    ↓
Writer Node — synthesizes final structured report
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | LangGraph + Send API |
| LLM | LLaMA 3.3 70B via Groq API |
| Web Search | Tavily Search API |
| Backend | FastAPI |
| Frontend | Streamlit |
| Monitoring | LangSmith |
| Backend Deployment | Railway |
| Frontend Deployment | Streamlit Cloud |

---

## What makes this different

- **True parallel execution** — uses LangGraph's `Send` API to dispatch multiple agent instances simultaneously. Each agent runs independently and writes back to shared state via an `operator.add` reducer. Faster and more comprehensive than sequential research.
- **Human in the Loop** — agent pauses after critique using `interrupt_before`, you review all findings and add specific instructions before the report is written
- **Quality gate** — critic agent scores research 1-10 and identifies gaps before you approve, ensuring the final report is based on solid research
- **Production ready** — FastAPI backend, LangSmith tracing on every run, Docker + Railway deployment

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/research` | Start research — runs until HITL pause |
| POST | `/approve` | Resume with human feedback — writes report |

---

## Setup

1. Clone the repo
```bash
git clone https://github.com/ankursingh0604/Research-Assistant
cd Research-Assistant
```

2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

3. Create `.env` file
```
GROQ_API_KEY=your-groq-api-key
TAVILY_API_KEY=your-tavily-api-key
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=research-assistant
```

4. Run
```bash
# Terminal 1
uvicorn api:app --reload

# Terminal 2
streamlit run app.py
```

---

## Project Structure

```
Research-Assistant/
├── agents/
│   └── research_agent.py   ← LangGraph multi-agent with Send API + HITL
├── api.py                   ← FastAPI two-step endpoints
├── app.py                   ← Streamlit frontend with random example topics
├── requirements.txt
└── Dockerfile
```

---

## Author

**Ankur Singh** — CS undergrad building RAG systems and AI agents

[GitHub](https://github.com/ankursingh0604) • [LinkedIn](your-linkedin-url) • [X](https://x.com/ankur_builds)
