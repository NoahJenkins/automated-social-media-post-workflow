import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.saver import saver_node
from src.state import AgentState

def test_saver_node():
    # Mock state with a real image URL (using httpbin.org for testing)
    state = {
        "selected_post": "This is a test post.",
        "image_url": "https://httpbin.org/image/png",
        "topic": "Test Topic"
    }
    
    print("Running saver_node with mock state...")
    result = saver_node(state)
    print(f"Result: {result}")
    
    # Check if file exists
    # Note: The filename generation logic in saver.py uses the current timestamp, 
    # so we can't predict the exact filename easily without modifying the code or listing the directory.
    # For this test, we'll just check if the images directory exists and has files.
    
    images_dir = "social_media_posts/images"
    if os.path.exists(images_dir) and os.listdir(images_dir):
        print(f"Success: Images directory '{images_dir}' exists and is not empty.")
        print(f"Files in images directory: {os.listdir(images_dir)}")
    else:
        print(f"Failure: Images directory '{images_dir}' does not exist or is empty.")

if __name__ == "__main__":
    test_saver_node()
