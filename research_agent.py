import os
from typing import TypedDict, Annotated, Optional, List
import operator
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AnyMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()

# State 

class ResearchState(TypedDict):
    # Input
    topic: str

    # Computed by planner
    subtopics: List[str]

    # Computed by parallel search agents
    research_results: Annotated[list, operator.add]

    # Computed by critic
    critique: Optional[str]
    quality_score: Optional[int]

    # Human in the loop
    human_feedback: Optional[str]

    # Final output
    report: Optional[str]

    # Messages
    messages: Annotated[list[AnyMessage], operator.add]


# Individual search state — for each parallel agent
class SearchState(TypedDict):
    topic: str        # main topic
    subtopic: str     # this agent's specific subtopic


# LLM 

def get_llm(temperature=0.3):
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile",
        temperature=temperature
    )

# Node 1: Planner 

def planner_node(state: ResearchState) -> dict:
    """Break the main topic into 3 focused subtopics"""
    print(f"\n📋 Planning research for: {state['topic']}")

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a research planner. Break the given topic into exactly 3 "
            "focused subtopics that together give a comprehensive understanding. "
            "Return ONLY a Python list of 3 strings, nothing else. "
            "Example: [\"Subtopic 1\", \"Subtopic 2\", \"Subtopic 3\"]"
        )),
        ("human", "Break this into 3 research subtopics: {topic}")
    ])

    llm = get_llm(temperature=0)
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"topic": state["topic"]})

    # Parse the list safely
    try:
        import ast
        subtopics = ast.literal_eval(result.strip())
        if isinstance(subtopics, list):
            subtopics = [str(s) for s in subtopics[:3]]
        else:
            raise ValueError
    except Exception:
        # Fallback: split by newline
        lines = [l.strip().lstrip("123.-) ") for l in result.strip().splitlines() if l.strip()]
        subtopics = lines[:3]

    print(f"✅ Subtopics: {subtopics}")
    return {"subtopics": subtopics}


# Node 2: Individual Search Agent (runs in parallel)

def search_agent_node(state: SearchState) -> dict:
    """One search agent — researches one subtopic"""
    subtopic = state["subtopic"]
    topic = state["topic"]

    print(f"\n🔍 Searching: {subtopic}")

    search = TavilySearchResults(max_results=3)
    try:
        results = search.invoke(f"{topic} {subtopic} 2026")
        raw_content = "\n\n".join(
            f"Source: {r['url']}\n{r['content'][:500]}"
            for r in results
        )
    except Exception as e:
        raw_content = f"Search failed for {subtopic}: {str(e)}"

    # Synthesize the search results
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a research analyst. Synthesize the search results into "
            "a clear, factual summary. Be specific and cite key points. "
            "Write 2-3 paragraphs maximum."
        )),
        ("human", (
            f"Topic: {topic}\n"
            f"Subtopic: {subtopic}\n\n"
            f"Search Results:\n{raw_content}\n\n"
            "Write a clear research summary for this subtopic:"
        ))
    ])

    llm = get_llm(temperature=0.1)
    chain = prompt | llm | StrOutputParser()
    summary = chain.invoke({})

    print(f"✅ Research complete: {subtopic}")

    # Return as a structured result
    return {
        "research_results": [{
            "subtopic": subtopic,
            "summary": summary,
            "sources": [r['url'] for r in results] if isinstance(results, list) else []
        }]
    }


# Node 3: Critic 

def critic_node(state: ResearchState) -> dict:
    """Review research quality and identify gaps"""
    print(f"\n🔬 Critiquing research quality...")

    research_text = "\n\n".join(
        f"### {r['subtopic']}\n{r['summary']}"
        for r in state["research_results"]
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a rigorous research critic. Evaluate the quality of this research. "
            "Be specific about what's good and what's missing. "
            "Give a quality score from 1-10."
        )),
        ("human", (
            f"Topic: {state['topic']}\n\n"
            f"Research:\n{research_text}\n\n"
            "Evaluate with:\n"
            "✅ Strengths: what's well covered\n"
            "⚠️ Gaps: what's missing or shallow\n"
            "💡 Suggestions: what to improve\n"
            "Score: X/10"
        ))
    ])

    llm = get_llm(temperature=0.1)
    chain = prompt | llm | StrOutputParser()
    critique = chain.invoke({})

    # Extract score
    import re
    score_match = re.search(r'(\d+)/10', critique)
    quality_score = int(score_match.group(1)) if score_match else 7

    print(f"✅ Quality score: {quality_score}/10")
    return {"critique": critique, "quality_score": quality_score}


# Node 4:Writer 

def writer_node(state: ResearchState) -> dict:
    """Write the final structured report"""
    print(f"\n✍️ Writing final report...")

    research_text = "\n\n".join(
        f"### {r['subtopic']}\n{r['summary']}"
        for r in state["research_results"]
    )

    all_sources = []
    for r in state["research_results"]:
        all_sources.extend(r.get("sources", []))

    human_feedback = state.get("human_feedback", "") or ""

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert research writer. Write a comprehensive, "
            "well-structured research report. Use markdown formatting. "
            "Include an executive summary, detailed sections, and key takeaways. "
            "Be specific, factual, and cite sources where relevant."
        )),
        ("human", (
            f"Topic: {state['topic']}\n\n"
            f"Research:\n{research_text}\n\n"
            f"Critic's feedback:\n{state.get('critique', '')}\n\n"
            f"Additional instructions: {human_feedback if human_feedback else 'None'}\n\n"
            "Write a comprehensive research report in markdown:"
        ))
    ])

    llm = get_llm(temperature=0.5)
    chain = prompt | llm | StrOutputParser()
    report = chain.invoke({})

    print(f"✅ Report written!")
    return {"report": report}


# Parallel dispatch: Send API 

def dispatch_search_agents(state: ResearchState):
    """
    This is the key LangGraph pattern for parallel execution.
    Send() creates one instance of search_agent_node per subtopic.
    All run simultaneously.
    """
    return [
        Send("search_agent", {
            "topic": state["topic"],
            "subtopic": subtopic
        })
        for subtopic in state["subtopics"]
    ]


# Build Graph 

def build_research_agent():
    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("search_agent", search_agent_node)
    graph.add_node("critic", critic_node)
    graph.add_node("writer", writer_node)

    # Entry point
    graph.set_entry_point("planner")

    # After planner — dispatch parallel search agents using Send API
    graph.add_conditional_edges(
        "planner",
        dispatch_search_agents,
        ["search_agent"]
    )

    # After ALL parallel agents finish — go to critic
    graph.add_edge("search_agent", "critic")

    # After critic — pause for human review
    graph.add_edge("critic", "writer")

    memory = MemorySaver()

    return graph.compile(
        checkpointer=memory,
        interrupt_before=["writer"]  # HITL — pause before writing report
    )


# Singleton
research_agent = build_research_agent()
