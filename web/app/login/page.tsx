"use client";

import { FormEvent, useState } from "react";

export default function Login() {
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      const result = await fetch("/api/session", {
        method: "POST",
        headers: { "content-type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ token: data.get("token") }),
      });
      if (!result.ok) {
        const body = (await result.json()) as { detail?: string };
        setError(body.detail || "Authentication failed.");
        return;
      }
      window.location.replace("/");
    } catch {
      setError("Authentication service unavailable.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="shell">
      <h1>Local Program OS access</h1>
      <p>Enter the separate PROGRAM_OS_UI_TOKEN configured on your local server.
        This prototype is not enterprise SSO and must not be published on the internet.</p>
      <form onSubmit={login} className="panel">
        <label htmlFor="token">Local UI access token</label>
        <input id="token" name="token" type="password" autoComplete="off" required minLength={32} />
        <button type="submit" disabled={submitting}>{submitting ? "Checking…" : "Unlock local preview"}</button>
        {error && <p role="alert">{error}</p>}
      </form>
    </main>
  );
}
