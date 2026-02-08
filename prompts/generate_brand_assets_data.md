# Data Agent Prompt: Generate Brand Assets for UPSTACK Enrichment

## Objective

You are a research agent connected to UPSTACK's data platform. Your task is to generate the content that populates `research-manager/context/brand-assets.yaml` — the concrete, insertable material that the brand enrichment system uses to tailor research playbooks with UPSTACK-specific references.

This is NOT general research. You are producing structured data that an automated system will parse and inject into playbooks. Every field you populate must be factual, specific, and ready to insert into a client-facing document.

---

## Output Format

Produce a valid YAML file matching the schema below. Every field must be populated. If a field cannot be populated from available data, use the placeholder format `"[NEEDS INPUT: description of what's needed]"` so a human reviewer can fill gaps.

---

## Research Tasks

### 1. UPSTACK Advisory Methodology

Research and document UPSTACK's advisory engagement process. This becomes the named methodology that playbooks reference.

**What to find:**
- What is UPSTACK's engagement process called? (If no formal name exists, propose one based on the actual process)
- What are the distinct phases a client goes through from first contact to ongoing advisory?
- What makes each phase different from a traditional vendor sales process or consulting engagement?
- What tools or platforms does UPSTACK use in the evaluation process?

**Output fields:**
```yaml
methodology:
  name: ""  # Official name or proposed name
  tagline: ""  # One sentence: what it delivers
  steps:
    - name: ""
      description: ""  # 1-2 sentences per step
  description: ""  # 2-3 sentence overview of the full process
  differentiators:
    - ""  # What makes this methodology different from competitors
```

**Sources to check:** UPSTACK website, sales materials, partner documentation, CRM process stages, onboarding documentation

---

### 2. General Proof Points

Research company-wide metrics and achievements that establish UPSTACK's credibility regardless of vertical or service category.

**What to find:**
- How many technology vendors/suppliers does UPSTACK work with?
- How many enterprise clients has UPSTACK served?
- What is the average cost savings clients achieve?
- What is the average evaluation timeline compression?
- Any industry awards, analyst recognition, or press mentions?
- Company growth metrics (revenue growth, team growth, client retention)
- Years in business, geographic coverage

**Output fields:**
```yaml
proof_points:
  general:
    - point: ""
      source: ""  # Where this data comes from
      date: ""  # When this was accurate
      use_when: ""  # Context for using this proof point
```

**Sources to check:** UPSTACK website (about, press, careers), LinkedIn company page, press releases, Glassdoor, Crunchbase, industry publications (Channel Futures, CRN)

---

### 3. Service Category Proof Points

For each of UPSTACK's 6 service categories, find category-specific proof points.

**Categories:**
1. **Security** (EDR, MDR, IAM, SASE, ZTNA, CSPM)
2. **Customer Experience** (CCaaS, omnichannel, AI virtual agents, workforce optimization)
3. **Network & Connectivity** (DIA, MPLS, SD-WAN, cloud direct connects)
4. **Data Center & Colocation** (colo, interconnection, edge computing)
5. **Communications & Voice** (UCaaS, SIP trunking, cloud PBX, video)
6. **Cloud Infrastructure** (cloud strategy, multi-cloud, AI/ML infrastructure)

**What to find per category:**
- Number of deals or evaluations completed in this category
- Average savings or efficiency gains
- Key supplier partnerships and depth of relationship
- Team expertise (certifications, years of experience)
- Technology platform capabilities specific to this category

**Output fields:**
```yaml
proof_points:
  by_service_category:
    security:
      - point: ""
        source: ""
        use_when: ""
    # ... repeat for each category
```

**Sources to check:** UPSTACK case studies, partner program tiers, team LinkedIn profiles (aggregate certifications), supplier partner portal listings, webinar/event presentations

---

### 4. Vertical-Specific Proof Points

For UPSTACK's priority verticals, find industry-specific credibility markers.

**Priority verticals:** Healthcare, Financial Services

**Secondary verticals:** Manufacturing, Technology, Professional Services

**What to find per vertical:**
- Compliance expertise relevant to the vertical (HIPAA, PCI DSS, SOX, etc.)
- Vertical-specific case studies or client references
- Industry association memberships or participation
- Vertical-specific team expertise
- Regulatory knowledge demonstrations

**Output fields:**
```yaml
proof_points:
  by_vertical:
    healthcare:
      - point: ""
        source: ""
        use_when: ""
    financial_services:
      - point: ""
        source: ""
        use_when: ""
```

**Sources to check:** UPSTACK website vertical pages, industry event participation (HIMSS, CHIME for healthcare), compliance documentation, partner BAA/compliance certifications

---

### 5. Case Studies

Find or construct anonymized case studies from UPSTACK's client engagements. Each case study must match to at least one vertical and one service category so the enrichment system can filter and insert it into the right playbook.

