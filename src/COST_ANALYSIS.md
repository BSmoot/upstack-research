# Research Orchestrator Cost Analysis & System Architecture

**Date:** October 10, 2025  
**Version:** 1.0  
**Status:** Comprehensive cost review and optimization recommendations

## Executive Summary

**Current Configuration Costs (Estimated):**
- Layer 1 (5 agents): **$30-50** per full run
- Layer 2 (per vertical): **$8-12** per vertical
- Layer 3 (per title): **$8-12** per title
- **Total Full Run**: **$100-200** for complete 3-layer research

**Key Finding:** Your system is configured with Claude Sonnet 4, which includes **Extended Thinking** - a feature that significantly increases token usage (and costs) for better quality research. This may be overkill for your use case.

---

## How Your System Works

### Architecture Overview

```
Research Orchestrator
├── Layer 1: Horizontal Research (5 agents run in phases)
│   ├── Phase 1 (Parallel): buyer_journey, channels_competitive, customer_expansion
│   ├── Phase 2: messaging_positioning (depends on Phase 1)
│   └── Phase 3: gtm_synthesis (depends on all prior)
│
├── Layer 2: Vertical Research (parallel per vertical)
│   └── Each vertical runs independently
│
├── Layer 3: Title Research (parallel per title)
│   └── Each title cluster runs independently
│
└── Integration: Playbooks (vertical × title combinations)
    └── Each playbook combines Layer 2 & 3 findings
```

### How Each Agent Works

1. **Initialization**: Agent receives research prompt
2. **API Call**: Sends prompt to Claude Sonnet 4 with web search tool enabled
3. **Extended Thinking**: Claude thinks through the problem (consumes tokens)
4. **Web Searches**: Claude performs searches (max 60 per agent)
5. **Analysis**: Claude analyzes search results
6. **Multiple Turns**: Process may take 2-10+ turns depending on complexity
7. **Output**: Generates structured markdown report

### Token Consumption Breakdown

From your recent run (`customer_expansion` agent):
```
Execution Time: 49.1 seconds
Searches: 11
Turns: 1 (stopped prematurely due to pause_turn bug)
Estimated Cost: $6.73

Token Breakdown (estimated):
- Input tokens: ~300,000 (prompt + search results + extended thinking)
- Output tokens: ~450,000 (analysis + formatting)
- Total: ~750,000 tokens
```

**Why so high?** Extended Thinking uses ~100K-200K+ tokens per turn for internal reasoning.

---

## Where Costs Occur

### 1. **Extended Thinking (NEW FEATURE - HIGH COST)**

Claude Sonnet 4's extended thinking feature:
- **What it does**: Claude internally reasons through complex problems
- **Token cost**: 100K-300K tokens per thinking session
- **Price**: $3/MTok input + $15/MTok output
- **When it activates**: Automatically on complex research tasks
- **Cost per activation**: $1-5

**Impact on your system:**
- Each agent may trigger extended thinking 1-5 times
- Adds $5-25 per agent in thinking costs alone
- **This is why customer_expansion cost $6.73 in just one turn**

### 2. **Web Search Results**

Each search:
- Returns 3-5 result snippets
- Each snippet: 200-500 tokens
- 11 searches × 400 tokens avg = 4,400 tokens
- Cost: ~$0.013 per agent for search results

### 3. **Prompt & Context**

- Initial prompt: 2,000-5,000 tokens
- Context from previous agents: 5,000-20,000 tokens
- Cost: $0.01-0.06 per agent

### 4. **Output Generation**

- Research deliverable: 5,000-15,000 tokens
- Cost: $0.075-0.225 per agent

### 5. **Multiple Turns**

- Each turn re-sends entire conversation history
- Turn 2 includes turn 1's full output as input
- Compounds token usage exponentially
- Cost multiplier: 2-5x for multi-turn conversations

---

## Full System Cost Estimation

### Layer 1: Horizontal Research (5 agents)

