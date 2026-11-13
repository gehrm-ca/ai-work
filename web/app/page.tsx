export const dynamic = "force-dynamic";

type DemoPayload = {
  evidence_count: number;
  monday_actions: Array<{
    action_id: string;
    issue_or_risk: string;
    project_id: string;
    impact: string;
    probability: string;
    next_step: string;
    priority_score: number;
    evidence_ids: string[];
  }>;
  signals: Array<{
    kind: string;
    project_id: string;
    severity: string;
    summary: string;
    evidence_ids: string[];
  }>;
  recommendation: null | {
    action: string;
    expected_benefit: string;
    downstream_consequences: string[];
    confidence: string;
    evidence_ids: string[];
  };
  friday_status: {
    official_rag: string;
    forecast_rag: string;
    confidence: string;
    trend: string;
    launch_date: string;
    top_risks: string[];
    contradictions: string[];
    next_milestone: string;
    budget_tracking: string;
    summary: string;
  };
};

async function getDemo(): Promise<DemoPayload | null> {
  const base = process.env.PROGRAM_OS_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${base}/atlas/demo`, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

function Rag({ value }: { value: string }) {
  return <span className={`rag rag-${value.toLowerCase()}`}>{value}</span>;
}

export default async function Home() {
  const data = await getDemo();

  if (!data) {
    return (
      <main className="shell">
        <p className="eyebrow">PROGRAM OS / V2</p>
        <h1>Atlas portfolio control</h1>
        <div className="panel">
          API unavailable. Start the FastAPI service on port 8000, then reload.
        </div>
      </main>
    );
  }

  const status = data.friday_status;

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">PROGRAM OS / ATLAS LAUNCH PROGRAM</p>
          <h1>The dashboard says GREEN. The evidence does not.</h1>
          <p className="lede">
            {data.evidence_count} immutable evidence records reconciled across delivery,
            risk, quality, scope, resource, decision, and executive-status sources.
          </p>
        </div>
        <div className="statusCard">
          <div><span>Official</span><Rag value={status.official_rag} /></div>
          <div><span>Forecast</span><Rag value={status.forecast_rag} /></div>
          <div><span>Confidence</span><strong>{status.confidence}</strong></div>
          <div><span>Trend</span><strong>{status.trend}</strong></div>
        </div>
      </header>

      <section>
        <div className="sectionHead">
          <div><p className="eyebrow">MONDAY</p><h2>Intervention queue</h2></div>
          <span className="muted">Criticality × probability × impact × time sensitivity</span>
        </div>
        <div className="actions">
          {data.monday_actions.map((action, index) => (
            <article className="action" key={action.action_id}>
              <div className="rank">{String(index + 1).padStart(2, "0")}</div>
              <div>
                <div className="actionMeta">
                  <span>{action.project_id}</span>
                  <span>Impact {action.impact}</span>
                  <span>P {action.probability}</span>
                  <span>Score {action.priority_score.toFixed(3)}</span>
                </div>
                <h3>{action.issue_or_risk}</h3>
                <p>{action.next_step}</p>
                <p className="evidence">Evidence: {action.evidence_ids.join(", ")}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="grid2">
        <article className="panel">
          <p className="eyebrow">PORTFOLIO TRADEOFF</p>
          <h2>{data.recommendation?.action ?? "No intervention generated"}</h2>
          <p>{data.recommendation?.expected_benefit}</p>
          <ul>
            {data.recommendation?.downstream_consequences.map((item) => <li key={item}>{item}</li>)}
          </ul>
          <p className="evidence">Evidence: {data.recommendation?.evidence_ids.join(", ")}</p>
        </article>

        <article className="panel">
          <p className="eyebrow">THURSDAY / FRIDAY</p>
          <h2>Evidence-backed status</h2>
          <p>{status.summary}</p>
          <dl>
            <div><dt>Launch</dt><dd>{status.launch_date}</dd></div>
            <div><dt>Next milestone</dt><dd>{status.next_milestone}</dd></div>
            <div><dt>Budget</dt><dd>{status.budget_tracking}</dd></div>
          </dl>
        </article>
      </section>

      <section>
        <div className="sectionHead">
          <div><p className="eyebrow">TRUST CONTRACT</p><h2>Signals and contradictions</h2></div>
        </div>
        <div className="signalGrid">
          {data.signals.map((signal) => (
            <article className="signal" key={signal.kind}>
              <span className="pill">{signal.project_id}</span>
              <h3>{signal.kind.replaceAll("_", " ")}</h3>
              <p>{signal.summary}</p>
              <p className="evidence">{signal.evidence_ids.join(", ")}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
