import { NextResponse } from "next/server";
import { protectedActionGranted, sameRequestOrigin } from "../../../lib/local-access";

export const dynamic = "force-dynamic";

const ALLOWED_RAG = new Set(["GREEN", "AMBER", "RED", "UNKNOWN"]);

function cleanOptional(value: unknown, maxLength: number): string | null {
  if (value === undefined || value === null || value === "") return null;
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed ? trimmed.slice(0, maxLength) : null;
}

export async function POST(request: Request) {
  if (!sameRequestOrigin(request)) {
    return NextResponse.json(
      { detail: "Human-decision requests must originate from the local Program OS UI." },
      { status: 403 },
    );
  }

  if (!(await protectedActionGranted())) {
    return NextResponse.json({ detail: "An authenticated local UI session is required." }, { status: 401 });
  }

  const token = process.env.PROGRAM_OS_API_TOKEN;
  if (!token) {
    return NextResponse.json(
      {
        detail:
          "Protected local decisions are disabled. Configure PROGRAM_OS_API_TOKEN and restart the demo.",
      },
      { status: 503 },
    );
  }

  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Request body must be valid JSON." }, { status: 400 });
  }

  const rationale = typeof body.rationale === "string" ? body.rationale.trim() : "";
  const newStatus = typeof body.new_status === "string" ? body.new_status : "";

  if (!rationale || rationale.length > 2000) {
    return NextResponse.json(
      { detail: "Rationale is required and must be 2000 characters or fewer." },
      { status: 400 },
    );
  }
  if (!ALLOWED_RAG.has(newStatus)) {
    return NextResponse.json({ detail: "new_status must be a valid RAG value." }, { status: 400 });
  }

  const payload = {
    actor: "local-authenticated-operator",
    assessment_id: "atlas-portfolio",
    new_status: newStatus,
    rationale,
    missed_context: cleanOptional(body.missed_context, 2000),
    exception_type: "one_time_exception",
    expected_consequence_if_wrong: cleanOptional(
      body.expected_consequence_if_wrong,
      2000,
    ),
  };

  const apiBase = process.env.PROGRAM_OS_API_URL ?? "http://127.0.0.1:8000";
  try {
    const upstream = await fetch(`${apiBase}/atlas/override`, {
      method: "POST",
      headers: {
        authorization: `Bearer ${token}`,
        "content-type": "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });

    let responseBody: unknown;
    try {
      responseBody = await upstream.json();
    } catch {
      responseBody = {
        detail: `Program OS API returned HTTP ${upstream.status} without JSON.`,
      };
    }

    return NextResponse.json(responseBody, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { detail: "The local Program OS API could not be reached." },
      { status: 502 },
    );
  }
}
