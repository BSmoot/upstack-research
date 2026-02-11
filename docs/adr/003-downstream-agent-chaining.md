# ADR-003: Downstream Agent Chaining Architecture

**Status**: Proposed
**Date**: 2026-02-08
**Authors**: apex-architect

---

## Context

The Upstack research system produces structured markdown outputs through a multi-layer pipeline:

```
Layer 0 (Service Categories) -> Layer 1 (Horizontal GTM) -> Layer 2 (Vertical)
-> Layer 3 (Title/Persona) -> Playbooks (2D/3D) -> Validation -> Brand Alignment
```

Currently, all outputs are terminal -- markdown files consumed by humans. But these outputs contain structured intelligence (messaging frameworks, competitive positioning, buyer journey maps, persona pain points) that downstream AI agents could consume to produce derivative content: case studies, email sequences, landing pages, knowledge bases, and more.

The system needs a contract-driven architecture that lets downstream agents declare what research outputs they need, receive only those outputs, and produce their own derivative outputs. This must work for Python agents running in the same process, external processes in other languages, and remote services (webhooks, MCP servers).

### Business Drivers

1. **Content velocity**: Manual content creation from playbooks is slow. Downstream agents can generate first drafts of case studies, email sequences, and landing pages from structured research in minutes.
2. **Knowledge accessibility**: Research outputs are large markdown files. A knowledge agent with progressive reveal can surface the right insight at the right time for sales teams.
3. **Composability**: Different teams need different derivative outputs. A declarative agent contract lets teams define new downstream agents without modifying the orchestrator.
4. **Reproducibility**: Versioned manifests and knowledge bases let teams trace any piece of content back to the specific research run that produced it.

### Existing Patterns (Honored)

This design follows the patterns established in the orchestrator for validation and brand alignment:

- **Post-processing stage pattern**: `execute_validation()` and `execute_brand_alignment()` in `orchestrator.py` iterate over completed playbooks, initialize tracking state, execute agents in parallel, and use the same `mark_in_progress` / `mark_complete` / `mark_failed` lifecycle.
- **State tracking**: `StateTracker` uses flat dictionaries keyed by layer name (`validation`, `brand_alignment`) with `initialize_*()`, `is_agent_complete()`, and `get_agent_output()` methods.
- **Checkpoint/resume**: Atomic JSON writes via temp file + rename. Backward-compatible key addition.
- **Config schema**: Pydantic models in `config_schema.py` with `Field(default_factory=...)` for optional sections.
- **Output directory structure**: `outputs/{execution_id}/{layer}/` with `.md` files per agent.

---

## Decision

Implement a downstream agent chaining system with seven components:

1. **Output Manifest** -- a machine-readable index of all research outputs generated per run
2. **Agent Contract** (`agent.yaml`) -- a declarative spec each downstream agent provides
3. **Context Bundle Assembly** -- the mechanism that matches agent inputs to manifest outputs
4. **Knowledge Base Export** -- a versioned, domain-organized export for the support/knowledge agent
5. **Progressive Reveal Architecture** -- routing and sub-agent design for the knowledge agent
6. **Pipeline Extension Mechanism** -- how downstream agents integrate with the orchestrator
6b. **Hardcoded Layer Name Remediation** -- addressing 7+ hardcoded layer lists in existing code
7. **External Escape Hatch Protocol** -- a file-based protocol for non-Python agents
8. **Budget Integration** -- how downstream agents participate in global cost/search tracking
9. **Integration Points** -- MCP, Claude Code, webhook, and observability connections

---

## Detailed Design

### 1. Output Manifest Schema

The manifest is generated at the end of every research run from existing checkpoint state. No new data collection is required -- the orchestrator already tracks output paths, agent names, and completion metadata in the `StateTracker`.

**Generation trigger**: After brand alignment completes (or after validation if brand alignment is disabled), the orchestrator calls `generate_manifest()`.

**File location**: `outputs/{execution_id}/manifest.json`

**Schema**:

```json
{
  "schema_version": "1.0.0",
  "execution_id": "research_20260208_143000",
  "produced_at": "2026-02-08T14:45:00Z",
  "config_source": "build/config/projects/gtm_phase1.yaml",
  "context_files": {
    "baseline": "research-manager/context/baseline.yaml",
    "writing_standards": "research-manager/context/writing-standards.yaml",
    "glossary": "research-manager/context/glossary.yaml",
    "audience_personas": "research-manager/context/audience-personas.yaml"
  },
  "outputs": [
    {
      "agent_name": "service_category_security",
      "type": "service_category",
      "layer": "layer_0",
      "dimensions": { "service_category": "security" },
      "tags": ["layer_0", "security", "service_category"],
      "path": "outputs/research_20260208_143000/layer_0/service_category_security.md",
      "completed_at": "2026-02-08T14:32:00Z",
      "searches_performed": 15,
      "completion_status": "complete"
    },
    {
      "agent_name": "buyer_journey",
      "type": "horizontal",
      "layer": "layer_1",
      "dimensions": {},
      "tags": ["layer_1", "horizontal", "buyer_journey"],
      "path": "outputs/research_20260208_143000/layer_1/buyer_journey.md",
      "completed_at": "2026-02-08T14:35:00Z",
      "searches_performed": 20,
      "completion_status": "complete"
    },
    {
      "agent_name": "playbook_healthcare_cfo_cluster_security",
      "type": "playbook_3d",
      "layer": "integrations",
      "dimensions": {
        "vertical": "healthcare",
        "title": "cfo_cluster",
        "service_category": "security"
      },
      "tags": ["playbook", "3d", "healthcare", "cfo_cluster", "security"],
      "path": "outputs/research_20260208_143000/playbooks/playbook_healthcare_cfo_cluster_security.md",
      "completed_at": "2026-02-08T14:43:00Z",
      "searches_performed": 20,
      "completion_status": "complete"
    }
  ],
  "summary": {
    "total_outputs": 3,
    "by_layer": { "layer_0": 1, "layer_1": 1, "integrations": 1 },
    "verticals": ["healthcare"],
    "titles": ["cfo_cluster"],
    "service_categories": ["security"]
  }
}
```

**Implementation note**: The manifest is built by iterating over all layers in `StateTracker.state`, filtering for `status == 'complete'`, and extracting `output_path` and metadata. The `type` field is derived from the layer name and agent name prefix. The `dimensions` dictionary is parsed from the agent name following existing conventions.

**Type derivation rules**:

| Agent Name Pattern | Type |
|---|---|
| `service_category_{sc}` | `service_category` |
| `buyer_journey`, `channels_competitive`, etc. | `horizontal` |
| `vertical_{v}` | `vertical` |
| `title_{t}` | `title` |
| `playbook_{v}_{t}` (2 parts after prefix) | `playbook_2d` |
| `playbook_{v}_{t}_{sc}` (3 parts after prefix) | `playbook_3d` |
| `validate_*` | `validation` |
| `align_*` | `brand_alignment` |

---

### 2. Downstream Agent Contract (agent.yaml)

Each downstream agent provides a declarative YAML spec that defines its inputs, outputs, execution model, and resource requirements. The orchestrator reads these specs to assemble context bundles and execute agents in the correct order.

**File location**: Each agent lives in a directory under `downstream/agents/{agent_name}/agent.yaml`.

**Schema**:

