import os
from crewai import Agent, LLM
from src.tools import search_tool, image_gen_tool, x_post_tool

# Define LLMs
# Using OpenRouter via OpenAI-compatible API

# Models
# using x-ai/grok-4.1-fast for searching/research (note: :free may not be a valid model suffix)
search_model = LLM(model="openrouter/x-ai/grok-4.1-fast")
# using openai/gpt-5-mini for text creation and other tasks
text_model = LLM(model="openrouter/openai/gpt-5-mini")

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
    llm=search_model
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
    llm=text_model
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
    llm=text_model
)

prompt_engineer = Agent(
    role='Visual Director',
    goal='Create a detailed image generation prompt based on the selected post text.',
    backstory="""You are a visual storytelling expert.
    You know how to translate abstract concepts into concrete visual descriptions.
    You create prompts that generative AI models can understand perfectly.""",
    verbose=True,
    allow_delegation=False,
    llm=text_model
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
    llm=text_model
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
    llm=text_model
)