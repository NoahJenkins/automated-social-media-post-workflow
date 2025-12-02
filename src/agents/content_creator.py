from src.state import AgentState
from src.config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

def content_creator_node(state: AgentState):
    """
    Generates 3 draft posts based on the researched topic.
    """
    print("--- CONTENT CREATOR AGENT ---")
    topic = state["topic"]
    research = state["research_results"]
    day = state.get("day_of_week", "a weekday")
    theme = state.get("theme", "tech life")
    
    llm = get_llm("gpt-5")
    
    prompt = f"""
    Topic: {topic}
    Context: {research}
    
    Task: Write 3 distinct social media posts (tweets) about this topic.
    Context: Today is {day}. The theme is {theme}. Make the posts reflect this vibe (e.g., if Friday, make it about the weekend/wrapping up).
    Tone: Casual, Fun, Engaging, Relatable for Tech Workers.
    Constraints:
    - Under 280 characters.
    - Use 1-2 emojis.
    - No hashtags (or max 1).
    
    Output format:
    1. [Post 1 text]
    2. [Post 2 text]
    3. [Post 3 text]
    """
    
    messages = [
        SystemMessage(content="You are a witty social media manager for a tech company."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Simple parsing to get list
    drafts = []
    for line in content.split('\n'):
        if line.strip().startswith(('1.', '2.', '3.')):
            drafts.append(line.split('.', 1)[1].strip())
            
    # Fallback if parsing fails
    if len(drafts) < 3:
        drafts = [content]

    return {"draft_posts": drafts}