```yaml
# downstream/agents/case_study_generator/agent.yaml

name: "case_study_generator"
version: "1.0.0"
description: "Generates customer case studies from playbook messaging and proof points"

# What this agent needs from the research manifest
inputs:
  # Required outputs matched by type and dimension filters
  required:
    - type: "playbook_3d"
      description: "3D playbooks with service-specific messaging and proof points"
      # Dimension filters narrow which outputs are matched
      # Omit a dimension to match all values for that dimension
      dimensions: {}

    - type: "vertical"
      description: "Vertical research for industry context"
      dimensions: {}

  # Optional outputs -- agent works without these but produces better results
  optional:
    - type: "validation"
      description: "Validation reports to skip low-scoring playbooks"
      dimensions: {}

    - type: "brand_alignment"
      description: "Brand-aligned versions preferred over raw playbooks"
      dimensions: {}

  # Context files from the research-manager/context/ directory
  context_files:
    required:
      - "baseline"
      - "writing_standards"
    optional:
      - "glossary"

  # External data sources (files outside the research output tree)
  # Paths are relative to the project config directory
  external:
    - name: "crm_deals"
      path: "data/crm_closed_deals.csv"
      description: "Closed deal data for proof points and customer references"
      required: false

# What this agent produces
outputs:
  - name: "case_study"
    path_template: "downstream/case_study_generator/{vertical}_{title}_{service_category}_case_study.md"
    description: "Formatted case study document"
    variables:
      - "vertical"
      - "title"
      - "service_category"

  - name: "case_study_index"
    path_template: "downstream/case_study_generator/index.json"
    description: "Index of all generated case studies with metadata"

# Execution configuration
execution:
  # python: in-process DownstreamAgent subclass
  # subprocess: separate Python/other process
  # webhook: HTTP POST to endpoint
  # mcp: MCP server tool call
  type: "python"

  # For type: python
  module: "downstream.agents.case_study_generator.agent"
  class: "CaseStudyGenerator"

  # For type: subprocess (alternative)
  # command: "python -m downstream.agents.case_study_generator"
  # working_dir: "."

  # For type: webhook (alternative)
  # url: "https://agents.internal.example.com/case-study"
  # method: "POST"
  # headers:
  #   Authorization: "${AGENT_API_KEY}"

  # For type: mcp (alternative)
  # server: "case-study-mcp"
  # tool: "generate_case_study"

# Dependencies on other downstream agents
depends_on: []

# Model configuration (for Python/subprocess agents that use Claude)
model:
  name: "claude-sonnet-4-20250514"
  max_tokens: 16000
  temperature: 1.0

# Resource limits
budget:
  max_cost_usd: 5.0
  timeout_seconds: 300
  max_searches: 0
```

**GTM Content Creator (depends on case study generator)**:

```yaml
# downstream/agents/gtm_content_creator/agent.yaml

name: "gtm_content_creator"
version: "1.0.0"
description: "Creates GTM content assets from messaging frameworks and buyer journey research"

inputs:
  required:
    - type: "horizontal"
      description: "Buyer journey and messaging frameworks"
      dimensions: {}

    - type: "playbook_2d"
      description: "Playbook messaging and positioning"
      dimensions: {}

  optional:
    - type: "brand_alignment"
      description: "Brand-aligned playbooks preferred"
      dimensions: {}

  context_files:
    required:
      - "baseline"
      - "writing_standards"
    optional:
      - "audience_personas"

  # Outputs from other downstream agents
  downstream_inputs:
    - agent: "case_study_generator"
      output: "case_study"
      description: "Generated case studies to reference in content"
      required: true

outputs:
  - name: "email_sequence"
    path_template: "downstream/gtm_content_creator/{vertical}_{title}_email_sequence.md"
    variables: ["vertical", "title"]

  - name: "blog_article"
    path_template: "downstream/gtm_content_creator/{vertical}_{title}_article.md"
    variables: ["vertical", "title"]

  - name: "social_posts"
    path_template: "downstream/gtm_content_creator/{vertical}_{title}_social.md"
    variables: ["vertical", "title"]

execution:
  type: "python"
  module: "downstream.agents.gtm_content_creator.agent"
  class: "GTMContentCreator"

depends_on:
  - "case_study_generator"

model:
  name: "claude-sonnet-4-20250514"
  max_tokens: 16000

budget:
  max_cost_usd: 10.0
  timeout_seconds: 600
  max_searches: 0
```

**Support Knowledge Agent**:

```yaml
# downstream/agents/knowledge_base/agent.yaml

name: "knowledge_base"
version: "1.0.0"
description: "Builds structured knowledge base with progressive reveal from full research corpus"

inputs:
  required:
    - type: "service_category"
      dimensions: {}
    - type: "horizontal"
      dimensions: {}
    - type: "vertical"
      dimensions: {}
    - type: "title"
      dimensions: {}
    - type: "playbook_2d"
      dimensions: {}
    - type: "playbook_3d"
      dimensions: {}

  optional:
    - type: "brand_alignment"
      dimensions: {}

  context_files:
    required:
      - "baseline"
      - "writing_standards"
      - "glossary"

outputs:
  - name: "knowledge_base"
    path_template: "downstream/knowledge_base/kb_v{schema_version}/"
    variables: ["schema_version"]

  - name: "kb_manifest"
    path_template: "downstream/knowledge_base/kb_manifest.json"

execution:
  type: "python"
  module: "downstream.agents.knowledge_base.agent"
  class: "KnowledgeBaseBuilder"

depends_on: []

model:
  name: "claude-haiku-4-5-20251001"
  max_tokens: 16000

budget:
  max_cost_usd: 15.0
  timeout_seconds: 900
  max_searches: 0
```

**Contract validation**: At orchestrator startup, all `agent.yaml` files under `downstream/agents/` are loaded and validated:

1. Required fields present (`name`, `version`, `inputs`, `outputs`, `execution`)
2. `depends_on` references exist (no dangling references)
3. `downstream_inputs` reference agents that are in the `depends_on` chain
4. No circular dependencies (topological sort must succeed)
5. Dimension filter keys are valid (`vertical`, `title`, `service_category`)
6. Execution type has required sub-fields (`module`/`class` for python, `command` for subprocess, `url` for webhook, `server`/`tool` for mcp)

---

### 3. Context Bundle Assembly

The context bundle is the data package delivered to each downstream agent. It is assembled by the orchestrator after manifest generation, using the agent contract to select relevant outputs.

**Assembly algorithm**:

```python
@dataclass
class ContextBundle:
    """Data package for a downstream agent invocation."""
    agent_name: str
    execution_id: str
    manifest: dict
    research_outputs: dict[str, list[OutputEntry]]  # type -> list of matched outputs
    context_files: dict[str, str]                    # name -> file content
    external_data: dict[str, str]                    # name -> file content
    downstream_outputs: dict[str, list[str]]         # agent_name -> list of output paths
    dimensions: dict[str, list[str]]                 # available dimension values

@dataclass
class OutputEntry:
    """A single matched research output."""
    agent_name: str
    type: str
    layer: str
    dimensions: dict[str, str]
    path: str
    content: str  # loaded file content
```

**Matching logic** (pseudocode):

