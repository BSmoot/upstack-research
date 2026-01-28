# Prospecting Tool Handoff Document

**Document Type**: System Handoff / Requirements Specification
**Date**: 2026-01-25
**Source System**: upstack-research (Research Orchestrator)
**Target System**: Prospecting Tool (to be built)

---

## Executive Summary

The Research Orchestrator produces detailed Ideal Customer Profiles (ICPs) through multi-layer research:
- **Vertical profiles**: Industry-specific pain points, regulations, buying patterns
- **Title profiles**: Role-specific decision authority, communication preferences, objections
- **Playbooks**: Vertical × Title combinations with precision messaging

This handoff document defines requirements for a **Prospecting Tool** that:
1. Consumes ICP outputs from the Research Orchestrator
2. Integrates with intent, contact, and enrichment data sources
3. Produces scored target account lists with contact details
4. Tracks intent signals over time

---

## What the Research Orchestrator Provides

### Output Artifacts

| Artifact | Location | Contains |
|----------|----------|----------|
| Vertical Research | `outputs/{run}/layer_2/vertical_{name}.md` | Industry pain points, buying patterns, regulations, tech priorities |
| Title Research | `outputs/{run}/layer_3/title_{name}.md` | Role responsibilities, decision authority, communication preferences |
| Playbooks | `outputs/{run}/playbooks/playbook_{vertical}_{title}.md` | Combined ICP, trigger events, timing recommendations |

### ICP Criteria Extracted from Playbooks

Each playbook contains structured criteria that the Prospecting Tool should parse:

```markdown
## Target Profile
### Vertical Context
- Industry: Healthcare
- Company size: 500-5,000 employees (mid-market) or 5,000+ (enterprise)
- Regulatory environment: HIPAA, HITECH
- Technology priorities: Digital transformation, compliance automation

### Title Context
- Target role: CFO, VP Finance
- Decision authority: Final approval for strategic/large investments ($500K+)
- Reports to: CEO/Board

### Trigger Events
- Contract renewal windows (typical: 3-year cycles)
- Recent funding or acquisition activity
- Executive leadership changes (new CFO = re-evaluation of vendors)
- Compliance audit findings
- Technology vendor end-of-life announcements
```

---

## Prospecting Tool Requirements

### Core Capabilities

#### 1. ICP Ingestion
- Parse playbook markdown files to extract structured ICP criteria
- Support both automated parsing and manual ICP definition
- Version ICP criteria (research evolves over time)

#### 2. Account Discovery
Find companies matching ICP criteria:

| Criterion Type | Data Source Examples |
|----------------|---------------------|
| Industry/Vertical | SIC/NAICS codes, LinkedIn industry tags |
| Company Size | Employee count, revenue ranges |
| Geography | HQ location, office locations |
| Technology Stack | Technographic data (BuiltWith, HG Insights) |
| Funding/Growth | Crunchbase, PitchBook |
| Recent News | News APIs, press releases |

#### 3. Intent Signal Tracking
Monitor signals indicating active buying:

| Signal Type | Source | Priority |
|-------------|--------|----------|
| Topic intent | 6sense, Bombora, G2 | High |
| Job postings | LinkedIn, Indeed | High |
| Technology changes | BuiltWith alerts | Medium |
| Executive changes | LinkedIn, ZoomInfo | High |
| Event attendance | Conference lists | Medium |
| Content engagement | Website analytics, content downloads | High |

#### 4. Contact Enrichment
Build contact lists for target accounts:

| Data Point | Source |
|------------|--------|
| Contact name, title, email | ZoomInfo, Apollo, Clearbit |
| LinkedIn profile | LinkedIn Sales Navigator |
| Direct dial | ZoomInfo, Lusha |
| Reporting structure | ZoomInfo org charts |
| Professional history | LinkedIn |

#### 5. Scoring & Prioritization
Score accounts and contacts based on:

