/**
 * Catch-all API proxy route handler.
 *
 * All requests to /api/* from the frontend are forwarded to the FastAPI backend.
 * This approach:
 * - Uses a server-side runtime env var (BACKEND_URL), not a build-time one
 * - Eliminates CORS issues (browser talks to same origin)
 * - Works on Railway without special Docker build args
 * - Can use Railway internal networking (e.g. http://backend.railway.internal:8000)
 */

import { NextRequest, NextResponse } from "next/server";

function getBackendUrl(): string {
  // BACKEND_URL is a server-side env var (not NEXT_PUBLIC_), read at runtime.
  // On Railway, set this to the internal URL: http://google-maps-scraper.railway.internal:8000
  return (
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000"
  );
}

async function proxyRequest(request: NextRequest): Promise<NextResponse> {
  const backendUrl = getBackendUrl();

  // Build the target URL: replace the origin but keep the path and query
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
    console.error(`[API Proxy] Error forwarding to ${targetUrl}:`, error);
    return NextResponse.json(
      {
        detail: `Nu s-a putut contacta serverul backend. Verificați dacă serviciul backend rulează. (${backendUrl})`,
        error: error instanceof Error ? error.message : "Unknown error",
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
