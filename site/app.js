const esc = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const rag = (value) =>
  `<span class="rag rag-${esc(String(value).toLowerCase())}">${esc(value)}</span>`;

let evidenceById = new Map();

async function loadDemo() {
  const response = await fetch("./atlas-demo.json", { cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function evidenceLinks(ids, { prefix = "Evidence: " } = {}) {
  if (!ids?.length) return "";
  return `<span class="evidence-label">${esc(prefix)}</span>${ids.map((id) =>
    `<button class="evidence-link" type="button" data-evidence-id="${esc(id)}">${esc(id)}</button>`
  ).join('<span class="evidence-separator"> · </span>')}`;
}

function trustDetails(reasoningFactors = [], whatWouldChange = []) {
  if (!reasoningFactors.length && !whatWouldChange.length) return "";
  const list = (items) => items.map((item) => `<li>${esc(item)}</li>`).join("");
  return `
    <details class="trust-details">
      <summary>Why this conclusion · what would change it</summary>
      <div class="trust-detail-grid">
        <div>
          <span>Reasoning factors</span>
          <ul>${list(reasoningFactors)}</ul>
        </div>
        <div>
          <span>What would change it</span>
          <ul>${list(whatWouldChange)}</ul>
        </div>
      </div>
    </details>
  `;
}

function evidenceTitle(record) {
  const payload = record?.payload ?? {};
  return payload.title ?? payload.summary ?? payload.cycle ?? record.evidence_id;
}

function renderEvidenceDetail(record) {
  const dialog = document.getElementById("evidence-dialog");
  const detail = document.getElementById("evidence-detail");
  if (!dialog || !detail) return;

  const payload = JSON.stringify(record.payload ?? {}, null, 2);
  detail.innerHTML = `
    <p class="eyebrow">IMMUTABLE EVIDENCE / ${esc(record.evidence_id)}</p>
    <h2>${esc(evidenceTitle(record))}</h2>
    <div class="evidence-meta-grid">
      <div><span>Source</span><strong>${esc(record.source_type)}</strong></div>
      <div><span>Project</span><strong>${esc(String(record.project_id).toUpperCase())}</strong></div>
      <div><span>Authority tier</span><strong>${esc(record.authority_tier)}</strong></div>
      <div><span>Source updated</span><strong>${esc(record.source_updated_at)}</strong></div>
      <div><span>Retrieved</span><strong>${esc(record.retrieved_at)}</strong></div>
      <div><span>Source object</span><strong>${esc(record.source_id)}</strong></div>
    </div>
    <div class="evidence-payload">
      <span>Observed payload</span>
      <pre>${esc(payload)}</pre>
    </div>
    <p class="fine-print evidence-note">
      Atlas is synthetic. This view shows the immutable observation used by Program OS;
      interpretation and recommendations remain separate records.
    </p>
  `;

  if (typeof dialog.showModal === "function") {
    dialog.showModal();
  } else {
    dialog.setAttribute("open", "");
  }
}

function renderStatus(data) {
  const s = data.friday_status;
  document.getElementById("evidence-count").textContent = data.evidence_count;
  document.getElementById("status-card").innerHTML = `
    <div class="status-row"><span>Official RAG</span>${rag(s.official_rag)}</div>
    <div class="status-row"><span>Forecast RAG</span>${rag(s.forecast_rag)}</div>
    <div class="status-row"><span>Confidence</span><strong>${esc(s.confidence)}</strong></div>
    <div class="status-row"><span>Trend</span><strong>${esc(s.trend)}</strong></div>
  `;
}

function renderActions(data) {
  const el = document.getElementById("actions");
  el.innerHTML = data.monday_actions.map((a, index) => `
    <article class="action">
      <div class="rank">${String(index + 1).padStart(2, "0")}</div>
      <div>
        <div class="meta">
          <span>${esc(String(a.project_id).toUpperCase())}</span>
          <span>Impact ${esc(a.impact)}</span>
          <span>Probability ${esc(a.probability)}</span>
          <span>Score ${Number(a.priority_score).toFixed(3)}</span>
        </div>
        <h3>${esc(a.issue_or_risk)}</h3>
        <p>${esc(a.next_step)}</p>
        <p class="evidence">${evidenceLinks(a.evidence_ids)}</p>
        ${trustDetails(a.reasoning_factors, a.what_would_change)}
      </div>
    </article>
  `).join("");
}

function renderTradeoff(data) {
  const r = data.recommendation;
  const el = document.getElementById("tradeoff");
  if (!r) {
    el.innerHTML = '<p class="eyebrow">PORTFOLIO TRADEOFF</p><p>No intervention generated.</p>';
    return;
  }
  el.innerHTML = `
    <p class="eyebrow">PORTFOLIO TRADEOFF</p>
    <h2>${esc(r.action)}</h2>
    <p>${esc(r.expected_benefit)}</p>
    <ul>${r.downstream_consequences.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
    <p class="evidence">${evidenceLinks(r.evidence_ids)}</p>
    ${trustDetails(r.reasoning_factors, r.what_would_change)}
  `;
}

function renderFriday(data) {
  const s = data.friday_status;
  document.getElementById("friday").innerHTML = `
    <p class="eyebrow">THURSDAY / FRIDAY</p>
    <h2>Evidence-backed status</h2>
    <p>${esc(s.summary)}</p>
    <dl class="status-list">
      <div><dt>Launch</dt><dd>${esc(s.launch_date)}</dd></div>
      <div><dt>Next milestone</dt><dd>${esc(s.next_milestone)}</dd></div>
      <div><dt>Budget</dt><dd>${esc(s.budget_tracking)}</dd></div>
      <div><dt>Forecast</dt><dd>${esc(s.forecast_rag)} / ${esc(s.confidence)}</dd></div>
    </dl>
    ${trustDetails(s.reasoning_factors, s.what_would_change)}
  `;
}

function renderSignals(data) {
  document.getElementById("signals").innerHTML = data.signals.map((s) => `
    <article class="signal">
      <span class="pill">${esc(String(s.project_id).toUpperCase())}</span>
      <h3>${esc(s.kind.replaceAll("_", " "))}</h3>
      <p>${esc(s.summary)}</p>
      <p class="evidence">${evidenceLinks(s.evidence_ids, { prefix: "" })}</p>
      ${trustDetails(s.reasoning_factors, s.what_would_change)}
    </article>
  `).join("");
}

document.addEventListener("click", (event) => {
  const target = event.target.closest?.("[data-evidence-id]");
  if (!target) return;
  const record = evidenceById.get(target.dataset.evidenceId);
  if (record) renderEvidenceDetail(record);
});

loadDemo()
  .then((data) => {
    evidenceById = new Map(
      (data.evidence_records ?? []).map((record) => [record.evidence_id, record])
    );
    renderStatus(data);
    renderActions(data);
    renderTradeoff(data);
    renderFriday(data);
    renderSignals(data);
  })
  .catch((error) => {
    const message = `Could not load deterministic demo data: ${esc(error.message)}`;
    document.getElementById("status-card").innerHTML = `<p class="error">${message}</p>`;
    document.getElementById("actions").innerHTML = `<p class="error">${message}</p>`;
  });