```python
def assemble_bundle(contract: AgentContract, manifest: Manifest) -> ContextBundle:
    research_outputs = {}

    for input_spec in contract.inputs.required + contract.inputs.optional:
        matched = []
        for output in manifest.outputs:
            if output.type != input_spec.type:
                continue
            # Dimension filter: all specified dimensions must match
            if all(output.dimensions.get(k) == v
                   for k, v in input_spec.dimensions.items()):
                matched.append(OutputEntry(
                    agent_name=output.agent_name,
                    type=output.type,
                    layer=output.layer,
                    dimensions=output.dimensions,
                    path=output.path,
                    content=read_file(output.path)
                ))
        research_outputs[input_spec.type] = matched

        # Fail if required input has zero matches
        if input_spec in contract.inputs.required and len(matched) == 0:
            raise MissingRequiredInput(
                agent=contract.name,
                input_type=input_spec.type,
                dimensions=input_spec.dimensions
            )

    # Load context files
    context_files = {}
    for name in contract.inputs.context_files.required:
        path = manifest.context_files.get(name)
        if not path:
            raise MissingContextFile(contract.name, name)
        context_files[name] = read_file(path)

    for name in contract.inputs.context_files.optional:
        path = manifest.context_files.get(name)
        if path and file_exists(path):
            context_files[name] = read_file(path)

    # Load external data
    external_data = {}
    for ext in contract.inputs.external:
        if file_exists(ext.path):
            external_data[ext.name] = read_file(ext.path)
        elif ext.required:
            raise MissingExternalData(contract.name, ext.name, ext.path)

    # Collect downstream outputs (from already-completed agents)
    downstream_outputs = {}
    for dep in contract.inputs.get("downstream_inputs", []):
        dep_outputs = get_agent_outputs(dep.agent, dep.output)
        downstream_outputs[dep.agent] = dep_outputs
        if dep.required and len(dep_outputs) == 0:
            raise MissingDownstreamOutput(contract.name, dep.agent, dep.output)

    return ContextBundle(
        agent_name=contract.name,
        execution_id=manifest.execution_id,
        manifest=manifest.to_dict(),
        research_outputs=research_outputs,
        context_files=context_files,
        external_data=external_data,
        downstream_outputs=downstream_outputs,
        dimensions=extract_available_dimensions(research_outputs)
    )
```

**Dimension extraction**: The `dimensions` field on the bundle tells the agent what dimension values are available across its matched outputs. For example, if matched playbook_3d outputs have dimensions `{"vertical": "healthcare", "title": "cfo_cluster", "service_category": "security"}` and `{"vertical": "finance", "title": "cfo_cluster", "service_category": "security"}`, the bundle dimensions would be `{"vertical": ["healthcare", "finance"], "title": ["cfo_cluster"], "service_category": ["security"]}`. This lets agents iterate over dimension combinations to produce per-combination outputs.

**Memory management**: For large research runs with many outputs, the bundle loads file content lazily. The `content` field on `OutputEntry` is populated on first access, not at assembly time. This prevents loading 50+ research files into memory simultaneously.


---

### 4. Knowledge Base Export with Versioning

The knowledge base agent produces a structured, versioned export optimized for retrieval by the progressive reveal system. Unlike other downstream agents that produce individual content pieces, the knowledge base agent transforms the entire research corpus into a domain-organized hierarchy.

**Directory structure**:

```
downstream/knowledge_base/
  kb_manifest.json              # Current version pointer and changelog
  kb_v1/
    domains/
      security/
        overview.md             # Service category summary
        buyer_journey.md        # Security-specific buyer journey extract
        verticals/
          healthcare/
            overview.md         # Healthcare + security intersection
            personas/
              cfo_cluster.md    # CFO persona in healthcare security
              ciso.md           # CISO persona in healthcare security
            playbooks/
              cfo_cluster.md    # Full playbook content
              ciso.md
          finance/
            overview.md
            personas/
              cfo_cluster.md
            playbooks/
              cfo_cluster.md
      cx/
        overview.md
        buyer_journey.md
        verticals/
          ...
    cross_cutting/
      messaging_frameworks.md   # Consolidated messaging across all verticals
      competitive_landscape.md  # Consolidated competitive intelligence
      proof_points.md           # All proof points indexed by vertical/persona
    index.json                  # Full content index with paths and summaries
  kb_v2/
    ...
```

**Versioning model**: Each research run that modifies the knowledge base creates a new version directory. The `kb_manifest.json` tracks all versions:

```json
{
  "schema_version": "1.0.0",
  "current_version": 2,
  "versions": [
    {
      "version": 1,
      "created_at": "2026-02-08T15:00:00Z",
      "source_execution_id": "research_20260208_143000",
      "source_manifest": "outputs/research_20260208_143000/manifest.json",
      "domains": ["security", "cx"],
      "verticals": ["healthcare", "finance"],
      "total_documents": 24,
      "total_size_bytes": 245000
    },
    {
      "version": 2,
      "created_at": "2026-02-15T10:00:00Z",
      "source_execution_id": "research_20260215_090000",
      "source_manifest": "outputs/research_20260215_090000/manifest.json",
      "domains": ["security", "cx", "network"],
      "verticals": ["healthcare", "finance", "legal"],
      "total_documents": 42,
      "total_size_bytes": 520000,
      "changelog": [
        "Added network domain (6 documents)",
        "Added legal vertical across all domains (12 documents)",
        "Updated healthcare/security with new proof points"
      ]
    }
  ]
}
```

**Content index** (`kb_v{n}/index.json`): A flat index of all documents with metadata for the progressive reveal router:

```json
{
  "documents": [
    {
      "path": "domains/security/verticals/healthcare/personas/cfo_cluster.md",
      "domain": "security",
      "vertical": "healthcare",
      "persona": "cfo_cluster",
      "type": "persona_brief",
      "summary": "CFO-cluster pain points and messaging for healthcare security",
      "keywords": ["budget justification", "compliance cost", "ROI", "risk quantification"],
      "detail_level": "summary",
      "related": [
        "domains/security/verticals/healthcare/playbooks/cfo_cluster.md"
      ]
    }
  ]
}
```

**Incremental updates**: When a new research run covers the same domain/vertical/persona as an existing KB version, the knowledge base agent performs a merge rather than a full replacement. The merge strategy is:

1. New research output replaces existing content for the same dimension combination
2. Existing content for dimension combinations NOT in the new run is preserved
3. Cross-cutting documents (messaging frameworks, competitive landscape) are regenerated from the full corpus
4. A changelog entry is generated summarizing what changed


---

### 5. Progressive Reveal Support Architecture

The progressive reveal system is a multi-agent chat architecture that sits on top of the knowledge base. It answers sales team questions by routing to the right depth of information, starting with summaries and drilling down on request.

**Architecture**:

```
User Query
    |
    v
[Router Agent] -- reads index.json, determines domain/vertical/persona
    |
    +---> [Summary Agent] -- reads overview.md files, returns 2-3 sentence answer
    |         |
    |         +---> (user asks for more detail)
    |         |
    |         v
    |     [Detail Agent] -- reads persona briefs, returns structured detail
    |         |
    |         +---> (user asks for full research)
    |         |
    |         v
    |     [Full Research Agent] -- reads playbook content, returns comprehensive answer
    |
    +---> [Cross-Cutting Agent] -- for questions spanning domains/verticals
              reads cross_cutting/*.md files
```

**Router agent logic**: The router uses the KB index to classify each query:

1. **Domain detection**: Match query keywords against domain names and document keywords
2. **Vertical detection**: Match against vertical names in the index
3. **Persona detection**: Match against persona names and associated keywords
4. **Depth assessment**: Start at summary level unless the query explicitly asks for detail ("tell me everything about...", "give me the full analysis of...")
5. **Cross-cutting detection**: If the query spans multiple domains or asks for comparison, route to the cross-cutting agent

**Three-tier response model**:

| Tier | Source Files | Response Length | Trigger |
|------|-------------|-----------------|---------|
| Summary | `overview.md` files | 2-3 sentences | Default for new topics |
| Detail | Persona briefs, buyer journey extracts | 1-2 paragraphs with bullet points | "Tell me more", follow-up questions |
| Full Research | Full playbook content | Comprehensive structured response | "Give me everything", explicit deep-dive requests |

**Conversation state**: The progressive reveal system tracks conversation state to avoid re-routing:

```python
@dataclass
class ConversationState:
    """Tracks the current depth and focus of a progressive reveal conversation."""
    session_id: str
    current_domain: str | None
    current_vertical: str | None
    current_persona: str | None
    current_tier: Literal["summary", "detail", "full_research"]
    documents_referenced: list[str]  # paths of documents already surfaced
    turn_count: int
```

