**`ARCHITECTURE.md`** (continued)

```markdown
# Social Media Automation System Architecture

## Executive Summary

An AI-powered social media automation system using Crew AI agents, Azure Application Insights for observability, and OpenRouter as a unified API gateway. The system automatically researches trending topics, generates content, creates images, reviews for brand safety, and publishes to X (Twitter) with optional human approval.

**Key Technologies:**
- **Agent Framework**: Crew AI (multi-agent orchestration)
- **API Gateway**: OpenRouter (unified LLM access)
- **Observability**: Azure Application Insights + OpenTelemetry
- **Cloud Platform**: Azure Functions (target deployment)
- **Primary Platform**: X (Twitter), expandable to multi-platform via Metricool

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Trigger (Timer/Manual)                     │
│                  • Local: Manual execution                   │
│                  • Azure: Timer trigger (2-3x/week)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                Azure Application Insights                    │
│           • Auto-instrumentation via OpenTelemetry          │
│           • Custom metrics for cost/performance             │
│           • Correlation IDs for end-to-end tracing          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Main Orchestration Layer (Python)               │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │         Crew AI Multi-Agent Workflow                 │   │
│  │         (Sequential Process)                        │   │
│  └────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  Agent 1: Research Trending Topics                          │
│  ├─ Tool: DuckDuckGo Search                                 │
│  ├─ LLM: Via OpenRouter                                     │
│  └─ Output: 3-5 trending topics                             │
│                          ↓                                  │
│  Agent 2: Content Creator                                   │
│  ├─ LLM: Via OpenRouter                                     │
│  ├─ Context: Brand guidelines + trends                      │
│  └─ Output: 3 post variations                               │
│                          ↓                                  │
│  Agent 3: Content Selector                                  │
│  ├─ LLM: Via OpenRouter                                     │
│  ├─ Evaluation: Engagement, brand fit, authenticity         │
│  └─ Output: Best post text                                  │
│                          ↓                                  │
│  Agent 4: Image Prompt Creator                              │
│  ├─ LLM: Via OpenRouter                                     │
│  ├─ Context: Selected post + brand aesthetics               │
│  └─ Output: Detailed image generation prompt                │
│                          ↓                                  │
│  Agent 5: Image Generator (Tool Agent)                      │
│  ├─ Service: OpenAI DALL-E 3 / GPT Image 1 Mini            │
│  ├─ Tool: generate_image()                                  │
│  └─ Output: Image URL                                       │
│                          ↓                                  │
│  Agent 6: Image Reviewer                                    │
│  ├─ LLM: Via OpenRouter (vision-capable model)              │
│  ├─ Checks: Safety, brand alignment, quality                │
│  └─ Output: Approval decision + confidence score            │
│                          ↓                                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │    Human Approval Gate (Configurable)               │   │
│  │    • If enabled: Request human approval              │   │
│  │    • If disabled: Auto-proceed                       │   │
│  │    • Storage: Azure Table Storage (draft queue)      │   │
│  └────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  Agent 7: Publisher                                         │
│  ├─ Tools: download_image(), publish_to_x()                 │
│  ├─ Platform: X (Twitter) API v2 + v1.1                     │
│  └─ Output: Published post URL                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│                                                             │
│  OpenRouter (Unified LLM Gateway)                           │
│  ├─ Models: Llama 3.3 70B, GPT-4o, Claude, etc.            │
│  ├─ Cost: ~$0.10-0.50 per 1M tokens                         │
│  └─ Failover: Automatic model switching                     │
│                                                             │
│  OpenAI API (Image Generation)                              │
│  ├─ Model: DALL-E 3 → GPT Image 1 Mini (future)            │
│  └─ Cost: $0.040 → $0.005 per image                         │
│                                                             │
│  X (Twitter) API                                            │
│  ├─ API v2: Tweet posting                                   │
│  ├─ API v1.1: Media upload                                  │
│  └─ OAuth 1.0a authentication                               │
│                                                             │
│  DuckDuckGo Search API                                      │
│  └─ Free, no API key required                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Azure Storage                             │
│                                                             │
│  Blob Storage (Hot Tier)                                    │
│  ├─ Container: social-media-images                          │
│  ├─ Purpose: Generated image storage                        │
│  └─ Retention: 30-90 days                                   │
│                                                             │
│  Table Storage                                              │
│  ├─ Table: PostHistory                                      │
│  │   • Post text, image URL, platform IDs, timestamp        │
│  ├─ Table: ApprovalQueue (if human approval enabled)        │
│  │   • Pending drafts awaiting approval                     │
│  └─ Table: AgentFailures                                    │
│      • Failure logs for debugging                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Azure Key Vault                           │
│                                                             │
│  Secrets:                                                   │
│  ├─ OPENROUTER_API_KEY                                      │
│  ├─ OPENAI_API_KEY                                          │
│  ├─ TWITTER_API_KEY                                         │
│  ├─ TWITTER_API_SECRET                                      │
│  ├─ TWITTER_ACCESS_TOKEN                                    │
│  ├─ TWITTER_ACCESS_TOKEN_SECRET                             │
│  └─ TWITTER_BEARER_TOKEN                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Agent Workflow (Crew AI)

**Framework**: Crew AI v0.86.0+
**Process Type**: Sequential (agents execute in order)
**Language**: Python 3.11+

#### Agent Definitions

| Agent | Role | Tools | LLM Model | Max Iterations |
|-------|------|-------|-----------|----------------|
| **Research Agent** | Senior Research Analyst | search_trending_topics | Llama 3.3 70B | 3 |
| **Content Creator** | Social Media Content Creator | None (LLM only) | Llama 3.3 70B | 3 |
| **Content Selector** | Content Strategy Expert | None (LLM only) | Llama 3.3 70B | 2 |
| **Image Prompt Agent** | Visual Content Specialist | None (LLM only) | Llama 3.3 70B | 2 |
| **Image Generator** | (Tool executor) | generate_image | N/A | 2 |
| **Image Reviewer** | Image Quality & Safety Reviewer | None (LLM only) | GPT-4o Vision | 2 |
| **Publisher Agent** | Social Media Publisher | download_image, publish_to_x | Llama 3.3 70B | 2 |

#### Retry Logic

Each agent supports automatic retry with exponential backoff:
- **Max Retries**: 3 attempts (configurable via `MAX_RETRIES`)
- **Backoff**: 2^attempt seconds (2s, 4s, 8s)
- **Failure Handling**: After 3 failures, skip task and log to Azure Table Storage
- **Telemetry**: Track retry count, failure reasons, correlation IDs

---

### 2. API Gateway (OpenRouter)

**Why OpenRouter?**
- Single API endpoint for 200+ models
- OpenAI-compatible API format
- Automatic failover and load balancing
- Cost-effective model routing
- $5 free credits to start

#### Configuration

```python
from crewai.llm import LLM

