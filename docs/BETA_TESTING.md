# Beta testing Program OS

Use the beta in one of three modes. Do not mix the trust boundaries.

## Track A — hosted synthetic review

**Use this for most external reviewers.**

Open: https://gehrm-ca.github.io/ai-work/

- no install;
- no account;
- no API key;
- synthetic Atlas data only;
- read-only;
- safe to send broadly.

Ask the reviewer to spend about ten minutes on:

1. Compare official GREEN with forecast AMBER.
2. Read the Monday intervention queue from the top down.
3. Open evidence behind the first two findings.
4. Expand **Why this conclusion · what would change it**.
5. Review the portfolio tradeoff and its downside.
6. Read the Friday status.
7. Record which finding they would act on first and what would stop them from trusting the output.

Do not paste employer/customer data into a GitHub issue or other public feedback channel.

## Track B — local synthetic product review

**Use this for technical reviewers who want to inspect the full workflow.**

Prerequisites:

- macOS/Linux: Python 3.12+ and Node.js 20.9+;
- Windows or users who prefer containers: Docker Desktop or compatible Docker + Compose.

From the repository:

~~~bash
git clone https://github.com/gehrm-ca/ai-work.git
cd ai-work
make demo
~~~

Open http://127.0.0.1:3000.

For Docker:

~~~bash
docker compose up --build
~~~

Open http://127.0.0.1:3000.

To exercise the audited human-decision flow, set a local token before starting:

~~~bash
export PROGRAM_OS_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export PROGRAM_OS_UI_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
~~~

The browser never receives the backend API token. Log in at http://127.0.0.1:3000/login with the **separate** UI token before recording a decision. No UI authentication is needed for the default synthetic read-only demo.

The Docker path stores audit events in the named volume `program_os_audit`. To inspect it:

~~~bash
docker compose exec api cat /var/program-os/audit.jsonl
~~~

To remove the containers and the retained audit volume after testing:

~~~bash
docker compose down -v
~~~

## Track C — controlled real-data connector pilot

**Use this only with an invited design partner. This is not a self-serve production beta.**

Supported real-data activity today:

- validate a local JSON export against the read-only evidence contract;
- fetch a read-only Jira Cloud snapshot;
- assess evidence readiness;
- freeze a private pilot record;
- run the design-partner protocol.

The current Atlas signal logic and dashboard are not generic enough to claim that arbitrary company data drives the full Monday → Friday product without integration work.

For employer/customer data:

- run ingestion locally or in an approved private environment;
- keep exports outside the repository;
- do not use the public GitHub Actions Jira smoke workflow for confidential partner data;
- do not expose ports 3000 or 8000 to the public internet;
- do not point the Atlas API at custom data unless the custom-data API guard, bearer token, separate local UI access token, and localhost-only boundary are intentionally enabled;
- keep live model calls disabled unless the organization has explicitly approved the model-provider/data-processing boundary;
- do not enable consequential write-back.

See [Use Program OS on your own](USE_YOUR_OWN_PROGRAM.md) and [Design-partner pilot protocol](DESIGN_PARTNER_PILOT.md).

## Real-data model boundary

The live-agent path is off by default.

Enabling it requires all of:

- `PROGRAM_OS_ENABLE_LIVE_AGENT=true`;
- `PROGRAM_OS_API_TOKEN`;
- `OPENAI_API_KEY`.

When enabled, normalized evidence payload content is sent to the configured OpenAI model. Connector principal, permission metadata, and source URLs are removed from model context, but the business content in the evidence payload can still be sensitive.

Do not enable the live-agent path on employer/customer data without explicit organizational approval for that data flow.

## Feedback

For public/synthetic feedback, use the repository beta-feedback issue template.

For any security issue or feedback containing private program context, do not use a public issue. Follow [SECURITY.md](../SECURITY.md) or use an agreed private channel with the design partner.

Useful beta questions:

- Which finding would you act on first?
- Did the evidence make the conclusion auditable?
- Was the reasoning understandable without explanation from the author?
- What was wrong, missing, or noisy?
- What would you need before raising the finding in a real operating review?
- Would you run the workflow again next week?
