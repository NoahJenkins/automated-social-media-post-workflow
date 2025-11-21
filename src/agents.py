import os
from crewai import Agent, LLM
from src.tools import search_tool, image_gen_tool, x_post_tool

# Define LLMs
# Note: CrewAI uses LiteLLM under the hood.
# We need to set OPENAI_API_BASE to OpenRouter's URL and OPENAI_API_KEY to OpenRouter Key
# However, since we might want different models for different agents, we can instantiate them directly.

# Helper to create Gemini LLM instance
def create_gemini_llm(model_name):
    return LLM(
        model=f"gemini/{model_name}",
        api_key=os.getenv("GEMINI_API_KEY")
    )

# Models
# using gemini-2.5-pro for complex tasks (research, writing)
research_model = create_gemini_llm("gemini-2.5-pro")
# using gemini-2.5-flash for faster/simpler tasks (editing, image prompt, etc)
fast_model = create_gemini_llm("gemini-2.5-flash")

# Agents

researcher = Agent(
    role='Trend Researcher',
    goal='Find the most relevant and trending topics in the user\'s niche.',
    backstory="""You are an expert researcher who lives on the internet. 
    You know exactly what is trending and what people are talking about. 
    Your job is to find the hottest topics that would make for great social media content.""",
    verbose=True,
    allow_delegation=False,
    tools=[search_tool],
    llm=research_model
)

writer = Agent(
    role='Social Media Writer',
    goal='Draft 3 engaging and viral-worthy social media posts based on research.',
    backstory="""You are a creative copywriter with a knack for viral content. 
    You understand the nuances of social media platforms like X (Twitter). 
    You avoid generic excitement and clichés. Instead, you use wit, strong opinions, or intriguing questions to drive engagement.
    You always provide 3 distinct options for every topic.""",
    verbose=True,
    allow_delegation=False,
    llm=research_model
)

editor = Agent(
    role='Chief Editor',
    goal='Review drafts and select the single best option for publication.',
    backstory="""You are a seasoned editor with a sharp eye for quality. 
    You ensure that all content aligns with the brand's voice and is error-free. 
    You prioritize posts that have a clear Call to Action and are likely to spark conversation.
    You are decisive and can pick the winner from a set of options.""",
    verbose=True,
    allow_delegation=False,
    llm=fast_model
)

prompt_engineer = Agent(
    role='Visual Director',
    goal='Create a detailed image generation prompt based on the selected post text.',
    backstory="""You are a visual storytelling expert. 
    You know how to translate abstract concepts into concrete visual descriptions. 
    You create prompts that generative AI models can understand perfectly.""",
    verbose=True,
    allow_delegation=False,
    llm=fast_model
)

image_reviewer = Agent(
    role='Image Reviewer',
    goal='Generate an image and review it to ensure it matches the prompt and quality standards.',
    backstory="""You are a quality assurance specialist for visual assets. 
    You are responsible for generating the image using the provided tools and then inspecting it.
    If the image is good, you approve it. If not, you might need to try again (though for this workflow, we'll assume one shot for now).""",
    verbose=True,
    allow_delegation=False,
    tools=[image_gen_tool], # This agent uses the image gen tool
    llm=fast_model
)

poster = Agent(
    role='Social Media Manager',
    goal='Publish the final approved content to X (Twitter).',
    backstory="""You are the final step in the pipeline. 
    You take the polished text and the approved image and broadcast them to the world. 
    You ensure the technical delivery is flawless.""",
    verbose=True,
    allow_delegation=False,
    tools=[x_post_tool],
    llm=fast_model
)