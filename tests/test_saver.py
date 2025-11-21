import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.saver import saver_node
from src.state import AgentState

def test_saver():
    print("Testing saver node...")
    
    # Mock state
    state = {
        "selected_post": "This is a test post for the saver node.",
        "image_url": "https://via.placeholder.com/150", # Use a placeholder image
        "topic": "Test Topic",
        "retry_count": 0,
        "image_approved": True
    }
    
    result = saver_node(state)
    print(f"Result: {result}")
    
    # Check if file exists
    # Note: Filename depends on timestamp, so we just check if any file exists in the directory
    files = os.listdir("social_media_posts")
    if files:
        print(f"Found files in social_media_posts: {files}")
        print("Test PASSED")
    else:
        print("No files found in social_media_posts")
        print("Test FAILED")

if __name__ == "__main__":
    test_saver()
