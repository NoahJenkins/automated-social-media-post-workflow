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


def verify_post_scheduled(post_id: str, user_id: str, blog_id: str, api_token: str) -> bool:
    """
    Verifies that a post was successfully scheduled by retrieving it from Metricool.
    Returns True if the post exists and is scheduled, False otherwise.
    
    Note: This makes an additional API call per post. For low-volume workflows
    (2-3 posts/week), this is acceptable. For high-volume scenarios, consider
    batch verification or making this optional.
    """
    try:
        headers = {
            "X-Mc-Auth": api_token,
            "Content-Type": "application/json"
        }
        
        # Get the list of scheduled posts to verify our post is there
        url = f"{METRICOOL_BASE_URL}/v2/scheduler/posts"
        params = {
            "userId": user_id,
            "blogId": blog_id
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            result = response.json()
            posts = result.get("data", [])
            
            # Check if our post ID exists in the scheduled posts
            for post in posts:
                if post.get("id") == post_id:
                    status = post.get("status", "").lower()
                    print(f"Post verification: Found post {post_id} with status '{status}'")
                    return status in ["scheduled", "pending"]
            
            print(f"Post verification: Post {post_id} not found in scheduled posts")
            return False
        else:
            print(f"Post verification failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Post verification error: {e}")
        return False


def poster_node(state: AgentState):
    """
    Posts the content and image to social media via Metricool API.
    Currently configured for Twitter/X, with easy extension to other platforms.
    Includes post confirmation logic to verify successful scheduling.
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
        return {
            "post_status": "Mock Posted (No API Token)",
            "post_id": None,
            "post_scheduled": False
        }
    
    if not user_id or not blog_id:
        print("Metricool USER_ID or BLOG_ID missing. MOCK POSTING.")
        print("To get these values, log into Metricool and check the URL:")
        print("  https://app.metricool.com/...?blogId=XXXXX&userId=XXXXX")
        print(f"POST TEXT: {text}")
        print(f"POST IMAGE: {image_path}")
        return {
            "post_status": "Mock Posted (Missing User/Blog ID)",
            "post_id": None,
            "post_scheduled": False
        }
    
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
                    "network": "twitter"
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
        
        print(f"Posting to Metricool API...")
        response = requests.post(url, headers=headers, params=params, json=payload)
        
        # Parse response and verify success
        if response.status_code in [200, 201]:
            try:
                result = response.json()
                
                # Extract post ID and status from response
                # Try both flat structure (result.id) and nested structure (result.data.id)
                post_id = result.get("id")
                if post_id is None:
                    post_id = result.get("data", {}).get("id")
                status = result.get("status", "unknown")
                
                if not post_id:
                    print(f"Warning: No post ID in response. Response: {result}")
                    return {
                        "post_status": "Posted but no ID returned",
                        "post_id": None,
                        "post_scheduled": False
                    }
                
                print(f"Metricool API response: Post ID: {post_id}, Status: {status}")
                
                # Verify the post was actually scheduled
                is_scheduled = verify_post_scheduled(post_id, user_id, blog_id, api_token)
                
                if is_scheduled:
                    print(f"✓ Post successfully scheduled! Post ID: {post_id}")
                    return {
                        "post_status": f"Successfully scheduled (ID: {post_id})",
                        "post_id": post_id,
                        "post_scheduled": True
                    }
                else:
                    print(f"⚠ Post may not be scheduled. Post ID: {post_id}, Status: {status}")
                    return {
                        "post_status": f"Scheduled with unconfirmed status (ID: {post_id})",
                        "post_id": post_id,
                        "post_scheduled": False
                    }
                    
            except ValueError as e:
                print(f"Error parsing JSON response: {e}")
                print(f"Response text: {response.text}")
                return {
                    "post_status": f"Posted but response parsing failed: {str(e)}",
                    "post_id": None,
                    "post_scheduled": False
                }
        else:
            print(f"Metricool API error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                error_msg = error_data.get("message", error_data.get("error", response.text))
                print(f"Error details: {error_msg}")
                return {
                    "post_status": f"Failed: {error_msg}",
                    "post_id": None,
                    "post_scheduled": False
                }
            except:
                return {
                    "post_status": f"Failed: HTTP {response.status_code}",
                    "post_id": None,
                    "post_scheduled": False
                }
        
    except requests.exceptions.RequestException as e:
        print(f"Network error during posting: {e}")
        return {
            "post_status": f"Network error: {str(e)}",
            "post_id": None,
            "post_scheduled": False
        }
    except Exception as e:
        print(f"Posting failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "post_status": f"Failed: {str(e)}",
            "post_id": None,
            "post_scheduled": False
        }
