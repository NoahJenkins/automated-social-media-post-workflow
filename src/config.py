import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

# Load environment variables
load_dotenv()

# Initialize LLM cache for repeated prompts (reduces costs on retries/similar themes)
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))

# Validate API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

# Metricool Configuration
METRICOOL_API_TOKEN = os.getenv("METRICOOL_API")
METRICOOL_USER_ID = os.getenv("METRICOOL_USER_ID")
METRICOOL_BLOG_ID = os.getenv("METRICOOL_BLOG_ID")

# Azure Storage Configuration (for image uploads to Metricool)
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

# Social Networks Configuration
# Comma-separated list of networks to post to: twitter, facebook, instagram, linkedin
# Default is twitter only for backward compatibility
SOCIAL_NETWORKS = os.getenv("SOCIAL_NETWORKS", "twitter").lower().split(",")
SOCIAL_NETWORKS = [net.strip() for net in SOCIAL_NETWORKS if net.strip()]
# Ensure at least one network is configured, default to twitter
if not SOCIAL_NETWORKS:
    SOCIAL_NETWORKS = ["twitter"]

# Feature Flags
ENABLE_POSTING = os.getenv("ENABLE_POSTING", "False").lower() == "true"

if not OPENAI_API_KEY and not OPENROUTER_API_KEY:
    raise ValueError("Neither OPENAI_API_KEY (or OPENAI_KEY) nor OPENROUTER_API_KEY is set in .env")

# Initialize Models
def get_llm(model_name="gpt-5-mini"):
    """Returns a ChatOpenAI instance for the specified model."""
    if OPENROUTER_API_KEY:
        # OpenRouter Configuration
        return ChatOpenAI(
            model=model_name,
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
            model="gpt-5",
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            max_tokens=1000,
            temperature=0  # Deterministic for consistent image reviews
        )
    else:
        return ChatOpenAI(model="gpt-5", max_tokens=1000, temperature=0)
