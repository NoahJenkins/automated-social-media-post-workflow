from src.state import AgentState
from src.config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

def prompt_engineer_node(state: AgentState):
    """
    Generates a DALL-E 3 prompt based on the selected post.
    On retries, incorporates critique from image reviewer for better results.
    """
    print("--- PROMPT ENGINEER AGENT ---")
    selected_post = state["selected_post"]
    current_retries = state.get("retry_count", 0)
    critique = state.get("critique", "")
    
    llm = get_llm("gpt-5-mini")
    
    # Build base prompt
    base_instructions = f"""
    Based on this social media post: "{selected_post}"
    
    Create a detailed prompt for DALL-E 3 to generate an accompanying image.
    Style: Modern, minimal, tech-focused, vibrant colors. 
    No text in the image.
    
    Return ONLY the prompt text.
    """
    
    # On retries, include the critique to fix specific issues
    if current_retries > 0 and critique:
        prompt = f"""{base_instructions}
    
    IMPORTANT: The previous image was rejected. Here's the feedback:
    {critique}
    
    Please create a NEW prompt that addresses these issues.
    """
    else:
        prompt = base_instructions
    
    messages = [
        SystemMessage(content="You are an expert AI art prompter."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    image_prompt = response.content.strip()
    
    return {"image_prompt": image_prompt, "retry_count": current_retries + 1}
