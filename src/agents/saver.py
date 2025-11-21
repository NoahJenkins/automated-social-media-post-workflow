import os
import base64
import requests
from datetime import datetime
from src.state import AgentState

def saver_node(state: AgentState):
    """
    Saves the generated post and image to a local markdown file.
    """
    print("--- SAVER AGENT ---")
    
    post_text = state.get("selected_post")
    image_url = state.get("image_url")
    topic = state.get("topic", "unknown_topic")
    
    # Sanitize topic for filename
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_', '-')).rstrip().replace(' ', '_')
    safe_topic = safe_topic[:50] # Truncate to avoid file name too long errors
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create directories
    posts_dir = "social_media_posts"
    images_dir = os.path.join(posts_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    filename = f"{posts_dir}/{timestamp}_{safe_topic}.md"
    
    image_markdown = ""
    
    if image_url:
        if image_url.startswith("data:"):
            try:
                print("Image is a data URI, decoding and saving...")
                # Extract base64 data from data URI
                # Format: data:image/png;base64,<base64_data>
                base64_data = image_url.split(",")[1]
                image_data = base64.b64decode(base64_data)
                
                image_filename = f"{timestamp}_{safe_topic}.png"
                image_path = os.path.join(images_dir, image_filename)
                
                with open(image_path, "wb") as f:
                    f.write(image_data)
                
                # Use relative path for markdown
                relative_image_path = f"images/{image_filename}"
                image_markdown = f"![Generated Image]({relative_image_path})"
                print(f"Image saved to {image_path}")
                
            except Exception as e:
                print(f"Failed to decode or save data URI: {e}")
                image_markdown = f"> [!WARNING]\n> Failed to save image from data URI\n> Error: {e}"
        else:
            try:
                print(f"Downloading image from: {image_url}")
                response = requests.get(image_url)
                response.raise_for_status()
                
                image_filename = f"{timestamp}_{safe_topic}.png"
                image_path = os.path.join(images_dir, image_filename)
                
                with open(image_path, "wb") as f:
                    f.write(response.content)
                
                # Use relative path for markdown
                relative_image_path = f"images/{image_filename}"
                image_markdown = f"![Generated Image]({relative_image_path})"
                print(f"Image saved to {image_path}")
                
            except Exception as e:
                print(f"Failed to download or save image: {e}")
                image_markdown = f"> [!WARNING]\n> Failed to download image from {image_url}\n> Error: {e}"
    else:
        print("No image URL found in state.")
        image_markdown = "> [!NOTE]\n> No image was generated for this post."

    content = f"""# Social Media Post
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Topic:** {topic}

## Content
{post_text}

## Image
{image_markdown}
"""

    try:
        with open(filename, "w") as f:
            f.write(content)
        print(f"Saved post to {filename}")
    except Exception as e:
        print(f"Failed to save post to file: {e}")

    return {"post_status": "Saved"}
