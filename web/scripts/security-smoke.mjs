import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

const port = 31879;
const origin = "http://127.0.0.1:" + port;
const uiToken = "security-smoke-local-ui-token-very-long-123456";
const child = spawn(process.execPath, [
  "./node_modules/next/dist/bin/next", "start",
  "--hostname", "127.0.0.1", "--port", String(port),
], {
  env: {
    ...process.env,
    PROGRAM_OS_UI_TOKEN: uiToken,
    PROGRAM_OS_API_TOKEN: "backend-only-token",
    PROGRAM_OS_API_URL: "http://127.0.0.1:39999",
    PROGRAM_OS_ALLOW_CUSTOM_DATA_API: "false",
  },
  stdio: ["ignore", "pipe", "pipe"],
});
let logs = "";
child.stdout.on("data", (chunk) => { logs += chunk.toString(); });
child.stderr.on("data", (chunk) => { logs += chunk.toString(); });

async function request(path, init = {}) {
  return fetch(origin + path, { redirect: "manual", ...init });
}
async function post(path, body, headers = {}) {
  return request(path, {
    method: "POST",
    headers: { origin, "content-type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
}

try {
  let up = false;
  for (let i = 0; i < 100; i += 1) {
    if (child.exitCode !== null) throw new Error("Next exited unexpectedly: " + logs);
    try {
      const response = await request("/login");
      if (response.status === 200) { up = true; break; }
    } catch { /* server is starting */ }
    await delay(200);
  }
  assert.ok(up, "Next did not start: " + logs);
  const page = await request("/");
  assert.ok([302, 303, 307, 308].includes(page.status), "Private root page was not redirected");
  assert.ok((page.headers.get("location") || "").includes("/login"));
  const evidence = await request("/evidence/ATLAS-101");
  assert.ok([302, 303, 307, 308].includes(evidence.status), "Private evidence page was not redirected");

  const payload = { new_status: "RED", rationale: "Controlled test only", actor: "spoofed" };
  const anonymous = await post("/api/override", payload);
  assert.equal(anonymous.status, 401, "Unauthenticated override must be blocked");
  const badLogin = await post("/api/session", { token: "incorrect" });
  assert.equal(badLogin.status, 401);
  const login = await post("/api/session", { token: uiToken });
  assert.equal(login.status, 200, "Valid local token must sign in");
  const setCookie = login.headers.get("set-cookie") || "";
  assert.match(setCookie, /httponly/i);
  assert.match(setCookie, /samesite=strict/i);
  assert.doesNotMatch(setCookie, new RegExp(uiToken));
  const cookie = setCookie.split(";")[0];

  const withSession = await post("/api/override", payload, { cookie });
  assert.equal(withSession.status, 502, "Authenticated call must reach protected backend proxy");
  const wrongOrigin = await post("/api/override", payload, { cookie, origin: "https://attacker.invalid" });
  assert.equal(wrongOrigin.status, 403, "Cross-site request must be blocked");
  const authenticatedPage = await request("/", { headers: { cookie } });
  assert.equal(authenticatedPage.status, 200);
  console.log("Local UI security smoke: PASS");
} finally {
  child.kill("SIGTERM");
  await delay(100);
}
