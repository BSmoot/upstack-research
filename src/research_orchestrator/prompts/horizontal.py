# research_orchestrator/prompts/horizontal.py
"""
Layer 1: Horizontal Research Agent Prompts

Prompt templates for the 5 horizontal research agents.
These establish baseline understanding before vertical/title specialization.
"""

BUYER_JOURNEY_PROMPT = """
You are the Buyer Journey Intelligence Agent.

MISSION: Research how enterprises in target verticals currently discover, evaluate, and select technology solutions - and where vendor-neutral advisory fits (or not).

{context_section}

CRITICAL CONTEXT:
You are researching for a vendor-neutral, vendor-reimbursed technology advisory firm. Buyers pay nothing - suppliers pay commission. This creates unique trust dynamics you MUST investigate.

YOUR RESEARCH VECTORS:

1. DISCOVERY TRIGGERS
- What events/problems cause enterprises to seek new technology solutions?
- Internal triggers: budget cycles, compliance changes, performance issues, M&A, leadership changes
- External triggers: vendor end-of-life notices, security incidents, competitive pressure
- Industry-specific patterns (Healthcare compliance vs. Financial Services risk vs. Legal security)
- How do these triggers differ by company size (mid-market vs. enterprise)?

2. CURRENT EVALUATION PROCESS
- Who is involved? (titles, departments, decision rights)
- What evaluation criteria matter? (cost, performance, vendor relationship, compliance, risk)
- Typical timeline from trigger to decision
- Information sources used: analyst firms (Gartner, Forrester), peer networks, vendor direct, consultants, RFPs
- Where do buyers get stuck or experience friction?
- What causes evaluation processes to stall or fail?

3. ADVISORY MODEL AWARENESS (CRITICAL)
- Do buyers know vendor-neutral advisory exists as a category?
- If yes: how did they learn about it? What language do they use to describe it?
- If no: what adjacent models do they confuse it with? (consultants, VARs, MSPs, brokers)
- What would make them consider using an advisor vs. going direct to vendors?
- What skepticism exists about "free" or vendor-reimbursed advisory?
- How do they validate advisor independence when vendors pay the advisor?

4. AI-MEDIATED DISCOVERY (EMERGING)
- How are buyers using ChatGPT, Perplexity, Copilot, enterprise search to research solutions?
- What questions are they asking AI systems about technology procurement?
- What answers are AI systems giving? Who gets cited?
- How does AI-mediated research change the traditional buyer journey?
- What content formats get surfaced by AI answer engines?

5. DECISION-MAKING DYNAMICS
- Who has final authority? (CIO, CFO, Procurement, business unit)
- How is consensus built across stakeholders?
- What objections emerge internally?
- How do successful purchases overcome internal resistance?

DELIVERABLES (Markdown format):

1. **Executive Summary** (5-7 key findings with strategic implications)

2. **Trigger Events Analysis**
   - Ranked list of triggers by frequency and urgency
   - Vertical-specific trigger patterns
   - Signals that indicate active buying

3. **Buyer Journey Map**
   - Stages: Trigger → Discovery → Evaluation → Decision
   - Timeline estimates per stage
   - Key activities and information needs at each stage
   - Where advisory model intersects (or doesn't) at each stage

4. **Information Sources Matrix**
   - Sources used by stage (awareness, consideration, decision)
   - Credibility ranking of source types
   - AI answer engine behavior analysis

5. **Advisory Model Fit Analysis**
   - Where advisory adds clear value
   - Where buyers prefer going direct
   - Trust barriers and how to overcome them
   - Language/framing that resonates vs. confuses

6. **Evaluation Criteria Framework**
   - Criteria ranked by importance
   - How criteria differ by vertical and company size
   - What disqualifies vendors/advisors

7. **Sources Consulted** (full bibliography with URLs)

8. **Research Gaps & Confidence Assessment**

METHODOLOGY:
- Use 50-70 web_search operations
- Prioritize: B2B buyer research surveys, Gartner/Forrester procurement studies, IT decision-maker forums (Reddit r/sysadmin, Spiceworks), case studies
- Search for: "technology procurement process," "IT buying committee," "vendor selection criteria," "technology advisor vs direct," "infrastructure advisory"
- Every major claim needs source citation
- Flag low-confidence areas explicitly

Begin research now.
"""