**Implementation note**: The progressive reveal system is a downstream agent that produces a *service* rather than static files. Its `agent.yaml` output declares an MCP server endpoint or a CLI chat mode, not markdown files. The knowledge base builder agent produces the data; the progressive reveal agent consumes it at query time.


---

### 6. Pipeline Extension Mechanism

Downstream agent execution follows the same post-processing stage pattern used by validation and brand alignment. This section defines the state tracking, orchestrator integration, and execution flow.

**State tracking extension**: Add a `downstream` key to `StateTracker.state`, following the same flat-dictionary pattern as `validation` and `brand_alignment`:

```python
# In StateTracker

def initialize_downstream(self, agent_names: list[str]) -> None:
    """Initialize tracking for downstream agents. Follows the same pattern
    as initialize_validation() and initialize_brand_alignment()."""
    if "downstream" not in self.state:
        self.state["downstream"] = {}
    for name in agent_names:
        if name not in self.state["downstream"]:
            self.state["downstream"][name] = {"status": "pending"}
    self._save_state()
```

**Checkpoint compatibility**: The `downstream` key is absent from existing checkpoint files. The `load_or_initialize()` method does NOT generically handle missing keys -- it only explicitly checks for `layer_0` and `validation` (lines 59-62 of `tracker.py`). To maintain the same pattern, a new backward-compatibility check must be added:

```python
# In load_or_initialize(), add after existing checks:
if 'downstream' not in state:
    state['downstream'] = {}
```

No data migration is needed -- the key is simply added on first load of an older checkpoint.

**State schema alignment**: Downstream agents use the same `mark_complete()` / `mark_in_progress()` / `mark_failed()` methods as all other layers. The existing `mark_complete(agent_name, outputs, layer)` method spreads `**outputs` into the agent state dict. Downstream agents MUST pass the same output schema used by existing agents:

```python
# What mark_complete() stores (from tracker.py line 224):
self.state[layer][agent_name] = {
    "status": "complete",
    "completed_at": datetime.utcnow().isoformat(),
    **outputs  # <- these fields must match existing convention
}

# Downstream agents pass:
self.state.mark_complete(
    agent_name=agent_name,
    outputs={
        "output_path": str(primary_output_path),
        "output_paths": [str(p) for p in all_output_paths],  # extension for multi-output
        "searches_performed": result.metrics.searches or 0,
        "total_turns": result.metrics.turns or 0,
        "tokens_used": result.metrics.tokens_used,
        "estimated_cost_usd": result.metrics.cost_usd,
        "execution_time_seconds": result.metrics.duration_seconds,
        "completion_status": "complete"
    },
    layer="downstream"
)
```

The `output_path` field (singular) is required for compatibility with `get_agent_output()` which reads this field. The `output_paths` field (plural) is an extension for downstream agents that produce multiple files. The `deliverables` field is omitted because downstream agents write directly to disk rather than returning content in-memory.

**Execution order**: Downstream agents are executed in topological order based on `depends_on` declarations. Agents with no dependencies (or whose dependencies are all complete) run in parallel within a "wave":

```python
def resolve_execution_order(contracts: dict[str, AgentContract]) -> list[list[str]]:
    """Topological sort of downstream agents into execution waves.

    Returns a list of waves, where each wave is a list of agent names
    that can execute in parallel.

    Raises CircularDependencyError if the dependency graph has cycles.
    """
    # Build adjacency list
    graph: dict[str, set[str]] = {name: set() for name in contracts}
    in_degree: dict[str, int] = {name: 0 for name in contracts}

    for name, contract in contracts.items():
        for dep in contract.depends_on:
            if dep not in contracts:
                raise DanglingDependencyError(name, dep)
            graph[dep].add(name)
            in_degree[name] += 1

    # Kahn's algorithm with wave tracking
    waves = []
    current_wave = [n for n, d in in_degree.items() if d == 0]

    processed = 0
    while current_wave:
        waves.append(sorted(current_wave))  # sort for deterministic order
        next_wave = []
        for node in current_wave:
            processed += 1
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_wave.append(neighbor)
        current_wave = next_wave

    if processed != len(contracts):
        raise CircularDependencyError(contracts.keys())

    return waves
```

**Orchestrator integration** -- `execute_downstream()` method:

```python
async def execute_downstream(self) -> None:
    """Execute downstream agents after brand alignment (or validation).

    Follows the same pattern as execute_validation() and
    execute_brand_alignment(): initialize state, resolve order,
    execute in parallel waves, checkpoint after each wave.
    """
    if not self.config.downstream.enabled:
        logger.info("Downstream agents disabled, skipping")
        return

    # Load and validate all agent contracts
    contracts = load_agent_contracts(self.config.downstream.agents_dir)
    validate_contracts(contracts)

    # Generate manifest from current state
    manifest = generate_manifest(
        state=self.state,
        execution_id=self.execution_id,
        config_source=self.config_path
    )
    manifest_path = self.output_dir / "manifest.json"
    write_json_atomic(manifest_path, manifest.to_dict())

    # Filter to enabled agents
    enabled = {
        name: c for name, c in contracts.items()
        if name in self.config.downstream.enabled_agents or
           self.config.downstream.enabled_agents == ["*"]
    }

    # Resolve execution order
    waves = resolve_execution_order(enabled)

    # Initialize state tracking
    all_agent_names = [name for wave in waves for name in wave]
    self.state.initialize_downstream(all_agent_names)

    for wave_idx, wave in enumerate(waves):
        logger.info(f"Downstream wave {wave_idx + 1}/{len(waves)}: {wave}")

        # Skip already-complete agents (checkpoint/resume support)
        pending = [
            name for name in wave
            if not self.state.is_agent_complete(name)
        ]

        if not pending:
            logger.info(f"Wave {wave_idx + 1} already complete, skipping")
            continue

        # Assemble context bundles
        bundles = {}
        for name in pending:
            try:
                bundles[name] = assemble_bundle(enabled[name], manifest)
            except MissingRequiredInput as e:
                self.state.mark_failed(name, str(e), "downstream")
                logger.error(f"Failed to assemble bundle for {name}: {e}")
                continue

        # Execute in parallel
        tasks = []
        for name, bundle in bundles.items():
            self.state.mark_in_progress(name, "downstream")
            tasks.append(self._execute_downstream_agent(
                contract=enabled[name],
                bundle=bundle
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        self._check_gather_results(results)

        # Checkpoint after each wave
        self.state._save_state()

    # Review gate (optional)
    if self.config.get('execution_settings', {}).get('review_gates', {}).get('after_downstream', False):
        if not self._prompt_for_review("Downstream Agents"):
            self.logger.info("Execution halted by user after downstream agents")
            return

    logger.info("Downstream agent execution complete")
```

**Orchestrator call site** -- in `execute_full_research()`, after brand alignment (around line 372):

```python
# After brand alignment block, before "Final summary":

# Downstream agents (if enabled)
downstream_config = self.config.get('downstream', {})
if downstream_config.get('enabled', False):
    self.logger.info("\n" + "=" * 80)
    self.logger.info("DOWNSTREAM: Agent Execution")
    self.logger.info("=" * 80)
    await self.execute_downstream()

# Final summary
self.logger.info("\n" + "=" * 80)
self.logger.info("RESEARCH PROGRAM COMPLETE")
```

**Partial output cleanup on failure**: When a downstream agent fails, any output files it created during the failed execution are left in place (not deleted). On resume, the agent re-executes from scratch and overwrites any existing files at the same paths. The `result.json` from a successful re-execution is authoritative -- only paths listed in the successful result are considered valid outputs. The orchestrator does NOT proactively delete orphaned files, as determining which files are orphaned requires knowledge of the agent's intended output set (which is only known after successful completion).