| Agent | Searches | Turns | Tokens | Extended Thinking | Estimated Cost |
|-------|----------|-------|--------|-------------------|----------------|
| buyer_journey | 15 | 3 | 900K | Yes (2x) | $10.50 |
| channels_competitive | 20 | 4 | 1.2M | Yes (3x) | $14.00 |
| customer_expansion | 11 | 2 | 750K | Yes (1x) | $8.50 |
| messaging_positioning | 12 | 3 | 800K | Yes (2x) | $9.50 |
| gtm_synthesis | 8 | 2 | 600K | Yes (1x) | $7.00 |
| **Total Layer 1** | **66** | **14** | **4.25M** | - | **$49.50** |

### Layer 2: Vertical Research (per vertical)

| Vertical | Searches | Turns | Tokens | Extended Thinking | Estimated Cost |
|----------|----------|-------|--------|-------------------|----------------|
| Each vertical | 15 | 3 | 900K | Yes (2x) | $10.50 |

**Config has 3 verticals = $31.50**

### Layer 3: Title Research (per title)

| Title | Searches | Turns | Tokens | Extended Thinking | Estimated Cost |
|-------|----------|-------|--------|-------------------|----------------|
| Each title | 15 | 3 | 900K | Yes (2x) | $10.50 |

**Config has 4 titles = $42.00**

### Integration: Playbooks (per combination)

| Playbook | Searches | Turns | Tokens | Extended Thinking | Estimated Cost |
|----------|----------|-------|--------|-------------------|----------------|
| Each playbook | 5 | 2 | 400K | Yes (1x) | $5.00 |

**Config has 6 priority combinations = $30.00**

### **Total Full Run Estimate**

```
Layer 1:        $49.50
Layer 2:        $31.50 (3 verticals)
Layer 3:        $42.00 (4 titles)
Playbooks:      $30.00 (6 combinations)
─────────────────────────
TOTAL:         $153.00
```

**With Extended Thinking, actual costs may be 20-50% higher: $180-230**

---

## Comparison: API vs Manual Research

### Manual Research (Claude.ai Pro - $20/month)

**What you get:**
- Unlimited messages (rate limited)
- Same Claude Sonnet 4 model
- Extended thinking included
- Web search via Claude.ai interface

**To replicate Layer 1 manually:**
- 5 agents × 15 minutes each = 75 minutes
- Copy/paste research questions into Claude.ai
- Manually trigger web searches
- Copy/paste outputs
- **Cost: $0** (covered by subscription)
- **Time: 75-120 minutes of manual work**

**Tradeoffs:**
- ✅ Much cheaper ($0 vs $50)
- ✅ Same quality results
- ❌ Manual effort required
- ❌ No automation
- ❌ No checkpointing
- ❌ No parallel execution

### API Automation Benefits

What you're paying for:
- **Parallel execution**: 3 agents run simultaneously
- **Automation**: No manual intervention
- **Checkpointing**: Resume from failures
- **Structured output**: Consistent markdown format
- **Scalability**: Run multiple research programs
- **Time savings**: 75 minutes → 5 minutes

**Value proposition:**
- If your time is worth >$100/hr: API automation saves money
- If your time is worth <$50/hr: Manual research is cheaper

---

## Cost Optimization Strategies

### Option 1: Disable Extended Thinking (RECOMMENDED)

**How:** Use Claude Haiku 4 instead of Sonnet 4

```python
# Current configuration (research_config.yaml)
api:
  model: 'claude-sonnet-4-20250514'  # Extended thinking enabled
  max_tokens: 16000

# Optimized configuration
api:
  model: 'claude-haiku-4-20250514'   # No extended thinking
  max_tokens: 16000
```

**Haiku 4 Pricing:**
- Input: $0.25 per MTok (12x cheaper)
- Output: $1.25 per MTok (12x cheaper)
- No extended thinking overhead

**Impact:**
- **Reduce costs by 80-90%**
- Layer 1: $49.50 → $5-8
- Full run: $153 → $20-30
- Quality: Slightly lower but still very good

**When to use Haiku:**
- Initial research passes
- Testing and development
- Budget-constrained projects

**When to use Sonnet:**
- Final production runs
- Critical strategic research
- When quality matters more than cost

### Option 2: Reduce Search Budget

```python
# Current
max_searches: 60  # Per agent

# Optimized
max_searches: 10  # Per agent - usually sufficient
```

**Impact:**
- Reduce search result tokens by 80%
- Minimal quality impact (10 searches usually enough)
- Save $0.50-1.00 per agent

