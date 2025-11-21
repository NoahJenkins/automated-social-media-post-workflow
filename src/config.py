import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Validate API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

# Feature Flags
ENABLE_POSTING = os.getenv("ENABLE_POSTING", "False").lower() == "true"

if not OPENAI_API_KEY and not OPENROUTER_API_KEY:
    raise ValueError("Neither OPENAI_API_KEY (or OPENAI_KEY) nor OPENROUTER_API_KEY is set in .env")

# Initialize Models
def get_llm(model_name="gpt-4o"):
    """Returns a ChatOpenAI instance for the specified model."""
    if OPENROUTER_API_KEY:
        # OpenRouter Configuration
        return ChatOpenAI(
            model=f"openai/{model_name}", # OpenRouter often requires 'provider/model' or just 'model' depending on mapping. 'openai/gpt-4o' is safe.
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7
        )
    else:
        return ChatOpenAI(model=model_name, temperature=0.7)

def get_vision_llm():
    """Returns a ChatOpenAI instance for vision tasks."""
    if OPENROUTER_API_KEY:
        return ChatOpenAI(
            model="openai/gpt-4o",
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            max_tokens=1000
        )
    else:
        return ChatOpenAI(model="gpt-4o", max_tokens=1000)