llm = LLM(
    model="openrouter/meta-llama/llama-3.3-70b-instruct",
    api_key=os.getenv('OPENROUTER_API_KEY'),
    base_url="https://openrouter.ai/api/v1"
)
```

#### Model Selection Strategy

| Use Case | Model | Provider | Cost (per 1M tokens) |
|----------|-------|----------|---------------------|
| **Agent reasoning** | Llama 3.3 70B | Meta via OpenRouter | $0.55 input / $0.80 output |
| **Image review** | GPT-4o Vision | OpenAI via OpenRouter | $2.50 input / $10.00 output |
| **Fallback** | Claude Sonnet 4 | Anthropic via OpenRouter | $3.00 input / $15.00 output |

#### Cost Optimization

- **Primary model**: Llama 3.3 70B (cost-effective for reasoning tasks)
- **Vision tasks only**: GPT-4o or Claude for image review
- **Caching**: OpenRouter supports prompt caching for repeated contexts
- **Automatic failover**: If primary model unavailable, auto-route to fallback

---

### 3. Telemetry & Observability

**Platform**: Azure Application Insights
**Protocol**: OpenTelemetry (OTLP)
**Instrumentation**: Automatic via OpenInference SDK

#### Telemetry Architecture

```
┌──────────────────────────────────────────────────────────┐
│           Application (Python + Crew AI)                  │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │   OpenTelemetry SDK (Auto-configured)          │    │
│  │   • Tracer Provider                            │    │
│  │   • Meter Provider (Metrics)                   │    │
│  │   • Logger Provider                            │    │
│  └────────────────────────────────────────────────┘    │
│                      ↓                                   │
│  ┌────────────────────────────────────────────────┐    │
│  │   OpenInference Instrumentation                │    │
│  │   • CrewAIInstrumentor().instrument()          │    │
│  │   • Captures: Agent traces, LLM calls, tools   │    │
│  └────────────────────────────────────────────────┘    │
│                      ↓                                   │
│  ┌────────────────────────────────────────────────┐    │
│  │   Custom Metrics Tracker                       │    │
│  │   • Agent duration                             │    │
│  │   • LLM token usage & cost                     │    │
│  │   • Image generation cost                      │    │
│  │   • Approval rates                             │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
                      ↓ (OTLP Export)
