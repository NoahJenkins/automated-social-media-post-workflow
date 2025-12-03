"""
LangSmith Online Evaluators for Social Media Content.
Evaluates selected_post for hallucination, relevance, and conciseness,
then submits feedback scores to LangSmith.
"""

import logging
import os
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import Client
from langsmith.run_helpers import get_current_run_tree

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Evaluation model - using gpt-4o-mini for cost efficiency
EVAL_MODEL = "gpt-4o-mini"


def get_eval_llm() -> ChatOpenAI:
    """Returns a ChatOpenAI instance for evaluation tasks using gpt-4o-mini."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        return ChatOpenAI(
            model=EVAL_MODEL,
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.0  # Deterministic for evaluation
        )
    else:
        return ChatOpenAI(model=EVAL_MODEL, temperature=0.0)


def evaluate_hallucination(
    selected_post: str,
    research_results: str,
    llm: ChatOpenAI
) -> Dict[str, Any]:
    """
    Evaluate if the selected post contains hallucinations (facts not grounded in research).
    
    Returns:
        Dict with 'score' (0-1, higher = more grounded), 'reasoning', and 'passed'
    """
    system_prompt = """You are an expert fact-checker evaluating social media content for hallucinations.

Your task is to determine if the claims and facts in the POST are grounded in the provided RESEARCH.

Scoring criteria:
- 1.0: All facts in the post are directly supported by the research
- 0.7-0.9: Most facts are supported, minor embellishments that don't mislead
- 0.4-0.6: Some facts supported, but contains unsupported claims
- 0.1-0.3: Many unsupported claims or misleading information
- 0.0: Completely fabricated or contradicts the research

Respond in this exact format:
SCORE: [0.0-1.0]
REASONING: [Your explanation]"""

    user_prompt = f"""RESEARCH CONTEXT:
{research_results}

POST TO EVALUATE:
{selected_post}

Evaluate whether the post is grounded in the research provided."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Parse response
    try:
        lines = content.strip().split('\n')
        score_line = [l for l in lines if l.startswith('SCORE:')][0]
        score = float(score_line.replace('SCORE:', '').strip())
        reasoning = content.split('REASONING:')[-1].strip() if 'REASONING:' in content else content
    except (IndexError, ValueError):
        score = 0.5
        reasoning = content
    
    return {
        "score": score,
        "reasoning": reasoning,
        "passed": score >= 0.7
    }


def evaluate_relevance(
    selected_post: str,
    topic: str,
    theme: Optional[str],
    llm: ChatOpenAI
) -> Dict[str, Any]:
    """
    Evaluate if the selected post is relevant to the topic and theme.
    
    Returns:
        Dict with 'score' (0-1, higher = more relevant), 'reasoning', and 'passed'
    """
    system_prompt = """You are an expert content evaluator assessing relevance of social media posts.

Your task is to determine if the POST adequately addresses the given TOPIC and THEME.

Scoring criteria:
- 1.0: Post directly and thoroughly addresses the topic and fits the theme perfectly
- 0.7-0.9: Post addresses the topic well with minor tangents
- 0.4-0.6: Post somewhat relates to topic but misses key aspects
- 0.1-0.3: Post only loosely connected to the topic
- 0.0: Post is completely off-topic

Respond in this exact format:
SCORE: [0.0-1.0]
REASONING: [Your explanation]"""

    theme_text = f"\nTHEME: {theme}" if theme else ""
    user_prompt = f"""TOPIC: {topic}{theme_text}

POST TO EVALUATE:
{selected_post}

Evaluate whether the post is relevant to the topic and theme."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Parse response
    try:
        lines = content.strip().split('\n')
        score_line = [l for l in lines if l.startswith('SCORE:')][0]
        score = float(score_line.replace('SCORE:', '').strip())
        reasoning = content.split('REASONING:')[-1].strip() if 'REASONING:' in content else content
    except (IndexError, ValueError):
        score = 0.5
        reasoning = content
    
    return {
        "score": score,
        "reasoning": reasoning,
        "passed": score >= 0.7
    }


def evaluate_conciseness(
    selected_post: str,
    llm: ChatOpenAI
) -> Dict[str, Any]:
    """
    Evaluate if the selected post is concise and appropriate for social media.
    Checks character count, verbosity, and repetition.
    
    Returns:
        Dict with 'score' (0-1, higher = more concise), 'reasoning', and 'passed'
    """
    char_count = len(selected_post)
    
    # Hard check for social media length
    length_penalty = 0.0
    if char_count > 280:
        length_penalty = min(0.3, (char_count - 280) / 200)
    
    system_prompt = """You are an expert social media content evaluator assessing conciseness.

Your task is to evaluate if the POST is appropriately concise for social media:
- Not overly verbose or wordy
- No unnecessary repetition
- Gets the point across efficiently
- Appropriate length for social media (ideally under 280 characters)

Scoring criteria:
- 1.0: Perfectly concise, every word serves a purpose
- 0.7-0.9: Well-written with minor wordiness
- 0.4-0.6: Contains some redundancy or verbosity
- 0.1-0.3: Overly wordy or repetitive
- 0.0: Extremely verbose or highly repetitive

Respond in this exact format:
SCORE: [0.0-1.0]
REASONING: [Your explanation]"""

    user_prompt = f"""POST TO EVALUATE ({char_count} characters):
{selected_post}

