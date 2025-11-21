import os
from src.workflow import build_graph
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("Starting Automated Social Media Post Workflow...")
    
    app = build_graph()
    
    # Initial State
    initial_state = {
        "topic": None,
        "research_results": None,
        "draft_posts": [],
        "selected_post": None,
        "image_prompt": None,
        "image_url": None,
        "image_approved": False,
        "critique": None,
        "post_status": None
    }
    
    # Run the graph
    try:
        for output in app.stream(initial_state):
            for key, value in output.items():
                print(f"Finished Node: {key}")
                # print(f"Output: {value}") # Verbose
                
    except Exception as e:
        print(f"Workflow failed: {e}")

if __name__ == "__main__":
    main()
