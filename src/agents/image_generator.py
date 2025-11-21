from src.state import AgentState
from src.config import OPENAI_API_KEY, OPENROUTER_API_KEY
from openai import OpenAI
import os

def image_generator_node(state: AgentState):
    """
    Generates an image using DALL-E 3 via OpenAI or OpenRouter.
    """
    print("--- IMAGE GENERATOR AGENT ---")
    prompt = state["image_prompt"]
    
    # Determine Client Configuration
    api_key = OPENAI_API_KEY or OPENROUTER_API_KEY or os.getenv("OPENAI_KEY")
    base_url = "https://openrouter.ai/api/v1" if OPENROUTER_API_KEY and not (OPENAI_API_KEY or os.getenv("OPENAI_KEY")) else None
    
    if not api_key:
        print("No API Key for Image Generation.")
        return {"image_url": None}
        
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    try:
        # Model name might need adjustment for OpenRouter
        model = "openai/gpt-image-1-mini" if OPENROUTER_API_KEY and not (OPENAI_API_KEY or os.getenv("OPENAI_KEY")) else "gpt-image-1-mini"
        
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="medium"
        )
        
        image_url = response.data[0].url
        return {"image_url": image_url}
        
    except Exception as e:
        print(f"Image generation failed: {e}")
        return {"image_url": None}
