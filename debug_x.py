import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

def test_x():
    print("--- TESTING X API ---")
    
    api_key = os.getenv("X_API_KEY") or os.getenv("X_CONSUMER_KEY")
    api_secret = os.getenv("X_API_SECRET") or os.getenv("X_CONSUMER_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
    
    print(f"API Key Present: {bool(api_key)}")
    print(f"Access Token Present: {bool(access_token)}")
    
    if not (api_key and api_secret and access_token and access_token_secret):
        print("ERROR: Missing Keys")
        return

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    
    try:
        me = client.get_me()
        print(f"Authenticated as: {me.data.name} (@{me.data.username})")
        print("Authentication Successful!")
    except Exception as e:
        print(f"Authentication Failed: {e}")
        return

    try:
        print("Attempting to post test tweet...")
        response = client.create_tweet(text="Test tweet from automated workflow debug script.")
        print(f"SUCCESS! Posted tweet ID: {response.data['id']}")
    except Exception as e:
        print(f"Posting Failed: {e}")

if __name__ == "__main__":
    test_x()
