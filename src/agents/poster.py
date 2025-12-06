import os
import requests
import base64
from datetime import datetime, timezone, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from src.state import AgentState
from src.config import SOCIAL_NETWORKS

# Metricool API Configuration
METRICOOL_BASE_URL = "https://app.metricool.com/api"


def upload_image_to_metricool(image_input: str) -> str | None:
    """
    Uploads an image (data URI, URL, or local path) to Azure Blob Storage
    and returns the public blob URL for use in Metricool API.
    """
    if not image_input:
        print("Warning: No image provided to upload_image_to_metricool")
        return None
    
    try:
        # Get Azure credentials
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
        
        if not connection_string or not container_name:
            print("⚠️  WARNING: Azure Storage credentials missing!")
            print("    Set AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER_NAME")
            print("    in your .env file to upload images to Metricool.")
            print("    Post will be created WITHOUT an image.")
            return None
        
        # Get image bytes from input
        image_bytes = None
        if image_input.startswith("data:"):
            # Data URI: extract base64 and decode
            try:
                header, encoded = image_input.split(",", 1)
                image_bytes = base64.b64decode(encoded)
            except ValueError:
                print(f"Invalid data URI format: {image_input[:50]}...")
                return None
        elif image_input.startswith("http://") or image_input.startswith("https://"):
            # HTTP URL: fetch the image
            try:
                response = requests.get(image_input, timeout=30)
                response.raise_for_status()
                image_bytes = response.content
            except requests.RequestException as e:
                print(f"Failed to fetch image from URL: {e}")
                return None
        else:
            # Assume local file path
            if os.path.exists(image_input):
                with open(image_input, "rb") as f:
                    image_bytes = f.read()
            else:
                print(f"Local image file not found: {image_input}")
                return None
        
        if not image_bytes:
            print("No image data to upload")
            return None
        
        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Generate unique blob name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        # Sanitize topic for filename if available, else use generic
        topic_part = "social_post_image"  # fallback
        blob_name = f"{timestamp}_{topic_part}.png"  # assume PNG, but could detect
        
        # Upload to blob
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(image_bytes, overwrite=True)
        
        # Generate SAS URL for public access
        # Extract account name and key from connection string
        account_name = connection_string.split("AccountName=")[1].split(";")[0]
        account_key = connection_string.split("AccountKey=")[1].split(";")[0]
        
        # Generate SAS token valid for 24 hours
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        
        # Return public SAS URL
        public_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        
        print(f"Image uploaded to Azure Blob Storage: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"Error uploading image to Azure: {e}")
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
            # The API returns {posts: [...]} not {data: [...]}
            posts = result.get("posts", [])
            
            # Check if our post ID exists in the scheduled posts
            for post in posts:
                if str(post.get("id")) == str(post_id):
                    status = post.get("status", "").lower()
                    print(f"Post verification: Found post {post_id} with status '{status}'")
                    return status in ["scheduled", "pending"]
            
            print(f"Post verification: Post {post_id} not found in {len(posts)} scheduled posts")
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
    Supports multiple networks: Twitter/X, Facebook, Instagram, LinkedIn.
    Networks are configured via SOCIAL_NETWORKS environment variable.
    Includes post confirmation logic to verify successful scheduling.
    """
    print("--- POSTER AGENT (Metricool) ---")
    
    text = state["selected_post"]
    image_path = state.get("image_url")  # This can be a URL, data URI, or local file path
    
    # Get Metricool credentials
    api_token = os.getenv("METRICOOL_API")
    user_id = os.getenv("METRICOOL_USER_ID")
    blog_id = os.getenv("METRICOOL_BLOG_ID")
    
    print(f"Configured networks: {', '.join(SOCIAL_NETWORKS)}")
    
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
        # Schedule post 5 minutes in the future (Metricool may not support immediate posting)
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        scheduled_time = now + timedelta(minutes=5)
        publication_date = {
            "dateTime": scheduled_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "timezone": "UTC"
        }
        
        # Prepare media if we have an image
        media_urls = []
        if image_path:
            print(f"Attempting to upload image: {image_path[:100]}...")
            media_url = upload_image_to_metricool(image_path)
            if media_url:
                media_urls.append(media_url)
                print(f"✓ Image uploaded successfully")
            else:
                print(f"⚠️  Image upload failed - posting without image")
        else:
            print("ℹ️  No image provided for this post")
        
        # Build the providers array from configured networks
        # Metricool network names: twitter, facebook, instagram, linkedin
        providers = []
        for network in SOCIAL_NETWORKS:
            providers.append({"network": network})
        
        if not providers:
            print("⚠️  WARNING: No social networks configured! Defaulting to Twitter.")
            providers = [{"network": "twitter"}]
        
        # Build the post payload
        payload = {
            "text": text,
            "publicationDate": publication_date,
            "providers": providers,
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
        print(f"  Networks: {', '.join([p['network'] for p in providers])}")
        print(f"  Media attached: {'Yes' if media_urls else 'No'}")
        print(f"  Scheduled for: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        response = requests.post(url, headers=headers, params=params, json=payload)
        
        # Parse response and verify success
        if response.status_code in [200, 201]:
            try:
                result = response.json()
                print(f"DEBUG: Full Metricool API response: {result}")
                
                # Extract post data from response
                # API returns {'data': {...}} structure
                post_data = result.get("data", {})
                post_id = post_data.get("id")
                
                if not post_id:
                    print(f"Warning: No post ID in response. Response: {result}")
                    return {
                        "post_status": "Posted but no ID returned",
                        "post_id": None,
                        "post_scheduled": False
                    }
                
                # Check providers status to verify scheduling
                providers_response = post_data.get("providers", [])
                if providers_response:
                    # Check if any provider has PENDING or scheduled status
                    provider_statuses = [p.get("status", "").upper() for p in providers_response]
                    is_scheduled = any(status in ["PENDING", "SCHEDULED"] for status in provider_statuses)
                    status_str = ", ".join([f"{p.get('network')}: {p.get('status')}" for p in providers_response])
                    
                    print(f"Metricool API response: Post ID: {post_id}")
                    print(f"  Provider statuses: {status_str}")
                    print(f"  Media included: {'Yes' if media_urls else 'No'}")
                    
                    if is_scheduled:
                        networks_str = ", ".join([p.get('network') for p in providers_response])
                        print(f"✓ Post successfully scheduled for: {networks_str}")
                        return {
                            "post_status": f"Successfully scheduled on {networks_str} (ID: {post_id})",
                            "post_id": post_id,
                            "post_scheduled": True
                        }
                    else:
                        print(f"⚠ Post created but status unclear: {status_str}")
                        return {
                            "post_status": f"Created with status: {status_str} (ID: {post_id})",
                            "post_id": post_id,
                            "post_scheduled": False
                        }
                else:
                    print(f"⚠ No providers in response. Post ID: {post_id}")
                    return {
                        "post_status": f"Created but no provider status (ID: {post_id})",
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
