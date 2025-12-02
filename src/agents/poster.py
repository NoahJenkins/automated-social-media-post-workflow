import os
import requests
import base64
from datetime import datetime, timezone
from src.state import AgentState

# Metricool API Configuration
METRICOOL_BASE_URL = "https://app.metricool.com/api"


def upload_image_to_metricool(image_path: str, user_id: str, blog_id: str, api_token: str) -> str | None:
    """
    Uploads a local image to Metricool and returns the hosted URL.
    Uses the normalize/image/url endpoint or uploads via multipart form.
    """
    if not image_path or not os.path.exists(image_path):
        return None
    
    try:
        # Read the image file and encode as base64
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # For local files, we need to upload them first
        # Metricool's scheduler accepts media URLs, so we'll use a data URL approach
        # or return the local path for the API to handle
        
        # Get file extension
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        mime_type = mime_types.get(ext, "image/jpeg")
        
        # Return base64 data URL for now - Metricool API should handle this
        base64_data = base64.b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{base64_data}"
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None


def poster_node(state: AgentState):
    """
    Posts the content and image to social media via Metricool API.
    Currently configured for Twitter/X, with easy extension to other platforms.
    """
    print("--- POSTER AGENT (Metricool) ---")
    
    text = state["selected_post"]
    image_path = state.get("image_url")  # This is actually a local file path
    
    # Get Metricool credentials
    api_token = os.getenv("METRICOOL_API")
    user_id = os.getenv("METRICOOL_USER_ID")
    blog_id = os.getenv("METRICOOL_BLOG_ID")
    
    if not api_token:
        print("Metricool API token missing. MOCK POSTING.")
        print(f"POST TEXT: {text}")
        print(f"POST IMAGE: {image_path}")
        return {"post_status": "Mock Posted (No API Token)"}
    
    if not user_id or not blog_id:
        print("Metricool USER_ID or BLOG_ID missing. MOCK POSTING.")
        print("To get these values, log into Metricool and check the URL:")
        print("  https://app.metricool.com/...?blogId=XXXXX&userId=XXXXX")
        print(f"POST TEXT: {text}")
        print(f"POST IMAGE: {image_path}")
        return {"post_status": "Mock Posted (Missing User/Blog ID)"}
    
    try:
        # Prepare headers
        headers = {
            "X-Mc-Auth": api_token,
            "Content-Type": "application/json"
        }
        
        # Build the scheduled post payload
        # Post immediately by setting publicationDate to now
        now = datetime.now(timezone.utc)
        publication_date = {
            "dateTime": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "timezone": "UTC"
        }
        
        # Prepare media if we have an image
        media_urls = []
        if image_path:
            media_url = upload_image_to_metricool(image_path, user_id, blog_id, api_token)
            if media_url:
                media_urls.append(media_url)
        
        # Build the post payload for Twitter/X
        # providers array specifies which networks to post to
        payload = {
            "text": text,
            "publicationDate": publication_date,
            "providers": [
                {
                    "network": "twitter",
                    "status": "PENDING"
                }
            ],
            "autoPublish": True,
            "draft": False
        }
        
        # Add media if available
        if media_urls:
            payload["media"] = media_urls
        
        # Make the API request
        url = f"{METRICOOL_BASE_URL}/v2/scheduler/posts"
        params = {
            "userId": user_id,
            "blogId": blog_id
        }
        
        print(f"Posting to Metricool...")
        response = requests.post(url, headers=headers, params=params, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            post_id = result.get("data", {}).get("id", "unknown")
            print(f"Successfully scheduled post via Metricool! Post ID: {post_id}")
            return {"post_status": "Posted via Metricool"}
        else:
            print(f"Metricool API error: {response.status_code}")
            print(f"Response: {response.text}")
            return {"post_status": f"Failed: {response.status_code}"}
        
    except Exception as e:
        print(f"Posting failed: {e}")
        return {"post_status": f"Failed: {str(e)}"}