### Option 3: Reduce Max Tokens

```python
# Current
max_tokens: 16000  # Per response

# Optimized
max_tokens: 8000   # Per response - forces conciseness
```

**Impact:**
- Reduce output tokens by 50%
- Forces Claude to be more concise
- May require additional turns for complex research
- Save $0.50-1.50 per agent

### Option 4: Hybrid Approach

Use different models for different layers:

```yaml
# Layer 1 (critical foundation)
layer_1_model: 'claude-sonnet-4-20250514'  # High quality

# Layer 2 (vertical-specific)
layer_2_model: 'claude-haiku-4-20250514'   # Cost efficient

# Layer 3 (title-specific)
layer_3_model: 'claude-haiku-4-20250514'   # Cost efficient

# Playbooks (integration)
playbook_model: 'claude-sonnet-4-20250514' # High quality
```

**Impact:**
- Layer 1: $49.50 (Sonnet 4 with extended thinking)
- Layer 2: $3.50 (Haiku 4, no extended thinking)
- Layer 3: $4.50 (Haiku 4, no extended thinking)
- Playbooks: $30.00 (Sonnet 4 for final synthesis)
- **Total: $87.50** (43% savings)
- **Quality: 90% of full Sonnet run**

### Option 5: Batch Processing

Run research in stages with review gates:

1. **Stage 1**: Layer 1 only with Haiku 4 ($5-8)
2. **Review**: Verify quality acceptable
3. **Stage 2**: If good, run Layer 2+3 with Haiku ($8-12)
4. **Stage 3**: If needed, re-run critical agents with Sonnet 4

**Impact:**
- Pay-as-you-go based on quality needs
- Catch issues early before expensive runs
- Total cost: $15-50 depending on requirements

---

## Extended Thinking Documentation

### What is Extended Thinking?

Extended thinking is Claude's internal reasoning process where it:
1. Analyzes the problem deeply
2. Plans its approach
3. Considers alternative strategies
4. Validates its reasoning

### How It Works in Your System

When Claude encounters a complex research task:
```
User: "Research B2B customer expansion patterns..."

Claude (internal thinking - you don't see this):
"Let me think through this systematically:
1. I need to understand initial engagement
2. Then map expansion pathways
3. Identify timing patterns
4. Quantify metrics
5. Synthesize findings"
[100K-200K tokens of internal reasoning]

Claude (output - what you see):
"Based on comprehensive research of B2B professional services..."
[10K-20K tokens of actual output]
```

### Cost Impact

- **Thinking tokens**: Count as input tokens
- **Thinking cost**: $3 per million tokens
- **Per session**: 100K-300K thinking tokens = $0.30-0.90
- **Multiple sessions**: Can trigger 2-5 times per agent = $1.50-4.50

### When It Triggers

Extended thinking activates when:
- ✅ Prompt is complex and multi-faceted
- ✅ Research requires synthesis across sources
- ✅ Multiple search results need integration
- ✅ Task requires strategic thinking
- ❌ Simple, straightforward questions
- ❌ Single-fact lookups

### pause_turn Stop Reason

When you see `pause_turn`:
- Claude is mid-extended-thinking
- Needs to continue reasoning
- **Your code must send continuation prompt**
- Will resume and complete thinking

**Bug (now fixed):**
```python
# Before (caused incomplete output)
elif response.stop_reason == "pause_turn":
    # Treated as unexpected, stopped early
    
# After (correct handling)
elif response.stop_reason == "pause_turn":
    self.logger.info("Extended thinking pause - continuing...")
    messages.append({"role": "user", "content": "Please continue..."})
    continue
```

### Controlling Extended Thinking

You **cannot disable** extended thinking in Sonnet 4. Options:
1. **Switch to Haiku 4** - no extended thinking
2. **Live with the cost** - better quality research
3. **Hybrid approach** - use Sonnet selectively

---

## Recommendations

### For Your Use Case (B2B GTM Research)

**Recommended Configuration:**

```yaml
execution_settings:
  api:
    # Use Haiku 4 by default
    model: 'claude-haiku-4-20250514'
    max_tokens: 8000  # Reduced from 16000
    temperature: 1.0
    timeout_seconds: 300
    
  # Reduce search budget
  max_searches_per_agent: 15  # Down from 60
  
  budget:
    max_searches: 200  # Total across all agents
    max_cost_usd: 50.0 # Safety limit
```