**Python agent base class**:

```python
from abc import ABC, abstractmethod

class DownstreamAgent(ABC):
    """Base class for in-process Python downstream agents."""

    def __init__(self, contract: AgentContract, bundle: ContextBundle):
        self.contract = contract
        self.bundle = bundle
        self.output_paths: list[str] = []

    @abstractmethod
    async def execute(self) -> list[str]:
        """Execute the agent and return list of output file paths.

        The agent should:
        1. Read inputs from self.bundle.research_outputs
        2. Read context from self.bundle.context_files
        3. Produce outputs according to self.contract.outputs
        4. Return the list of output file paths created
        """
        ...

    def get_output_dir(self) -> Path:
        """Returns the output directory for this agent within the execution output tree."""
        return Path(self.bundle.execution_id) / "downstream" / self.contract.name

    def resolve_output_path(self, template: str, variables: dict[str, str]) -> Path:
        """Resolve an output path template with dimension variables."""
        resolved = template.format(**variables)
        return self.get_output_dir() / resolved
```


---

### 6b. Hardcoded Layer Name Remediation

The existing codebase has 7+ locations where layer names are hardcoded as lists. Adding `"downstream"` requires updating each location. This section documents every location and the approach for each.

**Locations requiring `"downstream"` addition:**

| # | File | Line(s) | Code | Action |
|---|------|---------|------|--------|
| 1 | `tracker.py` | 69-86 | `load_or_initialize()` initial state dict | Add `"downstream": {}` to initial state |
| 2 | `tracker.py` | 58-63 | `load_or_initialize()` backward compat block | Add `if 'downstream' not in state: state['downstream'] = {}` |
| 3 | `tracker.py` | 132 | `is_agent_complete()` layer search list | Add `'downstream'` to list |
| 4 | `tracker.py` | 287 | `mark_for_rerun()` layer search list | Add `'downstream'` to list |
| 5 | `tracker.py` | 364 | `get_agent_output()` layer search list | Add `'downstream'` to list |
| 6 | `tracker.py` | 543-557 | `get_execution_summary()` status entries | Add `'downstream_status': self.get_layer_status('downstream')` |
| 7 | `orchestrator.py` | 138 | Directory creation loop | Add `'downstream'` to list |
| 8 | `orchestrator.py` | 1624-1642 | `_save_agent_output()` directory mapping | Add `elif layer == 'downstream': output_dir = self.output_dir / 'downstream'` |
| 9 | `orchestrator.py` | 1708 | `_print_execution_summary()` layer list | Add `'downstream_status'` to list |

**Refactoring strategy (recommended for Phase 1):**

Rather than just appending to each hardcoded list, introduce a `KNOWN_LAYERS` constant in `tracker.py` that all methods reference:

```python
# tracker.py - top of file
KNOWN_LAYERS: tuple[str, ...] = (
    'layer_0', 'layer_1', 'layer_2', 'layer_3',
    'integrations', 'validation', 'brand_alignment', 'downstream'
)
```

Then refactor each search method to use it:

```python
# Before (7 different hardcoded lists):
for layer_name in ['layer_0', 'layer_1', 'layer_2', 'layer_3', 'integrations', 'validation', 'brand_alignment']:

# After (single source of truth):
for layer_name in KNOWN_LAYERS:
```

Similarly in `orchestrator.py`, import and use this constant for directory creation and output routing. The `_save_agent_output()` layer-to-directory mapping should become a dict:

```python
LAYER_OUTPUT_DIRS: dict[str, str] = {
    'layer_0': 'layer_0',
    'layer_1': 'layer_1',
    'layer_2': 'layer_2',
    'layer_3': 'layer_3',
    'integrations': 'playbooks',
    'validation': 'validation',
    'brand_alignment': 'brand_alignment',
    'downstream': 'downstream',
}
```

This prevents the "add to N lists" problem from recurring when future layers are added.

**Note on `get_context_for_agent()` (tracker.py lines 371-440):** This function uses prefix-based routing (`startswith('vertical_')`, `startswith('title_')`, etc.) and has no case for downstream agent names. Downstream agents do NOT need this function because they receive context via the `ContextBundle` assembly mechanism (Section 3), not via the state tracker's prefix routing. However, a defensive `else` clause should be added:

```python
# At the end of get_context_for_agent(), before return:
elif agent_name.startswith('downstream_') or layer == 'downstream':
    # Downstream agents use ContextBundle assembly, not state-based context
    # Return empty context -- downstream executor handles input assembly
    pass
```

---

### 7. External Escape Hatch Protocol

For downstream agents written in other languages (TypeScript, Go, Rust) or running as external services, the orchestrator provides a file-based protocol. This avoids requiring a Python runtime for all agents.

**Protocol overview**: The orchestrator writes a `context_bundle.json` file to a handoff directory, invokes the external agent (subprocess, webhook, or MCP), and reads back a `result.json` file from the same directory.

**Handoff directory**: `outputs/{execution_id}/downstream/{agent_name}/`

**Context bundle file** (`context_bundle.json`):

```json
{
  "schema_version": "1.0.0",
  "agent_name": "case_study_generator",
  "execution_id": "research_20260208_143000",
  "manifest_path": "outputs/research_20260208_143000/manifest.json",
  "research_outputs": {
    "playbook_3d": [
      {
        "agent_name": "playbook_healthcare_cfo_cluster_security",
        "type": "playbook_3d",
        "layer": "integrations",
        "dimensions": {
          "vertical": "healthcare",
          "title": "cfo_cluster",
          "service_category": "security"
        },
        "path": "outputs/research_20260208_143000/playbooks/playbook_healthcare_cfo_cluster_security.md",
        "content_path": "outputs/research_20260208_143000/playbooks/playbook_healthcare_cfo_cluster_security.md"
      }
    ],
    "vertical": [
      {
        "agent_name": "vertical_healthcare",
        "type": "vertical",
        "layer": "layer_2",
        "dimensions": { "vertical": "healthcare" },
        "path": "outputs/research_20260208_143000/layer_2/vertical_healthcare.md",
        "content_path": "outputs/research_20260208_143000/layer_2/vertical_healthcare.md"
      }
    ]
  },
  "context_files": {
    "baseline": {
      "name": "baseline",
      "path": "research-manager/context/baseline.yaml",
      "content_path": "research-manager/context/baseline.yaml"
    },
    "writing_standards": {
      "name": "writing_standards",
      "path": "research-manager/context/writing-standards.yaml",
      "content_path": "research-manager/context/writing-standards.yaml"
    }
  },
  "downstream_outputs": {},
  "dimensions": {
    "vertical": ["healthcare"],
    "title": ["cfo_cluster"],
    "service_category": ["security"]
  },
  "output_dir": "outputs/research_20260208_143000/downstream/case_study_generator/"
}
```

**Note on content delivery**: The `content_path` fields point to the actual files on disk. External agents read file content directly from these paths. The orchestrator does NOT inline large markdown content into the JSON bundle -- this keeps the bundle small and avoids JSON escaping issues with complex markdown.

**Result file** (`result.json`):

```json
{
  "schema_version": "1.0.0",
  "agent_name": "case_study_generator",
  "status": "complete",
  "outputs": [
    {
      "name": "case_study",
      "path": "outputs/research_20260208_143000/downstream/case_study_generator/healthcare_cfo_cluster_security_case_study.md",
      "dimensions": {
        "vertical": "healthcare",
        "title": "cfo_cluster",
        "service_category": "security"
      }
    },
    {
      "name": "case_study_index",
      "path": "outputs/research_20260208_143000/downstream/case_study_generator/index.json"
    }
  ],
  "metrics": {
    "duration_seconds": 45,
    "tokens_used": 12000,
    "cost_usd": 0.36
  },
  "errors": []
}
```

