"""
LangSmith Online Evaluators for Social Media Content.
Evaluates selected_post for hallucination, relevance, and conciseness,
then submits feedback scores to LangSmith.
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
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
    
    # Run all evaluations in parallel (~3x speed improvement)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(evaluate_hallucination, selected_post, research_results, llm): "hallucination",
            executor.submit(evaluate_relevance, selected_post, topic, theme, llm): "relevance",
            executor.submit(evaluate_conciseness, selected_post, llm): "conciseness"
        }
        
        eval_results = {}
        for future in as_completed(futures):
            eval_name = futures[future]
            try:
                eval_results[eval_name] = future.result()
            except Exception as e:
                logger.error(f"Evaluation {eval_name} failed: {e}")
                eval_results[eval_name] = {"score": 0.0, "passed": False, "reasoning": f"Error: {e}"}
    
    hallucination_result = eval_results["hallucination"]
    relevance_result = eval_results["relevance"]
    conciseness_result = eval_results["conciseness"]
    
    logger.info(f"Hallucination/Groundedness: {hallucination_result['score']:.2f} - {'PASS' if hallucination_result['passed'] else 'FAIL'}")
    logger.info(f"Relevance: {relevance_result['score']:.2f} - {'PASS' if relevance_result['passed'] else 'FAIL'}")
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
    
    # Add character count to state for metrics tracking
    char_count = len(selected_post) if selected_post else 0
    
    return {
        "evaluation_results": evaluation_results,
        "post_char_count": char_count
    }


# =============================================================================
# COMPOSITE EVALUATOR (LangSmith Best Practice)
# =============================================================================

def calculate_composite_score(
    evaluation_results: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate a weighted composite score from individual evaluations.
    
    This follows LangSmith best practices for aggregating multiple metrics
    into a single quality score for easier comparison across runs.
    
    Args:
        evaluation_results: Dict containing hallucination, relevance, conciseness scores
        weights: Optional custom weights. Defaults to balanced weighting.
    
    Returns:
        Dict with composite_score, breakdown, and overall assessment
    """
    default_weights = {
        "groundedness": 0.4,  # Most important - factual accuracy
        "relevance": 0.35,   # Topic alignment
        "conciseness": 0.25  # Format appropriateness
    }
    weights = weights or default_weights
    
    # Map evaluation keys to weight keys
    score_mapping = {
        "hallucination": "groundedness",
        "relevance": "relevance", 
        "conciseness": "conciseness"
    }
    
    total_score = 0.0
    breakdown = {}
    total_weight = 0.0
    
    for eval_key, weight_key in score_mapping.items():
        if eval_key in evaluation_results:
            score = evaluation_results[eval_key].get("score", 0)
            weight = weights.get(weight_key, 0)
            weighted_score = score * weight
            total_score += weighted_score
            total_weight += weight
            breakdown[weight_key] = {
                "raw_score": score,
                "weight": weight,
                "weighted_score": weighted_score
            }
    
    # Normalize if weights don't sum to 1
    if total_weight > 0:
        composite = total_score / total_weight
    else:
        composite = 0.0
    
    return {
        "composite_score": round(composite, 3),
        "breakdown": breakdown,
        "passed": composite >= 0.7,
        "quality_tier": (
            "excellent" if composite >= 0.9 else
            "good" if composite >= 0.75 else
            "acceptable" if composite >= 0.6 else
            "needs_improvement"
        )
    }


def submit_composite_feedback(
    evaluation_results: Dict[str, Any],
    run_id: Optional[str] = None
) -> None:
    """
    Calculate and submit composite score as additional LangSmith feedback.
    
    Args:
        evaluation_results: Dict containing individual evaluation scores
        run_id: Optional run_id for LangSmith feedback
    """
    try:
        composite = calculate_composite_score(evaluation_results)
        
        client = Client()
        
        if run_id is None:
            try:
                run_tree = get_current_run_tree()
                if run_tree:
                    run_id = str(run_tree.id)
            except Exception:
                pass
        
        if run_id:
            client.create_feedback(
                run_id=run_id,
                key="composite_quality",
                score=composite["composite_score"],
                comment=f"Quality tier: {composite['quality_tier']}"
            )
            logger.info(f"Submitted composite quality feedback: {composite['composite_score']} ({composite['quality_tier']})")
        
    except Exception as e:
        logger.error(f"Failed to submit composite feedback: {e}")


# =============================================================================
# CHARACTER COUNT COMPLIANCE EVALUATOR
# =============================================================================

def evaluate_character_compliance(selected_post: str) -> Dict[str, Any]:
    """
    Evaluate character count compliance for social media platforms.
    
    Platform limits:
    - Twitter/X: 280 characters (standard), 25,000 (premium)
    - LinkedIn: 3,000 characters
    - Instagram caption: 2,200 characters
    
    Returns:
        Dict with compliance scores per platform
    """
    char_count = len(selected_post)
    
    platforms = {
        "twitter_standard": {"limit": 280, "compliant": char_count <= 280},
        "twitter_premium": {"limit": 25000, "compliant": char_count <= 25000},
        "linkedin": {"limit": 3000, "compliant": char_count <= 3000},
        "instagram": {"limit": 2200, "compliant": char_count <= 2200}
    }
    
    # Score is 1.0 if under limit, scales down as you exceed
    twitter_score = min(1.0, 280 / max(char_count, 1)) if char_count > 280 else 1.0
    
    return {
        "char_count": char_count,
        "platforms": platforms,
        "twitter_compliance_score": round(twitter_score, 3),
        "is_twitter_ready": char_count <= 280
    }