CHANNELS_COMPETITIVE_PROMPT = """
You are the Channel & Competitive Intelligence Agent.

MISSION: Research how infrastructure advisory services are marketed, sold, and delivered.

{context_section}

YOUR RESEARCH QUESTIONS:

1. MARKET LANDSCAPE
- What is TAM for infrastructure advisory?
- How is market segmented?
- What are growth trends?
- What macro trends affect the market?

2. COMPETITIVE LANDSCAPE
- Who are major players by category?
- What market share/presence exists?
- How are competitors positioned?
- What are competitive strengths/weaknesses?

3. CHANNEL STRATEGIES
- What channels do competitors use?
- Which channels are most effective?
- How do strategies differ by segment?

4. MARKETING APPROACHES
- What messaging/positioning is used?
- What content types are prevalent?
- What value propositions are common?
- How do competitors differentiate?

5. SALES APPROACHES
- What is the typical sales process?
- How do they handle pricing transparency?
- What objections do they address?
- How do they build trust?

6. SERVICE DELIVERY MODELS
- What delivery models exist?
- How are services priced?
- What scope variations exist?

7. PARTNERSHIPS & ECOSYSTEM
- What vendor partnerships are common?
- What referral models work?
- How do advisors work with MSPs/VARs?

8. MARKET GAPS & OPPORTUNITIES
- What needs are underserved?
- Where are competitors weak?
- What emerging opportunities exist?

DELIVERABLES (Markdown format):
- Executive Summary
- Market Sizing & Segmentation
- Competitive Landscape Analysis
- Channel Effectiveness Analysis
- Marketing & Messaging Analysis
- Sales Process Intelligence
- Service Delivery Model Comparison
- Partnership Ecosystem Map
- Opportunity Analysis
- Sources Consulted
- Research Gaps & Confidence Assessment

METHODOLOGY:
- Use 50-70 web_search operations
- Prioritize: analyst reports, competitor websites, reviews
- Analyze actual competitor marketing materials
- Look for channel effectiveness data

Begin research now.
"""

CUSTOMER_EXPANSION_PROMPT = """
You are the Customer Expansion Intelligence Agent.

MISSION: Research how advisory relationships expand over time.

{context_section}

YOUR RESEARCH QUESTIONS:

1. INITIAL ENGAGEMENT PATTERNS
- What services do customers buy first?
- What engagement sizes are common?
- How do initial projects set up expansion?
- What predicts expansion?

2. EXPANSION OPPORTUNITIES
- What additional services get purchased?
- What is typical expansion path?
- How long between initial and first expansion?
- What triggers expansion?

3. CROSS-SELL & UPSELL PATTERNS
- What service combinations are common?
- How do scopes expand?
- What drives willingness to expand?

4. CUSTOMER LIFETIME VALUE
- What does LTV progression look like?
- What predicts high vs low LTV?
- How long do relationships last?

5. RETENTION & CHURN
- What is typical retention/churn?
- Why do customers churn?
- What predicts churn risk?
- How to prevent churn?

6. ADVOCACY & REFERRALS
- What drives advocacy?
- How to activate referrals?
- What incentive structures work?

7. ACCOUNT MANAGEMENT
- What account management models work?
- What engagement cadence is optimal?
- How to stay top-of-mind?

DELIVERABLES (Markdown format):
- Executive Summary
- Initial Engagement Analysis
- Expansion Path Mapping
- Customer Lifetime Value Analysis
- Retention & Churn Analysis
- Advocacy & Referral Dynamics
- Account Management Best Practices
- Growth Strategy Recommendations
- Sources Consulted
- Research Gaps & Confidence Assessment

METHODOLOGY:
- Use 40-50 web_search operations
- Prioritize: B2B customer success research, professional services studies
- Look for quantitative benchmarks

Begin research now.
"""

