# Behavioral Design Specification: Research System User Interface

**Version**: 1.0
**Date**: 2025-01-13
**Status**: Draft for Review
**Target Users**: Marketing managers, sales leaders, executives (non-technical)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [User Personas](#user-personas)
3. [Core Behaviors](#core-behaviors)
4. [User Journeys](#user-journeys)
5. [Interface States](#interface-states)
6. [Interaction Patterns](#interaction-patterns)
7. [Error Handling & Recovery](#error-handling--recovery)
8. [Success Criteria](#success-criteria)
9. [Appendix: Behavioral Scenarios](#appendix-behavioral-scenarios)

---

## Executive Summary

### Purpose

Provide a simple, conversational interface that allows non-technical users to:
1. Define and launch market research projects
2. Monitor research progress
3. Understand costs and timelines
4. Package results for stakeholders
5. Manage multiple research runs without technical knowledge

### Design Philosophy

**"Conversation over Configuration"**

- Users describe what they want in plain language
- System asks clarifying questions (progressive disclosure)
- System prevents mistakes through guided flows
- Technical details hidden unless requested
- Results delivered in stakeholder-ready formats

### Key Principles

1. **Natural Language First** - No YAML files, no command-line arguments
2. **Progressive Disclosure** - Show complexity only when needed
3. **Smart Defaults** - System recommends best practices
4. **Visual Feedback** - Clear progress indicators and status
5. **Error Prevention** - Guide users away from mistakes before they happen
6. **Contextual Help** - In-line assistance when and where needed

---

## User Personas

### Persona 1: Marketing Manager (Primary)

**Name**: Sarah
**Role**: VP Marketing
**Technical Skill**: Low (uses email, Google Docs, CRM)
**Goals**:
- Understand how buyers in new verticals make decisions
- Validate current messaging resonates with target personas
- Get insights to inform campaign strategy

**Pain Points**:
- Doesn't understand technical jargon
- Needs results in executive-friendly format
- Limited time to learn new tools
- Budget-conscious, needs cost predictability

**Key Behaviors**:
- Describes research goals conversationally
- Expects system to guide her through setup
- Checks progress occasionally (not real-time monitoring)
- Needs "share with stakeholders" button

### Persona 2: Sales Leader (Secondary)

**Name**: Marcus
**Role**: VP Sales
**Technical Skill**: Medium (uses Salesforce, analytics tools)
**Goals**:
- Understand objections by buyer persona
- Get playbooks for reps to use in field
- Identify competitive positioning gaps

**Pain Points**:
- Needs actionable outputs (not raw research)
- Time-sensitive (needs results quickly)
- Skeptical of "research projects" without clear ROI

**Key Behaviors**:
- Wants to see examples before committing
- Monitors costs vs. value delivered
- Needs tactical deliverables (playbooks, scripts)
- May run multiple research projects concurrently

### Persona 3: Executive Sponsor (Tertiary)

**Name**: David
**Role**: Chief Strategy Officer
**Technical Skill**: Low
**Goals**:
- Understand market trends for strategic planning
- Validate market entry decisions
- Get high-level insights without details

**Pain Points**:
- Extremely limited time
- Needs 1-page summaries
- Delegating research to team but needs visibility

**Key Behaviors**:
- Reviews results only (doesn't manage runs)
- Needs executive summaries
- May ask team to "run this for X vertical"

---

## Core Behaviors

### CB-1: Research Project Setup

**Trigger**: User wants to start new research

**User Experience**:
```
USER INTENT: "I want to understand how CFOs in healthcare buy infrastructure services"

SYSTEM BEHAVIOR:
1. Acknowledge intent: "Great! Let me help you set up healthcare research."
2. Ask clarifying questions (one at a time):
   - "Is this pure discovery or testing your current messaging?"
   - "Which healthcare segments? (Providers, Insurance, Devices...)"
   - "Which buyer personas matter? (CFO, CIO, VP Ops...)"
3. Show configuration summary:
   - What will be researched
   - Estimated cost ($24-26)
   - Estimated time (2-3 days)
   - What deliverables they'll get
4. Ask for confirmation: "Ready to start?"
5. Launch research or save as draft
```

**Key Behaviors**:
- Questions are plain language, not technical
- One question at a time (not overwhelming)
- Provides context for each question (why we're asking)
- Shows cost/time before commitment
- Allows "save draft" to finish later

### CB-2: Research Monitoring

**Trigger**: User checks on running research

**User Experience**:
```
USER INTENT: "How is my healthcare research going?"

SYSTEM BEHAVIOR:
1. Show progress visually:
   ████████░░ 80% Complete

2. Break down by stage:
   ✅ Market Analysis (Complete)
   ✅ Competitor Research (Complete)
   🔄 Healthcare Providers Analysis (In Progress - 6 hours remaining)
   ⏸️ Health Insurance Analysis (Waiting)
   ⏸️ Playbook Generation (Waiting)

3. Show key metrics:
   - Time elapsed: 18 hours
   - Cost so far: $18.50 of $24-26 estimated
   - Expected completion: Tomorrow at 2 PM

4. Offer actions:
   - "View detailed logs" (for curious users)
   - "Pause research" (if needed)
   - "Get notified when complete"
```

**Key Behaviors**:
- Visual progress bars (not just percentages)
- Plain language stage names (not "Layer 2, Agent 3")
- Time and cost transparency
- Proactive notifications (not just on-demand checks)
- Option to dive deeper without forcing it

### CB-3: Results Review & Packaging

**Trigger**: Research completes

**User Experience**:
```
SYSTEM NOTIFICATION: "Your healthcare research is complete! 🎉"

USER CLICKS: "View Results"

SYSTEM BEHAVIOR:
1. Show high-level summary:
   - 6 playbooks created
   - 12 market insights discovered
   - $25.30 total cost
   - Ready to package for stakeholders

2. Ask: "Who will read these results?"
   Options:
   - 📊 Executives (1-page summary)
   - 🎯 Sales/Marketing Team (playbooks & frameworks)
   - 📈 Strategy Team (complete research)
   - ✏️ Custom (I'll choose what to include)

3. USER SELECTS: "Executives"

4. SYSTEM GENERATES:
   - Creates 1-page executive summary
   - Shows preview
   - Offers download options:
     - 📧 Email to recipients
     - 💾 Download PDF
     - 🔗 Share link (view-only)
     - 📁 Save to Google Drive / Dropbox
```

**Key Behaviors**:
- Proactive notification (user doesn't have to check)
- Results preview before downloading
- Stakeholder-appropriate packaging
- Multiple sharing options (not just "download ZIP")
- Preview before sharing

### CB-4: Context Management

**Trigger**: User wants to add company information

**User Experience**:
```
USER INTENT: "I want to include our current messaging in this research"

SYSTEM BEHAVIOR:
1. Explain implications:
   "Adding your current messaging will:
   ✅ Show how it compares to market expectations
   ✅ Identify gaps between your story and buyer needs
   ⚠️ This is a VALIDATION study, not pure discovery

   Cost: Same ($24-26)
   Time: Same (2-3 days)
   Output: Includes gap analysis"

2. Ask: "How would you like to provide your messaging?"
   Options:
   - 📝 Paste content here
   - 📎 Upload file (PDF, Word, Google Doc)
   - 🔗 Link to webpage
   - 💬 Describe it, I'll format it

3. USER UPLOADS: website_copy.pdf

4. SYSTEM CONFIRMS:
   "✅ Messaging added to this research run
   📁 Stored in: healthcare_validation_20250113
   🔒 Isolated from other research runs

   This content will NOT affect your other research projects."
```

**Key Behaviors**:
- Explains consequences of adding context
- Offers multiple input methods (file, paste, link, describe)
- Visual confirmation of isolation
- Clear that this won't contaminate other runs
- Shows where content is stored (transparency)

### CB-5: Multi-Run Management

**Trigger**: User has multiple research projects

**User Experience**:
```
USER VIEW: Dashboard / "My Research Projects"

SYSTEM SHOWS:
┌─────────────────────────────────────────────┐
│ 🔄 Running (1)                              │
├─────────────────────────────────────────────┤
│ Healthcare Discovery                         │
│ ████████░░ 80% • $18.50 • ~6 hours left     │
│ [Pause] [Monitor] [Details]                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ ⏸️  Waiting for Review (1)                   │
├─────────────────────────────────────────────┤
│ Financial Services Validation                │
│ Ready for your approval to continue          │
│ [Review Outputs] [Approve] [Reject]         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ ✅ Completed (2)                             │
├─────────────────────────────────────────────┤
│ Manufacturing Competitive • Jan 10           │
│ 6 playbooks • $26.10                         │
│ [View Results] [Package] [Share]            │
│                                              │
│ Healthcare Messaging Test • Jan 8            │
│ 4 playbooks • $22.50                         │
│ [View Results] [Package] [Share]            │
└─────────────────────────────────────────────┘

[+ Start New Research]
```

**Key Behaviors**:
- Visual grouping by status (running, waiting, completed)
- Quick actions on each card (no drilling down for common tasks)
- Cost and time visible at a glance
- Clear calls-to-action for each state
- "Start New Research" prominent but not overwhelming

---

## User Journeys

### Journey 1: First-Time Discovery Research

**Scenario**: Sarah (Marketing Manager) wants to understand healthcare market for first time

**Steps**:

1. **Landing** (T+0:00)
   - Sarah opens interface
   - Sees: "Welcome! What would you like to research?"
   - Clicks: [Start New Research]

2. **Intent Capture** (T+0:30)
   - System asks: "What market question are you trying to answer?"
   - Sarah types: "How do healthcare CFOs buy infrastructure services?"
   - System confirms: "Got it! Healthcare market, CFO persona, buying behavior"

3. **Research Type** (T+1:00)
   - System asks: "Is this pure discovery or testing existing messaging?"
   - Shows visual explanation:
     - **Discovery**: Unbiased market truth (recommended for first time)
     - **Validation**: Compare market to your current approach
   - Sarah selects: Discovery

4. **Target Definition** (T+2:00)
   - System: "Which healthcare segments?"
   - Shows options with explanations:
     - Healthcare Providers (hospitals, clinics)
     - Health Insurance (payers, managed care)
     - Medical Devices (manufacturers, distributors)
   - Sarah selects: Providers, Insurance

5. **Persona Selection** (T+2:30)
   - System: "Which buyer personas?"
   - Options: CFO, CIO, VP Operations, Procurement
   - Sarah selects: CFO, CIO

6. **Configuration Review** (T+3:00)
   - System shows summary:
     ```
     Research Configuration
     ----------------------
     Type: Pure Discovery (unbiased market research)
     Verticals: Healthcare Providers, Health Insurance
     Personas: CFO, CIO
     Deliverables: 4 playbooks (2 verticals × 2 personas)

     Timeline: 2-3 days
     Cost: $20-22

     You'll get:
     - How CFOs and CIOs research solutions
     - What triggers buying decisions
     - Competitive landscape analysis
     - Decision-making process insights
     ```
   - Buttons: [Looks Good - Start Research] [Save as Draft] [Change Settings]

7. **Launch Confirmation** (T+3:30)
   - Sarah clicks: [Looks Good - Start Research]
   - System: "✅ Research started! I'll notify you when complete."
   - Shows: Progress card, monitoring link, estimated completion time

8. **Passive Monitoring** (T+6 hours)
   - Sarah receives email: "Healthcare research 25% complete"
   - Optionally clicks link to see detailed progress

9. **Completion Notification** (T+48 hours)
   - Email: "🎉 Healthcare research complete!"
   - Sarah clicks: [View Results]

10. **Results Review** (T+48:05)
    - System shows preview:
      - 4 playbooks generated
      - 8 key insights discovered
      - $21.80 final cost
    - System asks: "Package for stakeholders?"
    - Sarah selects: [Executive Package]

11. **Delivery** (T+48:10)
    - System generates 1-page summary + playbooks
    - Sarah downloads PDF
    - Emails to CEO with one click
    - **Journey Complete** ✅

**Duration**: ~3 minutes setup, 2-3 days execution, 5 minutes packaging
**Touchpoints**: 4 (setup, progress notification, completion, packaging)
**User Effort**: Low (answers questions, reviews results)
**Technical Knowledge Required**: None

### Journey 2: Validation Study (Experienced User)

**Scenario**: Marcus (Sales Leader) wants to test current messaging against market reality

**Steps**:

1. **Returning User** (T+0:00)
   - Marcus opens interface
   - Sees dashboard with previous research
   - Clicks: [Start New Research]

2. **Intent Capture** (T+0:15)
   - System: "What would you like to research?"
   - Marcus types: "Test our financial services messaging"
   - System detects "test" keyword → suggests Validation type

3. **Research Type Pre-Selected** (T+0:30)
   - System: "I detected you want to validate messaging. Correct?"
   - Shows:
     ```
     Validation Study
     ----------------
     ✅ Research market reality
     ✅ Compare to your current approach
     ✅ Identify gaps and opportunities

     You'll need to provide: Current messaging materials
     ```
   - Marcus confirms: [Yes, Validation Study]

4. **Quick Configuration** (T+1:00)
   - System: "Which vertical and personas?" (single screen, not multiple steps)
   - Marcus selects: Financial Services, CFO + CIO
   - System: "Same config as your last study - want to reuse settings?"
   - Marcus: [Yes, Reuse Settings]

5. **Context Upload** (T+1:30)
   - System: "Upload your current messaging materials"
   - Marcus drags: website_copy.pdf, sales_deck.pptx
   - System: "✅ Files uploaded. I'll extract key messages automatically."
   - Shows preview of extracted content
   - Marcus confirms: [Looks Good]

6. **Fast Launch** (T+2:00)
   - System shows summary (shorter, since Marcus is experienced)
   - Timeline: 2-3 days, Cost: $24-26
   - Marcus: [Start Research]

7. **Active Monitoring** (T+12 hours)
   - Marcus checks dashboard
   - Sees progress, drills into detailed logs (he's curious)
   - Notes: "Market analysis found 3 gaps" (preview)

8. **Completion** (T+52 hours)
   - Email notification
   - Marcus clicks: [View Gap Analysis]

9. **Gap Review** (T+52:05)
   - System highlights:
     ```
     Market vs. Your Messaging
     -------------------------
     ✅ Value proposition aligns well
     ⚠️ Gap: Market prioritizes compliance, you emphasize speed
     ⚠️ Gap: CFOs want ROI calculator, you don't mention
     ❌ Mismatch: You say "best-in-class", market sees as generic

     Recommendations:
     1. Add compliance messaging (high priority)
     2. Create ROI calculator tool
     3. Replace "best-in-class" with specific differentiators
     ```
   - Marcus: [Package for Sales Team]

10. **Tactical Delivery** (T+52:10)
    - System generates:
      - Updated messaging framework
      - Playbooks with gap-closing strategies
      - Competitive positioning guide
    - Marcus: [Share with Team] → Sends Slack link

**Duration**: 2 minutes setup, 2-3 days execution, 5 minutes review
**Efficiency Gains**: 33% faster setup (reused settings, smart defaults)
**Value**: Actionable gap analysis, not just research

### Journey 3: Quick Status Check (Mobile)

**Scenario**: Sarah checks research progress on phone while in meeting

**Steps**:

1. **Mobile Open** (T+0:00)
   - Sarah opens mobile app/web
   - Sees condensed dashboard

2. **Status Card** (T+0:02)
   - Taps: Running research card
   - Full-screen progress view:
     ```
     Healthcare Discovery

     ████████░░ 75%

     6 hours remaining
     $17.20 / $20-22

     Current: Analyzing Health Insurance segment

     [View Details] [Get Notification]
     ```

3. **Quick Action** (T+0:05)
   - Sarah taps: [Get Notification]
   - System: "I'll text you when complete"
   - Sarah closes app
   - **Journey Complete** ✅

**Duration**: 5 seconds
**Platform**: Mobile-optimized
**Key Feature**: Quick glance, minimal interaction

### Journey 4: Error Recovery

**Scenario**: Research fails mid-execution, system guides recovery

**Steps**:

1. **Failure Notification** (T+12 hours into run)
   - Email: "⚠️ Healthcare research encountered an issue"
   - Sarah clicks: [View Details]

2. **Error Explanation** (T+0:30)
   - System shows:
     ```
     What Happened
     -------------
     Research paused at Healthcare Providers analysis

     Reason: Budget limit reached ($25 of $22 estimated)

     Why: Healthcare segment required more searches than typical

     Your Options
     ------------
     1. ✅ Increase budget to $30 and resume (recommended)
        Cost: $5 more, Complete in 8 hours

     2. Skip Healthcare Providers segment
        Cost: No additional charge, Complete in 2 hours
        Note: You'll only get Health Insurance playbooks

     3. Cancel and refund
        Refund: $12 (you keep partial results)
     ```

3. **Recovery Selection** (T+1:00)
   - Sarah selects: [Increase Budget & Resume]
   - System: "✅ Research resumed! I'll be more careful with budget."
   - Shows updated progress

4. **Completion** (T+20 hours total)
   - Research completes successfully
   - Final cost: $28.50 (within new budget)
   - **Recovery Complete** ✅

**Key Behaviors**:
- Clear explanation (not technical error codes)
- Options with implications (cost, time, deliverables)
- Recommendation from system
- One-click recovery (no complex troubleshooting)

---

## Interface States

### State 1: Empty State (First Use)

**When**: User has no research projects yet

**Display**:
```
┌─────────────────────────────────────────────┐
│                                              │
│         Welcome to Research Manager          │
│                                              │
│     Discover how your buyers make            │
│     decisions with AI-powered research       │
│                                              │
│     [Start Your First Research Project]      │
│                                              │
│     Or: [Watch Demo] [See Example Results]   │
│                                              │
└─────────────────────────────────────────────┘

Quick Tips:
• Research takes 2-3 days, costs $20-30
• Get playbooks for each vertical × persona
• No technical knowledge required
```

**Goals**:
- Welcoming, not intimidating
- Clear value proposition
- Low-friction start
- Education options for cautious users

### State 2: Setup In Progress

**When**: User is answering configuration questions

**Display**:
```
┌─────────────────────────────────────────────┐
│ New Research Project                         │
│                                              │
│ Step 2 of 4: Select Verticals                │
│ ████████░░░░░░░░ 50%                         │
│                                              │
│ Which industries do you want to research?    │
│                                              │
│ [ ] Healthcare Providers                     │
│ [ ] Health Insurance                         │
│ [ ] Medical Devices                          │
│ [ ] Financial Services                       │
│ [ ] Manufacturing                            │
│ [+] Add Custom Industry...                   │
│                                              │
│ [← Back] [Continue →]                        │
│                                              │
│ [Save Draft] [Cancel]                        │
└─────────────────────────────────────────────┘

💡 Tip: Select 2-3 verticals for best results
```

**Key Elements**:
- Progress indicator (know where you are)
- Back navigation (fix mistakes)
- Save draft (pause and resume)
- Contextual tips
- Clear next action

### State 3: Research Running

**When**: Research is executing

**Display**:
```
┌─────────────────────────────────────────────┐
│ Healthcare Discovery                         │
│ Started: Jan 13, 2:30 PM                     │
│                                              │
│ Overall Progress                             │
│ ████████████░░░░ 75%                         │
│ 6 hours remaining • $17.20 spent             │
│                                              │
│ Current Stage                                │
│ 🔄 Analyzing Health Insurance segment        │
│                                              │
│ Completed                                    │
│ ✅ Market Analysis                           │
│ ✅ Competitive Research                      │
│ ✅ Healthcare Providers Analysis             │
│                                              │
│ Up Next                                      │
│ ⏸️ Playbook Generation                       │
│                                              │
│ [Pause Research] [View Logs] [Change Budget] │
│                                              │
│ 🔔 [Notify me when complete]                 │
└─────────────────────────────────────────────┘
```

**Key Elements**:
- Visual progress (not just percentage)
- Stage names in plain language
- What's happening now (gives sense of progress)
- Cost tracking (transparency)
- Action buttons appropriate to state
- Notification option (passive monitoring)

### State 4: Review Required

**When**: Human review gate reached

**Display**:
```
┌─────────────────────────────────────────────┐
│ Healthcare Discovery                         │
│ ⏸️ Waiting for Your Review                   │
│                                              │
│ Market Analysis Complete                     │
│ Before continuing to vertical research,      │
│ please review these findings:                │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ 📊 Key Findings Preview                 │ │
│ │                                         │ │
│ │ • CFOs prioritize compliance over cost  │ │
│ │ • 73% research solutions online first   │ │
│ │ • Average buying cycle: 4-6 months      │ │
│ │ • Top trigger: Technology refresh       │ │
│ │                                         │ │
│ │ [View Full Report]                      │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ These findings will guide the next stage.    │
│ If you see issues, you can stop here.        │
│                                              │
│ [✅ Looks Good - Continue] [⏸️ Pause & Review] [❌ Stop Here] │
│                                              │
│ Cost so far: $8.20                           │
│ If you continue: $14 more (total ~$22)       │
└─────────────────────────────────────────────┘
```

**Key Elements**:
- Clear why review is needed
- Preview of findings (not full dump)
- Option to view more details
- Explicit cost implications
- Three clear choices (approve, pause, stop)
- No pressure (user controls pace)

### State 5: Completed

**When**: Research finished successfully

**Display**:
```
┌─────────────────────────────────────────────┐
│ Healthcare Discovery                         │
│ ✅ Completed Jan 15, 4:30 PM                 │
│                                              │
│ Research Summary                             │
│ • Duration: 2 days, 2 hours                  │
│ • Final Cost: $21.80                         │
│ • Deliverables: 4 playbooks, 12 insights     │
│                                              │
│ Key Insights                                 │
│ 🔑 CFOs prioritize compliance, not cost      │
│ 🔑 Online research happens 3-6 months early  │
│ 🔑 CIOs control technical eval, CFOs approve │
│                                              │
│ [📦 Package for Stakeholders]                │
│ [📊 View All Results]                        │
│ [🔄 Run Similar Research]                    │
│                                              │
│ Share Results                                │
│ [📧 Email] [🔗 Link] [💾 Download PDF]       │
└─────────────────────────────────────────────┘
```

**Key Elements**:
- Success confirmation
- Summary stats (time, cost, deliverables)
- Preview of key insights (teaser)
- Primary actions prominent (package, view, share)
- Easy to run similar research (learning from success)

### State 6: Failed/Error

**When**: Research encountered unrecoverable error

**Display**:
```
┌─────────────────────────────────────────────┐
│ Healthcare Discovery                         │
│ ❌ Stopped Due to Error                      │
│                                              │
│ What Happened                                │
│ The research stopped at Health Insurance     │
│ analysis due to an API connection issue.     │
│                                              │
│ What You Have                                │
│ • Partial results (Market Analysis complete) │
│ • Cost: $8.20 (saved, not charged)           │
│                                              │
│ What You Can Do                              │
│                                              │
│ 1. [🔄 Resume from Checkpoint]               │
│    Continue where it left off                │
│    Time: ~18 hours remaining                 │
│    Cost: ~$14 more                           │
│                                              │
│ 2. [📦 Keep Partial Results]                 │
│    Download what completed successfully      │
│    No additional charge                      │
│                                              │
│ 3. [❌ Cancel & Start Fresh]                 │
│    Delete this run, try again                │
│    No charge                                 │
│                                              │
│ Need Help? [Contact Support]                 │
└─────────────────────────────────────────────┘
```

**Key Elements**:
- Plain language explanation (no error codes)
- What user has (partial value)
- Clear recovery options
- Cost implications for each option
- Support escape hatch

---

## Interaction Patterns

### Pattern 1: Progressive Disclosure

**Principle**: Show complexity only when user needs it

**Examples**:

**Level 1: Simple View (Default)**
```
Healthcare Discovery
████████░░ 75% • 6 hours left • $17.20
[View Details]
```

**Level 2: Expanded View (User Clicks "View Details")**
```
Healthcare Discovery
────────────────────
Overall Progress: 75%
Time: 6 hours remaining
Cost: $17.20 / $20-22 estimated

Stages:
✅ Market Analysis (Complete)
✅ Competitive Research (Complete)
✅ Healthcare Providers (Complete)
🔄 Health Insurance (In Progress)
⏸️ Playbook Generation (Not Started)

[View Technical Logs] [Change Settings]
```

**Level 3: Technical View (Advanced User)**
```
Healthcare Discovery
────────────────────
Execution ID: healthcare_research_2025
Checkpoint: ../src/checkpoints/healthcare_research_2025.json

Layer 1: Complete (5/5 agents)
  ✅ buyer_journey (3.2h, $4.50)
  ✅ channels_competitive (2.8h, $3.80)
  ✅ customer_expansion (2.1h, $2.90)
  ✅ messaging_positioning (1.9h, $2.10)
  ✅ gtm_synthesis (2.5h, $3.90)

Layer 2: In Progress (1/2 verticals)
  ✅ Healthcare Providers (4.2h, $5.80)
  🔄 Health Insurance (2.1h so far, $3.20)

[View Raw Logs] [Download Checkpoint] [Modify Config]
```

**Implementation**:
- Default view: Minimal, scannable
- One click → More context
- Two clicks → Full technical details
- User controls depth

### Pattern 2: Smart Defaults with Override

**Principle**: Recommend best practice, allow customization

**Example: Model Selection**

**Default Presentation**:
```
Research Configuration
----------------------
Model Strategy: Cost-Optimized (Recommended)
  • Uses Claude Haiku for research ($1-2 per agent)
  • Uses Claude Sonnet for synthesis ($4-6 per agent)
  • Estimated cost: $20-22

[Use Recommended Settings]
[Customize Model Selection] ← Advanced
```

**If User Clicks "Customize"**:
```
Model Selection
───────────────
Research Agents (Layers 1-3):
  • Claude Haiku (Fast, Economical) [Selected ✓]
  • Claude Sonnet (Higher Quality, 5x cost) [ ]

Synthesis Agents:
  • Claude Sonnet (Recommended) [Selected ✓]
  • Claude Opus (Best Quality, 3x cost) [ ]

Estimated Cost Impact:
Current: $20-22
If all Sonnet: $150-180
If all Opus: $450-500

💡 Tip: Haiku for research, Sonnet for synthesis gives
   best value. Only use Opus for critical decisions.

[Save Custom Settings] [Reset to Recommended]
```

**Key Behaviors**:
- Default is always visible and one-click
- Advanced options behind progressive disclosure
- Show cost impact of changes immediately
- Provide recommendation even in advanced mode
- Easy to reset if user goes too deep

### Pattern 3: Contextual Help

**Principle**: Provide help when and where needed, not in separate docs

**Example: Research Type Selection**

```
What type of research?

┌─────────────────────────────────────┐
│ ( ) Pure Discovery                  │
│     Unbiased market research        │
│     [?] When to use this            │ ← Click for help
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ( ) Validation                      │
│     Test your current messaging     │
│     [?] When to use this            │
└─────────────────────────────────────┘
```

**If User Clicks [?] on "Pure Discovery"**:
```
Pure Discovery
──────────────
✅ Use when:
   • Entering new market/vertical
   • Want unbiased buyer insights
   • Don't have existing messaging to test
   • First time researching this space

❌ Don't use when:
   • You have messaging to validate
   • Want to compare to competitors
   • Need gap analysis

📊 What you get:
   • How buyers actually research solutions
   • What triggers buying decisions
   • Decision-making process insights
   • Competitive landscape (objective)

💰 Cost: $20-30 (same as validation)
⏱️ Time: 2-3 days

[Close] [Use Pure Discovery]
```

**Key Behaviors**:
- Help icon next to every unfamiliar term
- Inline expansion (no navigation away)
- Specific to context (not generic help)
- Action button in help (can select from help popup)
- Examples and anti-examples (when to use, when not to)

### Pattern 4: Undo/Recovery

**Principle**: Users can always go back, nothing is permanent until confirmed

**Example: Research Setup**

```
Step 4 of 4: Review Configuration
──────────────────────────────────

Research Type: Pure Discovery          [Change]
Verticals: Healthcare Providers,       [Change]
           Health Insurance
Personas: CFO, CIO                     [Change]
Cost: $20-22                           [Change Budget]
Time: 2-3 days

Deliverables:
• 4 playbooks (2 verticals × 2 personas)
• Competitive landscape analysis
• Buyer journey maps

[← Back] [Start Research]
[Save as Draft] [Cancel]
```

**Key Behaviors**:
- Every previous choice can be edited
- [Change] links go back to that specific step
- "Back" button for sequential editing
- "Save as Draft" for pausing
- Nothing committed until "Start Research"
- Even after starting, can pause/modify budget

**After Start**:
```
Research Started
────────────────
✅ Healthcare Discovery is running

Wait! Made a mistake?

[⏸️ Pause & Modify] ← Available for 5 minutes
[Continue]

After 5 minutes, you can still:
• Pause research
• Change budget limits
• Stop and resume later
```

### Pattern 5: Batch Actions

**Principle**: Allow operating on multiple items when appropriate

**Example: Dashboard with Multiple Completed Runs**

```
Completed Research (3)

[ ] Healthcare Discovery      Jan 15  $21.80  [Package] [Share]
[ ] Financial Validation      Jan 12  $26.10  [Package] [Share]
[ ] Manufacturing Competitive Jan 10  $24.50  [Package] [Share]

[Select All]

With Selected (0):
[📦 Package All] [📧 Email All] [🗑️ Archive]
```

**When User Selects 2 Items**:
```
With Selected (2):
[📦 Package All] → Creates single ZIP with both
[📧 Email All] → Single email with both reports
[🗑️ Archive] → Moves both to archive
[📊 Compare Results] ← New option when 2+ selected
```

**Key Behaviors**:
- Checkboxes for multi-select
- Actions disabled until selection
- Actions adapt based on selection count
- New options appear when relevant (compare for 2+)
- Clear selection count

---

## Error Handling & Recovery

### Error Pattern 1: Prevention Over Cure

**Principle**: Stop errors before they happen

**Example: Budget Limit**

**During Setup**:
```
Set Budget Limit
────────────────
Maximum cost for this research:

$ [30] ← User typing

⚠️ Warning: Estimated cost is $20-22.
   Setting limit to $30 is good practice.

Setting limit too low ($15 or less) may cause:
• Research stopping mid-execution
• Incomplete deliverables
• Wasted time and money

Recommendation: $25-30 (gives 20% buffer)

[Use Recommended: $27] [Keep My Limit: $30]
```

**Key Behaviors**:
- Real-time validation as user types
- Explain consequences before they commit
- Provide specific recommendation
- Allow override but with warning
- Clear what "too low" means

### Error Pattern 2: Graceful Degradation

**Principle**: Partial success is better than total failure

**Example: One Vertical Fails**

**What Happens**:
```
Research Update
───────────────
⚠️ Issue with Health Insurance segment

Healthcare Providers research completed successfully ✅

Health Insurance research failed due to:
"Insufficient data available for this segment"

Your Options:
────────────

1. ✅ Continue with Healthcare Providers only
   • Get 2 playbooks (Providers × CFO/CIO)
   • Cost: $12 (50% of estimate)
   • Time: Already complete
   • Refund: $10

2. 🔄 Retry Health Insurance with different approach
   • Cost: $5 more
   • Time: 12 hours
   • May or may not succeed

3. ❌ Cancel entire research
   • Refund: Full $22
   • Lose Healthcare Providers results

Recommendation: Take Healthcare Providers results (#1).
They're valuable even without Health Insurance.

[Accept Recommendation] [Choose Option 2] [Choose Option 3]
```

**Key Behaviors**:
- Don't throw away partial success
- Explain what succeeded vs. failed
- Show value of partial results
- Provide recommendation
- Fair refund for what didn't complete

### Error Pattern 3: Self-Healing

**Principle**: Fix problems automatically when possible, notify user

**Example: API Rate Limit**

**Background Behavior**:
```
[System detects rate limit error]
[System waits 60 seconds]
[System retries]
[Success]
```

**User Notification (Optional)**:
```
🔔 Minor Issue Resolved

Healthcare Discovery research briefly paused due to
API rate limit, but automatically resumed.

No action needed. Research continues normally.

Time impact: +2 minutes
Cost impact: None

[Dismiss] [View Details]
```

**Key Behaviors**:
- System handles routine errors automatically
- User notified for transparency
- No action required from user
- Clear impact statement (time, cost)
- Option to see details for curious users

### Error Pattern 4: Expert Escalation

**Principle**: Know when to ask for help

**Example: Unrecoverable Error**

```
Research Stopped
────────────────
❌ Healthcare Discovery encountered an error we
   couldn't automatically resolve.

Error Type: Configuration Issue
What Happened: Invalid vertical configuration detected

This is unusual and may require technical support.

What We've Done:
✅ Saved your progress (no data lost)
✅ Preserved checkpoint (can resume)
✅ Created error report

What You Can Do:

1. [📧 Contact Support] (Recommended)
   We'll fix the issue and resume for you.
   Typical response: 2-4 hours

2. [📋 Copy Error Report]
   Share with your technical team

3. [🔄 Start Fresh]
   Try a new research project

Support will receive:
• Error details (not sensitive data)
• Your research configuration
• Checkpoint to resume from

Support will NOT receive:
• Your company context/files
• Research outputs
• Personal information

[Contact Support] [I'll Handle It Myself]
```

**Key Behaviors**:
- Admit when system can't self-heal
- Explain what happened in plain language
- Show what system has done to protect user
- Recommend expert help
- Transparency about what support receives
- Privacy assurance
- Still offer DIY option

---

## Success Criteria

### User Success Metrics

**Metric 1: Time to First Research**
- **Target**: < 5 minutes from landing to launch
- **Measurement**: Time from "Start New Research" to "Research Started"
- **Success**: 80% of users complete in < 5 minutes

**Metric 2: Completion Rate**
- **Target**: > 90% of started research completes successfully
- **Measurement**: (Completed runs) / (Started runs)
- **Success**: < 10% failure rate

**Metric 3: User Confidence**
- **Target**: Users understand what they're getting before committing
- **Measurement**: Post-setup survey: "I know what results I'll get" (1-5 scale)
- **Success**: Average score > 4.0

**Metric 4: Results Utilization**
- **Target**: Users actually use the research outputs
- **Measurement**: % of completed research that gets packaged/shared
- **Success**: > 75% of completed research gets packaged

**Metric 5: Error Recovery**
- **Target**: Users can recover from errors without support
- **Measurement**: % of errors resolved without support ticket
- **Success**: > 70% self-service recovery

### System Success Metrics

**Metric 6: Cost Predictability**
- **Target**: Actual cost within 20% of estimate
- **Measurement**: |Actual - Estimate| / Estimate
- **Success**: < 20% variance for 90% of runs

**Metric 7: Time Predictability**
- **Target**: Completion time within 25% of estimate
- **Measurement**: |Actual - Estimate| / Estimate
- **Success**: < 25% variance for 85% of runs

**Metric 8: Notification Timeliness**
- **Target**: Users notified of status changes within 5 minutes
- **Measurement**: Time from status change to notification
- **Success**: 95% of notifications within 5 minutes

### Behavioral Success Indicators

**Indicator 1: Question Answering Rate**
- **Good**: Users answer all setup questions (no abandonment)
- **Measurement**: % of users completing all setup steps
- **Target**: > 85%

**Indicator 2: Default Acceptance Rate**
- **Good**: Users trust recommended settings
- **Measurement**: % of users using recommended vs. custom settings
- **Target**: > 70% use defaults (indicates good recommendations)

**Indicator 3: Help Usage**
- **Good**: Users find contextual help helpful
- **Measurement**: % of help clicks that lead to action (vs. confusion)
- **Target**: > 60% of help interactions lead to positive action

**Indicator 4: Repeat Usage**
- **Good**: Users come back for more research
- **Measurement**: % of users who run 2+ research projects
- **Target**: > 50% become repeat users within 30 days

**Indicator 5: Results Sharing**
- **Good**: Users share results with stakeholders
- **Measurement**: % of completed research that gets shared (email/link/download)
- **Target**: > 70%

---

## Appendix: Behavioral Scenarios

### Scenario A: Mobile-First User

**User**: Sarah using mobile device exclusively

**Behaviors**:
1. All critical actions available on mobile
2. Progress check takes < 5 seconds (no drilling)
3. Notifications delivered to mobile (push, SMS options)
4. Results preview optimized for small screen
5. Sharing options include mobile-native (AirDrop, etc.)

**Key Screens**:
- Dashboard: Card-based, thumb-friendly
- Setup: One question per screen
- Monitoring: Full-screen progress, swipe for details
- Results: Tap to expand, share sheet integration

### Scenario B: Delegation User

**User**: David (Executive) delegates research to Sarah, wants visibility

**Behaviors**:
1. Sarah sets up research, adds David as "Viewer"
2. David receives notifications (low-frequency, high-level)
3. David can view progress but not modify
4. David receives executive package automatically when complete
5. David can comment/approve without technical knowledge

**Permissions Model**:
- **Owner** (Sarah): Full control
- **Viewer** (David): Read-only, notifications
- **Collaborator**: Can modify settings, not delete
- **Recipient**: Gets results only, no process visibility

### Scenario C: Batch Research Manager

**User**: Marcus runs 5 research projects simultaneously

**Behaviors**:
1. Dashboard shows all 5 with status at a glance
2. Can filter by status (running, waiting, complete)
3. Can compare results across projects
4. Can clone successful configurations
5. Budget tracking across all projects

**Dashboard View**:
```
My Research Projects (5)

🔄 Running (2):
  Healthcare Discovery     ████░░ 60%  $15/$25
  Manufacturing Comp       ██░░░░ 30%  $8/$28

⏸️ Review Required (1):
  Financial Validation     Needs Review

✅ Completed (2):
  Healthcare Test          $22.10  [Package]
  Tech Services Discovery  $19.80  [Package]

Total Budget: $95 / $150 allocated
```

### Scenario D: First-Time User with Skepticism

**User**: Marcus trying system for first time, skeptical

**Behaviors**:
1. Lands on page, sees "Watch Demo" prominently
2. Watches 2-minute video showing end-to-end flow
3. Sees example results before committing
4. Starts with smallest possible project (1 vertical, 1 persona)
5. System shows "Quick Start" option for trial

**Trust Building**:
- Demo video (see it work)
- Example results (see quality)
- Cost calculator (see transparency)
- Small trial option (low commitment)
- Testimonials/case studies (social proof)

### Scenario E: Power User Wanting Control

**User**: Technical marketer wants to customize everything

**Behaviors**:
1. System detects engagement with advanced options
2. Offers "Advanced Mode" toggle
3. Advanced mode shows technical details by default
4. Can edit YAML configs directly (optional)
5. Can access API for automation

**Progressive Complexity**:
- **Level 1**: Conversational (default for all users)
- **Level 2**: Advanced options revealed (click to expand)
- **Level 3**: Configuration files (optional direct edit)
- **Level 4**: API access (for automation)

**UI Adaptation**:
```
Settings
────────
[ ] Simple Mode (Recommended for most users)
[✓] Advanced Mode (Show technical details)
[ ] Expert Mode (Direct config editing)

Current: Advanced Mode

You'll see:
✅ Model selection options
✅ Budget controls
✅ Layer-by-layer progress
✅ Log file access
✅ Checkpoint management

[Save Preference]
```

### Scenario F: Results-Only User

**User**: Executive who only wants to see final results

**Behaviors**:
1. Someone else (Sarah) runs research
2. Executive added as "Results Recipient"
3. Receives email when complete: "Results ready"
4. Clicks link → Auto-packaged executive summary
5. One-page view, downloadable PDF
6. Can drill into details if curious (but not required)

**Email Template**:
```
Subject: Healthcare Research Results Ready

Hi David,

The healthcare market research you requested is complete.

Key Findings:
• CFOs prioritize compliance over cost (73% vs 27%)
• Average buying cycle: 4-6 months
• Online research starts 3-6 months before purchase

View Full Results → [link to one-pager]

Download PDF → [direct download link]

Cost: $21.80 | Duration: 2 days
Research by: Sarah Martinez
```

**One-Pager Structure**:
```
┌─────────────────────────────────────────────┐
│ Healthcare Market Research                   │
│ Executive Summary                            │
│                                              │
│ Objective: Understand CFO buying behavior    │
│                                              │
│ Top 3 Insights                               │
│ 1. Compliance trumps cost (73% prioritize)  │
│ 2. Buying cycle averages 4-6 months         │
│ 3. Online research 3-6 months pre-purchase  │
│                                              │
│ Recommended Actions                          │
│ 1. Lead with compliance messaging            │
│ 2. Nurture campaigns for 6-month cycle      │
│ 3. Invest in SEO/content marketing          │
│                                              │
│ Investment: $21.80 | Duration: 2 days        │
│                                              │
│ [Download Full Report] [See Playbooks]       │
└─────────────────────────────────────────────┘
```

---

## Implementation Notes

### Phase 1: MVP (Minimum Viable Product)

**Must Have**:
1. Conversational setup (research-new flow)
2. Progress monitoring (visual status)
3. Basic packaging (executive + tactical)
4. Email notifications (start, complete, error)
5. Web interface (responsive, mobile-friendly)

**Can Defer**:
- Advanced customization options
- Batch operations
- Comparison tools
- API access
- Collaboration features (multi-user)

### Phase 2: Enhancement

**Add**:
1. Mobile app (native iOS/Android)
2. Advanced options (model selection, budget controls)
3. Collaboration (share runs, viewer roles)
4. Batch operations (multi-select, compare)
5. Integration (Slack, email, calendar)

### Phase 3: Scale

**Add**:
1. API for automation
2. Template library (save configurations)
3. Organization management (teams, budgets)
4. Analytics (ROI tracking, usage patterns)
5. AI recommendations (suggest research based on history)

### Technology Considerations

**Frontend Options**:
- **Web**: React/Next.js (responsive, mobile-friendly)
- **Mobile**: React Native (iOS + Android from single codebase)
- **Desktop**: Electron (optional, if offline needed)

**Backend**:
- Already exists (research-orchestrator)
- Need: REST API or GraphQL wrapper
- WebSocket for real-time progress updates

**Notifications**:
- Email (SendGrid, AWS SES)
- SMS (Twilio)
- Push (Firebase Cloud Messaging)
- Webhook (for integrations)

### Accessibility Requirements

**WCAG 2.1 AA Compliance**:
- Keyboard navigation (no mouse required)
- Screen reader support (ARIA labels)
- Color contrast (4.5:1 minimum)
- Resizable text (up to 200%)
- Focus indicators (visible tab order)

**Inclusive Design**:
- Plain language (no jargon)
- Progressive disclosure (not overwhelming)
- Error messages in plain language
- Multiple input methods (type, upload, paste, link)
- Support for assistive technology

---

## Glossary for Non-Technical Users

**Terms to Avoid** (Use Plain Language Instead):

| Technical Term | Plain Language |
|----------------|----------------|
| "Layer 1 execution" | "Market analysis stage" |
| "Agent completion" | "Research step finished" |
| "Checkpoint state" | "Saved progress" |
| "Execution ID" | "Research tracking number" |
| "YAML config" | "Research settings" |
| "API error" | "Connection issue" |
| "Token usage" | "Processing time" |
| "Model selection" | "Quality level" |

**Acceptable Terms** (With Contextual Explanation):

- **Research Run**: A specific research project (e.g., "Healthcare Discovery")
- **Playbook**: Step-by-step guide for selling to specific buyer (e.g., "CFO Playbook")
- **Vertical**: Industry or market segment (e.g., "Healthcare")
- **Persona**: Buyer role or title (e.g., "CFO", "CIO")
- **Discovery**: Unbiased market research (no existing assumptions)
- **Validation**: Testing your current approach against market reality
- **Gap Analysis**: Comparing what market wants vs. what you offer

---

**End of Behavioral Specification**

This specification should be reviewed with:
1. UX designers (for mockups)
2. Product managers (for prioritization)
3. Non-technical test users (for validation)
4. Developers (for feasibility)

Next Steps:
1. Create wireframes from key scenarios
2. Prototype conversational flow (research-new)
3. User testing with target personas
4. Technical architecture design
5. MVP development