┌──────────────────────────────────────────────────────────┐
│        Azure Application Insights                         │
│                                                          │
│  Data Storage:                                           │
│  ├─ traces: Agent execution paths                        │
│  ├─ customMetrics: Performance & cost metrics            │
│  ├─ exceptions: Error tracking                           │
│  └─ dependencies: External API calls                     │
│                                                          │
│  Query Language: Kusto (KQL)                             │
│  Retention: 31 days (free), up to 730 days (paid)       │
└──────────────────────────────────────────────────────────┘
```

#### Custom Metrics Tracked

```python
# Performance Metrics
- social_media.agent.duration_ms
  Attributes: {agent, status}

- social_media.workflow.total_duration_seconds
  Attributes: {status}

# Cost Metrics
- social_media.llm.cost_usd
  Attributes: {model}

- social_media.llm.tokens
  Attributes: {model, token_type: input|output|total}

- social_media.image.generation_cost_usd
  Attributes: {model}

# Quality Metrics
- social_media.image.approval
  Attributes: {approved: true|false, confidence_bucket: high|medium|low}

- social_media.agent.retry_count
  Attributes: {agent, attempt}

# Business Metrics
- social_media.post.published
  Attributes: {platform}
```

#### Key Kusto Queries

```kusto
// Agent Performance by Role
customMetrics
| where name == "social_media.agent.duration_ms"
| extend agent = tostring(customDimensions.agent)
| summarize 
    avg_duration = avg(value),
    p95_duration = percentile(value, 95)
    by agent
| order by avg_duration desc

// Daily Cost Tracking
customMetrics
| where name contains "cost"
| summarize daily_cost = sum(value) by bin(timestamp, 1d)
| render timechart

// Image Approval Rate
customMetrics
| where name == "social_media.image.approval"
| extend approved = tostring(customDimensions.approved)
| summarize 
    total = count(),
    approved_count = countif(approved == "true")
    by bin(timestamp, 1d)
| extend approval_rate = 100.0 * approved_count / total
| render timechart

// Workflow Success Rate
traces
| where message contains "workflow"
| extend status = tostring(customDimensions["workflow.status"])
| summarize 
    total = count(),
    success = countif(status == "success")
| extend success_rate = 100.0 * success / total
```

---

### 4. Brand Guidelines & Safety

**Configuration Method**: Environment variables + Python dataclass
**Enforcement**: Injected into agent system prompts

#### Brand Guidelines Structure

```python
@dataclass
class BrandGuidelines:
    company_name: str
    values: str  # "Christ-centered, relationship-building, amazing tech"
    safety_rules: str  # "No graphic, rude, or derogatory content"
    
    def to_prompt_context(self) -> str:
        """Convert to LLM prompt context"""
```

#### Safety Checks

**Level 1: Content Creation (Agent 2)**
- Brand values embedded in system prompt
- Guidelines enforce tone, style, messaging

**Level 2: Content Selection (Agent 3)**
- Evaluates brand alignment
- Filters inappropriate content

**Level 3: Image Review (Agent 6)**
- Vision model checks generated images
- Criteria: Safety, brand values, quality, relevance
- Output: Approval (yes/no), Confidence (0.0-1.0), Reason

**Level 4: Human Approval (Optional)**
- Manual review before publishing
- Configurable via `HUMAN_APPROVAL_REQUIRED` flag

---

### 5. Image Generation

**Current**: OpenAI DALL-E 3
**Future**: GPT Image 1 Mini (when available in Azure)

#### Image Generation Workflow

```
1. Agent 4 creates detailed prompt
   ├─ Includes: Visual elements, lighting, color palette
   ├─ Brand-aligned: Christ-centered aesthetics (subtle)
   └─ Professional: Tech company standards

