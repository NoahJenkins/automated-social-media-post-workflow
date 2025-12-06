# Implementation Guide: Content Quality Improvements

This guide provides step-by-step instructions for implementing the recommendations from the Post Quality Analysis.

---

## Quick Win #1: Value-First Content Creation Prompt (30 minutes)

### Objective
Replace generic "fun and engaging" prompt with structured value-delivery framework.

### Files to Modify
- `src/agents/content_creator.py`

### Implementation Steps

1. **Backup Current File**
   ```bash
   cp src/agents/content_creator.py src/agents/content_creator.py.backup
   ```

2. **Replace the Prompt Section** (lines 17-32)

**CURRENT CODE:**
```python
prompt = f"""
Topic: {topic}
Context: {research}

Task: Write 3 distinct social media posts (tweets) about this topic.
Context: Today is {day}. The theme is {theme}. Make the posts reflect this vibe (e.g., if Friday, make it about the weekend/wrapping up).
Tone: Casual, Fun, Engaging, Relatable for Tech Workers.
Constraints:
- Under 280 characters.
- Use 1-2 emojis.
- No hashtags (or max 1).

Output format:
1. [Post 1 text]
2. [Post 2 text]
3. [Post 3 text]
"""
```

**REPLACE WITH:**
```python
prompt = f"""
Topic: {topic}
Research Context: {research}
Day: {day} | Theme: {theme}

Task: Create 3 social media posts that provide GENUINE VALUE to tech professionals.

VALUE REQUIREMENT - Each post MUST include at least ONE:
✓ Actionable Insight: A specific takeaway readers can apply immediately
✓ Fresh Perspective: A unique angle or contrarian view on the topic
✓ Educational Moment: Teach something new (framework, concept, specific tool/technique)
✓ Data-Driven Hook: Start with a surprising statistic or research finding
✓ Problem + Solution: Identify specific pain point with concrete solution

STRUCTURE GUIDELINES (choose format that fits content):
• Hook + Insight + Value/Implication
• Problem + Framework/Solution + Example
• Contrarian take + Reasoning + Practical application
• Surprising stat + Context + Actionable takeaway

QUALITY STANDARDS:
✓ SPECIFIC over generic (name tools, cite numbers, reference frameworks)
✓ ACTIONABLE over theoretical (what can reader do with this?)
✓ FRESH over obvious (avoid common knowledge statements)
✓ EXPERT VOICE not corporate marketing (knowledgeable but conversational)

AVOID:
✗ Generic buzzwords without context ("game-changing", "revolutionary")
✗ Vague questions without leading insight
✗ Obvious statements everyone knows
✗ Pure engagement bait with no substance

CONSTRAINTS:
- Under 280 characters (prioritize substance over fluff)
- Emojis ONLY if they clarify meaning (not decoration)
- Max 1 hashtag, only if highly relevant
- Must pass the "So what?" test: Why would an expert share this?

Consider the {day} theme ({theme}) in your framing, but don't sacrifice value for theme.

Output format:
1. [Post 1 - specify which value type it delivers]
2. [Post 2 - specify which value type it delivers]
3. [Post 3 - specify which value type it delivers]
"""
```

3. **Test the Change**
   ```bash
   # Run the workflow to test new prompts
   python main.py
   
   # Review generated posts in social_media_posts/
   # Check that posts have specific insights, not generic statements
   ```

4. **Rollback if Needed**
   ```bash
   # If results are worse, restore backup
   mv src/agents/content_creator.py.backup src/agents/content_creator.py
   ```

### Expected Results
- Posts will include specific examples, tools, or frameworks
- Reduced generic statements like "AI is transforming things"
- More actionable content readers can apply
- Clear value proposition in each post

---

## Quick Win #2: Post Structure Templates (1 hour)

### Objective
Implement proven post structures to guide content creation with high-engagement patterns.

### Files to Create
- `src/templates/post_structures.py` (new file)

### Files to Modify
- `src/agents/content_creator.py`

### Implementation Steps

**Step 1: Create Template Module**

Create `src/templates/post_structures.py`:

```python
"""
Proven social media post templates for high engagement.
Each template is designed to deliver specific value types.
"""

POST_TEMPLATES = {
    "data_driven": {
        "structure": "{stat} → {insight} → {implication}",
        "example": "73% of devs report burnout. Root cause? Context-switching 40+ times/day. Fix: Time-block deep work, batch comms. Results: 2x output, less stress.",
        "value_type": "Educational + Actionable",
        "char_guide": "~200-250 chars for depth"
    },
    
    "problem_solution": {
        "structure": "{specific_problem}? {concrete_solution}. {evidence/result}",
        "example": "AWS bill spiraling? Try: 1) Delete unused EBS volumes 2) Right-size over-provisioned instances 3) Use Savings Plans for steady workloads. Avg savings: 40%.",
        "value_type": "Actionable Solution",
        "char_guide": "~220-270 chars"
    },
    
    "contrarian": {
        "structure": "Unpopular opinion: {contrarian_take}. Why: {reasoning} → {implication}",
        "example": "Unpopular opinion: Writing tests AFTER code is fine. Why: You learn requirements by coding. Then tests document what you built. TDD isn't always optimal.",
        "value_type": "Fresh Perspective",
        "char_guide": "~200-260 chars"
    },
    
    "framework": {
        "structure": "{concept} = {component_1} + {component_2} + {component_3}",
        "example": "Good PR reviews = Code logic check + Security scan + Performance impact + Test coverage. Skip any one → bugs leak through. All four → quality code ships.",
        "value_type": "Educational Framework",
        "char_guide": "~210-270 chars"
    },
    
    "comparison": {
        "structure": "{option_a} vs {option_b}: {key_difference}. When to use: {guidance}",
        "example": "REST vs GraphQL: REST → simple CRUD, multiple endpoints. GraphQL → complex data, single endpoint, flexible queries. Use REST for microservices, GraphQL for rich clients.",
        "value_type": "Educational + Actionable",
        "char_guide": "~230-280 chars"
    },
    
    "mistake_lesson": {
        "structure": "I thought {misconception}. Reality: {truth}. Now I: {action}",
        "example": "I thought microservices = scalability. Reality: They add complexity cost. Now I: Monolith first, split only when scaling demands it. Saved 6mo engineering time.",
        "value_type": "Insight + Actionable",
        "char_guide": "~200-260 chars"
    },
    
    "tool_showcase": {
        "structure": "{problem} → {tool/technique} → {specific_benefit}. Bonus: {tip}",
        "example": "Debugging async JS? → Chrome DevTools async stack traces → See full call chain across promises. Bonus: Enable in Settings > Experiments. Cuts debug time 50%.",
        "value_type": "Actionable + Educational",
        "char_guide": "~220-280 chars"
    },
    
    "insight_thread_starter": {
        "structure": "{surprising_observation} + {why_it_matters} + {discussion_prompt}",
        "example": "Junior devs who ask 'why?' outgrow seniors who just say 'how'. Curiosity > experience in learning velocity. What skill accelerated your growth most?",
        "value_type": "Insight + Engagement",
        "char_guide": "~180-250 chars"
    }
}

def get_random_template():
    """Return a random template from available structures."""
    import random
    template_name = random.choice(list(POST_TEMPLATES.keys()))
    return template_name, POST_TEMPLATES[template_name]

def get_template_by_value_type(value_type):
    """
    Get template that matches desired value type.
    
    value_type options:
    - "actionable": Problem-solution, Tool-showcase
    - "educational": Framework, Comparison, Data-driven
    - "perspective": Contrarian, Mistake-lesson
    - "engagement": Insight-thread-starter
    """
    value_map = {
        "actionable": ["problem_solution", "tool_showcase"],
        "educational": ["framework", "comparison", "data_driven"],
        "perspective": ["contrarian", "mistake_lesson"],
        "engagement": ["insight_thread_starter", "data_driven"]
    }
    
    import random
    templates = value_map.get(value_type, list(POST_TEMPLATES.keys()))
    template_name = random.choice(templates)
    return template_name, POST_TEMPLATES[template_name]

def format_template_guide(template_name, template_data):
    """Format template information for inclusion in LLM prompt."""
    return f"""
SUGGESTED STRUCTURE ({template_name}):
Pattern: {template_data['structure']}
Example: {template_data['example']}
Value Type: {template_data['value_type']}
Length Guide: {template_data['char_guide']}

Use this as inspiration but adapt to your specific content. Don't copy the example literally.
"""
```

**Step 2: Modify Content Creator to Use Templates**

Update `src/agents/content_creator.py`:

