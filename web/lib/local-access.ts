import { createHash, createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

export const SESSION_COOKIE = "program_os_local_session";
const MAX_SESSION_AGE = 8 * 60 * 60;

function configuredToken(): string | null {
  const token = process.env.PROGRAM_OS_UI_TOKEN;
  return token && token.length >= 32 ? token : null;
}

export function localAccessConfigured(): boolean {
  return configuredToken() !== null;
}

export function localAccessRequired(): boolean {
  // Custom-data mode always requires a local UI session, even if no token was configured.
  return Boolean(process.env.PROGRAM_OS_UI_TOKEN) ||
    (process.env.PROGRAM_OS_ALLOW_CUSTOM_DATA_API ?? "").toLowerCase() === "true";
}

export function constantTimeTokenMatch(supplied: string): boolean {
  const expected = configuredToken();
  if (!expected || supplied.length > 512) return false;
  const providedHash = createHash("sha256").update(supplied).digest();
  const expectedHash = createHash("sha256").update(expected).digest();
  return timingSafeEqual(providedHash, expectedHash);
}

export function createLocalSession(nowSeconds = Math.floor(Date.now() / 1000)): string {
  const key = configuredToken();
  if (!key) throw new Error("Local UI authentication is not configured.");
  const timestamp = String(nowSeconds);
  const signature = createHmac("sha256", key).update(timestamp).digest("hex");
  return timestamp + "." + signature;
}

export function verifyLocalSession(value: string | undefined, nowSeconds = Math.floor(Date.now() / 1000)): boolean {
  const key = configuredToken();
  if (!key || !value) return false;
  const match = /^([0-9]{10,12})\.([0-9a-f]{64})$/.exec(value);
  if (!match) return false;
  const issued = Number(match[1]);
  if (!Number.isSafeInteger(issued) || issued > nowSeconds + 30 || nowSeconds - issued > MAX_SESSION_AGE) return false;
  const expected = createHmac("sha256", key).update(match[1]).digest();
  const given = Buffer.from(match[2], "hex");
  return given.length === expected.length && timingSafeEqual(given, expected);
}

export async function localAccessGranted(): Promise<boolean> {
  if (!localAccessRequired()) return true;
  const jar = await cookies();
  return verifyLocalSession(jar.get(SESSION_COOKIE)?.value);
}

export async function protectedActionGranted(): Promise<boolean> {
  if (!localAccessConfigured()) return false;
  const jar = await cookies();
  return verifyLocalSession(jar.get(SESSION_COOKIE)?.value);
}

export function sameRequestOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return false;
  try {
    const host = request.headers.get("host");
    const parsed = new URL(origin);
    // Origin is a CSRF guard only; a forged Host/Origin pair is not authentication.
    return Boolean(host && (parsed.protocol === "http:" || parsed.protocol === "https:") && parsed.host === host);
  } catch {
    return false;
  }
}