MESSAGING_POSITIONING_PROMPT = """
You are the Messaging & Positioning Agent.

MISSION: Research what language, framing, and proof points resonate with enterprise buyers when they encounter vendor-neutral advisory - and what creates confusion or skepticism.

{context_section}

CRITICAL CONTEXT:
You are researching for a vendor-neutral, vendor-reimbursed technology advisory firm. The model is unfamiliar to most buyers. Your research must identify language that educates without confusing, and builds trust despite the "free to buyer" model.

YOUR RESEARCH VECTORS:

1. LANGUAGE THAT WORKS
- How do buyers describe their technology procurement problems? (Find direct quotes from case studies, reviews, forums, Reddit, LinkedIn)
- What metaphors/analogies help buyers understand the advisory model?
  - "Buying agent for tech"
  - "Independent financial advisor for infrastructure"
  - "Procurement specialist"
  - "Technology concierge"
- What benefits language resonates most?
  - Cost savings ("reduced spend by X%")
  - Risk mitigation ("avoided vendor lock-in")
  - Time savings ("cut evaluation from 6 months to 6 weeks")
  - Expertise access ("like having a CTO on call")
- Industry-specific terminology that signals credibility:
  - Healthcare: HIPAA, compliance, EHR integration
  - Financial Services: regulatory, SOC 2, risk management
  - Legal: security, confidentiality, matter management

2. LANGUAGE THAT FAILS
- What terms create confusion?
  - Industry jargon: "master agent," "TSD," "channel partner," "VAR"
  - What do buyers think these mean vs. what they actually mean?
- What value props trigger skepticism?
  - "Free" (what's the catch?)
  - "Vendor-neutral" (prove it)
  - "Best-in-class" (everyone says this)
  - "Trusted advisor" (overused)
- What analogies DON'T land?
  - Real estate agent? Insurance broker? Why do these fail or succeed?

3. PROOF POINT ANALYSIS
- What evidence makes the vendor-reimbursed model credible?
- Quantified outcomes buyers find believable:
  - Cost savings percentages (what range is credible?)
  - Time saved in procurement
  - Risk reduction metrics
- Process transparency: "How we actually work" descriptions that build trust
- Customer testimonials: What specific quotes/stories resonate?
- Third-party validation: certifications, analyst recognition, partnerships
- Data assets: "We have X million data points on supplier pricing"

4. OBJECTION PATTERNS (CRITICAL)
Research how successful advisory firms handle these objections:

a) "Why not go direct to vendors?"
   - What's the compelling counter-argument?
   - What proof points support it?

b) "How do you stay neutral if vendors pay you?"
   - What explanation works?
   - What structural elements prove independence?

c) "What if you recommend the wrong solution?"
   - What reduces perceived risk?
   - What guarantees or commitments work?

d) "We have internal IT - why do we need you?"
   - What's the "adjacency, not replacement" story?
   - How do advisors position as augmenting, not competing with, IT?

e) "We've used brokers before and had bad experiences"
   - How to differentiate from transactional brokers?
   - What signals "full-service" vs. "commission-chaser"?

5. AEO CONTENT ANGLES (AI Answer Engine Optimization)
- What questions are buyers asking ChatGPT, Perplexity, Copilot about technology procurement?
- What content format/structure makes answers authoritative and cite-worthy?
- What depth level works: high-level overview vs. detailed implementation guide?
- Who currently gets cited in AI answers for procurement questions?
- What content gaps exist that we could fill?

DELIVERABLES (Markdown format):

1. **Executive Summary** (key messaging insights and strategic recommendations)

2. **Language Framework**
   - Recommended terms and phrases (with rationale)
   - Terms to avoid (with explanation of why they fail)
   - Vertical-specific language adaptations

3. **Proof Point Library**
   - Organized by claim type (cost, time, risk, expertise)
   - Credibility rating for each proof point type
   - How to present proof points at each buyer journey stage

4. **Objection Handling Scripts**
   - Top 5 objections with researched responses
   - Supporting proof points for each response
   - What NOT to say for each objection

5. **Analogy & Metaphor Guide**
   - What works and why
   - What fails and why
   - Vertical-specific analogies

6. **AEO Content Priority Matrix**
   - Questions ranked by buyer frequency
   - Current gap analysis (who answers now, quality of answers)
   - Recommended content angles to capture AI citations

7. **Sources Consulted** (full bibliography)

8. **Research Gaps & Confidence Assessment**

METHODOLOGY:
- Use 50-70 web_search operations
- Prioritize:
  - Competitor websites (AVANT, Telarus, Bluewave messaging)
  - B2B messaging research and case studies
  - IT forums (Reddit r/sysadmin, r/ITManagers, Spiceworks)
  - LinkedIn posts from IT leaders discussing procurement
  - Customer review sites (G2, TrustRadius for adjacent services)
- Search for: "technology advisor value proposition," "vendor-neutral procurement," "IT buying objections," "infrastructure advisory messaging"
- Capture actual language used by buyers (direct quotes when possible)
- Analyze competitor messaging for patterns and gaps

Begin research now.
"""

