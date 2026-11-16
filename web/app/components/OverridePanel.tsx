"use client";

import { FormEvent, useState } from "react";

type OverrideReceipt = {
  override?: {
    override_id?: string;
    actor?: string;
    new_status?: string;
    rationale?: string;
    created_at?: string;
  };
  audit_event?: {
    event_id?: string;
    event_type?: string;
    created_at?: string;
  };
  learning_proposal?: {
    proposal_id?: string;
    approved?: boolean;
  };
  detail?: string;
};

export function OverridePanel({
  enabled,
  defaultStatus,
}: {
  enabled: boolean;
  defaultStatus: string;
}) {
  const [state, setState] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [receipt, setReceipt] = useState<OverrideReceipt | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!enabled || state === "submitting") return;

    setState("submitting");
    setReceipt(null);

    const form = new FormData(event.currentTarget);
    const payload = {
      actor: String(form.get("actor") ?? ""),
      new_status: String(form.get("new_status") ?? ""),
      rationale: String(form.get("rationale") ?? ""),
      missed_context: String(form.get("missed_context") ?? ""),
      expected_consequence_if_wrong: String(
        form.get("expected_consequence_if_wrong") ?? "",
      ),
    };

    try {
      const response = await fetch("/api/override", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = (await response.json()) as OverrideReceipt;
      setReceipt(body);
      setState(response.ok ? "success" : "error");
    } catch {
      setReceipt({ detail: "The local decision service could not be reached." });
      setState("error");
    }
  }

  return (
    <section className="decisionSection">
      <div className="sectionHead">
        <div>
          <p className="eyebrow">HUMAN ACCOUNTABILITY</p>
          <h2>Record the program manager&apos;s decision</h2>
        </div>
        <span className="muted">
          Local full demo only. The public hosted showcase remains read-only.
        </span>
      </div>

      <div className="decisionGrid">
        <div className="panel">
          <h3>Override the forecast assessment</h3>
          <p>
            This creates an audited human override and an unapproved learning proposal.
            It does not silently retrain the system or mutate source evidence.
          </p>

          {!enabled ? (
            <div className="decisionDisabled">
              <strong>Protected decisions are disabled.</strong>
              <p>
                Set <code>PROGRAM_OS_API_TOKEN</code> before starting the local demo.
                The token stays on the server and is never sent to the browser.
              </p>
            </div>
          ) : (
            <form className="decisionForm" onSubmit={submit}>
              <label>
                <span>Actor</span>
                <input
                  name="actor"
                  autoComplete="name"
                  maxLength={120}
                  placeholder="Program manager"
                  required
                />
              </label>

              <label>
                <span>Human status decision</span>
                <select name="new_status" defaultValue={defaultStatus}>
                  <option value="GREEN">GREEN</option>
                  <option value="AMBER">AMBER</option>
                  <option value="RED">RED</option>
                  <option value="UNKNOWN">UNKNOWN</option>
                </select>
              </label>

              <label className="decisionWide">
                <span>Rationale</span>
                <textarea
                  name="rationale"
                  rows={4}
                  maxLength={2000}
                  placeholder="Why does the human decision differ from or confirm the system assessment?"
                  required
                />
              </label>

              <label className="decisionWide">
                <span>Context the system may have missed</span>
                <textarea
                  name="missed_context"
                  rows={3}
                  maxLength={2000}
                  placeholder="Optional project-specific context."
                />
              </label>

              <label className="decisionWide">
                <span>Expected consequence if this decision is wrong</span>
                <textarea
                  name="expected_consequence_if_wrong"
                  rows={3}
                  maxLength={2000}
                  placeholder="Optional accountability statement."
                />
              </label>

              <div className="decisionWide decisionActions">
                <button type="submit" disabled={state === "submitting"}>
                  {state === "submitting" ? "Recording…" : "Record audited decision"}
                </button>
              </div>
            </form>
          )}
        </div>

        <div className="panel decisionReceipt">
          <p className="eyebrow">DECISION RECEIPT</p>
          {state === "idle" && (
            <p>
              No decision has been submitted in this browser session. Source evidence
              and the system forecast remain unchanged.
            </p>
          )}

          {state === "submitting" && <p>Recording the protected local decision…</p>}

          {state === "error" && (
            <>
              <h3>Decision was not recorded</h3>
              <p className="decisionError">{receipt?.detail ?? "Unknown error."}</p>
            </>
          )}

          {state === "success" && (
            <>
              <h3>Human decision recorded</h3>
              <dl>
                <div>
                  <dt>Status</dt>
                  <dd>{receipt?.override?.new_status ?? "Recorded"}</dd>
                </div>
                <div>
                  <dt>Override ID</dt>
                  <dd>{receipt?.override?.override_id ?? "Unavailable"}</dd>
                </div>
                <div>
                  <dt>Audit event</dt>
                  <dd>{receipt?.audit_event?.event_id ?? "Unavailable"}</dd>
                </div>
                <div>
                  <dt>Learning</dt>
                  <dd>
                    {receipt?.learning_proposal?.approved === false
                      ? "Proposed only — not approved"
                      : "No automatic behavior change"}
                  </dd>
                </div>
              </dl>
              <p className="decisionSuccess">
                The override is auditable. No source evidence was edited and no global
                model behavior was changed automatically.
              </p>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
