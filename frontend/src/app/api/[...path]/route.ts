/**
 * Catch-all API proxy route handler.
 *
 * All requests to /api/* from the frontend are forwarded to the FastAPI backend.
 * This approach:
 * - Uses a server-side runtime env var (BACKEND_URL), not a build-time one
 * - Eliminates CORS issues (browser talks to same origin)
 * - Works on Railway without special Docker build args
 * - Can use Railway internal networking
 *
 * BACKEND_URL examples:
 *   - "http://google-maps-scraper.railway.internal:8000"
 *   - "google-maps-scraper.railway.internal"  (auto-adds http:// and :8000)
 *   - "https://my-backend.up.railway.app"
 */

import { NextRequest, NextResponse } from "next/server";

function getBackendUrl(): string {
  let raw =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";

  // Trim whitespace
  raw = raw.trim();

  // Remove trailing slash
  raw = raw.replace(/\/+$/, "");

  // Add protocol if missing
  if (!raw.startsWith("http://") && !raw.startsWith("https://")) {
    raw = `http://${raw}`;
  }

  // Add default port :8000 if no port is specified and it's an internal/localhost URL
  try {
    const parsed = new URL(raw);
    // If no explicit port and it looks like an internal URL, add :8000
    if (
      !parsed.port &&
      (parsed.hostname.endsWith(".railway.internal") ||
        parsed.hostname === "localhost" ||
        parsed.hostname === "127.0.0.1")
    ) {
      parsed.port = "8000";
    }
    return parsed.origin;
  } catch {
    // If URL parsing fails, return as-is with :8000 appended
    if (!raw.includes(":", raw.indexOf("//") + 2)) {
      return `${raw}:8000`;
    }
    return raw;
  }
}

async function proxyRequest(request: NextRequest): Promise<NextResponse> {
  const backendUrl = getBackendUrl();

  // Build the target URL: keep the path and query, change the origin
  const url = new URL(request.url);
  const targetUrl = `${backendUrl}${url.pathname}${url.search}`;

  try {
    // Read the request body for methods that support it
    let body: string | undefined;
    if (request.method !== "GET" && request.method !== "HEAD") {
      try {
        body = await request.text();
      } catch {
        // No body
      }
    }

    // Forward headers, stripping hop-by-hop headers
    const headers = new Headers();
    request.headers.forEach((value, key) => {
      const hopByHop = [
        "connection",
        "keep-alive",
        "transfer-encoding",
        "te",
        "trailer",
        "upgrade",
        "host",
      ];
      if (!hopByHop.includes(key.toLowerCase())) {
        headers.set(key, value);
      }
    });

    // Make the proxied request
    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body: body || undefined,
      cache: "no-store",
    });

    // Forward the response
    const responseBody = await response.arrayBuffer();
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      const skip = ["content-encoding", "transfer-encoding", "connection"];
      if (!skip.includes(key.toLowerCase())) {
        responseHeaders.set(key, value);
      }
    });

    return new NextResponse(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : "Unknown error";
    console.error(
      `[API Proxy] Failed to reach backend at ${targetUrl}: ${errMsg}`
    );
    console.error(
      `[API Proxy] BACKEND_URL env = "${process.env.BACKEND_URL || "(not set)"}"`
    );
    console.error(`[API Proxy] Resolved backend URL = "${backendUrl}"`);

    return NextResponse.json(
      {
        detail:
          `Nu s-a putut contacta serverul backend la ${targetUrl}. ` +
          `Verificați: (1) serviciul backend rulează, ` +
          `(2) BACKEND_URL="${process.env.BACKEND_URL || "(nesetat)"}" este corect, ` +
          `(3) portul 8000 este accesibil.`,
        resolved_url: targetUrl,
        backend_env: process.env.BACKEND_URL || null,
        error: errMsg,
      },
      { status: 502 }
    );
  }
}

export async function GET(request: NextRequest) {
  return proxyRequest(request);
}

export async function POST(request: NextRequest) {
  return proxyRequest(request);
}

export async function PUT(request: NextRequest) {
  return proxyRequest(request);
}

export async function PATCH(request: NextRequest) {
  return proxyRequest(request);
}

export async function DELETE(request: NextRequest) {
  return proxyRequest(request);
}
