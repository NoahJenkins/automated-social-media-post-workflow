# Configuration Examples

This file provides example `.env` configurations for different use cases.

## Example 1: Single Network (Twitter/X Only) - Basic Setup

```ini
# LLM Provider (required)
OPENAI_API_KEY=sk-...

# Search Provider (optional, falls back to static topics if missing)
TAVILY_API_KEY=tvly-...

# Metricool Credentials (required for posting)
METRICOOL_API=your-metricool-api-token
METRICOOL_USER_ID=your-user-id
METRICOOL_BLOG_ID=your-blog-id

# Social Networks (optional, defaults to twitter)
SOCIAL_NETWORKS=twitter

# Enable posting (set to true to actually post)
ENABLE_POSTING=true

# Azure Storage for Images (optional but recommended)
# Without this, posts will be created WITHOUT images
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=social-media-images
```

## Example 2: Multi-Network (Twitter, Facebook, Instagram, LinkedIn)

```ini
# LLM Provider (required)
OPENAI_API_KEY=sk-...

# Search Provider (optional)
TAVILY_API_KEY=tvly-...

# Metricool Credentials (required for posting)
METRICOOL_API=your-metricool-api-token
METRICOOL_USER_ID=your-user-id
METRICOOL_BLOG_ID=your-blog-id

# Social Networks - Post to all major platforms
SOCIAL_NETWORKS=twitter,facebook,instagram,linkedin

# Enable posting
ENABLE_POSTING=true

# Azure Storage for Images (REQUIRED for images on all platforms)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=social-media-images

# LangSmith Tracing (optional, for observability)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2-...
LANGCHAIN_PROJECT=social-media-agent
```

## Example 3: Development/Testing (No Posting, Local Save Only)

```ini
# LLM Provider (required)
OPENAI_API_KEY=sk-...

# Search Provider (optional)
TAVILY_API_KEY=tvly-...

# Disable posting - workflow will only save to local files
ENABLE_POSTING=false

# Social Networks - configure what you would post to (for testing)
SOCIAL_NETWORKS=twitter,facebook,instagram,linkedin

# Azure Storage (optional for testing - images will be saved locally)
# AZURE_STORAGE_CONNECTION_STRING=...
# AZURE_STORAGE_CONTAINER_NAME=...
```

## Example 4: Using OpenRouter Instead of OpenAI

```ini
# OpenRouter API (alternative to OpenAI)
OPENROUTER_API_KEY=sk-or-...

# Search Provider
TAVILY_API_KEY=tvly-...

# Metricool Credentials
METRICOOL_API=your-metricool-api-token
METRICOOL_USER_ID=your-user-id
METRICOOL_BLOG_ID=your-blog-id

# Social Networks
SOCIAL_NETWORKS=twitter,facebook,instagram,linkedin

# Enable posting
ENABLE_POSTING=true

# Azure Storage for Images
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=social-media-images
```

## Getting Metricool Credentials

1. Log into your Metricool account
2. Navigate to your dashboard
3. Check the URL - it will contain your User ID and Blog ID:
   ```
   https://app.metricool.com/...?blogId=XXXXX&userId=XXXXX
   ```
4. For the API token, go to Settings → API → Generate Token

## Setting up Azure Storage

1. Create an Azure Storage account in the Azure Portal
2. Create a container named `social-media-images` (or your preferred name)
3. Get the connection string from Access Keys section
4. Set the `AZURE_STORAGE_CONNECTION_STRING` and `AZURE_STORAGE_CONTAINER_NAME` in your `.env`

**Note**: Without Azure Storage configured, the workflow will still create posts but they will **not include images**.

## Connecting Metricool to Social Networks

Before you can post to multiple networks, ensure your Metricool account is connected to:
- Twitter/X
- Facebook Page
- Instagram Business Account
- LinkedIn Profile or Company Page

Configure these connections in the Metricool dashboard before running the workflow.
