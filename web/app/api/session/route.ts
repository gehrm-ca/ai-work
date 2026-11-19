import { NextRequest, NextResponse } from "next/server";
import {
  SESSION_COOKIE,
  constantTimeTokenMatch,
  createLocalSession,
  localAccessConfigured,
  sameRequestOrigin,
} from "../../../lib/local-access";

export const dynamic = "force-dynamic";

const attempts = new Map<string, { count: number; until: number }>();
const WINDOW_MS = 15 * 60 * 1000;
const LIMIT = 5;

export async function POST(request: NextRequest) {
  if (!sameRequestOrigin(request)) {
    return NextResponse.json({ detail: "Invalid request origin." }, { status: 403 });
  }
  if (!localAccessConfigured()) {
    return NextResponse.json({ detail: "A secure PROGRAM_OS_UI_TOKEN (32+ characters) is required." }, { status: 503 });
  }
  const key = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  // In-process throttling is defense in depth for localhost only; never trust a forwarded IP for public security.
  const now = Date.now();
  const prior = attempts.get(key);
  const entry = prior && prior.until > now ? prior : { count: 0, until: now + WINDOW_MS };
  if (entry.count >= LIMIT) {
    return NextResponse.json({ detail: "Too many attempts." }, { status: 429 });
  }
  let supplied: unknown;
  try {
    const body = await request.json();
    supplied = body?.token;
  } catch {
    supplied = null;
  }
  if (typeof supplied !== "string" || !constantTimeTokenMatch(supplied)) {
    attempts.set(key, { count: entry.count + 1, until: entry.until });
    return NextResponse.json({ detail: "Invalid access token." }, { status: 401 });
  }
  attempts.delete(key);
  const response = NextResponse.json({ authenticated: true });
  response.cookies.set(SESSION_COOKIE, createLocalSession(), {
    httpOnly: true,
    sameSite: "strict",
    secure: request.nextUrl.protocol === "https:",
    path: "/",
    maxAge: 8 * 60 * 60,
  });
  return response;
}

export async function DELETE(request: NextRequest) {
  if (!sameRequestOrigin(request)) {
    return NextResponse.json({ detail: "Invalid request origin." }, { status: 403 });
  }
  const response = NextResponse.json({ authenticated: false });
  response.cookies.delete(SESSION_COOKIE);
  return response;
}