```python
from src.state import AgentState
from src.config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from src.templates.post_structures import get_random_template, format_template_guide

def content_creator_node(state: AgentState):
    """
    Generates 3 draft posts based on the researched topic.
    Now uses proven templates to guide structure and value delivery.
    """
    print("--- CONTENT CREATOR AGENT ---")
    topic = state["topic"]
    research = state["research_results"]
    day = state.get("day_of_week", "a weekday")
    theme = state.get("theme", "tech life")
    
    llm = get_llm("gpt-5")
    
    # Get 3 different random templates for variety
    templates_guide = ""
    for i in range(3):
        template_name, template_data = get_random_template()
        templates_guide += f"\nFor Post {i+1}, consider using:\n"
        templates_guide += format_template_guide(template_name, template_data)
    
    prompt = f"""
Topic: {topic}
Research Context: {research}
Day: {day} | Theme: {theme}

{templates_guide}

Task: Create 3 distinct social media posts that provide GENUINE VALUE to tech professionals.

VALUE REQUIREMENT - Each post MUST include at least ONE:
✓ Actionable Insight: A specific takeaway readers can apply immediately
✓ Fresh Perspective: A unique angle or contrarian view on the topic
✓ Educational Moment: Teach something new (framework, concept, specific tool/technique)
✓ Data-Driven Hook: Start with a surprising statistic or research finding
✓ Problem + Solution: Identify specific pain point with concrete solution

QUALITY STANDARDS:
✓ SPECIFIC over generic (name tools, cite numbers, reference frameworks)
✓ ACTIONABLE over theoretical (what can reader do with this?)
✓ FRESH over obvious (avoid common knowledge statements)
✓ EXPERT VOICE not corporate marketing (knowledgeable but conversational)

AVOID:
✗ Generic buzzwords without context ("game-changing", "revolutionary")
✗ Vague questions without leading insight
✗ Obvious statements everyone knows
✗ Pure engagement bait with no substance

CONSTRAINTS:
- Under 280 characters (prioritize substance over fluff)
- Emojis ONLY if they clarify meaning (not decoration)
- Max 1 hashtag, only if highly relevant

Output format:
1. [Post 1 text]
2. [Post 2 text]
3. [Post 3 text]
"""
    
    messages = [
        SystemMessage(content="You are an expert tech content strategist who creates highly valuable, specific social media content."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Simple parsing to get list
    drafts = []
    for line in content.split('\n'):
        if line.strip().startswith(('1.', '2.', '3.')):
            drafts.append(line.split('.', 1)[1].strip())
            
    # Fallback if parsing fails
    if len(drafts) < 3:
        drafts = [content]

    return {"draft_posts": drafts}
```

**Step 3: Create the templates directory**
```bash
mkdir -p src/templates
touch src/templates/__init__.py
```

**Step 4: Test the Implementation**
```bash
python main.py

# Check generated posts for:
# - Use of structured patterns
# - Specific examples and frameworks
# - Clear value delivery
```

### Expected Results
- Posts follow proven high-engagement structures
- More consistent value delivery
- Better use of character limit for substance
- Variety in post formats

---

## Quick Win #3: Enhanced Content Review Criteria (1 hour)

### Objective
Replace subjective review criteria with multi-dimensional scoring system.

### Files to Modify
- `src/agents/content_reviewer.py`

### Implementation Steps

**Step 1: Backup Current File**
```bash
cp src/agents/content_reviewer.py src/agents/content_reviewer.py.backup
```

**Step 2: Replace Content Reviewer Logic**

**CURRENT CODE:**
```python
prompt = f"""
Review the following 3 social media post drafts:

1. {drafts[0] if len(drafts) > 0 else "N/A"}
2. {drafts[1] if len(drafts) > 1 else "N/A"}
3. {drafts[2] if len(drafts) > 2 else "N/A"}

Criteria:
- Must be fun, casual, and engaging.
- Must be relevant to the topic: {state.get('topic', 'Tech')}
- No cringey corporate speak.

Task: Select the best post. Return ONLY the text of the selected post. Do not add quotes or "Selected Post:" prefix.
"""
```

**REPLACE WITH:**
```python
prompt = f"""
Review these 3 social media posts for tech professionals:

Post 1: {drafts[0] if len(drafts) > 0 else "N/A"}
Post 2: {drafts[1] if len(drafts) > 1 else "N/A"}
Post 3: {drafts[2] if len(drafts) > 2 else "N/A"}

Topic: {state.get('topic', 'Tech')}
Theme: {state.get('theme', 'General')}

EVALUATION CRITERIA - Score each post on 5 dimensions (0-10 each):

1. VALUE DENSITY (0-10): Does it teach, inform, or provide actionable insight?
   • 0-3: Generic statement, no specific value or takeaway
   • 4-6: Some value present but could be more specific/actionable
   • 7-8: Clear actionable insight, specific learning, or practical framework
   • 9-10: Exceptional depth, multiple layers of value, highly actionable

2. SPECIFICITY (0-10): Concrete examples vs vague statements?
   • 0-3: All generic/vague ("AI is changing things", "work is hard")
   • 4-6: Mix of generic and specific elements
   • 7-8: Mostly specific (names tools, cites numbers, references frameworks)
   • 9-10: Highly specific throughout, citable facts/examples

3. UNIQUENESS (0-10): Fresh perspective or generic content?
   • 0-3: Could be from any AI tool, very common take
   • 4-6: Somewhat fresh angle but still fairly predictable
   • 7-8: Fresh perspective, non-obvious insight, or specific angle
   • 9-10: Contrarian, highly original, or expert-level nuance

4. ENGAGEMENT POTENTIAL (0-10): Would target audience save/share/discuss?
   • 0-3: Likely scrolled past, no hook or value
   • 4-6: Some might pause, limited sharing appeal
   • 7-8: Strong hook and value, likely saves/shares
   • 9-10: Highly shareable, conversation-starter, viral potential

5. AUTHENTICITY (0-10): Human expert voice or AI-generated feel?
   • 0-3: Obviously AI (generic enthusiasm, buzzwords, exclamation marks)
   • 4-6: Somewhat natural but detectably AI-ish
   • 7-8: Natural expert voice, minimal AI tells
   • 9-10: Indistinguishable from human expert, authoritative yet conversational

SELECTION PROCESS:
1. Score each post across all 5 dimensions
2. Calculate total score for each (max 50 points)
3. Select the post with HIGHEST total score
4. If ALL posts score below 25/50, note quality concerns

RESPONSE FORMAT:
Total Scores: Post 1: [X]/50 | Post 2: [Y]/50 | Post 3: [Z]/50
Selected Post (highest scorer): [return the EXACT text of the winning post, nothing else]

IMPORTANT: In your final line, return ONLY the selected post text without any labels, quotes, or prefixes.
"""
```