2. Agent 5 calls generate_image tool
   ├─ API: OpenAI Images API
   ├─ Model: dall-e-3 (standard quality)
   ├─ Size: 1024x1024
   └─ Cost: $0.040 per image

3. Image URL returned
   └─ Temporary URL (24-hour expiration)

4. Agent 6 reviews image
   ├─ Vision LLM evaluates safety/brand fit
   └─ Confidence score determines approval

5. Agent 7 downloads image
   ├─ Saves to local temp file
   └─ Uploads to X via media API
```

#### Cost Optimization Strategy

**Current State** (Prototype):
- DALL-E 3: $0.040 per image
- Projected: ~$0.48/month (12 posts × $0.040)

**Target State** (Production):
- Switch to GPT Image 1 Mini: $0.005 per image
- Projected: ~$0.06/month (12 posts × $0.005)
- **Savings: 87.5%**

---

### 6. Publishing (X/Twitter)

**API Version**: Twitter API v2 + v1.1 (hybrid)
**Authentication**: OAuth 1.0a
**Required Credentials**: 5 tokens (API key, secret, access token, access token secret, bearer token)

#### Publishing Workflow

```python
def publish_to_x(text: str, image_path: str = None) -> dict:
    """
    1. Upload media (API v1.1)
       └─ Endpoint: POST /1.1/media/upload.json
       └─ Returns: media_id
    
    2. Create tweet (API v2)
       └─ Endpoint: POST /2/tweets
       └─ Payload: {text, media_ids: [media_id]}
    
    3. Return tweet URL
       └─ Format: https://twitter.com/i/web/status/{tweet_id}
    """
```

#### Rate Limits

- **Posts per day**: 2400 (way above our 2-3/week usage)
- **Media uploads**: 500/15 min
- **No concerns** for current usage pattern

#### Future: Multi-Platform via Metricool

**Phase 2** will replace direct X API calls with Metricool API:

```python
# Future implementation
def publish_to_metricool(text: str, image_url: str, platforms: list) -> dict:
    """
    Single API call publishes to:
    - X (Twitter)
    - LinkedIn
    - Instagram
    - Facebook
    """
    payload = {
        "text": text,
        "media": [{"url": image_url}],
        "platforms": platforms,  # ["twitter", "linkedin", "instagram", "facebook"]
        "schedule": "now"
    }
    # POST to Metricool API
```

---

### 7. Human Approval Gate

**Status**: Optional (toggleable via config)
**Default**: Enabled for prototype
**Storage**: Azure Table Storage

#### Approval Flow

```
┌─────────────────────────────────────────────────┐
│  Agent 6 completes image review                 │
│  └─ Image APPROVED by AI                        │
└─────────────────────────────────────────────────┘
                    ↓
         ┌──────────────────────┐
         │ HUMAN_APPROVAL_       │
         │ REQUIRED = true?      │
         └──────────────────────┘
          ↓ YES           ↓ NO
┌────────────────┐   ┌──────────────┐
│ Store draft in │   │ Auto-proceed │
│ Table Storage  │   │ to publishing│
│                │   └──────────────┘
│ Display to     │
│ human reviewer │
│                │
│ Wait for input │
│ (yes/no)       │
└────────────────┘
    ↓ YES    ↓ NO