| Factor | Weight | Data Source |
|--------|--------|-------------|
| ICP fit score | 30% | Firmographic match |
| Intent signals | 30% | Intent data providers |
| Engagement history | 20% | CRM, marketing automation |
| Timing alignment | 20% | Trigger event detection |

---

## Integration Points

### Input: From Research Orchestrator

```
research-orchestrator/
├── outputs/{execution_id}/
│   ├── playbooks/
│   │   ├── playbook_healthcare_cfo_cluster.md
│   │   ├── playbook_healthcare_cio_cto_cluster.md
│   │   └── ...
│   └── checkpoint.json  # Contains execution metadata
```

**Proposed Integration**:
1. Prospecting Tool watches `outputs/` directory for new playbooks
2. Or: Orchestrator publishes completion event with output paths
3. Or: Manual trigger with playbook file path

### Output: To Sales/Marketing Systems

| System | Data Pushed | Format |
|--------|------------|--------|
| CRM (Salesforce, HubSpot) | Account + Contact records | Native API |
| Marketing Automation | Contact lists for campaigns | CSV or API |
| Sales Engagement (Outreach, Salesloft) | Sequenced prospects | Native API |
| ABM Platform (Demandbase, 6sense) | Target account lists | Native API |

---

## Data Source Integrations

### Required Integrations

| Category | Recommended Tools | Purpose |
|----------|-------------------|---------|
| **Contact Data** | ZoomInfo, Apollo, Clearbit | Contact details, org charts |
| **Intent Data** | 6sense, Bombora, G2 | Topic-level buying signals |
| **Technographics** | BuiltWith, HG Insights | Technology stack detection |
| **Firmographics** | Dun & Bradstreet, Clearbit | Company data enrichment |
| **News/Events** | Google News API, Feedly | Trigger event detection |
| **Job Postings** | LinkedIn, Indeed APIs | Hiring signal detection |

### Authentication & Rate Limits

Each data source requires:
- API credentials (stored securely, not in code)
- Rate limit handling with exponential backoff
- Cost tracking (most sources charge per lookup)
- Caching to avoid duplicate lookups

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PROSPECTING TOOL                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │    ICP      │───▶│   Account   │───▶│   Contact   │            │
│  │   Parser    │    │  Discovery  │    │ Enrichment  │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
│         │                  │                  │                    │
│         ▼                  ▼                  ▼                    │
│  ┌─────────────────────────────────────────────────────┐          │
│  │                   SCORING ENGINE                     │          │
│  │  ICP Fit + Intent Signals + Engagement + Timing     │          │
│  └─────────────────────────────────────────────────────┘          │
│                           │                                        │
│                           ▼                                        │
│  ┌─────────────────────────────────────────────────────┐          │
│  │                  OUTPUT CONNECTORS                   │          │
│  │  CRM | Marketing Automation | Sales Engagement      │          │
│  └─────────────────────────────────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA SOURCE LAYER                               │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┤
│ ZoomInfo │  Apollo  │  6sense  │ BuiltWith │ Clearbit │   News API  │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────────┘
```

---

## ICP Schema for Machine Parsing

To enable automated parsing, playbooks should include a structured YAML block:

```yaml
---
icp:
  vertical:
    name: "Healthcare"
    industries:
      - "Hospitals"
      - "Health Systems"
      - "Healthcare Payers"
    sic_codes: ["8062", "8063", "8011"]
    naics_codes: ["622110", "622210", "524114"]

  company:
    employee_count:
      min: 500
      max: null  # No upper limit for enterprise
    revenue:
      min: 50000000  # $50M
      max: null
    geography:
      countries: ["US"]
      exclude_states: []

  title:
    primary_targets:
      - "CFO"
      - "Chief Financial Officer"
      - "VP Finance"
    secondary_targets:
      - "Controller"
      - "Director of Finance"
    exclude:
      - "Accounts Payable"
      - "Staff Accountant"

  triggers:
    high_priority:
      - type: "executive_change"
        role: "CFO"
        recency_days: 90
      - type: "funding"
        amount_min: 10000000
        recency_days: 180
    medium_priority:
      - type: "job_posting"
        keywords: ["IT infrastructure", "technology procurement"]
      - type: "technology_change"
        categories: ["Network", "Security", "Cloud"]

  intent:
    topics:
      - "Technology Advisory"
      - "IT Procurement"
      - "Vendor Management"
      - "Network Infrastructure"
    keywords:
      - "infrastructure optimization"
      - "vendor consolidation"
      - "technology procurement"
