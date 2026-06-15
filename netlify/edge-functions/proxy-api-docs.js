import { DOMParser } from "https://deno.land/x/deno_dom@v0.1.56/deno-dom-wasm.ts";

export default async (request, context) => {
  const url = new URL(request.url);
  const originalOrigin = url.origin;

  // Frame/partial requests (for example, ?partial=true) return HTML fragments,
  // not the full document. They must never share a CDN cache entry with the
  // root page, or a cached fragment gets served as the root document (and vice
  // versa). Handled by the cache-control / Netlify-Vary headers on the HTML
  // response below.
  const isPartialRequest = url.searchParams.has("partial");

  // Redirects from old API paths to new ones
  const redirects = {
    "/api/doc": "/api",
    "/api/admin-api": "/api/doc/admin/",
    "/api/http-proxy-api": "/api/doc/http-proxy/",
    "/api/schema-registry-api": "/api/doc/schema-registry/",
    "/api/cloud-controlplane-api": "/api/doc/cloud-controlplane/",
    "/api/cloud-dataplane-api": "/api/doc/cloud-dataplane/",
    "/api/cloud-api": "/api/doc/cloud-controlplane/",
  };

  const normalizedPath = url.pathname.endsWith("/")
    ? url.pathname.slice(0, -1)
    : url.pathname;

  if (redirects[normalizedPath]) {
    return Response.redirect(`${url.origin}${redirects[normalizedPath]}`, 301);
  }

  // Content negotiation: redirect to .md URL if markdown is explicitly requested
  // Only match text/markdown per agent-friendly docs spec (text/plain is too broad)
  const acceptHeader = request.headers.get('accept') || '';
  const wantsMarkdown = acceptHeader.includes('text/markdown');

  if (wantsMarkdown && !url.pathname.endsWith('.md')) {
    // Construct markdown URL - append .md to the path
    const mdPath = normalizedPath + '.md';
    return Response.redirect(`${url.origin}${mdPath}`, 302);
  }

  // Map paths to header background colors (8% component color mixed with white)
  const headerColors = {
    "/api/doc/admin": "color-mix(in srgb, #9F1239 8%, white)",              // self-managed (rose)
    "/api/doc/cloud-controlplane": "color-mix(in srgb, #1D4ED8 8%, white)", // cloud (blue)
    "/api/doc/cloud-dataplane": "color-mix(in srgb, #1D4ED8 8%, white)",    // cloud (blue)
  };

  const matchedPath = Object.keys(headerColors).find((path) =>
    normalizedPath.startsWith(path)
  );
  const headerColor = headerColors[matchedPath] || "color-mix(in srgb, #1D4ED8 8%, white)"; // default to cloud

  // Build the proxied Bump.sh URL
  const bumpUrl = new URL(request.url);
  bumpUrl.host = "bump.sh";
  bumpUrl.pathname = `/redpanda/hub/redpanda${bumpUrl.pathname.replace("/api", "")}`;

  const secret = Netlify.env.get("BUMP_PROXY_SECRET");

  // Validate secret exists
  if (!secret) {
    console.error("❌ BUMP_PROXY_SECRET environment variable not set");
    return new Response("Service temporarily unavailable", {
      status: 503,
      headers: {
        "content-type": "text/plain; charset=utf-8",
        "cache-control": "public, max-age=60",
      }
    });
  }

  try {
    const bumpRes = await fetchWithRetry(bumpUrl, {
      headers: {
        "X-BUMP-SH-PROXY": secret,
        "X-BUMP-SH-EMBED": "true",
        "User-Agent": "Redpanda-Docs-Proxy/1.0",
      },
    });

    // Handle non-successful responses
    if (!bumpRes.ok) {
      console.error(`❌ Bump.sh returned ${bumpRes.status}: ${bumpRes.statusText}`);
      throw new Error(`Bump.sh API error: ${bumpRes.status}`);
    }

    const contentType = bumpRes.headers.get("content-type") || "";

  if (!contentType.includes("text/html")) {
    // If requesting .md file, ensure correct content-type for markdown
    if (url.pathname.endsWith('.md')) {
      const body = await bumpRes.text();
      return new Response(body, {
        status: bumpRes.status,
        headers: {
          "content-type": "text/markdown; charset=utf-8",
          "cache-control": bumpRes.headers.get("cache-control") || "public, max-age=300",
        },
      });
    }
    return bumpRes;
  }

  // Load Bump.sh page and widgets
  const [
    originalHtml,
    headScript,
    headerWidget,
    footerWidget,
    chatPanelWidget,
  ] = await Promise.all([
    bumpRes.text(),
    fetchWidget(`${originalOrigin}/assets/widgets/head-bump.html`, "head-bump"),
    fetchWidget(`${originalOrigin}/assets/widgets/header.html`, "header"),
    fetchWidget(`${originalOrigin}/assets/widgets/footer.html`, "footer"),
    fetchWidget(`${originalOrigin}/assets/widgets/chat-panel-bump.html`, "chat-panel"),
  ]);

  let document;
  try {
    document = new DOMParser().parseFromString(originalHtml, "text/html");
  } catch (error) {
    console.error("❌ Failed to initialize DOMParser (WASM issue):", error);
    // Return unmodified HTML if DOM parsing fails
    return new Response(originalHtml, {
      status: 200,
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  }

  if (!document) {
    console.error("❌ Failed to parse Bump.sh HTML.");
    return new Response(originalHtml, {
      status: 200,
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  }

  // Inject head script
  const head = document.querySelector("head");
  if (head && headScript) {
    const temp = document.createElement("div");
    temp.innerHTML = headScript;
    for (const node of temp.childNodes) {
      head.appendChild(node);
    }
  }

  // Inject header with dynamic background color
  const topBody = document.querySelector("#embed-top-body");
  if (topBody && headerWidget) {
    // Add background color to the navbar element
    const coloredHeader = headerWidget.replace(
      /<nav([^>]*class="[^"]*navbar[^"]*")/,
      `<nav$1 style="background-color: ${headerColor};"`
    );

    const wrapper = document.createElement("div");
    wrapper.innerHTML = coloredHeader;
    while (wrapper.firstChild) {
      topBody.appendChild(wrapper.firstChild);
    }
  }

  // Inject footer
  const bottomBody = document.querySelector("#embed-bottom-body");
  if (bottomBody && footerWidget) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = footerWidget;
    while (wrapper.firstChild) {
      bottomBody.appendChild(wrapper.firstChild);
    }
  }

  // Inject chat panel (Ask AI drawer)
  if (bottomBody && chatPanelWidget) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = chatPanelWidget;
    while (wrapper.firstChild) {
      bottomBody.appendChild(wrapper.firstChild);
    }
  }

  // Inject llms.txt directive for AI agent discovery
  const body = document.querySelector("body");
  if (body) {
    // Create llms directive HTML - using same approach as header/footer injection
    const directiveHtml = `<blockquote class="llms-directive" tabindex="-1" aria-hidden="true"><p>For the complete documentation index, see <a href="/llms.txt" tabindex="-1" aria-hidden="true">llms.txt</a>. Component-specific: <a href="/api-full.txt" tabindex="-1" aria-hidden="true">api-full.txt</a></p></blockquote>`;

    // Insert directive at the beginning of body - same pattern as footer injection
    const wrapper = document.createElement("div");
    wrapper.innerHTML = directiveHtml;

    // Insert all child nodes from wrapper at start of body
    const firstChild = body.firstChild;
    while (wrapper.firstChild) {
      body.insertBefore(wrapper.firstChild, firstChild);
    }

    // Add CSS to visually hide the directive
    if (head) {
      const style = document.createElement("style");
      style.textContent = ".llms-directive{position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden}";
      head.appendChild(style);
    }

    // Inject CSS fixes for chat panel and dark mode on Bump.sh pages
    if (head) {
      const fixStyle = document.createElement("style");
      fixStyle.textContent = `
        /* Fix chat panel top offset - account for fixed navbar */
        .chat-panel { top: var(--navbar-height, 70px) !important; height: calc(100vh - var(--navbar-height, 70px)) !important; }

        /* Fix chat head icons - ensure SVGs are visible */
        .chat-head-btn svg { stroke: currentColor !important; }
        .chat-head-icon svg { fill: currentColor !important; }

        /* Dark mode fixes using html[data-theme="dark"] selector (Bump pages use this, not .dark-theme) */
        html[data-theme="dark"] .navbar { background: #0f172a !important; }
        html[data-theme="dark"] .chat-panel { background: #1a2332 !important; color: #e8eef6 !important; border-left-color: rgba(255,255,255,0.08) !important; }
        html[data-theme="dark"] .chat-head { border-bottom-color: rgba(255,255,255,0.08) !important; }
        html[data-theme="dark"] .chat-head-name { color: #e8eef6 !important; }
        html[data-theme="dark"] .chat-head-sub { color: #7c8ca8 !important; }
        html[data-theme="dark"] .chat-head-btn { color: #7c8ca8 !important; }
        html[data-theme="dark"] .chat-head-btn:hover { background: rgba(255,255,255,0.05) !important; color: #e8eef6 !important; }
        html[data-theme="dark"] .chat-foot { color: #7c8ca8 !important; border-top-color: rgba(255,255,255,0.08) !important; }
        html[data-theme="dark"] #chat-panel-kapa-root { color: #e8eef6 !important; }
        html[data-theme="dark"] #chat-panel-kapa-root .welcome-icon { background: linear-gradient(135deg, #312e81 0%, #3730a3 100%) !important; color: #a5b4fc !important; }
        html[data-theme="dark"] #chat-panel-kapa-root .welcome-title { color: #e8eef6 !important; }
        html[data-theme="dark"] #chat-panel-kapa-root .welcome-description { color: #7c8ca8 !important; }
        html[data-theme="dark"] #chat-panel-kapa-root .suggestion-card { background: #232f3e !important; border-color: rgba(255,255,255,0.1) !important; color: #aab8ca !important; }
        html[data-theme="dark"] #chat-panel-kapa-root .suggestion-card:hover { background: #2a3a4d !important; border-color: rgba(255,255,255,0.15) !important; color: #e8eef6 !important; }
        html[data-theme="dark"] #chat-panel-kapa-root .chat-input-wrapper { background: #232f3e !important; border-color: rgba(255,255,255,0.1) !important; }
        html[data-theme="dark"] #chat-panel-kapa-root .chat-input-wrapper .chat-input { background: transparent !important; color: #e8eef6 !important; }
        html[data-theme="dark"] #chat-panel-kapa-root .disclaimer { color: #7c8ca8 !important; background: #1a2332 !important; }
      `.replace(/\s+/g, ' ').trim();
      head.appendChild(fixStyle);
    }
  }

  const htmlOutput = document.documentElement?.outerHTML || originalHtml;
  return new Response(htmlOutput, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      // Vary the CDN cache key on the query string so frame/partial requests
      // can never collide with the root document. Additionally, don't store
      // partial fragments in the shared cache at all (defense in depth).
      "cache-control": isPartialRequest ? "no-store" : "public, max-age=300", // root docs: cache 5 minutes
      "netlify-vary": "query",
    },
  });

  } catch (error) {
    console.error("❌ Failed to fetch from Bump.sh after retries:", error);

    // Return a graceful fallback response with short cache to avoid hammering
    return new Response(
      `<html><head><title>API Documentation Temporarily Unavailable</title></head><body><h1>API Documentation Temporarily Unavailable</h1><p>Please try again later.</p></body></html>`,
      {
        status: 503,
        headers: {
          "content-type": "text/html; charset=utf-8",
          "cache-control": "public, max-age=60", // Cache errors briefly to reduce load
        }
      }
    );
  }
};

// Fetch with retry logic and exponential backoff
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        ...options,
        signal: AbortSignal.timeout(10000), // 10 second timeout
      });
      return response;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      console.warn(`Attempt ${attempt} failed for ${url}:`, errorMsg);

      if (attempt === maxRetries) {
        throw error;
      }

      // Exponential backoff: wait 2^attempt seconds
      const delay = Math.pow(2, attempt) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

// Helper function to fetch widget content with fallback
async function fetchWidget(url, label) {
  try {
    const res = await fetchWithRetry(url, {}, 2); // 2 retries for widgets
    if (res.ok) return await res.text();
    console.warn(`⚠️ Failed to load ${label} widget from ${url}`);
    return "";
  } catch (err) {
    console.error(`❌ Error fetching ${label} widget:`, err);
    return "";
  }
}