┌──────┐  ┌──────┐
│Publish│  │ Skip │
└──────┘  └──────┘
```

#### Table Schema: ApprovalQueue

```python
{
    "PartitionKey": "pending",  # or "approved", "rejected"
    "RowKey": str(uuid.uuid4()),  # Unique draft ID
    "text": "Post content...",
    "image_url": "https://...",
    "created_at": datetime.utcnow(),
    "status": "pending",  # or "approved", "rejected"
    "reviewed_by": "user@example.com",  # Optional
    "reviewed_at": datetime.utcnow()  # Optional
}
```

#### Future: HTTP-Triggered Approval

For Azure Functions deployment:

```
1. Agent workflow pauses after image review
2. Draft stored in Table Storage with status="pending"
3. Email/Teams notification sent with approval link
4. User clicks link → HTTP-triggered function
5. Function updates Table Storage status
6. If approved, separate function publishes post
```

---

## Deployment Architecture

### Local Development (Current)

```
┌─────────────────────────────────────────────────┐
│  Developer Machine                               │
│                                                 │
│  python main.py                                 │
│  ├─ Loads .env configuration                    │
│  ├─ Initializes Azure App Insights             │
│  ├─ Runs Crew AI workflow                      │
│  └─ Publishes to X                              │
└─────────────────────────────────────────────────┘
          ↓ (Telemetry via OTLP)
┌─────────────────────────────────────────────────┐
│  Azure Application Insights                      │
│  (Cloud-hosted, always on)                       │
└─────────────────────────────────────────────────┘
```

### Azure Functions Deployment (Target)

```
┌─────────────────────────────────────────────────┐
│  Azure Function App (Consumption Plan)          │
│  • Runtime: Python 3.11                          │
│  • OS: Linux                                     │
│  • Region: Same as App Insights                  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Function: social_media_workflow                 │
│  • Trigger: Timer (NCRONTAB expression)         │
│  • Schedule: "0 0 10 * * MON,WED,FRI"           │
│  • Timeout: 10 minutes (configurable)           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Function: approve_post (Optional)               │
│  • Trigger: HTTP POST                            │
│  • Route: /api/approve_post?draft_id={id}       │
│  • Auth: Function key required                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Configuration Sources                           │
│  • Application Settings (environment vars)       │
│  • Azure Key Vault (secrets)                     │
│  • Function App managed identity                 │
└─────────────────────────────────────────────────┘
```

#### Function App Configuration

**Application Settings:**
```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=@Microsoft.KeyVault(...)
OPENROUTER_API_KEY=@Microsoft.KeyVault(...)
OPENAI_API_KEY=@Microsoft.KeyVault(...)
TWITTER_API_KEY=@Microsoft.KeyVault(...)
# ... other secrets from Key Vault

