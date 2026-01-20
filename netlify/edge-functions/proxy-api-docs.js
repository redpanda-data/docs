import { DOMParser } from "https://deno.land/x/deno_dom@v0.1.56/deno-dom-wasm.ts";

export default async (request, context) => {
  const url = new URL(request.url);
  const originalOrigin = url.origin;

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

  // Map paths to header background colors
  const headerColors = {
    "/api/doc/admin": "#107569",
    "/api/doc/cloud-controlplane": "#014F86",
    "/api/doc/cloud-dataplane": "#014F86",
  };

  const matchedPath = Object.keys(headerColors).find((path) =>
    normalizedPath.startsWith(path)
  );
  const headerColor = headerColors[matchedPath] || "#d73d23";

  // Build the proxied Bump.sh URL
  const bumpUrl = new URL(request.url);
  bumpUrl.host = "bump.sh";
  bumpUrl.pathname = `/redpanda/hub/redpanda${bumpUrl.pathname.replace("/api", "")}`;

  const secret = Netlify.env.get("BUMP_PROXY_SECRET");

  // Validate secret exists
  if (!secret) {
    console.error("❌ BUMP_PROXY_SECRET environment variable not set");
    return new Response("Service temporarily unavailable", { status: 503 });
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
    return bumpRes;
  }

  // Load Bump.sh page and widgets
  const [
    originalHtml,
    headScript,
    headerWidget,
    footerWidget,
  ] = await Promise.all([
    bumpRes.text(),
    fetchWidget(`${originalOrigin}/assets/widgets/head-bump.html`, "head-bump"),
    fetchWidget(`${originalOrigin}/assets/widgets/header.html`, "header"),
    fetchWidget(`${originalOrigin}/assets/widgets/footer.html`, "footer"),
  ]);

  const document = new DOMParser().parseFromString(originalHtml, "text/html");
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
    const coloredHeader = headerWidget.replace(
      /(<nav[^>]*style="[^"]*background-color:\s*)#[^";]+/,
      `$1${headerColor}`
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

  return new Response(document.documentElement.outerHTML, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "public, max-age=300", // Cache for 5 minutes
    },
  });

  } catch (error) {
    console.error("❌ Failed to fetch from Bump.sh after retries:", error);

    // Return a graceful fallback response
    return new Response(
      `<html><head><title>API Documentation Temporarily Unavailable</title></head><body><h1>API Documentation Temporarily Unavailable</h1><p>Please try again later.</p></body></html>`,
      {
        status: 503,
        headers: { "content-type": "text/html; charset=utf-8" }
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
      console.warn(`Attempt ${attempt} failed for ${url}:`, error.message);

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
