# Program OS

Program OS is an AI-assisted operating system for complex enterprise programs.

The first product question is deliberately narrow:

> Can this initiative launch on the target date, and what evidence supports that conclusion?

The system will combine structured program data, unstructured project artifacts, tool access, evidence-grounded reasoning, and human approval for consequential actions.

## Product principles

1. **Decision support before chat.** The primary output is a defensible program decision, not a conversational answer.
2. **Evidence before confidence.** Material claims must trace to source evidence or be marked unknown.
3. **Measure before optimizing.** Every architecture change is evaluated against a fixed test set.
4. **One agent before many agents.** Complexity is added only when evaluation results justify it.
5. **Human accountability for consequential actions.** The system may recommend broadly; irreversible or externally visible actions require approval.
6. **Production-shaped, not production-pretending.** The demo will implement meaningful trust, cost, latency, and observability patterns while explicitly documenting what would still be required for enterprise deployment.

## Initial workflow

A program leader asks:

> Can Release 3 launch on November 15?

Program OS:

1. identifies the relevant release and launch criteria;
2. retrieves requirements, risks, dependencies, decisions, approvals, and relevant documents;
3. checks for missing or contradictory evidence;
4. calculates a structured readiness assessment;
5. returns status, blockers, confidence, evidence, unknowns, and recommended actions;
6. requires human approval before any consequential write action.

## Build stages

- Phase 0: product contract and evaluation design
- Phase 1: synthetic enterprise program dataset
- Phase 2: deliberately weak baseline
- Phase 3: structured program data model and grounded retrieval
- Phase 4: tool calling
- Phase 5: MCP interface and human approval
- Phase 6: workflow orchestration and evaluation
- Phase 7: observability, cost/latency experiments, trust boundaries
- Phase 8: portfolio-quality UI, deployment, and case study

See `docs/PRD.md`, `docs/EVALS.md`, and `docs/ARCHITECTURE.md`.