**Error result**:

```json
{
  "schema_version": "1.0.0",
  "agent_name": "case_study_generator",
  "status": "failed",
  "outputs": [],
  "metrics": {
    "duration_seconds": 12,
    "tokens_used": 3000,
    "cost_usd": 0.09
  },
  "errors": [
    {
      "code": "MISSING_INPUT",
      "message": "Required playbook_3d output not found for healthcare/cfo_cluster/security",
      "recoverable": false
    }
  ]
}
```

**Security: Path validation for external agents (CRITICAL):**

External agents write `result.json` with output file paths. A malicious or buggy agent could specify paths outside the expected output directory (path traversal). All paths in `result.json` MUST be validated before the orchestrator reads or records them:

```python
def validate_result_paths(result: dict, handoff_dir: Path) -> None:
    """Validate all output paths in result.json are within the handoff directory.

    Raises:
        PathTraversalError: If any path resolves outside the handoff directory.
    """
    allowed_root = handoff_dir.resolve()

    for output in result.get("outputs", []):
        output_path = Path(output["path"]).resolve()
        if not str(output_path).startswith(str(allowed_root)):
            raise PathTraversalError(
                f"Output path {output['path']} resolves to {output_path} "
                f"which is outside allowed root {allowed_root}"
            )
```

This check runs immediately after reading `result.json` and before updating state. The `handoff_dir` is always `outputs/{execution_id}/downstream/{agent_name}/` -- paths must resolve within this directory.

**Security: Webhook SSRF protection (CRITICAL):**

Webhook execution types POST the context bundle to a URL specified in `agent.yaml`. Without restrictions, this creates a Server-Side Request Forgery (SSRF) vector. Protections:

1. **URL allowlist**: The `DownstreamConfig` includes an optional `webhook_allowed_hosts` field. If set, only URLs matching these hosts are permitted:

```python
class DownstreamConfig(BaseModel):
    # ... existing fields ...
    webhook_allowed_hosts: List[str] = Field(default_factory=list)
    # Example: ["agents.internal.example.com", "*.cloud-run.app"]
```

2. **TLS enforcement**: Webhook URLs MUST use `https://`. Plain `http://` is rejected unless `webhook_allow_insecure: true` is explicitly set (for local development only):

```python
if not url.startswith("https://") and not config.downstream.webhook_allow_insecure:
    raise WebhookSecurityError(
        f"Webhook URL must use HTTPS: {url}. "
        "Set downstream.webhook_allow_insecure: true for local development."
    )
```

3. **Private IP blocking**: The orchestrator resolves the webhook URL's IP before connecting and rejects private/loopback addresses (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `::1`) unless `webhook_allow_private: true` is set.

4. **Authentication validation**: Webhook headers containing `${ENV_VAR}` references are resolved at execution time. If the referenced environment variable is not set, the agent fails with a clear error rather than sending an unauthenticated request.

**Subprocess execution flow**:

1. Orchestrator writes `context_bundle.json` to handoff directory
2. Orchestrator spawns subprocess with command from `agent.yaml`
3. Subprocess receives handoff directory path as first argument (or via `DOWNSTREAM_HANDOFF_DIR` environment variable)
4. Subprocess reads `context_bundle.json`, processes inputs, writes outputs, writes `result.json`
5. Orchestrator polls for `result.json` with timeout from `agent.yaml` budget
6. Orchestrator reads `result.json`, updates state tracker, records metrics

**Webhook execution flow**:

1. Orchestrator writes `context_bundle.json` to handoff directory
2. Orchestrator POSTs the bundle JSON to the webhook URL (with auth headers from `agent.yaml`)
3. Webhook returns immediately with `202 Accepted` and a `poll_url`
4. Orchestrator polls `poll_url` until completion or timeout
5. On completion, webhook response includes the result JSON
6. Orchestrator writes outputs to handoff directory and updates state

**MCP execution flow**:

1. Orchestrator writes `context_bundle.json` to handoff directory
2. Orchestrator calls the MCP tool specified in `agent.yaml` with the bundle path as argument
3. MCP tool processes the bundle and returns a result JSON
4. Orchestrator updates state from the result


---

### 8. Budget Integration

Downstream agents MUST participate in the orchestrator's existing budget tracking system. The orchestrator tracks two budget dimensions globally via `_update_budget()` and enforces limits via `_check_budget_limits()`, raising `BudgetExceededError` when thresholds are crossed. Downstream agents must integrate with both.

**Global budget participation:**

```python
# In _execute_downstream_agent(), after agent completes:
async def _execute_downstream_agent(
    self,
    contract: AgentContract,
    bundle: ContextBundle
) -> None:
    """Execute a single downstream agent with budget integration."""
    agent_name = contract.name

    try:
        self.state.mark_in_progress(agent_name, "downstream")

        # Check global budget BEFORE execution
        self._check_budget_limits()

        # Execute based on type
        if contract.execution.type == "python":
            result = await self._execute_python_downstream(contract, bundle)
        elif contract.execution.type == "subprocess":
            result = await self._execute_subprocess_downstream(contract, bundle)
        elif contract.execution.type == "webhook":
            result = await self._execute_webhook_downstream(contract, bundle)
        elif contract.execution.type == "mcp":
            result = await self._execute_mcp_downstream(contract, bundle)

        # Update GLOBAL budget tracking with agent's consumption
        self._update_budget(
            searches=result.metrics.get("searches_performed", 0),
            cost=result.metrics.get("cost_usd", 0.0)
        )

        # Check global budget AFTER execution (halts remaining agents)
        self._check_budget_limits()

        # Record completion
        self.state.mark_complete(
            agent_name=agent_name,
            outputs={
                "output_path": result.outputs[0].path if result.outputs else "",
                "output_paths": [o.path for o in result.outputs],
                "searches_performed": result.metrics.get("searches_performed", 0),
                "total_turns": result.metrics.get("turns", 0),
                "tokens_used": result.metrics.get("tokens_used", 0),
                "estimated_cost_usd": result.metrics.get("cost_usd", 0.0),
                "execution_time_seconds": result.metrics.get("duration_seconds", 0),
                "completion_status": "complete"
            },
            layer="downstream"
        )

    except BudgetExceededError:
        self.state.mark_failed(agent_name, "Budget exceeded", "downstream")
        raise  # Propagate to halt remaining agents

    except Exception as e:
        self.state.mark_failed(agent_name, str(e), "downstream")
        self.logger.error(f"Downstream agent {agent_name} failed: {e}")
```

**Per-agent budget enforcement:**

Each agent's `agent.yaml` declares per-agent budget limits (`budget.max_cost_usd`, `budget.timeout_seconds`). These are enforced independently of the global budget:

- **Cost cap**: The executor tracks per-agent cost during execution. For Python agents, this is tracked via the `ResearchSession` cost accumulator. For external agents, the `result.json` `metrics.cost_usd` field is checked.
- **Timeout**: `asyncio.wait_for()` wraps each agent execution with the declared `timeout_seconds`.
- **Search cap**: `budget.max_searches` is passed to the `ResearchSession` as `max_searches`.

```python
# Timeout enforcement in execute_downstream():
try:
    await asyncio.wait_for(
        self._execute_downstream_agent(contract, bundle),
        timeout=contract.budget.timeout_seconds
    )
except asyncio.TimeoutError:
    self.state.mark_failed(
        contract.name,
        f"Timeout after {contract.budget.timeout_seconds}s",
        "downstream"
    )
```

