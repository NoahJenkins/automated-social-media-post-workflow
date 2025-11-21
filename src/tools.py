import os
import requests
import tweepy
import base64
from crewai.tools import BaseTool
from crewai_tools import BraveSearchTool
from dotenv import load_dotenv

load_dotenv()

class ImageGenTool(BaseTool):
    name: str = "Image Generation Tool"
    description: str = "Generates an image based on a text prompt using OpenRouter's openai/gpt-5-image-mini model. Returns the local file path of the generated image."

    def _run(self, prompt: str) -> str:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return "Error: OPENROUTER_API_KEY not found in environment variables."

        # Using OpenRouter's image generation API
        url = "https://openrouter.ai/api/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-5-image-mini",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Extract image URL
            # Response format: {'data': [{'url': '...'}]}
            if 'data' in result and len(result['data']) > 0:
                image_url = result['data'][0]['url']

                # Download the image
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                image_data = image_response.content

                # Save to file
                filename = "generated_image.png"
                file_path = os.path.abspath(filename)
                with open(file_path, "wb") as f:
                    f.write(image_data)

                return file_path
            else:
                return f"Error: Unexpected response from OpenRouter. Response: {result}"

        except Exception as e:
            return f"Error generating image: {str(e)}"

class XPostTool(BaseTool):
    name: str = "X (Twitter) Posting Tool"
    description: str = "Posts text and optionally an image to X (formerly Twitter). Input should be a dictionary-like string or JSON with 'text' and optional 'image_url'."

    def _run(self, text: str, image_url: str = None) -> str:
        print("DEBUG: Starting XPostTool._run")
        consumer_key = os.getenv("X_CONSUMER_KEY")
        consumer_secret = os.getenv("X_CONSUMER_SECRET")
        access_token = os.getenv("X_ACCESS_TOKEN")
        access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

        if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
            print("DEBUG: Missing X API keys")
            return "Error: Missing X API keys in environment variables."

        try:
            print("DEBUG: Authenticating with Tweepy")
            # Authenticate v1.1 for media upload
            auth = tweepy.OAuth1UserHandler(
                consumer_key, consumer_secret, access_token, access_token_secret
            )
            # Create API with timeout
            api = tweepy.API(auth, timeout=30)

            # Authenticate v2 for posting
            client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            print("DEBUG: Authentication successful")

            media_id = None
            temp_filename = "temp_upload_image.jpg"

            if image_url:
                print(f"DEBUG: Processing image_url: {image_url}")
                # Check if it's a local file or URL
                if os.path.exists(image_url):
                    print(f"DEBUG: Image file exists: {os.path.exists(image_url)}")
                    file_size = os.path.getsize(image_url)
                    print(f"DEBUG: Image file size: {file_size} bytes")
                    if file_size == 0:
                        return "Error: Generated image file is empty"
                    if file_size > 5 * 1024 * 1024:  # 5MB limit for Twitter
                        return "Error: Image file too large (>5MB)"
                    print("DEBUG: Image is local file, uploading media")
                    # It's a local file
                    media = api.media_upload(filename=image_url)
                    media_id = media.media_id
                    print(f"DEBUG: Media uploaded, media_id: {media_id}")
                else:
                    print("DEBUG: Image is URL, downloading")
                    # Assume URL
                    response = requests.get(image_url, stream=True)
                    response.raise_for_status()
                    with open(temp_filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    print("DEBUG: Downloaded image, uploading media")
                    # Upload media using v1.1 API
                    media = api.media_upload(filename=temp_filename)
                    media_id = media.media_id
                    print(f"DEBUG: Media uploaded from URL, media_id: {media_id}")

                    # Clean up
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                        print("DEBUG: Cleaned up temp file")

            print("DEBUG: Creating tweet")
            # Post tweet using v2 API
            if media_id:
                response = client.create_tweet(text=text, media_ids=[media_id])
            else:
                response = client.create_tweet(text=text)

            print(f"DEBUG: Tweet created successfully, ID: {response.data['id']}")
            return f"Successfully posted to X! Tweet ID: {response.data['id']}"

        except Exception as e:
            print(f"DEBUG: Exception in XPostTool: {str(e)}")
            return f"Error posting to X: {str(e)}"

# Initialize tools
search_tool = BraveSearchTool()
image_gen_tool = ImageGenTool()
x_post_tool = XPostTool()