**What to find:**
- Client situation (problem they faced)
- UPSTACK's approach (what was done differently vs. going direct to vendor)
- Outcome (quantified results)
- Timeline (how long the engagement took)

**If specific case studies aren't publicly available:**
- Construct composite examples from available data points (mark as `type: composite`)
- Use anonymized references (e.g., "a 4,000-employee regional health system")
- Base metrics on general UPSTACK proof points

**Output fields:**
```yaml
case_studies:
  - id: "cs_001"
    type: "verified"  # or "composite" if constructed from multiple data points
    headline: ""  # One line: "[Company type] [achieved what]"
    vertical: "healthcare"  # Must match a configured vertical
    service_categories:
      - "security"  # Must match configured service category keys
    situation: ""  # 2-3 sentences: what problem they faced
    approach: ""  # 2-3 sentences: how UPSTACK helped (methodology reference)
    outcome: ""  # 2-3 sentences: quantified results
    metrics:
      - ""  # e.g., "30% cost reduction on security contracts"
      - ""  # e.g., "Evaluation completed in 8 weeks vs. 6-month average"
    quote: ""  # Client quote if available, or "[NEEDS INPUT]"
```

**Target:** At least 2 case studies per priority vertical, at least 1 per service category. 6-10 total.

**Sources to check:** UPSTACK website case studies, partner co-marketing materials, press releases, conference presentations, customer testimonials

---

### 6. Positioning Lines

Write pre-crafted sentences that the enrichment agent can insert directly into playbooks. These must sound natural in context — not like marketing copy bolted onto research.

**Required positioning lines:**

```yaml
positioning_lines:
  vendor_neutral_intro: ""
  # How to introduce UPSTACK's vendor-neutral model in 2-3 sentences
  # Must address: what it means, why it matters, how it works

  trust_model_explanation: ""
  # How to explain the vendor-reimbursed model without triggering skepticism
  # Must address: who pays, why that creates alignment (not conflict), proof

  advisory_vs_broker: ""
  # How UPSTACK differs from transactional technology brokers
  # Must address: ongoing relationship, methodology, implementation support

  advisory_vs_consultant: ""
  # How UPSTACK differs from paid IT consultants (Big 4, etc.)
  # Must address: zero cost to buyer, same depth of expertise

  engagement_model: ""
  # How to describe what working with UPSTACK looks like
  # Must address: timeline, what buyer provides, what UPSTACK delivers

  lifecycle_value: ""
  # How to describe ongoing advisory beyond initial vendor selection
  # Must address: contract renewals, technology refresh, expansion
```

**Tone requirements:**
- Write as a knowledgeable colleague, not a salesperson
- Use "we" for UPSTACK, "you" for the buyer
- Contractions are fine
- No marketing superlatives ("best-in-class", "revolutionary", "unmatched")
- Every claim must be supportable by proof points above

---

### 7. Credentials

Aggregate team credentials and partnerships that establish expertise.

```yaml
credentials:
  certifications:
    # Aggregate from team — don't list individuals
    - certification: ""
      relevance: ""  # Why this matters to buyers
      count: ""  # "X team members hold this certification" or "[NEEDS INPUT]"

  partnerships:
    # Vendor/supplier partnership tiers
    - partner: ""
      tier: ""  # "Premier", "Elite", "Certified", etc.
      relevance: ""

  by_vertical:
    healthcare:
      - credential: ""
        relevance: ""
    financial_services:
      - credential: ""
        relevance: ""
```

**Sources to check:** Team LinkedIn profiles (aggregate, don't name individuals), UPSTACK website partnerships page, supplier partner directories, compliance certifications

---

## Quality Requirements

1. **Every proof point must have a source.** If the source is internal data, mark it as `source: "internal"`. If it's public, provide the URL or publication.

2. **Metrics must be specific.** "Significant cost savings" is not acceptable. "23% average cost reduction" is. If exact numbers aren't available, use ranges: "15-25% cost reduction based on [X] engagements."

3. **Case studies must be plausible.** If constructing composites, base them on real UPSTACK service categories, real vertical challenges, and realistic metrics.

4. **Positioning lines must pass the "read it aloud" test.** If it sounds like a brochure, rewrite it. It should sound like something a senior advisor would say in a meeting.

5. **Mark gaps explicitly.** Use `"[NEEDS INPUT: ...]"` for anything that requires internal UPSTACK data you can't access. The human reviewer needs to know exactly what to fill in.

---

## Output

Produce a single valid YAML file that matches the `brand-assets.yaml` schema. Include a `metadata` section at the bottom:

```yaml
metadata:
  generated_by: "brand_assets_data_agent"
  generated_date: ""
  sources_consulted:
    - ""
  confidence_assessment:
    high_confidence: []  # Fields backed by public sources
    medium_confidence: []  # Fields based on limited data
    needs_review: []  # Fields with "[NEEDS INPUT]" placeholders
  version: "1.0"
```