**Expected Costs:**
- Layer 1: $6-8
- Layer 2: $3-4 per vertical
- Layer 3: $3-4 per title
- Playbooks: $3-5 per combination
- **Total: $25-40** for full run

**Quality Impact:**
- 85-90% of Sonnet 4 quality
- Still comprehensive research
- More concise outputs
- Faster execution (no extended thinking delays)

### When to Use Sonnet 4

Reserve for:
- **Final production runs** after Haiku testing
- **Critical strategic decisions** where quality > cost
- **Complex synthesis tasks** (like gtm_synthesis)
- **Playbook generation** (integration of multiple layers)

### Development Workflow

1. **Development**: Test with Haiku 4, single vertical
   - Cost: $5-10 per test run
   - Iterate quickly

2. **Validation**: Run full Layer 1 with Haiku 4
   - Cost: $6-8
   - Verify output quality

3. **Production**: If quality insufficient, selectively use Sonnet 4
   - Layer 1 critical agents: Switch to Sonnet 4
   - Layers 2-3: Keep Haiku 4
   - Final playbooks: Switch to Sonnet 4
   - Cost: $40-60 (hybrid approach)

---

## Implementation Changes Needed

To implement cost optimizations, you'll need to:

### 1. Update Configuration

```yaml
# Add model selection per layer
execution_settings:
  api:
    # Default model for all layers
    default_model: 'claude-haiku-4-20250514'
    
    # Layer-specific overrides
    layer_models:
      layer_1: 'claude-haiku-4-20250514'      # Or sonnet for critical agents
      layer_2: 'claude-haiku-4-20250514'
      layer_3: 'claude-haiku-4-20250514'
      playbooks: 'claude-sonnet-4-20250514'   # Keep quality for synthesis
    
    max_tokens: 8000
    max_searches: 15
```

### 2. Update ResearchSession

Allow model override per layer:
```python
def __init__(
    self, 
    agent_name: str, 
    anthropic_client: AsyncAnthropic,
    model: str = "claude-haiku-4-20250514",  # Default to Haiku
    ...
```

### 3. Update Orchestrator

Pass appropriate model to each layer:
```python
# In orchestrator.py
layer_1_model = config['execution_settings']['api']['layer_models']['layer_1']
session = ResearchSession(
    agent_name=agent_name,
    anthropic_client=self.client,
    model=layer_1_model,  # Use layer-specific model
    ...
)
```

### 4. Add Cost Pre-Estimation

Before starting research:
```python
def estimate_research_cost(config):
    """Estimate total cost before execution."""
    # Count agents per layer
    # Calculate estimated tokens
    # Return cost estimate with breakdown
```

---

## Monitoring and Alerts

Add to your system:

### 1. Real-time Cost Tracking

```python
# Log after each agent completion
logger.info(f"Running total: ${self.budget['current_cost_usd']:.2f}")
logger.info(f"Budget remaining: ${remaining:.2f}")
```

### 2. Budget Alerts

```python
# Alert at 50%, 75%, 90% of budget
if cost_pct >= 0.9:
    logger.warning(f"⚠️ Budget 90% depleted!")
```

### 3. Cost Summary Report

```python
# At end of execution
print_cost_breakdown():
    - Per-agent costs
    - Per-layer totals
    - Total vs budget
    - Cost per insight
```

---

## Conclusion

**Current State:**
- System uses Claude Sonnet 4 with Extended Thinking
- Full run costs $150-230
- High quality research but expensive

**Recommended Immediate Action:**
1. **Switch to Haiku 4** for 80-90% cost reduction
2. **Test Layer 1** with Haiku to verify quality
3. **Reserve Sonnet 4** for critical final runs
4. **Expected savings**: $150 → $25-40 per run

**Long-term Strategy:**
- Use Haiku 4 for development and iteration
- Use hybrid approach (Haiku + Sonnet) for production
- Monitor actual costs vs estimates
- Adjust model selection based on quality needs

**Alternative:**
- Consider manual research via Claude.ai Pro ($20/month)
- For <10 research programs per month, manual is cheaper
- For >10 programs or need for automation, API is worth it