**Budget interaction with waves:**

When a `BudgetExceededError` is raised during a wave, `_check_gather_results()` (which already handles this for research layers) propagates the error, halting all subsequent waves. Agents in the current wave that have already completed retain their results. Agents that were in-progress when the budget was exceeded are marked as failed. On resume, only the failed/pending agents in the interrupted wave re-execute.

**Config extension for downstream budget:**

The global budget in `defaults.yaml` applies to the entire pipeline including downstream. Optionally, a separate downstream budget cap can be set:

```yaml
downstream:
  enabled: false
  agents_dir: "downstream/agents"
  enabled_agents: ["*"]
  budget:
    max_cost_usd: 30.0     # Cap for ALL downstream agents combined
    max_searches: 0          # Downstream agents typically don't search
```

If `downstream.budget.max_cost_usd` is set, the downstream executor enforces it as an additional cap on top of the global budget. This prevents downstream processing from consuming the entire pipeline budget.

---

### 9. Integration Points

This section maps how the downstream agent architecture integrates with external systems beyond the core orchestrator.

**MCP Server Integration**: A downstream agent can expose its capabilities as an MCP server, allowing Claude Code or other MCP clients to invoke it directly. The knowledge base progressive reveal agent is the primary use case:

```yaml
# Example: Progressive reveal as MCP server
execution:
  type: "mcp"
  server: "upstack-knowledge"
  tool: "query_knowledge_base"
  config:
    kb_path: "downstream/knowledge_base/kb_v{current_version}/"
    index_path: "downstream/knowledge_base/kb_v{current_version}/index.json"
```

The MCP server wrapper reads the knowledge base index at startup, registers tools for querying by domain/vertical/persona, and implements the three-tier progressive reveal model described in section 5.

**Claude Code Agent Integration**: Claude Code agents can consume downstream agent outputs by reading the manifest and navigating to specific files. The manifest serves as the entry point:

```
1. Agent reads outputs/{execution_id}/manifest.json
2. Agent filters outputs by type and dimensions relevant to its task
3. Agent reads the matched files directly
4. Agent produces its output (code, documentation, analysis, etc.)
```

This requires no special integration -- the manifest is a standard JSON file readable by any agent. The downstream agent contract system is for agents that the orchestrator manages; Claude Code agents that consume outputs independently just need the manifest path.

**Webhook / External Service Integration**: For teams running agents as hosted services (AWS Lambda, Cloud Run, internal APIs), the webhook execution type provides HTTP-based integration:

1. The orchestrator POSTs the context bundle to the configured URL
2. The service processes asynchronously and reports status via polling
3. Results are written back to the handoff directory

**Authentication**: Webhook URLs can include environment variable references in headers (`${AGENT_API_KEY}`). The orchestrator resolves these from the process environment at execution time, never storing credentials in config files or state.

**Monitoring and Observability**: Each downstream agent execution produces structured log entries:

```python
logger.info("downstream_agent_start", extra={
    "agent_name": contract.name,
    "execution_type": contract.execution.type,
    "wave": wave_idx,
    "input_types": list(bundle.research_outputs.keys()),
    "input_count": sum(len(v) for v in bundle.research_outputs.values()),
})

logger.info("downstream_agent_complete", extra={
    "agent_name": contract.name,
    "duration_seconds": duration,
    "output_count": len(result.outputs),
    "cost_usd": result.metrics.cost_usd,
    "tokens_used": result.metrics.tokens_used,
})
```

These integrate with the existing structured logging in the orchestrator, allowing pipeline-wide cost and duration tracking.

---

## Consequences

### Positive

- **Declarative composability**: New downstream agents are added by creating a directory with `agent.yaml` and an implementation. No orchestrator code changes required.
- **Language agnostic**: The external escape hatch protocol (context_bundle.json / result.json) lets teams write agents in any language.
- **Checkpoint/resume**: Downstream agents participate in the existing checkpoint system. A failed agent run resumes from the last completed wave, not from scratch.
- **Cost tracking**: Per-agent budget limits and metrics collection provide visibility into downstream processing costs.
- **Reproducibility**: The manifest + versioned knowledge base let teams trace any derivative content back to the exact research run and agent version that produced it.
- **Progressive reveal**: Sales teams get instant access to research insights without reading 50-page playbooks, with the ability to drill down on demand.

### Negative

- **Increased system complexity**: Seven new components (manifest, contracts, bundles, KB export, progressive reveal, pipeline extension, escape hatch) add significant surface area.
- **Contract maintenance burden**: Agent contracts must be updated when manifest schema changes. The schema_version field provides forward-compatibility signaling but does not eliminate coordination.
- **Knowledge base storage growth**: Each KB version is a full copy. For large research corpora, this grows linearly with version count. Mitigation: implement a retention policy (keep last N versions, archive older ones).
- **Latency addition**: Downstream processing adds time to the overall pipeline. Mitigation: downstream execution is opt-in and runs after the core research pipeline is complete.

### Risks

- **Manifest schema drift**: If new research output types are added without updating the type derivation rules, downstream agents may not find their inputs. Mitigation: the manifest generator logs warnings for unrecognized agent name patterns.
- **External agent reliability**: Webhook and subprocess agents may fail due to network or runtime issues outside the orchestrator's control. Mitigation: timeout enforcement, structured error reporting, and checkpoint/resume.
- **Knowledge base consistency**: Incremental KB updates that merge new research with existing content may produce inconsistent cross-cutting documents. Mitigation: cross-cutting documents are always regenerated from the full corpus, not incrementally updated.


---

## Implementation Phases

### Phase 1: Foundation (Manifest + Contracts + Pipeline Extension)

**Scope**: Output manifest generation, agent contract schema, contract validation, basic pipeline extension with Python agent support.

**Files to create**:
- `src/research_orchestrator/downstream/__init__.py`
- `src/research_orchestrator/downstream/manifest.py` -- manifest generation from StateTracker
- `src/research_orchestrator/downstream/contracts.py` -- agent.yaml loading and validation
- `src/research_orchestrator/downstream/bundle.py` -- context bundle assembly
- `src/research_orchestrator/downstream/executor.py` -- wave execution, Python agent dispatch
- `src/research_orchestrator/downstream/base_agent.py` -- DownstreamAgent ABC

**Files to modify**:
- `src/research_orchestrator/orchestrator.py`:
  - Add `execute_downstream()` call in `execute_full_research()` after brand alignment (line ~372)
  - Add `'downstream'` to directory creation loop (line 138)
  - Add `'downstream'` case to `_save_agent_output()` (line ~1640)
  - Add `'downstream_status'` to `_print_execution_summary()` (line ~1708)
  - Import `KNOWN_LAYERS` from tracker (or define `LAYER_OUTPUT_DIRS` locally)
- `src/research_orchestrator/state/tracker.py`:
  - Add `KNOWN_LAYERS` constant at module level
  - Add `"downstream": {}` to initial state dict (line 69-86)
  - Add backward compat check in `load_or_initialize()` (line 58-63)
  - Add `initialize_downstream()` method (follows `initialize_brand_alignment()` pattern)
  - Add `'downstream'` to `is_agent_complete()` layer list (line 132)
  - Add `'downstream'` to `mark_for_rerun()` layer list (line 287)
  - Add `'downstream'` to `get_agent_output()` layer list (line 364)
  - Add `'downstream_status'` to `get_execution_summary()` (line 543-557)
  - Add defensive `else` clause to `get_context_for_agent()` for downstream agents (line ~440)