Evaluate the conciseness of this social media post."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Parse response
    try:
        lines = content.strip().split('\n')
        score_line = [l for l in lines if l.startswith('SCORE:')][0]
        base_score = float(score_line.replace('SCORE:', '').strip())
        reasoning = content.split('REASONING:')[-1].strip() if 'REASONING:' in content else content
    except (IndexError, ValueError):
        base_score = 0.5
        reasoning = content
    
    # Apply length penalty
    final_score = max(0.0, base_score - length_penalty)
    if length_penalty > 0:
        reasoning = f"[Length penalty: -{length_penalty:.2f} for {char_count} chars] " + reasoning
    
    return {
        "score": final_score,
        "reasoning": reasoning,
        "passed": final_score >= 0.6,
        "char_count": char_count
    }


def submit_feedback_to_langsmith(
    evaluation_results: Dict[str, Any],
    run_id: Optional[str] = None
) -> None:
    """
    Submit evaluation scores as feedback to LangSmith.
    
    Args:
        evaluation_results: Dict containing hallucination, relevance, conciseness scores
        run_id: Optional run_id to attach feedback to. If None, attempts to get current run.
    """
    try:
        client = Client()
        
        # Try to get current run ID if not provided
        if run_id is None:
            try:
                run_tree = get_current_run_tree()
                if run_tree:
                    run_id = str(run_tree.id)
            except Exception:
                pass
        
        if run_id is None:
            logger.warning("No run_id available - feedback will not be submitted to LangSmith")
            return
        
        # Submit hallucination feedback
        if "hallucination" in evaluation_results:
            client.create_feedback(
                run_id=run_id,
                key="groundedness",
                score=evaluation_results["hallucination"]["score"],
                comment=evaluation_results["hallucination"]["reasoning"]
            )
            logger.info(f"Submitted groundedness feedback: {evaluation_results['hallucination']['score']}")
        
        # Submit relevance feedback
        if "relevance" in evaluation_results:
            client.create_feedback(
                run_id=run_id,
                key="relevance",
                score=evaluation_results["relevance"]["score"],
                comment=evaluation_results["relevance"]["reasoning"]
            )
            logger.info(f"Submitted relevance feedback: {evaluation_results['relevance']['score']}")
        
        # Submit conciseness feedback
        if "conciseness" in evaluation_results:
            client.create_feedback(
                run_id=run_id,
                key="conciseness",
                score=evaluation_results["conciseness"]["score"],
                comment=evaluation_results["conciseness"]["reasoning"]
            )
            logger.info(f"Submitted conciseness feedback: {evaluation_results['conciseness']['score']}")
            
    except Exception as e:
        logger.error(f"Failed to submit feedback to LangSmith: {e}")


def run_evaluations(
    selected_post: str,
    research_results: str,
    topic: str,
    theme: Optional[str] = None,
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run all three evaluations on the selected post and submit feedback to LangSmith.
    
    Args:
        selected_post: The social media post to evaluate
        research_results: The research context the post should be grounded in
        topic: The topic the post should address
        theme: Optional theme for the day
        run_id: Optional LangSmith run_id to attach feedback to
    
    Returns:
        Dict containing all evaluation results
    """
    llm = get_eval_llm()
    
    logger.info("=" * 50)
    logger.info("RUNNING ONLINE EVALUATIONS")
    logger.info("=" * 50)
    
    # Run all evaluations
    hallucination_result = evaluate_hallucination(selected_post, research_results, llm)
    logger.info(f"Hallucination/Groundedness: {hallucination_result['score']:.2f} - {'PASS' if hallucination_result['passed'] else 'FAIL'}")
    
    relevance_result = evaluate_relevance(selected_post, topic, theme, llm)
    logger.info(f"Relevance: {relevance_result['score']:.2f} - {'PASS' if relevance_result['passed'] else 'FAIL'}")
    
    conciseness_result = evaluate_conciseness(selected_post, llm)
    logger.info(f"Conciseness: {conciseness_result['score']:.2f} - {'PASS' if conciseness_result['passed'] else 'FAIL'}")
    
    results = {
        "hallucination": hallucination_result,
        "relevance": relevance_result,
        "conciseness": conciseness_result,
        "overall_passed": all([
            hallucination_result["passed"],
            relevance_result["passed"],
            conciseness_result["passed"]
        ])
    }
    
    logger.info("-" * 50)
    logger.info(f"Overall: {'ALL PASSED' if results['overall_passed'] else 'SOME FAILED'}")
    logger.info("=" * 50)
    
    # Submit feedback to LangSmith
    submit_feedback_to_langsmith(results, run_id)
    
    return results


def evaluate_content_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that evaluates the selected_post and logs results.
    Non-blocking - always passes state through regardless of evaluation results.
    
    Args:
        state: AgentState containing selected_post, research_results, topic, theme
    
    Returns:
        Updated state with evaluation_results added
    """
    selected_post = state.get("selected_post")
    research_results = state.get("research_results")
    topic = state.get("topic")
    theme = state.get("theme")
    
    if not selected_post:
        logger.warning("No selected_post to evaluate")
        return {"evaluation_results": None}
    
    if not research_results:
        logger.warning("No research_results for grounding evaluation")
        research_results = ""
    
    if not topic:
        logger.warning("No topic for relevance evaluation")
        topic = "general social media content"
    
    # Run evaluations
    evaluation_results = run_evaluations(
        selected_post=selected_post,
        research_results=research_results,
        topic=topic,
        theme=theme
    )
    
    return {"evaluation_results": evaluation_results}
