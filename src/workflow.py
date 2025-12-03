from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.agents.researcher import researcher_node
from src.agents.content_creator import content_creator_node
from src.agents.content_reviewer import content_reviewer_node
from src.agents.prompt_engineer import prompt_engineer_node
from src.agents.image_generator import image_generator_node
from src.agents.image_reviewer import image_reviewer_node
from src.agents.poster import poster_node
from src.agents.saver import saver_node
from src.evaluators.feedback import evaluate_content_node
from src.utils.metrics import wrap_node_with_latency
from src.config import ENABLE_POSTING


# Wrap all nodes with latency tracking for observability
tracked_researcher = wrap_node_with_latency(researcher_node, "researcher")
tracked_content_creator = wrap_node_with_latency(content_creator_node, "content_creator")
tracked_content_reviewer = wrap_node_with_latency(content_reviewer_node, "content_reviewer")
tracked_evaluate_content = wrap_node_with_latency(evaluate_content_node, "evaluate_content")
tracked_prompt_engineer = wrap_node_with_latency(prompt_engineer_node, "prompt_engineer")
tracked_image_generator = wrap_node_with_latency(image_generator_node, "image_generator")
tracked_image_reviewer = wrap_node_with_latency(image_reviewer_node, "image_reviewer")
tracked_poster = wrap_node_with_latency(poster_node, "poster")
tracked_saver = wrap_node_with_latency(saver_node, "saver")


def build_graph():
    """
    Constructs the LangGraph workflow with latency-tracked nodes.
    """
    workflow = StateGraph(AgentState)

    # Add Nodes (with latency tracking)
    workflow.add_node("researcher", tracked_researcher)
    workflow.add_node("content_creator", tracked_content_creator)
    workflow.add_node("content_reviewer", tracked_content_reviewer)
    workflow.add_node("evaluate_content", tracked_evaluate_content)  # Online evaluators
    workflow.add_node("prompt_engineer", tracked_prompt_engineer)
    workflow.add_node("image_generator", tracked_image_generator)
    workflow.add_node("image_reviewer", tracked_image_reviewer)
    workflow.add_node("poster", tracked_poster)
    workflow.add_node("saver", tracked_saver)

    # Define Edges
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "content_creator")
    workflow.add_edge("content_creator", "content_reviewer")
    workflow.add_edge("content_reviewer", "evaluate_content")  # Run online evaluators after review
    workflow.add_edge("evaluate_content", "prompt_engineer")  # Continue workflow (non-blocking)
    workflow.add_edge("prompt_engineer", "image_generator")
    workflow.add_edge("image_generator", "image_reviewer")

    # Conditional Edge for Image Review
    def check_image_approval(state: AgentState):
        retry_count = state.get("retry_count", 0)
        
        if state.get("image_approved"):
            return "poster" if ENABLE_POSTING else "saver"
        elif retry_count >= 2:
            print("Max retries reached for image generation. Proceeding to post without image (or with rejected image).")
            return "poster" if ENABLE_POSTING else "saver"
        else:
            return "prompt_engineer"

    workflow.add_conditional_edges(
        "image_reviewer",
        check_image_approval,
        {
            "poster": "poster",
            "saver": "saver",
            "prompt_engineer": "prompt_engineer"
        }
    )

    workflow.add_edge("poster", "saver")
    workflow.add_edge("saver", END)

    # Compile
    app = workflow.compile()
    return app
