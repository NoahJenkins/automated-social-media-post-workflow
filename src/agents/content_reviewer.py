from src.state import AgentState
from src.config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

def content_reviewer_node(state: AgentState):
    """
    Reviews the 3 drafts and selects the best one.
    """
    print("--- CONTENT REVIEWER AGENT ---")
    drafts = state["draft_posts"]
    
    llm = get_llm("gpt-4o")
    
    prompt = f"""
    Review the following 3 social media post drafts:
    
    1. {drafts[0] if len(drafts) > 0 else "N/A"}
    2. {drafts[1] if len(drafts) > 1 else "N/A"}
    3. {drafts[2] if len(drafts) > 2 else "N/A"}
    
    Criteria:
    - Must be fun, casual, and engaging.
    - Must be relevant to the topic: {state.get('topic', 'Tech')}
    - No cringey corporate speak.
    
    Task: Select the best post. Return ONLY the text of the selected post. Do not add quotes or "Selected Post:" prefix.
    """
    
    messages = [
        SystemMessage(content="You are a senior social media editor. You have impeccable taste."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    selected_post = response.content.strip()
    
    return {"selected_post": selected_post}
