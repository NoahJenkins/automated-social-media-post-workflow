from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import BraveSearch
import datetime
from src.state import AgentState
from src.config import get_llm, TAVILY_API_KEY, BRAVE_API_KEY
from langchain_core.messages import SystemMessage, HumanMessage

def researcher_node(state: AgentState):
    """
    Researches trending topics in Tech & Work Culture.
    """
    print("--- RESEARCHER AGENT ---")
    
    # 1. Determine Day & Theme
    today = datetime.datetime.now().strftime("%A")
    
    daily_themes = {
        "Monday": "Motivation, Goals, Planning, Future Tech",
        "Tuesday": "Tools, Tips, Tutorials, How-to",
        "Wednesday": "Mid-week insights, AI trends, Deep dives",
        "Thursday": "Throwback, History of Tech, Coding challenges",
        "Friday": "Fun, Weekend vibes, wrapping up, humor",
        "Saturday": "Side projects, Learning, Relaxed coding",
        "Sunday": "Reflection, Preparation for the week, Career advice"
    }
    
    theme = daily_themes.get(today, "General Tech Trends")
    print(f"Today is {today}. Theme: {theme}")

    # 2. Search for trends with theme
    query = f"trending topics in tech industry {theme}"
    results = []
    
    try:
        if TAVILY_API_KEY:
            search = TavilySearchResults(max_results=5)
            results = search.invoke(query)
            # Format results for Tavily
            context = "\n".join([f"- {r['content']} (Source: {r['url']})" for r in results])
        elif BRAVE_API_KEY:
            search = BraveSearch.from_api_key(api_key=BRAVE_API_KEY, search_kwargs={"count": 5})
            # Brave returns a JSON string or dict, need to handle it. 
            # LangChain's BraveSearch usually returns a JSON string in 'run' or list of docs.
            # Let's use invoke which returns a JSON string usually.
            raw_results = search.invoke(query)
            # Brave tool output format can vary. Assuming it returns a string representation of results.
            context = str(raw_results)
        else:
            raise ValueError("No Search API Key found (Tavily or Brave).")
            
    except Exception as e:
        print(f"Search failed: {e}")
        context = "Could not fetch live trends. Using fallback topics: AI Agents, Remote Work Life, Developer Burnout."

    # 2. Summarize and pick a topic (Optional: could just pass raw results, but let's pick one)
    llm = get_llm("gpt-4o-mini")
    messages = [
        SystemMessage(content=f"You are a trend researcher. Today is {today} and the theme is '{theme}'. Analyze the search results and pick the ONE most engaging trending topic for a fun social media post about tech/work culture that fits this theme."),
        HumanMessage(content=f"Search Results:\n{context}")
    ]
    response = llm.invoke(messages)
    topic = response.content
    
    return {"topic": topic, "research_results": context, "day_of_week": today, "theme": theme}
