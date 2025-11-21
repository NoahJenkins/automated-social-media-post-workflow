import os
import time
import schedule
from crewai import Crew, Process
from dotenv import load_dotenv
from src.agents import researcher, writer, editor, prompt_engineer, image_reviewer, poster
from src.tasks import create_tasks

load_dotenv()

def run_social_media_workflow():
    print("Starting Social Media Workflow...")
    
    # Define the topic of interest (could be dynamic or config-based)
    topic_interest = "AI and Technology News"
    require_approval = os.getenv("REQUIRE_APPROVAL", "False").lower() == "true"
    
    # Create tasks
    tasks = create_tasks(topic_interest, require_approval=require_approval)
    
    # Create Crew
    social_media_crew = Crew(
        agents=[researcher, writer, editor, prompt_engineer, image_reviewer, poster],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    # Kickoff
    result = social_media_crew.kickoff()
    print("Workflow Completed!")
    print(f"Result: {result}")

def main():
    # Check for API keys
    required_keys = [
        "GEMINI_API_KEY", 
        "BRAVE_API_KEY", 
        "X_CONSUMER_KEY", 
        "X_CONSUMER_SECRET", 
        "X_ACCESS_TOKEN", 
        "X_ACCESS_TOKEN_SECRET"
    ]
    
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"Error: Missing environment variables: {', '.join(missing_keys)}")
        print("Please update your .env file.")
        return

    print("Social Media Automation Agent Started.")
    print("Scheduling: Running immediately for testing, then scheduled for Mon, Wed, Fri.")

    # Run immediately for testing purposes (as requested for initial setup)
    # In a real persistent deployment, we might comment this out.
    run_social_media_workflow() 

    # Schedule: Mon, Wed, Fri at 10:00 AM
    schedule.every().monday.at("10:00").do(run_social_media_workflow)
    schedule.every().wednesday.at("10:00").do(run_social_media_workflow)
    schedule.every().friday.at("10:00").do(run_social_media_workflow)

    print("Scheduler active. Waiting for next scheduled run...")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()