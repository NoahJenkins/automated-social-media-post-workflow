from src.state import AgentState
from src.config import get_vision_llm
from langchain_core.messages import SystemMessage, HumanMessage

def image_reviewer_node(state: AgentState):
    """
    Reviews the generated image using GPT-4o Vision.
    """
    print("--- IMAGE REVIEWER AGENT ---")
    image_url = state.get("image_url")
    prompt_text = state.get("image_prompt")
    
    if not image_url:
        return {"image_approved": False, "critique": "No image generated."}
    
    llm = get_vision_llm()
    
    msg = HumanMessage(
        content=[
            {"type": "text", "text": f"Does this image match the following prompt? Prompt: '{prompt_text}'. Is it safe for work and high quality? Answer YES or NO first, then explain."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    )
    
    response = llm.invoke([msg])
    content = response.content
    
    is_approved = "YES" in content.upper()
    
    return {"image_approved": is_approved, "critique": content}
