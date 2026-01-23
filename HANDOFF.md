# UPSTACK Research System Handoff

## What This Is

AI-powered market research system for UPSTACK, an infrastructure technology advisory firm. The system runs Claude agents that search the web and produce structured research outputs.

## Session Summary (2026-01-23)

Established shared context files and configured three-phase GTM research program.

---

## Repository Structure

```
upstack-research/
├── research-manager/           # User interface and context
│   └── context/                # SHARED CONTEXT (created this session)
│       ├── baseline.yaml       # Company, business model, competition, strategic priorities
│       ├── glossary.yaml       # 200+ industry terms (12 categories)
│       ├── audience-personas.yaml  # IT decision-maker profiles
│       └── writing-standards.yaml  # Output voice/tone guidelines
│
├── build/config/
│   ├── defaults.yaml           # Model strategy (Haiku research, Sonnet synthesis)
│   └── projects/               # PROJECT CONFIGS (created this session)
│       ├── gtm_phase1_2026.yaml    # Phase 1: Foundation research
│       └── gtm_phase2_2026.yaml    # Phase 2: Vertical adaptation
│
└── src/                        # Research orchestrator (Python)
    ├── run_research.py         # CLI entry point
    └── research_orchestrator/  # Execution engine
```

---

## Strategic Context

**UPSTACK's goal is NOT new vertical entry.**

They have customer concentration in: Healthcare, Financial Services, Manufacturing, Technology, Legal.

**The goal is service category expansion:**
- Expand **Security** services (EDR/MDR, SASE/ZTNA, IAM)
- Expand **CX/AI** services (CCaaS, Conversational AI, WFO)

Research should answer: *"How do existing customers evaluate and buy Security and CX/AI services?"*

---

## Three-Phase Research Plan

### Phase 1: Foundation (Before Q2)
**Purpose:** Inform marketing automation and AEO strategy

| Agent | Output | Usage |
|-------|--------|-------|
| buyer_journey | How buyers find/evaluate advisors | AEO content strategy |
| channels_competitive | Where competitors appear | Channel gap analysis |
| gtm_synthesis | Demand gen strategy | Marketing automation inputs |

**Run command:**
```bash
cd src
python run_research.py --agents buyer_journey,channels_competitive,gtm_synthesis \
  --config ../build/config/projects/gtm_phase1_2026.yaml
```

**Cost:** ~$10 | **Timeline:** 2-3 days

---

### Phase 2: Vertical Adaptation (Q2)
**Purpose:** Security/CX playbooks for Healthcare and Financial Services

**Verticals:** Healthcare, Financial Services

**Prerequisites:** Phase 1 checkpoint

**Run command:**
```bash
cd src
python run_research.py --layer 2 \
  --resume gtm_phase1_2026 \
  --config ../build/config/projects/gtm_phase2_2026.yaml
```

**Cost:** ~$6 | **Timeline:** 2-3 days

---

### Phase 3: Title Research (Q3)
**Purpose:** Buying committee tactics, objection handling

**Config:** Not yet created (create after Phase 2 review)

**Typical titles:** CIO/CTO, CFO, VP IT, VP Procurement, CISO

---

## Key Architecture Points

1. **Layer reuse:** Layer 1 runs once. Layer 2/3 run on top via `--resume`
2. **Context injection:** Shared context files feed into agent prompts
3. **Checkpoint system:** All outputs saved; can resume interrupted runs
4. **Model strategy:** Haiku for research ($1-2/agent), Sonnet for synthesis ($4-6)

---

## Business Model Context

- **Compensation:** Vendor-reimbursed (buyers pay nothing, suppliers pay commission)
- **Primary competition:** Direct vendor sales (buyers going direct to carriers/cloud)
- **Trust challenge:** Buyers skeptical of "free" advisory
- **Differentiator:** End-to-end lifecycle solutions + technology platform

---

## Files to Read for Full Context

```bash
# Company context
cat research-manager/context/baseline.yaml

# Phase 1 config
cat build/config/projects/gtm_phase1_2026.yaml

# Phase 2 config
cat build/config/projects/gtm_phase2_2026.yaml

# System documentation
cat research-manager/README.md
cat src/README.md
```

---

## Next Actions

1. **Run Phase 1** — Execute the three foundation agents
2. **Review outputs** — Check `src/outputs/layer_1/` after completion
3. **Run Phase 2** — Execute vertical research using Phase 1 checkpoint
4. **Create Phase 3 config** — After reviewing Phase 2 outputs

---

## Dependencies Confirmed

- Python 3.11+ ✅
- Anthropic API key in `src/.env` ✅
- pip requirements installed ✅