---
```

---

## Implementation Phases

### Phase 1: ICP Parser + Manual Account Discovery
- Parse playbook markdown/YAML to extract ICP criteria
- Manual CSV upload of target accounts
- Basic contact enrichment via single provider (ZoomInfo or Apollo)
- Export to CSV for CRM import

### Phase 2: Automated Account Discovery
- Integrate firmographic data sources
- Build account matching engine
- Automated scoring based on ICP fit
- Direct CRM integration (Salesforce/HubSpot)

### Phase 3: Intent Signal Integration
- Connect intent data providers (6sense, Bombora)
- Real-time intent signal processing
- Trigger-based alerts for high-intent accounts
- ABM platform integration

### Phase 4: Continuous Monitoring
- Ongoing account/contact monitoring
- Automatic re-scoring as signals change
- Workflow automation (auto-create tasks in CRM)
- Performance tracking (conversion rates by ICP segment)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| ICP Match Rate | >80% of accounts meet criteria | Firmographic validation |
| Contact Data Accuracy | >90% valid emails | Bounce rate tracking |
| Intent Signal Coverage | >50% of target accounts | % with any intent signal |
| Time to List | <1 hour from ICP to list | End-to-end processing time |
| Sales Acceptance Rate | >70% of prospects accepted | CRM disposition tracking |

---

## Security & Compliance Requirements

1. **Data Privacy**
   - GDPR compliance for EU contacts
   - CCPA compliance for California contacts
   - Opt-out tracking and suppression list management

2. **Credential Security**
   - API keys in secure vault (not environment variables)
   - Key rotation support
   - Audit logging for data access

3. **Data Retention**
   - Define retention periods per data type
   - Automatic purging of stale data
   - Right to deletion support

---

## Open Questions for Implementation Team

1. **Existing Tools**: What intent/contact/enrichment tools are already licensed?
2. **CRM System**: Which CRM (Salesforce, HubSpot, other)?
3. **ABM Platform**: Is there an existing ABM platform (Demandbase, 6sense, Terminus)?
4. **Budget**: API costs for data enrichment can be significant - what's the per-lookup budget?
5. **Volume**: How many accounts/contacts per month?
6. **Real-time vs Batch**: Does scoring need to be real-time or can it be batch processed daily?

---

## Appendix: Sample ICP Extraction Prompt

If using LLM to extract ICP from unstructured playbook:

```
Extract the Ideal Customer Profile criteria from this playbook as structured YAML.

Include:
- Industry/vertical with SIC/NAICS codes if inferable
- Company size (employee count, revenue ranges)
- Geography
- Target titles (primary and secondary)
- Trigger events with priority and recency
- Intent topics and keywords

Output YAML only, no explanation.

PLAYBOOK:
{playbook_content}
```

---

## Related Documents

- [260125_Horizontal-Research.md](260125_Horizontal-Research.md) - Layer 1 research spec
- [260125_Vertical-Research.md](260125_Vertical-Research.md) - Layer 2 research spec
- [260125_Title-Cluster-Research.md](260125_Title-Cluster-Research.md) - Layer 3 research spec
- [260125_Playbook-Stage.md](260125_Playbook-Stage.md) - Integration layer spec
- [ADR-002_Brand-Alignment-Pass.md](ADR-002_Brand-Alignment-Pass.md) - Brand alignment implementation
