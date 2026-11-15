const esc = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const rag = (value) =>
  `<span class="rag rag-${esc(String(value).toLowerCase())}">${esc(value)}</span>`;

async function loadDemo() {
  const response = await fetch("./atlas-demo.json", { cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
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
          <span>${esc(a.project_id)}</span>
          <span>Impact ${esc(a.impact)}</span>
          <span>P ${esc(a.probability)}</span>
          <span>Score ${Number(a.priority_score).toFixed(3)}</span>
        </div>
        <h3>${esc(a.issue_or_risk)}</h3>
        <p>${esc(a.next_step)}</p>
        <p class="evidence">Evidence: ${a.evidence_ids.map(esc).join(", ")}</p>
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
    <p class="evidence">Evidence: ${r.evidence_ids.map(esc).join(", ")}</p>
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
  `;
}

function renderSignals(data) {
  document.getElementById("signals").innerHTML = data.signals.map((s) => `
    <article class="signal">
      <span class="pill">${esc(s.project_id)}</span>
      <h3>${esc(s.kind.replaceAll("_", " "))}</h3>
      <p>${esc(s.summary)}</p>
      <p class="evidence">${s.evidence_ids.map(esc).join(", ")}</p>
    </article>
  `).join("");
}

loadDemo()
  .then((data) => {
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
