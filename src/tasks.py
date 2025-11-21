from crewai import Task
from src.agents import researcher, writer, editor, prompt_engineer, image_reviewer, poster

def create_tasks(topic_interest):
    # Task 1: Research
    research_task = Task(
        description=f"Research trending topics related to '{topic_interest}'. Find at least 3 specific, currently trending news items or discussions.",
        expected_output="A bulleted list of the top 3 trending topics with a brief summary and source link for each.",
        agent=researcher
    )

    # Task 2: Draft Content
    draft_task = Task(
        description="Based on the research provided, choose the most engaging topic and write 3 distinct social media posts (tweets). The tone should be fun, engaging, and fit for a cartoon/comic style visual. Each post MUST include a hook, body, relevant hashtags, and a clear Call to Action (CTA) (e.g., asking a question, encouraging a reply). Avoid generic statements like 'Check this out'. Keep them under 280 characters.",
        expected_output="Three clearly labeled options for a social media post (Option 1, Option 2, Option 3) written in a fun/comic style with clear CTAs.",
        agent=writer,
        context=[research_task]
    )

    # Task 3: Select Best Post
    selection_task = Task(
        description="Review the 3 drafted posts. Select the single best one that is most likely to drive engagement. Ensure the selected post has a strong Call to Action. Return ONLY the final selected text.",
        expected_output="The full text of the selected social media post, ready for publication.",
        agent=editor,
        context=[draft_task]
    )

    # Task 4: Create Image Prompt
    prompt_task = Task(
        description="Create a detailed, creative image generation prompt that visually represents the selected social media post. The prompt MUST specify a cartoon or comic book art style. Do NOT create photorealistic prompts. The prompt should be descriptive and suitable for a high-quality AI image generator.",
        expected_output="A single, detailed text prompt for image generation specifying a cartoon/comic style.",
        agent=prompt_engineer,
        context=[selection_task]
    )

    # Task 5: Generate and Review Image
    image_task = Task(
        description="Use the 'Image Generation Tool' to generate an image based on the provided prompt. Return the local file path of the generated image.",
        expected_output="The local file path of the generated and approved image.",
        agent=image_reviewer,
        context=[prompt_task]
    )

    # Task 6: Post to X
    posting_task = Task(
        description="Post the selected text and the generated image to X (Twitter) using the 'X (Twitter) Posting Tool'. Use the text from the selection task and the image file path from the image task.",
        expected_output="A confirmation message that the post was successfully published, including the Tweet ID.",
        agent=poster,
        context=[selection_task, image_task]
    )

    return [research_task, draft_task, selection_task, prompt_task, image_task, posting_task]