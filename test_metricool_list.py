import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_token = os.getenv("METRICOOL_API")
user_id = os.getenv("METRICOOL_USER_ID")
blog_id = os.getenv("METRICOOL_BLOG_ID")

url = "https://analytics.metricool.com/api/v2/scheduler/posts"
headers = {
    "X-Mc-Auth": api_token,
    "Content-Type": "application/json"
}
params = {
    "userId": user_id,
    "blogId": blog_id
}

response = requests.get(url, headers=headers, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
