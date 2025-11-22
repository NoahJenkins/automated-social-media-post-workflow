from typing import TypedDict, List, Optional

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
    retry_count: int
    day_of_week: Optional[str]
    theme: Optional[str]