HUMAN_APPROVAL_REQUIRED=true
MAX_RETRIES=3
BRAND_VALUES="Christ-centered, relationship-building, amazing tech"
SCHEDULE_CRON="0 0 10 * * MON,WED,FRI"
```

**Networking:**
```
├─ Outbound: Allow all (for API calls)
├─ Inbound: Function key required
└─ VNet Integration: Optional (for enterprise)
```

---

## Cost Analysis

### Monthly Cost Breakdown (Prototype Scale: 12 posts/month)

| Component | Details | Monthly Cost |
|-----------|---------|--------------|
| **Azure Functions** | 12 executions × 3 min avg @ $0.000016/GB-s | $0.50 |
| **Application Insights** | ~100MB telemetry | $0.00 (under 5GB free tier) |
| **Blob Storage** | 12 images × 2MB (hot tier) | $0.01 |
| **Table Storage** | Post history + failures | $0.01 |
| **Key Vault** | 7 secrets | $0.03 |
| **OpenRouter LLM** | 6 agents × 12 posts × ~10K tokens | ~$3.00 |
| **Image Generation** | 12 images × $0.040 (DALL-E 3) | $0.48 |
| **Image Review** | 12 reviews × GPT-4o Vision | ~$0.30 |
| **X API** | Free tier | $0.00 |
| **TOTAL** | | **~$4.33/month** |

### Production Scale Cost Projection (100 posts/month)

| Component | Monthly Cost |
|-----------|--------------|
| Azure Functions | $1.50 |
| Application Insights | $0.23 (1GB @ $2.30/GB) |
| Storage | $0.20 |
| OpenRouter LLM | ~$25.00 |
| Image Generation | $0.50 (switched to GPT Image 1 Mini) |
| Image Review | $2.50 |
| **TOTAL** | **~$29.93/month** |

---

## Security Considerations

### Secrets Management

**Azure Key Vault:**
- All API keys stored in Key Vault
- Function App uses Managed Identity
- No secrets in code or environment variables
- Automatic rotation support

### Network Security

**Outbound Traffic:**
- OpenRouter API: HTTPS only
- OpenAI API: HTTPS only
- X API: HTTPS only, OAuth 1.0a
- DuckDuckGo: HTTPS only

**Inbound Traffic:**
- Timer trigger: Internal only
- HTTP approval endpoint: Function key required
- No public endpoints exposed

### Data Privacy

**Sensitive Data:**
- Post content: Temporary (not logged to App Insights)
- Images: Deleted after 30 days from Blob Storage
- API responses: Not persisted

**Compliance:**
- Azure certifications: SOC 2, ISO 27001, HIPAA
- Data residency: Choose Azure region for compliance
- Audit logs: Available via Application Insights

---

## Error Handling & Resilience

### Retry Strategy

```python
def execute_with_retry(agent, task, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = agent.execute_task(task)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                # Log to Table Storage
                log_failure(agent.role, str(e), correlation_id)
                # Track metric
                metrics_tracker.track_agent_retry(agent.role, attempt + 1)
                raise
            # Exponential backoff
            time.sleep(2 ** attempt)
```

### Failure Scenarios & Handling

| Failure Type | Recovery Strategy | User Impact |
|--------------|-------------------|-------------|
| **LLM API timeout** | Retry 3x with backoff | Delayed execution |
| **LLM API rate limit** | OpenRouter auto-failover to different model | Transparent |
| **Image generation failure** | Retry 3x, then skip post | Post skipped, logged |
| **Image review rejection** | Skip post, log reason | Post not published |
| **X API failure** | Retry 3x with backoff | Delayed post or skip |
| **Human approval timeout** | Post remains in queue indefinitely | Manual intervention |
| **Azure Functions timeout** | Increase timeout limit (max 10 min) | Execution completes |

### Monitoring & Alerts

**Azure Monitor Alerts:**

```
1. High Failure Rate
   └─ Condition: >20% agent failures in 1 hour
   └─ Action: Email notification

2. Cost Threshold
   └─ Condition: Daily cost exceeds $2
   └─ Action: Email + Teams notification

3. Workflow Duration
   └─ Condition: Execution time >10 minutes
   └─ Action: Investigate for bottlenecks

4. Image Review Rejections
   └─ Condition: >3 rejections in a row
   └─ Action: Review image generation prompts
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_agents.py
def test_research_agent_output_format():
    """Verify research agent returns 3-5 topics"""

def test_content_creator_character_limit():
    """Verify posts are 220-280 characters"""

def test_image_reviewer_approval_format():
    """Verify reviewer returns required fields"""

# tests/test_tools.py
def test_search_tool_returns_results():
    """Verify search tool returns formatted results"""

def test_image_generation_cost_tracking():
    """Verify cost metric is recorded"""

def test_x_publisher_success():
    """Mock X API and verify publish logic"""
```

### Integration Tests

```python
# tests/test_integration.py
def test_end_to_end_workflow():
    """Run full workflow with mock APIs"""

def test_telemetry_emitted():
    """Verify all metrics/traces are sent to App Insights"""

def test_retry_logic():
    """Simulate failures and verify retries"""
```

### Manual Testing Checklist

```
□ Run locally with real APIs
□ Verify post published to X
□ Check telemetry in Azure Portal
□ Test human approval flow
□ Test with different topics
□ Verify brand guidelines enforcement
□ Check cost tracking accuracy
□ Test failure scenarios (invalid API keys)
□ Verify retry logic works
□ Check image quality and safety
```

---

## Configuration Reference

### Environment Variables

```bash
# Azure Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=https://...

# OpenRouter (Unified LLM Gateway)
OPENROUTER_API_KEY=sk-or-v1-xxx

# OpenAI (Image Generation)
OPENAI_API_KEY=sk-proj-xxx

# X (Twitter) API v2
TWITTER_API_KEY=xxx
TWITTER_API_SECRET=xxx
TWITTER_ACCESS_TOKEN=xxx-xxx
TWITTER_ACCESS_TOKEN_SECRET=xxx
TWITTER_BEARER_TOKEN=xxx

# Workflow Configuration
HUMAN_APPROVAL_REQUIRED=true
MAX_RETRIES=3
SCHEDULE_CRON=0 0 10 * * MON,WED,FRI

# Brand Configuration
COMPANY_NAME=YourCompany
BRAND_VALUES=Christ-centered, relationship-building, amazing tech
SAFETY_GUIDELINES=No graphic, rude, or derogatory content
```

### Directory Structure

```
social-media-automation/
├── .env                        # Local environment variables
├── .gitignore                  # Ignore .env, __pycache__, etc.
├── requirements.txt            # Python dependencies
├── README.md                   # Setup instructions
├── ARCHITECTURE.md             # This document
│
├── main.py                     # Main entry point (local)
├── function_app.py             # Azure Functions entry point
│
├── agents/
│   ├── __init__.py
│   └── agent_definitions.py    # Crew AI agents & tasks
│
├── tools/
│   ├── __init__.py
│   ├── search_tool.py          # DuckDuckGo trending topics
│   ├── image_generation_tool.py # OpenAI image generation
│   └── x_publisher_tool.py     # X (Twitter) publishing
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration classes
│
├── telemetry/
│   ├── __init__.py
│   └── custom_metrics.py       # Azure App Insights metrics
│
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_integration.py
│
└── infrastructure/
    ├── terraform/
    │   ├── main.tf              # Azure resources
    │   ├── variables.tf
    │   └── outputs.tf
    └── azure-pipelines.yml      # CI/CD pipeline
```

---

## Future Enhancements

### Phase 2: Multi-Platform Publishing

**Goal**: Replace direct X API with Metricool API

```python
# New tool: tools/metricool_publisher_tool.py
@tool("publish_to_metricool")
def publish_to_metricool(text: str, image_url: str, platforms: list) -> dict:
    """
    Publish to multiple platforms simultaneously:
    - X (Twitter)
    - LinkedIn
    - Instagram
    - Facebook
    """
```

**Changes Required:**
- Add Metricool API credentials to Key Vault
- Update Publisher Agent to use new tool
- Update telemetry to track per-platform success

### Phase 3: Response Automation

**Goal**: Respond to comments/mentions on social media

**Architecture:**
```
1. Webhook listener (Azure Functions HTTP trigger)
2. Parse incoming comment/mention
3. Sentiment analysis agent
4. Response generator agent
5. Approval gate (optional)
6. Auto-reply via platform API
```

**Challenges:**
- Real-time processing requirement
- Context awareness (conversation history)
- Tone matching (brand voice)
- Safety filters (avoid controversial topics)

### Phase 4: A/B Testing

**Goal**: Test multiple post variations and learn from engagement

**Features:**
- Generate 3 variations, post all with delay
- Track engagement metrics (likes, comments, retweets)
- Train selector agent on engagement data
- Improve content quality over time

### Phase 5: Visual Brand Assets

**Goal**: Use company logo, consistent color palette

**Implementation:**
- Upload brand assets to Blob Storage
- Image composition agent overlays logo
- Enforce color palette in prompts
- Generate templates for recurring post types

---

## Troubleshooting Guide

### Common Issues

**1. "No traces appearing in Azure Portal"**
```
Solution:
- Verify APPLICATIONINSIGHTS_CONNECTION_STRING is correct
- Wait 2-5 minutes for data to propagate
- Check time filter in Azure Portal (set to "Last 24 hours")
- Ensure openinference-instrumentation-crewai is installed
- Verify configure_azure_monitor() is called BEFORE CrewAIInstrumentor()
```

**2. "X API authentication failed"**
```
Solution:
- Verify all 5 Twitter credentials in .env
- Check app permissions: Must have Read & Write
- Regenerate keys if necessary
- Test with Twitter's API explorer first
```

**3. "Image generation failed"**
```
Solution:
- Check OpenAI API key validity
- Verify billing is enabled on OpenAI account
- Check API rate limits (5 requests/minute)
- Ensure prompt doesn't violate content policy
```

**4. "OpenRouter API error"**
```
Solution:
- Verify OPENROUTER_API_KEY is valid
- Check OpenRouter balance ($5 free credits)
- Ensure model name is correct (format: "openrouter/provider/model")
- Review OpenRouter dashboard for rate limits
```

**5. "Agent stuck in infinite loop"**
```
Solution:
- Set max_iter=2 or 3 on agents
- Review agent prompts for clarity
- Check if agent is waiting for tool that never responds
- Add timeout to LLM calls
```

### Debug Mode

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable Crew AI verbose mode
crew = Crew(
    agents=[...],
    tasks=[...],
    verbose=True  # Shows agent reasoning
)

# Test individual tools
from tools import search_trending_topics
result = search_trending_topics("AI trends")
print(result)
```

---

## Performance Benchmarks

### Typical Execution Times (Local)

| Phase | Duration | Notes |
|-------|----------|-------|
| Research (Agent 1) | 10-15s | DuckDuckGo search + LLM analysis |
| Content Creation (Agent 2) | 15-20s | Generate 3 variations |
| Selection (Agent 3) | 5-10s | Evaluate and choose best |
| Image Prompt (Agent 4) | 5-10s | Create detailed prompt |
| Image Generation (Agent 5) | 20-30s | DALL-E 3 generation time |
| Image Review (Agent 6) | 5-10s | Vision LLM analysis |
| Publishing (Agent 7) | 5-10s | Upload image + post to X |
| **Total** | **65-105s** | ~1.5-2 minutes end-to-end |

### Optimization Opportunities

1. **Parallel Agent Execution** (future)
   - Run content creation for all 3 variations in parallel
   - Reduce execution time by 30%

2. **Prompt Caching** (OpenRouter supports this)
   - Cache brand guidelines context
   - Reduce token costs by 50% for repeated context

3. **Image Pre-generation** (future)
   - Generate image library in advance
   - Select from library instead of generating each time

---

## Maintenance & Operations

### Weekly Tasks

- [ ] Review published posts for quality
- [ ] Check Azure Portal for errors/alerts
- [ ] Monitor cost trends in Application Insights
- [ ] Review image approval rates

### Monthly Tasks

- [ ] Analyze engagement metrics (if tracking enabled)
- [ ] Update brand guidelines if needed
- [ ] Review and optimize agent prompts
- [ ] Check for Crew AI / OpenTelemetry updates
- [ ] Rotate API keys (security best practice)

### Quarterly Tasks

- [ ] Evaluate LLM model performance (compare models)
- [ ] Review cost optimization opportunities
- [ ] Update to GPT Image 1 Mini when available
- [ ] Expand to additional platforms (Phase 2)

---

## Support & Resources

### Documentation Links

- **Crew AI**: https://docs.crewai.com
- **OpenRouter**: https://openrouter.ai/docs
- **Azure Application Insights**: https://learn.microsoft.com/azure/azure-monitor/app/
- **OpenTelemetry**: https://opentelemetry.io/docs/
- **X API**: https://developer.twitter.com/en/docs
- **Azure Functions**: https://learn.microsoft.com/azure/azure-functions/

### Community

- Crew AI Discord: https://discord.com/invite/X4JWnZnxPb
- OpenRouter Reddit: r/openrouter
- Azure Community: https://techcommunity.microsoft.com/azure

---

## Conclusion

This architecture provides a robust, cost-effective, and scalable solution for automated social media content generation and publishing. Key strengths:

✅ **Cost-Optimized**: ~$4-5/month for prototype scale
✅ **Observable**: Full telemetry via Azure Application Insights
✅ **Flexible**: Easy to add new platforms, agents, or models
✅ **Safe**: Multi-level safety checks + human approval gate
✅ **Maintainable**: Clear separation of concerns, well-documented
✅ **Scalable**: Ready to deploy to Azure Functions for production

The use of OpenRouter as a unified API gateway simplifies LLM management and provides cost-effective access to multiple models with automatic failover.

---

**Document Version**: 1.0
**Last Updated**: November 20, 2025
**Author**: Noah (with Claude assistance)
**Status**: Ready for Implementation
```

---

This complete architecture document can be imported directly into your codebase. An LLM reviewing this will understand:

1. **System design** - Complete component architecture
2. **Technical decisions** - Why OpenRouter, Azure App Insights, Crew AI
3. **Implementation details** - Code structure, APIs, data flows
4. **Cost analysis** - Detailed breakdown with projections
5. **Operational procedures** - Testing, monitoring, maintenance
6. **Future roadmap** - Clear phases for expansion
