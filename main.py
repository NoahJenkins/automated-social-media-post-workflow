import os
import time
from datetime import datetime
from src.workflow import build_graph
from src.evaluators.feedback import (
    submit_composite_feedback,
    submit_image_metrics_feedback,
    log_workflow_summary
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("Starting Automated Social Media Post Workflow...")
    
    app = build_graph()
    
    # Track workflow start time
    workflow_start = datetime.now()
    workflow_start_iso = workflow_start.isoformat()
    
    # Initial State with metrics tracking fields
    initial_state = {
        "topic": None,
        "research_results": None,
        "draft_posts": [],
        "selected_post": None,
        "image_prompt": None,
        "image_url": None,
        "image_approved": False,
        "critique": None,
        "post_status": None,
        "retry_count": 0,
        # Metrics tracking fields
        "node_latencies": {},
        "total_latency": None,
        "post_char_count": None,
        "image_generation_attempts": 0,
        "workflow_start_time": workflow_start_iso,
        "errors": []
    }
    
    # LangSmith run configuration with metadata (best practice)
    # This enables filtering and grouping runs in the LangSmith dashboard
    run_config = {
        "metadata": {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": "1.0.0",
            "workflow_type": "social_media_automation",
            "start_time": workflow_start_iso
        },
        "tags": [
            "social-media",
            "automated",
            os.getenv("ENVIRONMENT", "development")
        ],
        "run_name": f"social_media_post_{workflow_start.strftime('%Y%m%d_%H%M%S')}"
    }
    
    # Run the graph
    final_state = None
    try:
        for output in app.stream(initial_state, config=run_config):
            for key, value in output.items():
                print(f"Finished Node: {key}")
                final_state = value if isinstance(value, dict) else final_state
                
    except Exception as e:
        print(f"Workflow failed: {e}")
        if final_state is None:
            final_state = initial_state
        # Track error in state
        errors = final_state.get("errors", [])
        errors.append(str(e))
        final_state["errors"] = errors
    
    # Calculate total latency
    workflow_end = datetime.now()
    total_latency = (workflow_end - workflow_start).total_seconds()
    
    if final_state:
        final_state["total_latency"] = total_latency
        
        # Submit additional metrics to LangSmith
        eval_results = final_state.get("evaluation_results")
        if eval_results:
            submit_composite_feedback(eval_results)
        
        # Submit image metrics
        submit_image_metrics_feedback(final_state)
        
        # Log workflow summary
        log_workflow_summary(final_state)
    
    print(f"\nWorkflow completed in {total_latency:.2f} seconds")

if __name__ == "__main__":
    main()
