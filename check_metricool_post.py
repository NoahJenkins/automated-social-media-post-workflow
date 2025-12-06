import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("METRICOOL_API")
user_id = os.getenv("METRICOOL_USER_ID")
blog_id = os.getenv("METRICOOL_BLOG_ID")
post_id = "270571203"

print(f"\n=== Checking Post ID {post_id} ===")

# Check scheduled posts
url = "https://app.metricool.com/api/v2/scheduler/posts"
headers = {"Authorization": f"Bearer {api_key}"}
params = {"userId": user_id, "blogId": blog_id}

response = requests.get(url, headers=headers, params=params)
print(f"\nAPI Status: {response.status_code}")
data = response.json()

if response.status_code == 200:
    posts = data.get("posts", [])
    print(f"Total posts found: {len(posts)}")
    
    found_post = None
    for post in posts:
        if str(post.get("id")) == post_id:
            found_post = post
            break
    
    if found_post:
        print(f"\n✓ Post {post_id} FOUND:")
        print(f"  Status: {found_post.get('status')}")
        print(f"  Publication Date: {found_post.get('publicationDate')}")
        print(f"  Text: {found_post.get('text', '')[:100]}...")
        print(f"  Providers: {found_post.get('providers')}")
        print(f"  Media: {len(found_post.get('media', []))} item(s)")
    else:
        print(f"\n✗ Post {post_id} NOT FOUND in scheduled posts")
        if len(posts) > 0:
            print(f"\nMost recent post:")
            recent = posts[0]
            print(f"  ID: {recent.get('id')}")
            print(f"  Status: {recent.get('status')}")
            print(f"  Date: {recent.get('publicationDate')}")
else:
    print(f"Error: {data}")

