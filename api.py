import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from research_agent import research_agent

app = FastAPI(
    title="Multi-Agent Research Assistant",
    description="Parallel research agents that synthesize comprehensive reports",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# In-memory store for pending sessions
pending_sessions = {}

# Request/Response Models

class ResearchRequest(BaseModel):
    topic: str

class IntermediateResponse(BaseModel):
    thread_id: str
    topic: str
    subtopics: list
    research_results: list
    critique: str
    quality_score: int
    status: str = "awaiting_approval"

class ApprovalRequest(BaseModel):
    thread_id: str
    human_feedback: Optional[str] = ""

class FinalResponse(BaseModel):
    thread_id: str
    topic: str
    subtopics: list
    report: str
    quality_score: int

# Endpoints 

@app.get("/")
def root():
    return {"message": "Multi-Agent Research Assistant API", "status": "running"}


@app.post("/research", response_model=IntermediateResponse)
async def start_research(request: ResearchRequest):
    """
    Step 1 — Start research.
    Runs planner → parallel search agents → critic → PAUSES.
    Returns research results and critique for human review.
    """
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Run agent until interrupt
    research_agent.invoke(
        {
            "topic": request.topic,
            "subtopics": [],
            "research_results": [],
            "critique": None,
            "quality_score": None,
            "human_feedback": None,
            "report": None,
            "messages": []
        },
        config=config
    )

    # Get state after interrupt
    state = research_agent.get_state(config)
    values = state.values

    # Store session
    pending_sessions[thread_id] = {
        "config": config,
        "topic": request.topic
    }

    return IntermediateResponse(
        thread_id=thread_id,
        topic=request.topic,
        subtopics=values.get("subtopics", []),
        research_results=values.get("research_results", []),
        critique=values.get("critique", ""),
        quality_score=values.get("quality_score", 0),
        status="awaiting_approval"
    )


@app.post("/approve", response_model=FinalResponse)
async def approve_and_write(request: ApprovalRequest):
    """
    Step 2 — Human approves research and optionally adds feedback.
    Agent resumes and writes the final report.
    """
    thread_id = request.thread_id

    if thread_id not in pending_sessions:
        raise HTTPException(status_code=404, detail="Session not found or already completed")

    session = pending_sessions[thread_id]
    config = session["config"]

    # Inject human feedback
    research_agent.update_state(
        config,
        {"human_feedback": request.human_feedback or ""},
        as_node="critic"
    )

    # Resume — writes report
    result = research_agent.invoke(None, config=config)

    # Clean up
    del pending_sessions[thread_id]

    return FinalResponse(
        thread_id=thread_id,
        topic=session["topic"],
        subtopics=result.get("subtopics", []),
        report=result.get("report", ""),
        quality_score=result.get("quality_score", 0)
    )
