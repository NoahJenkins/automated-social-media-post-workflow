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
    description: str = "Generates an image based on a text prompt using Gemini's Imagen 4 model. Returns the local file path of the generated image."

    def _run(self, prompt: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY not found in environment variables."

        # Using Gemini's Imagen 4 model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1}
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract base64 image
            # Response format: {'predictions': [{'bytesBase64Encoded': '...'}]}
            if 'predictions' in result and len(result['predictions']) > 0:
                b64_data = result['predictions'][0]['bytesBase64Encoded']
                image_data = base64.b64decode(b64_data)
                
                # Save to file
                filename = "generated_image.png"
                file_path = os.path.abspath(filename)
                with open(file_path, "wb") as f:
                    f.write(image_data)
                
                return file_path
            else:
                return f"Error: Unexpected response from Gemini. Response: {result}"

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

            # Authenticate v2 for posting
            client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            media_id = None
            temp_filename = "temp_upload_image.jpg"

            if image_url:
                # Check if it's a local file or URL
                if os.path.exists(image_url):
                    # It's a local file
                    media = api.media_upload(filename=image_url)
                    media_id = media.media_id
                else:
                    # Assume URL
                    response = requests.get(image_url, stream=True)
                    response.raise_for_status()
                    with open(temp_filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
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
search_tool = BraveSearchTool()
image_gen_tool = ImageGenTool()
x_post_tool = XPostTool()