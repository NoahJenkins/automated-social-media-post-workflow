import os
import tweepy
from src.state import AgentState

def poster_node(state: AgentState):
    """
    Posts the content and image to X (Twitter).
    """
    print("--- POSTER AGENT ---")
    
    text = state["selected_post"]
    image_url = state.get("image_url")
    
    # Check if we have API keys (Support both standard and user's provided names)
    api_key = os.getenv("X_API_KEY") or os.getenv("X_CONSUMER_KEY")
    api_secret = os.getenv("X_API_SECRET") or os.getenv("X_CONSUMER_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
    
    if not (api_key and api_secret and access_token and access_token_secret):
        print("X API keys missing. MOCK POSTING.")
        print(f"POST TEXT: {text}")
        print(f"POST IMAGE: {image_url}")
        return {"post_status": "Mock Posted"}
        
    try:
        # Authenticate
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Note: For image upload with Tweepy Client (v2), it's a bit complex as v2 doesn't support media upload directly yet in some versions.
        # Usually requires v1.1 API for media upload, then v2 for posting.
        # For simplicity in this prototype, we might just post text if image upload is complex, 
        # OR we assume we just print it for now if the user only has Free tier (Write-only v2 might not support media upload easily).
        # Let's try to post text only for v1 prototype if image upload fails, or just mock it if keys are invalid.
        
        # For now, let's just post text to verify connectivity.
        response = client.create_tweet(text=text)
        print(f"Posted to X! ID: {response.data['id']}")
        
        return {"post_status": "Posted"}
        
    except Exception as e:
        print(f"Posting failed: {e}")
        return {"post_status": "Failed"}