**Step 3: Test the Enhanced Review**
```bash
python main.py

# Check that:
# - Selection is based on clear criteria
# - Higher quality posts are being chosen
# - Posts with specific value outperform generic ones
```

### Expected Results
- More rigorous quality assessment
- Data-driven selection instead of subjective "fun"
- Better filtering of generic content
- Quantifiable quality metrics

---

## Validation Checklist

After implementing Quick Wins, validate improvements:

### Quality Checks
- [ ] Posts include specific tools, frameworks, or numbers
- [ ] Posts have clear actionable takeaways
- [ ] Avoid generic buzzwords without context
- [ ] Expert voice (not corporate marketing)
- [ ] Pass the "So what?" test (provides genuine value)

### Technical Checks
- [ ] Workflow runs without errors
- [ ] Posts save to `social_media_posts/` directory
- [ ] Character limit respected (<280 chars)
- [ ] Images generate successfully
- [ ] All evaluators run without issues

### Before/After Comparison

Run workflow 3 times with OLD code, 3 times with NEW code:

**Scoring Matrix** (Rate 1-10):
| Metric | Old Avg | New Avg | Improvement |
|--------|---------|---------|-------------|
| Specificity | ___ | ___ | ___% |
| Actionability | ___ | ___ | ___% |
| Value Density | ___ | ___ | ___% |
| Uniqueness | ___ | ___ | ___% |
| Overall Quality | ___ | ___ | ___% |

---

## Troubleshooting

### Issue: Posts are too long (>280 chars)
**Solution**: Adjust template examples to be shorter, emphasize brevity in prompt

### Issue: Posts still generic despite new prompts
**Solution**: 
1. Check that research provides specific insights
2. May need to implement Priority 2 (enhanced research)
3. Increase temperature slightly for more creative output

### Issue: Template format not being followed
**Solution**: 
1. Make template guidance more explicit in prompt
2. Add few-shot examples in system message
3. Verify get_random_template() is working correctly

### Issue: Content reviewer not selecting best post
**Solution**:
1. Verify scoring criteria are clear in prompt
2. May need to add explicit scoring examples
3. Check that LLM is gpt-5-mini or better

---

## Next Steps After Quick Wins

Once Quick Wins are validated:

1. **Implement Priority 2 Recommendations**:
   - Enhanced research with multi-dimensional search
   - Source quality filtering
   - Insight extraction

2. **Add New Evaluators**:
   - Value proposition evaluator
   - Authenticity scorer
   - Engagement predictor

3. **Measure Results**:
   - Track engagement metrics on posted content
   - Compare to baseline from before implementation
   - Iterate on prompts based on real performance data

4. **Store Successful Patterns**:
   - Track which templates perform best
   - Build library of high-performing examples
   - Fine-tune template selection logic

---

## Rollback Procedure

If implementation causes issues:

```bash
# Restore backups
mv src/agents/content_creator.py.backup src/agents/content_creator.py
mv src/agents/content_reviewer.py.backup src/agents/content_reviewer.py

# Remove new templates (if needed)
rm -rf src/templates/

# Test rollback
python main.py
```

---

## Support & Questions

For implementation help:
1. Review the POST_QUALITY_ANALYSIS_AND_RECOMMENDATIONS.md for context
2. Check CONFIGURATION_EXAMPLES.md for environment setup
3. Test changes incrementally (one Quick Win at a time)
4. Compare generated posts before/after each change

**Remember**: The goal is specific, valuable content that tech professionals want to share. If a change doesn't improve that metric, revert and iterate.
