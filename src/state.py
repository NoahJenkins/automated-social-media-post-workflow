from typing import TypedDict, List, Optional, Dict, Any

class AgentState(TypedDict):
    """
    Represents the state of the social media posting workflow.
    """
    topic: Optional[str]
    research_results: Optional[str]
    draft_posts: Optional[List[str]]
    selected_post: Optional[str]
    image_prompt: Optional[str]
    image_url: Optional[str]
    image_approved: bool
    critique: Optional[str]
    post_status: Optional[str]
    post_id: Optional[str]  # Metricool post ID for verification
    post_scheduled: bool  # Whether post was successfully scheduled
    retry_count: int
    day_of_week: Optional[str]
    theme: Optional[str]
    # Evaluation results from online evaluators
    evaluation_results: Optional[Dict[str, Any]]
    
    # --- Metrics tracking (LangSmith best practices) ---
    # Per-node latency tracking (node_name -> seconds)
    node_latencies: Optional[Dict[str, float]]
    # Total workflow execution time in seconds
    total_latency: Optional[float]
    # Character count of the selected post
    post_char_count: Optional[int]
    # Image generation attempts (for retry rate tracking)
    image_generation_attempts: Optional[int]
    # Workflow start timestamp (ISO format)
    workflow_start_time: Optional[str]
    # Error messages collected during workflow
    errors: Optional[List[str]]
