from src.state import AgentState
from src.config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

def prompt_engineer_node(state: AgentState):
    """
    Generates a DALL-E 3 prompt based on the selected post.
    """
    print("--- PROMPT ENGINEER AGENT ---")
    selected_post = state["selected_post"]
    
    llm = get_llm("gpt-4o-mini")
    
    prompt = f"""
    Based on this social media post: "{selected_post}"
    
    Create a detailed prompt for DALL-E 3 to generate an accompanying image.
    Style: Modern, minimal, tech-focused, vibrant colors. 
    No text in the image.
    
    Return ONLY the prompt text.
    """
    
    messages = [
        SystemMessage(content="You are an expert AI art prompter."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    image_prompt = response.content.strip()
    
    # Increment retry count
    current_retries = state.get("retry_count", 0)
    
    return {"image_prompt": image_prompt, "retry_count": current_retries + 1}
