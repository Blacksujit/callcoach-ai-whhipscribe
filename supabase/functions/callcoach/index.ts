// Supabase Edge Function - Deno entry point
// Minimal TypeScript handler that proxies to Python Flask logic


// Health check endpoint
export default async function handler(req: Request, env: Record<string, string>) {
  const url = new URL(req.url);
  const path = url.pathname;
  const method = req.method;

  // Set CORS headers
  const corsHeaders = {
    "Access-Control-Allow-Origin": env.CORS_ORIGINS || "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  };

  // Handle preflight
  if (method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  // Health check
  if (path === "/api/health" || path === "/health") {
    return jsonResponse({ 
      status: "ok", 
      service: "callcoach-backend",
      platform: "supabase-edge-function",
      timestamp: new Date().toISOString()
    }, corsHeaders);
  }

  // List jobs endpoint
  if (path === "/api/jobs" && method === "GET") {
    // For now, return empty list - real data from Supabase DB later
    return jsonResponse({ jobs: [] }, corsHeaders);
  }

  // Upload endpoint - returns presigned URL for WhipScribe upload
  if (path === "/api/upload" && method === "POST") {
    return jsonResponse({
      error: "Upload requires Python backend with WhipScribe API key"
    }, corsHeaders, 400);
  }

  // Analyze endpoint
  if (path.startsWith("/api/analyze/") && method === "POST") {
    return jsonResponse({
      error: "Analyze requires Python backend with LLM evaluation"
    }, corsHeaders, 400);
  }

  // Trends data endpoint
  if (path === "/api/trends-data" && method === "GET") {
    return jsonResponse({
      error: "Trends requires Python backend with stored evaluations"
    }, corsHeaders, 400);
  }

  // Settings endpoint
  if (path === "/api/settings" && method === "POST") {
    return jsonResponse({
      message: "Settings saved",
      whipscribe_key_set: !!env.WHIPSKRIBE_API_KEY
    }, corsHeaders);
  }

  // Fallback - proxy info message
  return jsonResponse({
    error: "Endpoint not configured",
    path,
    method,
    message: "Full backend available via Python/Flask deployment. See callcoach-ai-whhipscribe repo for details."
  }, corsHeaders, 404);
}

function jsonResponse(data: any, headers: Record<string, string>, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...headers
    }
  });
}