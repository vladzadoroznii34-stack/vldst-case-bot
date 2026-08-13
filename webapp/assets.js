/* VLDST CASE — EMBEDDED ART ASSETS
   Все изображения ниже генерируются как SVG data: URL прямо в коде.
   Никаких PNG/JPG/WebP/GIF файлов для стандартного дизайна не требуется.
*/
(function () {
  "use strict";

  const esc = (v) => String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const data = (svg) =>
    "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg);

  const palettes = {
    violet: ["#6D2BFF", "#C75CFF"],
    blue: ["#1769FF", "#58C7FF"],
    gold: ["#FFB300", "#FFE66D"],
    orange: ["#FF5A36", "#FFB347"],
    cyan: ["#00C6FF", "#7B61FF"],
    green: ["#20D37A", "#5BE7FF"],
    pink: ["#FF3D9A", "#8B5CFF"],
    red: ["#FF365A", "#FF8A65"]
  };

  function art(kind = "item", label = "VLDST", rarity = "common", seed = 1) {
    const p = palettes[
      kind === "premium" ? "gold" :
      kind === "boost" ? "cyan" :
      kind === "case" ? (["violet","blue","pink","orange","red","gold"][seed % 6]) :
      kind === "game" ? "violet" :
      kind === "task" ? "green" :
      kind === "ref" ? "pink" :
      rarity === "mythic" ? "gold" :
      rarity === "legendary" ? "orange" :
      rarity === "epic" ? "violet" :
      rarity === "rare" ? "blue" : "cyan"
    ] || palettes.violet;

    const [a,b] = p;
    const safe = esc(label).slice(0, 22);
    const glow = seed % 2 ? a : b;

    let center = "";
    if (kind === "case") {
      center = `
        <rect x="148" y="112" width="304" height="196" rx="42" fill="#0A0D18" stroke="url(#g)" stroke-width="9"/>
        <rect x="174" y="138" width="252" height="142" rx="27" fill="#12162A"/>
        <path d="M206 173h188v72H206z" fill="url(#g)" opacity=".14"/>
        <path d="M300 155v108M247 209h106" stroke="${b}" stroke-width="5" opacity=".8"/>
        <circle cx="300" cy="209" r="26" fill="#0B0E1B" stroke="${a}" stroke-width="6"/>
        <path d="M300 192v34M283 209h34" stroke="#fff" stroke-width="5" stroke-linecap="round"/>
      `;
    } else if (kind === "premium") {
      center = `
        <path d="M185 235l36-91 79 61 79-61 36 91-115 65z" fill="url(#g)" opacity=".95"/>
        <path d="M221 144l79 61 79-61M185 235h230" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="5"/>
        <circle cx="300" cy="207" r="16" fill="#0A0D18" stroke="#fff" stroke-width="4"/>
      `;
    } else if (kind === "boost") {
      center = `
        <path d="M335 116L224 245h71l-30 91 111-142h-70z" fill="url(#g)" stroke="#fff" stroke-opacity=".55" stroke-width="4"/>
        <circle cx="300" cy="225" r="118" fill="none" stroke="${b}" stroke-opacity=".22" stroke-width="3"/>
      `;
    } else if (kind === "game") {
      center = `
        <rect x="158" y="145" width="284" height="128" rx="34" fill="#11162A" stroke="url(#g)" stroke-width="8"/>
        <circle cx="223" cy="209" r="27" fill="${a}" opacity=".3"/>
        <path d="M207 209h32M223 193v32" stroke="#fff" stroke-width="6" stroke-linecap="round"/>
        <circle cx="370" cy="195" r="8" fill="${b}"/>
        <circle cx="392" cy="218" r="8" fill="${a}"/>
      `;
    } else if (kind === "task") {
      center = `
        <rect x="180" y="120" width="240" height="220" rx="32" fill="#10172A" stroke="url(#g)" stroke-width="8"/>
        <path d="M224 185l18 18 38-42M224 245l18 18 38-42M224 305l18 18 38-42" fill="none" stroke="${b}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M304 182h78M304 242h78M304 302h78" stroke="#fff" stroke-opacity=".75" stroke-width="8" stroke-linecap="round"/>
      `;
    } else if (kind === "ref") {
      center = `
        <circle cx="250" cy="188" r="34" fill="url(#g)"/>
        <circle cx="350" cy="188" r="34" fill="url(#g)" opacity=".78"/>
        <path d="M185 300c10-52 50-74 65-74s55 22 65 74M285 300c10-52 50-74 65-74s55 22 65 74" fill="none" stroke="#fff" stroke-opacity=".72" stroke-width="9" stroke-linecap="round"/>
      `;
    } else {
      center = `
        <circle cx="300" cy="215" r="98" fill="#10162A" stroke="url(#g)" stroke-width="9"/>
        <path d="M300 150l20 45 49 5-37 32 12 48-44-25-44 25 12-48-37-32 49-5z" fill="url(#g)"/>
      `;
    }

    return data(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 450">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop stop-color="${a}"/>
            <stop offset="1" stop-color="${b}"/>
          </linearGradient>
          <radialGradient id="bg">
            <stop stop-color="${glow}" stop-opacity=".28"/>
            <stop offset="1" stop-color="${glow}" stop-opacity="0"/>
          </radialGradient>
          <filter id="blur"><feGaussianBlur stdDeviation="22"/></filter>
        </defs>
        <rect width="600" height="450" rx="38" fill="#070A12"/>
        <circle cx="100" cy="60" r="170" fill="url(#bg)" filter="url(#blur)"/>
        <circle cx="510" cy="390" r="170" fill="url(#bg)" filter="url(#blur)"/>
        <path d="M44 330C150 250 175 410 300 345s170-60 256 6" fill="none" stroke="${b}" stroke-opacity=".12" stroke-width="2"/>
        <rect x="35" y="35" width="530" height="380" rx="34" fill="url(#g)" opacity=".055" stroke="${b}" stroke-opacity=".45"/>
        <circle cx="92" cy="98" r="4" fill="#fff"/>
        <circle cx="518" cy="87" r="3" fill="#fff"/>
        <circle cx="485" cy="335" r="5" fill="#fff"/>
        ${center}
        <text x="300" y="378" text-anchor="middle" fill="#FFFFFF" font-family="Arial, sans-serif" font-size="27" font-weight="800" letter-spacing="1">${safe}</text>
        <text x="300" y="402" text-anchor="middle" fill="${b}" font-family="Arial, sans-serif" font-size="11" font-weight="700" letter-spacing="3">VLDST • ${kind.toUpperCase()}</text>
      </svg>
    `);
  }

  window.VLDST_ASSETS = {
    make: art,
    case: (label, seed = 1) => art("case", label, "common", seed),
    item: (label, rarity = "common", seed = 1) => art("item", label, rarity, seed),
    premium: (label = "PREMIUM") => art("premium", label, "mythic", 7),
    boost: (label = "BOOST") => art("boost", label, "epic", 8),
    game: (label = "VLDST RUSH") => art("game", label, "epic", 9),
    task: (label = "TASK") => art("task", label, "rare", 10),
    ref: (label = "REFERRALS") => art("ref", label, "epic", 11)
  };
})();
