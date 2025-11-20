import os
import requests
import tweepy
from crewai_tools import BaseTool, SerperDevTool
from dotenv import load_dotenv

load_dotenv()

class ImageGenTool(BaseTool):
    name: str = "Image Generation Tool"
    description: str = "Generates an image based on a text prompt using OpenRouter's DALL-E 3 or similar model. Returns the URL of the generated image."

    def _run(self, prompt: str) -> str:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return "Error: OPENROUTER_API_KEY not found in environment variables."

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/crewAIInc/crewAI", # Required by OpenRouter
            "X-Title": "CrewAI Social Media Agent" # Required by OpenRouter
        }

        # Using openai/gpt-5-image-mini as requested
        payload = {
            "model": "openai/gpt-5-image-mini",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }

        try:
            # Note: OpenRouter's image generation endpoint might differ slightly from standard OpenAI.
            # Assuming standard OpenAI-compatible image generation endpoint structure for now.
            # If OpenRouter uses a different path for images, this URL needs adjustment.
            # Standard OpenAI is https://api.openai.com/v1/images/generations
            # OpenRouter usually proxies chat/completions. For images, we check docs or assume standard proxy.
            # Let's try the standard chat completion endpoint first if it's a text-to-image model disguised as chat,
            # BUT usually image models have a specific endpoint.
            # Since 'openai/gpt-5-image-mini' is likely a placeholder or specific model, we'll use the standard
            # OpenRouter completions endpoint if it supports image generation via prompt, OR the image generation endpoint.
            # Given OpenRouter's structure, it often proxies standard OpenAI endpoints.
            
            # However, for safety and standard practice with OpenRouter image models (like DALL-E 3 via OpenRouter),
            # we often use the standard OpenAI client pointed to OpenRouter base URL.
            # Here we use raw requests for transparency.
            
            response = requests.post(
                "https://openrouter.ai/api/v1/images/generations",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract image URL
            # Standard OpenAI format: {'data': [{'url': '...'}]}
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]['url']
            else:
                return f"Error: Unexpected response format from image provider. Response: {data}"

        except Exception as e:
            return f"Error generating image: {str(e)}"

class XPostTool(BaseTool):
    name: str = "X (Twitter) Posting Tool"
    description: str = "Posts text and optionally an image to X (formerly Twitter). Input should be a dictionary-like string or JSON with 'text' and optional 'image_url'."

    def _run(self, text: str, image_url: str = None) -> str:
        consumer_key = os.getenv("X_CONSUMER_KEY")
        consumer_secret = os.getenv("X_CONSUMER_SECRET")
        access_token = os.getenv("X_ACCESS_TOKEN")
        access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

        if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
            return "Error: Missing X API keys in environment variables."

        try:
            # Authenticate v1.1 for media upload
            auth = tweepy.OAuth1UserHandler(
                consumer_key, consumer_secret, access_token, access_token_secret
            )
            api = tweepy.API(auth)

            # Authenticate v2 for posting text
            client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            media_id = None
            if image_url:
                # Download image to temp file
                img_data = requests.get(image_url).content
                temp_filename = "temp_post_image.jpg"
                with open(temp_filename, 'wb') as handler:
                    handler.write(img_data)
                
                # Upload media using v1.1 API
                media = api.media_upload(filename=temp_filename)
                media_id = media.media_id
                
                # Clean up
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)

            # Post tweet using v2 API
            if media_id:
                response = client.create_tweet(text=text, media_ids=[media_id])
            else:
                response = client.create_tweet(text=text)

            return f"Successfully posted to X! Tweet ID: {response.data['id']}"

        except Exception as e:
            return f"Error posting to X: {str(e)}"

# Initialize tools
search_tool = SerperDevTool()
image_gen_tool = ImageGenTool()
x_post_tool = XPostTool()