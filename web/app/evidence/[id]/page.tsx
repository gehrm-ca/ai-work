import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

type EvidenceRecord = {
  evidence_id: string;
  source_type: string;
  source_id: string;
  project_id: string;
  source_updated_at: string;
  retrieved_at: string;
  authority_tier: number;
  payload: Record<string, unknown>;
};

async function getEvidence(id: string): Promise<EvidenceRecord | null> {
  const base = process.env.PROGRAM_OS_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(
      `${base}/atlas/evidence/${encodeURIComponent(id)}`,
      { cache: "no-store" },
    );
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Evidence API returned ${response.status}`);
    return await response.json();
  } catch {
    return null;
  }
}

function evidenceTitle(record: EvidenceRecord): string {
  const payload = record.payload;
  const value = payload.title ?? payload.summary ?? payload.cycle;
  return typeof value === "string" ? value : record.evidence_id;
}

export default async function EvidencePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const record = await getEvidence(id);
  if (!record) notFound();

  return (
    <main className="shell evidencePage">
      <a className="backLink" href="/">← Back to Atlas control view</a>

      <header className="evidenceHero">
        <div>
          <p className="eyebrow">IMMUTABLE EVIDENCE / {record.evidence_id}</p>
          <h1>{evidenceTitle(record)}</h1>
          <p className="lede">
            This is the source observation Program OS used. The underlying evidence is
            preserved separately from later assessments, recommendations, and overrides.
          </p>
        </div>
      </header>

      <section className="evidenceMetaGrid">
        <div><span>Source</span><strong>{record.source_type}</strong></div>
        <div><span>Project</span><strong>{record.project_id.toUpperCase()}</strong></div>
        <div><span>Authority tier</span><strong>{record.authority_tier}</strong></div>
        <div><span>Source object</span><strong>{record.source_id}</strong></div>
        <div><span>Source updated</span><strong>{record.source_updated_at}</strong></div>
        <div><span>Retrieved</span><strong>{record.retrieved_at}</strong></div>
      </section>

      <section>
        <div className="sectionHead">
          <div>
            <p className="eyebrow">OBSERVED PAYLOAD</p>
            <h2>What the source said</h2>
          </div>
          <span className="muted">
            Synthetic Atlas data. No customer or employer data is shown.
          </span>
        </div>
        <pre className="evidencePayload">{JSON.stringify(record.payload, null, 2)}</pre>
      </section>
    </main>
  );
}
