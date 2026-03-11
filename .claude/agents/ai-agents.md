# ProjectForge AI Agents — Vision & Roadmap

## Overview

ProjectForge's AI layer is built around a framework of **specialized agents**, each
responsible for a distinct domain of project intelligence. Agents are implemented in
the `apps/ai-service` and exposed through versioned REST endpoints under
`/api/v1/agents/`.

All agents share a common `BaseAgent` interface (`apps/ai-service/src/agents/base.py`)
and use Vertex AI (Gemini 2.0 Flash) as the underlying LLM.

---

## Agent Catalogue

### 1. SOW Parser Agent (`sow_parser`) — Phase 1 ✅

**Endpoint**: `POST /api/v1/agents/sow/parse`

**Purpose**: Ingests a Statement of Work (PDF, DOCX, TXT, Markdown) and produces a
ready-to-import project scaffold.

**Input**: multipart file upload (max 10 MB)
**Output**:
- `ProjectSuggestion` — name, description, estimated duration, budget
- `MilestoneSuggestion[]` — major phases with offset days
- `TaskSuggestion[]` — concrete work items with priority, estimated hours, and
  milestone assignment
- `SOWSection[]` — detected document sections (scope, deliverables, timeline,
  budget, terms)
- `confidence` (0–1) and `warnings[]`

**Pipeline**:
```
Upload → SOWExtractor (text + section detection)
       → SOWAnalyzer  (Gemini prompt → JSON)
       → SOWParseResponse
```

**Key files**:
```
src/agents/sow_parser/
├── extractor.py   # text extraction + section heading detection
├── analyzer.py    # Gemini call + JSON parsing
├── prompts.py     # SOW_SYSTEM_PROMPT + builder
├── schemas.py     # Pydantic models
└── router.py      # FastAPI router
```

---

### 2. Risk Advisor Agent (`risk_advisor`) — Phase 2 🔜

**Endpoint**: `POST /api/v1/agents/risk/advise`

**Purpose**: Real-time risk assessment as the project evolves. Goes beyond the
copilot's point-in-time analysis by tracking risk trends over time.

**Capabilities**:
- Detect emerging risks from task/milestone delta events
- Correlate risks across projects in the same organisation
- Generate mitigation plans ranked by ROI
- Integrate with notification service to push alerts

---

### 3. Sprint Planner Agent (`sprint_planner`) — Phase 2 🔜

**Endpoint**: `POST /api/v1/agents/sprint/plan`

**Purpose**: Automatically draft sprint plans from a backlog using velocity,
team capacity, and task dependencies.

**Capabilities**:
- Load team capacity from org member profiles
- Respect task dependency graph
- Optimise for milestone proximity
- Output: `SprintPlan` with assigned tasks, story points, and capacity warnings

---

### 4. Meeting Notes Agent (`meeting_notes`) — Phase 3 🔜

**Endpoint**: `POST /api/v1/agents/meetings/extract`

**Purpose**: Extract action items, decisions, and risks from meeting transcripts or
audio (via Vertex AI Speech-to-Text).

**Output**: structured `MeetingExtract` → auto-creates tasks in ProjectForge

---

### 5. Document QA Agent (`doc_qa`) — exists as RAG service

**Endpoint**: `POST /api/v1/rag/query`

Already implemented in `src/rag/`. This agent answers questions grounded in
uploaded project documents.

---

### 6. Estimator Agent (`estimator`) — Phase 3 🔜

**Endpoint**: `POST /api/v1/agents/estimate`

**Purpose**: Given a feature description or set of requirements, produce effort
estimates using historical velocity data from completed projects in the tenant.

---

## Implementation Conventions

### Adding a New Agent

1. Create `src/agents/<agent_name>/` with the standard structure:
   ```
   __init__.py
   schemas.py     # Pydantic request/response models
   prompts.py     # SYSTEM_PROMPT + builder functions
   extractor.py   # optional: file/data extraction
   analyzer.py    # LLM call + response parsing, extends BaseAgent
   router.py      # FastAPI router, prefix="/agents/<name>"
   ```

2. Extend `BaseAgent` in `analyzer.py`:
   ```python
   class MyAnalyzer(BaseAgent):
       name = "my_agent"
       description = "What this agent does"

       async def run(self, **kwargs) -> MyResponse:
           ...
   ```

3. Register in `src/main.py`:
   ```python
   from .agents.my_agent.router import router as my_agent_router
   app.include_router(my_agent_router, prefix=settings.api_prefix)
   ```

4. Add tests in `tests/agents/test_<agent_name>.py`

### Prompt Design Principles

- Always instruct the model to return **valid JSON only** (no markdown fences)
- Use `temperature ≤ 0.3` for structured extraction tasks
- Include a `confidence` field (0–1) in the JSON schema so the model reports
  its own uncertainty
- Handle JSON parse failures with a graceful `_fallback_response()` method

### Tenant Isolation

Agent endpoints receive `X-Organization-ID` header. Any database reads inside an
agent MUST scope queries to that organisation. Never mix tenant data.

### Observability

- Log start/end of each agent invocation with `org_id`, `filename`, and result
  summary at INFO level
- Log warnings for LLM fallback scenarios
- Future: emit Cloud Trace spans for latency tracking

---

## Roadmap Summary

| Phase | Agent | Status |
|-------|-------|--------|
| 1 | SOW Parser | ✅ Implemented |
| 1 | Document QA (RAG) | ✅ Implemented |
| 1 | Project Copilot | ✅ Implemented |
| 2 | Risk Advisor | 🔜 Planned |
| 2 | Sprint Planner | 🔜 Planned |
| 3 | Meeting Notes | 🔜 Planned |
| 3 | Estimator | 🔜 Planned |