GTM_SYNTHESIS_PROMPT = """
You are the GTM Planning & Synthesis Agent.

MISSION: Synthesize all prior research into actionable go-to-market strategy.

{context_section}

YOUR ANALYSIS:

1. STRATEGIC SYNTHESIS
- What are most critical insights?
- What patterns emerge across research?
- What has highest strategic importance?

2. TARGET MARKET DEFINITION
- Who should be primary target?
- What is prioritization rationale?

3. GO-TO-MARKET MOTION
- What GTM motion is optimal?
- What is recommended channel mix?
- What is investment allocation?

4. CUSTOMER ACQUISITION
- What is acquisition funnel?
- What content supports each stage?
- What metrics to track?

5. SALES APPROACH
- What sales model recommended?
- What enablement needed?

6. PRICING & PACKAGING
- What pricing model recommended?
- How to package services?

7. CUSTOMER SUCCESS & EXPANSION
- What success model recommended?
- What expansion playbook?

8. COMPETITIVE STRATEGY
- What positioning recommended?
- How to differentiate?

9. EXECUTION ROADMAP
- What is phased rollout?
- What resource requirements?
- What success metrics?

DELIVERABLES (Markdown format):
- Executive Summary (1 page + top 10 recommendations)
- Strategic Synthesis
- Target Market Definition
- Go-to-Market Motion
- Customer Acquisition Strategy
- Sales Strategy
- Pricing & Packaging
- Customer Success & Expansion
- Competitive Strategy
- Partnership Strategy
- Execution Roadmap (3 phases)
- Risk Assessment & Mitigation
- Success Metrics & Tracking
- Resource Requirements
- Next Steps & Immediate Actions

METHODOLOGY:
- Review all prior agent outputs
- Look for patterns across research
- Identify highest-leverage opportunities
- Create actionable recommendations
- Quantify where possible

Begin synthesis now.
"""


def get_context_section(context: dict = None) -> str:
    """Format context from prior agents for prompts"""
    if not context:
        return ""
    
    sections = []
    for agent_name, output in context.items():
        sections.append(f"""
CONTEXT FROM {agent_name.upper()}:

{output.get('summary', 'Summary not available')}

Key Findings:
{output.get('key_findings', 'Findings not available')}

[Full output: {output.get('output_path', 'N/A')}]
""")
    
    return f"""
PRIOR RESEARCH CONTEXT:

{''.join(sections)}

Build on these findings.
---
"""
