# V2 Release Checklist

**Status:** Release candidate  
**Target:** End of weekend

## Implemented and tested

- [x] Atlas fictional five-workstream portfolio
- [x] 48 timestamped evidence artifacts with provenance and authority tiers
- [x] 16 fixed golden evaluation cases
- [x] weak baseline harness
- [x] canonical Pydantic domain model
- [x] immutable evidence observations
- [x] deterministic RAG hard gates
- [x] evidence-derived confidence model
- [x] Monday intervention priority
- [x] deterministic detection of planted Atlas signals
- [x] targeted evidence retrieval
- [x] single-agent structured OpenAI Agents SDK adapter
- [x] citation validation before assessment finalization
- [x] model output constrained by deterministic hard gates
- [x] official RAG versus forecast RAG
- [x] portfolio resource-tradeoff recommendation with downstream consequence
- [x] Monday action list
- [x] Friday status
- [x] PM override record
- [x] append-only audit event
- [x] governed learning proposal that does not change runtime behavior
- [x] FastAPI demo endpoints
- [x] Next.js demo UI
- [x] Python CI
- [x] Next.js production-build CI
- [x] reproducible baseline-vs-Program-OS live evaluation runner
- [x] manual GitHub Actions live-evaluation release gate

## Required before final V2 release

- [ ] run the weak baseline against the fixed 16-case gold set with a recorded model/configuration
- [ ] run Program OS against the identical gold set
- [ ] publish Safety/Trust, Detection, Judgment, and Decision Quality results
- [ ] confirm zero catastrophic release-gate failures
- [ ] record model, SDK version, system version, prompt/rule version, and run timestamp
- [ ] update README with measured results rather than projected results

## Explicitly deferred

- production Jira/Confluence OAuth
- enterprise SSO and full production RBAC
- PostgreSQL/pgvector persistence
- production observability/SLOs
- multi-agent Program OS runtime
- autonomous consequential writes
- enterprise deployment/compliance certification

## Release rule

V2 does not ship merely because the UI works. It ships when the evaluated vertical slice proves the trust and decision loop without a catastrophic failure.