# =============================================================================
# IMAGE RETRY RATE TRACKING
# =============================================================================

def calculate_image_retry_metrics(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate image generation retry metrics for quality monitoring.
    
    Tracks:
    - retry_count: Number of image regeneration attempts
    - first_attempt_success: Whether first image was approved
    - retry_rate: retry_count / total_attempts
    
    Args:
        state: AgentState with retry_count and image_approved
    
    Returns:
        Dict with retry metrics
    """
    retry_count = state.get("retry_count", 0)
    image_approved = state.get("image_approved", False)
    
    # Total attempts = retry_count + 1 (initial attempt)
    total_attempts = retry_count + 1
    
    return {
        "retry_count": retry_count,
        "total_attempts": total_attempts,
        "first_attempt_success": retry_count == 0 and image_approved,
        "final_approved": image_approved,
        "retry_rate": round(retry_count / total_attempts, 3) if total_attempts > 0 else 0,
        "hit_max_retries": retry_count >= 2
    }


def submit_image_metrics_feedback(
    state: Dict[str, Any],
    run_id: Optional[str] = None
) -> None:
    """
    Submit image generation metrics as LangSmith feedback.
    
    Args:
        state: AgentState with retry_count and image_approved
        run_id: Optional run_id for LangSmith feedback
    """
    try:
        metrics = calculate_image_retry_metrics(state)
        
        client = Client()
        
        if run_id is None:
            try:
                run_tree = get_current_run_tree()
                if run_tree:
                    run_id = str(run_tree.id)
            except Exception:
                pass
        
        if run_id:
            # Submit image approval as binary score
            client.create_feedback(
                run_id=run_id,
                key="image_approved",
                score=1.0 if metrics["final_approved"] else 0.0,
                comment=f"Attempts: {metrics['total_attempts']}, Retries: {metrics['retry_count']}"
            )
            
            # Submit first-attempt success rate
            client.create_feedback(
                run_id=run_id,
                key="image_first_attempt_success",
                score=1.0 if metrics["first_attempt_success"] else 0.0
            )
            
            logger.info(f"Submitted image metrics: approved={metrics['final_approved']}, attempts={metrics['total_attempts']}")
        
    except Exception as e:
        logger.error(f"Failed to submit image metrics feedback: {e}")


# =============================================================================
# SUMMARY EVALUATOR (Experiment-Level Metrics)
# =============================================================================

def fetch_experiment_summary_metrics(experiment_name: str) -> Dict[str, Any]:
    """
    Fetch experiment-level summary metrics from LangSmith.
    
    This retrieves the project stats which include:
    - latency_p50, latency_p99: Latency percentiles
    - total_tokens, prompt_tokens, completion_tokens: Token usage
    - total_cost: Estimated cost
    - error_rate: Percentage of failed runs
    - feedback_stats: Aggregated feedback scores
    
    Args:
        experiment_name: The LangSmith project/experiment name
    
    Returns:
        Dict with summary metrics or empty dict if unavailable
    """
    try:
        client = Client()
        project = client.read_project(project_name=experiment_name, include_stats=True)
        
        return {
            "experiment_name": experiment_name,
            "latency_p50": getattr(project, "latency_p50", None),
            "latency_p99": getattr(project, "latency_p99", None),
            "total_tokens": getattr(project, "total_tokens", None),
            "prompt_tokens": getattr(project, "prompt_tokens", None),
            "completion_tokens": getattr(project, "completion_tokens", None),
            "total_cost": getattr(project, "total_cost", None),
            "error_rate": getattr(project, "error_rate", None),
            "feedback_stats": getattr(project, "feedback_stats", {}),
            "run_count": getattr(project, "run_count", None)
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch experiment summary: {e}")
        return {}


def log_workflow_summary(state: Dict[str, Any]) -> None:
    """
    Log a summary of workflow metrics at completion.
    
    Args:
        state: Final AgentState with all metrics
    """
    logger.info("=" * 60)
    logger.info("WORKFLOW METRICS SUMMARY")
    logger.info("=" * 60)
    
    # Post metrics
    if state.get("post_char_count"):
        logger.info(f"Post character count: {state['post_char_count']}")
        logger.info(f"Twitter ready: {'Yes' if state['post_char_count'] <= 280 else 'No'}")
    
    # Image metrics
    image_metrics = calculate_image_retry_metrics(state)
    logger.info(f"Image attempts: {image_metrics['total_attempts']}")
    logger.info(f"Image approved: {image_metrics['final_approved']}")
    logger.info(f"First attempt success: {image_metrics['first_attempt_success']}")
    
    # Evaluation summary
    eval_results = state.get("evaluation_results", {})
    if eval_results:
        composite = calculate_composite_score(eval_results)
        logger.info(f"Composite quality: {composite['composite_score']} ({composite['quality_tier']})")
    
    # Latency
    if state.get("total_latency"):
        logger.info(f"Total latency: {state['total_latency']:.2f}s")
    
    if state.get("node_latencies"):
        logger.info("Node latencies:")
        for node, latency in state["node_latencies"].items():
            logger.info(f"  {node}: {latency:.2f}s")
    
    # Errors
    if state.get("errors"):
        logger.warning(f"Errors encountered: {len(state['errors'])}")
        for err in state["errors"]:
            logger.warning(f"  - {err}")
    
    logger.info("=" * 60)
