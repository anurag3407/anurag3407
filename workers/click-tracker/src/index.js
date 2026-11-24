const INITIAL_CLICKS = 4789;
const PROFILE_KEY = "github_profile";

const REDIRECT_TARGETS = {
  github: "https://github.com/anurag3407/",
  sayabot: "https://github.com/anurag3407/sayabot",
  "career-pilot": "https://github.com/anurag3407/career-pilot",
  storinary: "https://github.com/anurag3407/storinary",
  ghostfounder: "https://github.com/anurag3407/ghosthunter",
};

const NO_CACHE_HEADERS = {
  "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
  "CDN-Cache-Control": "no-store",
  Pragma: "no-cache",
  Expires: "0",
};

async function ensureAndRead(db, increment) {
  if (increment) {
    const updated = await db
      .prepare("UPDATE clicks SET count = count + 1 WHERE key = ?1 RETURNING count")
      .bind(PROFILE_KEY)
      .first();
    if (updated && typeof updated.count === "number") {
      return updated.count;
    }
    await db
      .prepare(
        "CREATE TABLE IF NOT EXISTS clicks (key TEXT PRIMARY KEY, count INTEGER NOT NULL);"
      )
      .run();
    await db
      .prepare("INSERT OR IGNORE INTO clicks (key, count) VALUES (?1, ?2)")
      .bind(PROFILE_KEY, INITIAL_CLICKS + 1)
      .run();
    const row = await db
      .prepare("SELECT count FROM clicks WHERE key = ?1")
      .bind(PROFILE_KEY)
      .first();
    return row?.count ?? INITIAL_CLICKS + 1;
  }

  const row = await db
    .prepare("SELECT count FROM clicks WHERE key = ?1")
    .bind(PROFILE_KEY)
    .first();
  if (row && typeof row.count === "number") {
    return row.count;
  }
  return INITIAL_CLICKS;
}

function formatNumber(n) {
  return Number(n).toLocaleString("en-US");
}

function renderObsidianTelemetrySvg(count) {
  const formatted = formatNumber(count);
  const W = 900;
  const H = 64;
  const MONO = "'SF Mono','JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace";
  const SANS = "-apple-system,BlinkMacSystemFont,'Helvetica Neue','Segoe UI',Arial,sans-serif";

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="GitHub profile click counter: ${formatted}">
<defs>
  <linearGradient id="cbg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0C0C11"/>
    <stop offset="1" stop-color="#07070A"/>
  </linearGradient>
  <linearGradient id="rim" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#1D1D26" stop-opacity="0"/>
    <stop offset="0.35" stop-color="#383846" stop-opacity="0.9"/>
    <stop offset="0.65" stop-color="#4A4A5C" stop-opacity="0.9"/>
    <stop offset="1" stop-color="#1D1D26" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
    <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.045"/>
    <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="clip"><rect x="1" y="1" width="898" height="62" rx="14"/></clipPath>
  <style>
    @media(prefers-reduced-motion:reduce){*{animation:none!important}}
    text{user-select:none}
    @keyframes pr{0%{transform:scale(1);opacity:.75}70%{transform:scale(2.3);opacity:0}100%{transform:scale(2.3);opacity:0}}
    @keyframes eq1{0%,100%{transform:scaleY(.35)}50%{transform:scaleY(1)}}
    @keyframes eq2{0%,100%{transform:scaleY(.9)}50%{transform:scaleY(.3)}}
    @keyframes eq3{0%,100%{transform:scaleY(.5)}50%{transform:scaleY(.95)}}
    @keyframes sweep{0%{transform:translateX(-240px) skewX(-18deg);opacity:0}18%{opacity:1}55%{transform:translateX(980px) skewX(-18deg);opacity:0}100%{transform:translateX(980px) skewX(-18deg);opacity:0}}
    .pr{transform-box:fill-box;transform-origin:center;animation:pr 2.4s cubic-bezier(.2,.8,.3,1) infinite}
    .b1{transform-box:fill-box;transform-origin:bottom;animation:eq1 1.1s ease-in-out infinite}
    .b2{transform-box:fill-box;transform-origin:bottom;animation:eq2 1.4s ease-in-out infinite}
    .b3{transform-box:fill-box;transform-origin:bottom;animation:eq3 0.9s ease-in-out infinite}
    .sw{animation:sweep 6.5s ease-in-out infinite}
  </style>
</defs>
<rect width="${W}" height="${H}" rx="14" fill="#050507"/>
<g clip-path="url(#clip)">
  <rect width="${W}" height="${H}" fill="url(#cbg)"/>
  <rect class="sw" x="0" y="0" width="160" height="${H}" fill="url(#sheen)"/>
  <circle cx="34" cy="32" r="4" fill="#10B981"/>
  <circle class="pr" cx="34" cy="32" r="4" fill="none" stroke="#10B981" stroke-width="1.4"/>
  <text x="50" y="36" font-family="${MONO}" font-size="10.5" font-weight="700" fill="#F4F4F6" letter-spacing="1.2">LIVE PROFILE TELEMETRY</text>
  <text x="244" y="35.5" font-family="${MONO}" font-size="10.2" fill="#646473">·</text>
  <text x="260" y="35.5" font-family="${MONO}" font-size="10.2" fill="#A2A2B0">github.com/anurag3407/</text>
  <rect class="b1" x="636" y="25" width="2.4" height="14" rx="1" fill="#10B981"/>
  <rect class="b2" x="641.5" y="25" width="2.4" height="14" rx="1" fill="#A2A2B0"/>
  <rect class="b3" x="647" y="25" width="2.4" height="14" rx="1" fill="#646473"/>
  <rect x="664" y="15" width="212" height="34" rx="9" fill="#13131B" stroke="#2E2E3C" stroke-width="1"/>
  <text x="680" y="36" font-family="${MONO}" font-size="9.5" font-weight="600" fill="#A2A2B0" letter-spacing="0.9">CLICKS</text>
  <text x="860" y="37" font-family="${SANS}" font-size="16" font-weight="700" fill="#F4F4F6" text-anchor="end" letter-spacing="-0.3">${formatted}</text>
</g>
<rect x="0.5" y="0.5" width="899" height="63" rx="14" fill="none" stroke="#1D1D26" stroke-width="1"/>
<line x1="14" y1="0.75" x2="886" y2="0.75" stroke="url(#rim)" stroke-width="1"/>
</svg>`;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/favicon.ico") {
      return new Response(null, { status: 204 });
    }

    if (path === "/stats") {
      const count = await ensureAndRead(env.DB, false);
      return Response.json(
        { key: PROFILE_KEY, count },
        { headers: NO_CACHE_HEADERS }
      );
    }

    if (path === "/go" || path.startsWith("/go/")) {
      const targetKey = path.replace(/^\/go\/?/, "") || "github";
      const dest = REDIRECT_TARGETS[targetKey] || REDIRECT_TARGETS.github;
      await ensureAndRead(env.DB, true);
      return new Response(null, {
        status: 302,
        headers: {
          Location: dest,
          ...NO_CACHE_HEADERS,
        },
      });
    }

    if (path === "/" || path === "/views.svg" || path === "/badge.svg") {
      const peek = url.searchParams.get("peek") === "1";
      const count = await ensureAndRead(env.DB, !peek);
      const svg = renderObsidianTelemetrySvg(count);
      return new Response(svg, {
        status: 200,
        headers: {
          "Content-Type": "image/svg+xml; charset=utf-8",
          ...NO_CACHE_HEADERS,
        },
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};