- `src/research_orchestrator/utils/config_schema.py`:
  - Add `DownstreamBudgetConfig` Pydantic model
  - Add `DownstreamConfig` Pydantic model
  - Add `after_downstream: bool = False` to `ReviewGatesConfig`
  - Add `downstream: Optional[DownstreamConfig] = None` to `ResearchConfig`

**Pydantic model** (`config_schema.py`):

```python
class DownstreamBudgetConfig(BaseModel):
    """Budget limits for downstream agent execution."""
    max_cost_usd: float = Field(default=30.0, ge=0.0)
    max_searches: int = Field(default=0, ge=0)


class DownstreamConfig(BaseModel):
    """Downstream agent chaining configuration."""
    enabled: bool = False
    agents_dir: str = "downstream/agents"
    enabled_agents: List[str] = Field(default_factory=lambda: ["*"])
    output_dir: str = "downstream"
    budget: DownstreamBudgetConfig = Field(default_factory=DownstreamBudgetConfig)
    webhook_allowed_hosts: List[str] = Field(default_factory=list)
    webhook_allow_insecure: bool = False
    webhook_allow_private: bool = False
```

Add to `ReviewGatesConfig`:

```python
class ReviewGatesConfig(BaseModel):
    """Review gates configuration."""
    after_layer_0: bool = False
    after_layer_1: bool = True
    after_layer_2: bool = True
    after_layer_3: bool = False
    after_playbooks: bool = False
    after_validation: bool = False
    after_downstream: bool = False  # NEW: gate after downstream execution
```

Add to `ResearchConfig`:

```python
class ResearchConfig(BaseModel):
    # ... existing fields ...
    brand_alignment: Optional[BrandAlignmentConfig] = None
    downstream: Optional[DownstreamConfig] = None  # NEW

    model_config = {"extra": "allow"}
```

**Config additions** (`build/config/defaults.yaml`):
```yaml
downstream:
  enabled: false
  agents_dir: "downstream/agents"
  enabled_agents: ["*"]
  output_dir: "downstream"
  budget:
    max_cost_usd: 30.0
    max_searches: 0
```

**Deliverable**: A working pipeline that generates a manifest, loads agent contracts, assembles context bundles, and executes a simple test agent.

### Phase 2: First Downstream Agents (Case Study + GTM Content)

**Scope**: Implement case study generator and GTM content creator as Python downstream agents. Validate the contract system end-to-end with real content generation.

**Files to create**:
- `downstream/agents/case_study_generator/agent.yaml`
- `downstream/agents/case_study_generator/agent.py`
- `downstream/agents/case_study_generator/prompts.py`
- `downstream/agents/gtm_content_creator/agent.yaml`
- `downstream/agents/gtm_content_creator/agent.py`
- `downstream/agents/gtm_content_creator/prompts.py`

**Deliverable**: Running the full pipeline with downstream enabled produces case studies and GTM content from research playbooks.

### Phase 3: Knowledge Base + Progressive Reveal

**Scope**: Implement the knowledge base builder agent and the progressive reveal routing system.

**Files to create**:
- `downstream/agents/knowledge_base/agent.yaml`
- `downstream/agents/knowledge_base/agent.py`
- `downstream/agents/knowledge_base/builder.py` -- domain-organized KB generation
- `downstream/agents/knowledge_base/merger.py` -- incremental update logic
- `downstream/agents/progressive_reveal/agent.yaml`
- `downstream/agents/progressive_reveal/router.py`
- `downstream/agents/progressive_reveal/agents.py` -- summary/detail/full sub-agents

**Deliverable**: A versioned knowledge base generated from research outputs, with a progressive reveal chat interface.

### Phase 4: External Escape Hatch + Advanced Execution Types

**Scope**: Implement subprocess, webhook, and MCP execution types. Build the context_bundle.json / result.json file protocol.

**Files to create**:
- `src/research_orchestrator/downstream/external.py` -- subprocess/webhook/MCP dispatch
- `src/research_orchestrator/downstream/protocols.py` -- context_bundle.json / result.json schemas

**Deliverable**: Non-Python agents can participate in the downstream pipeline via the file-based protocol.


---

## Cost Implications

**Manifest generation**: Zero additional API cost. Built entirely from existing StateTracker data.

**Contract validation**: Zero additional API cost. Pure schema validation at startup.

**Context bundle assembly**: Zero additional API cost. File reading and matching only.

**Downstream agent execution**: Variable cost depending on agent count and complexity. Per-agent budget limits enforce caps:

| Agent | Model | Estimated Cost Per Run | Budget Cap |
|-------|-------|----------------------|------------|
| Case Study Generator | claude-sonnet-4 | ~$2-4 | $5 |
| GTM Content Creator | claude-sonnet-4 | ~$4-8 | $10 |
| Knowledge Base Builder | claude-haiku-4-5 | ~$5-10 | $15 |
| Progressive Reveal (per query) | claude-haiku-4-5 | ~$0.01-0.05 | N/A (per-query) |

**Total additional pipeline cost**: ~$11-22 per full run with all agents enabled, capped at $30. This is roughly 15-30% of the core research pipeline cost.

---

## Alternatives Considered

### 1. Monolithic Post-Processor

A single post-processing step that generates all derivative content (case studies, emails, KB) in one large agent call.

**Rejected because**: No composability. Adding a new output type requires modifying the monolithic processor. No independent testing, no per-agent budgets, no selective execution. Violates the same separation-of-concerns principle that led to separate validation and brand alignment stages.

### 2. Event-Driven Architecture (Message Queue)

Publish manifest to a message queue (Redis Streams, RabbitMQ). Downstream agents subscribe and process independently.

**Rejected because**: Adds infrastructure dependency (message broker) that does not exist in the current stack. The research pipeline runs as a single Python process with file-based state. Introducing a message broker for 3-5 downstream agents is over-engineering. The file-based escape hatch protocol provides the same decoupling without the infrastructure.

### 3. Plugin Architecture (Dynamic Loading)

Downstream agents as Python plugins discovered via entry points or a plugin registry.

**Rejected because**: Tightly couples all agents to Python. The YAML contract approach is language-agnostic and supports the escape hatch protocol. Plugin discovery is also harder to reason about than explicit directory scanning.

### 4. Full API Gateway

Expose research outputs via a REST API. Downstream agents call the API to fetch their inputs.

**Rejected because**: Requires running a persistent server process. The current system is batch-oriented (run, produce outputs, exit). An API gateway would require deployment infrastructure that does not exist. The manifest file serves the same purpose as an API index without the operational overhead.

---

## Confidence: High

- Clear precedent exists in the codebase for post-processing stages (validation, brand alignment)
- The contract schema follows established YAML/Pydantic patterns
- The file-based escape hatch protocol is simple and well-understood
- The manifest is derived from existing StateTracker data with no new data collection

**What would increase confidence further**:
- Prototype the manifest generator against a real checkpoint file to validate type derivation rules
- Build the case study generator agent as a proof-of-concept to validate the context bundle assembly flow
- Test the base64 knowledge base export size with a full research run to validate storage estimates

---

## Verification Checklist

- [ ] Manifest schema covers all current output types (layer_0 through brand_alignment)
- [ ] Agent contract schema validates with Pydantic (no ambiguous fields)
- [ ] Context bundle assembly correctly matches dimension filters
- [ ] Topological sort handles all dependency patterns (independent, chain, diamond)
- [ ] External escape hatch protocol round-trips correctly (write bundle, read result)
- [ ] Knowledge base versioning handles incremental updates without data loss
- [ ] Progressive reveal router correctly classifies queries to domains/verticals/personas
- [ ] Pipeline extension integrates with existing checkpoint/resume (no regressions)
- [ ] Budget limits enforce per-agent caps (agent termination on exceed)
- [ ] All four execution types work: python, subprocess, webhook, mcp
