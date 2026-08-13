/* VLDST CASE — EMBEDDED ARTWORK
   Все стандартные изображения находятся прямо в этом JS-файле.
   PNG/JPG/WebP для интерфейса не нужны: SVG создаются как data: URL.
*/
(function () {
  "use strict";

  const enc = (svg) => "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg);
  const esc = (v) => String(v ?? "").replace(/[&<>\"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[c]));
  const hash = (value) => {
    let h = 2166136261;
    for (const ch of String(value ?? "VLDST")) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
    return Math.abs(h >>> 0);
  };

  const themes = [
    {a:"#7B2CFF",b:"#D45CFF",name:"NEON"},
    {a:"#1769FF",b:"#55D8FF",name:"CYBER"},
    {a:"#FF3D81",b:"#9B5CFF",name:"NIGHT"},
    {a:"#FF5A36",b:"#FFC15A",name:"FIRE"},
    {a:"#00C78A",b:"#59E6FF",name:"VOID"},
    {a:"#FFB000",b:"#FFF06A",name:"GOLD"},
    {a:"#E832FF",b:"#FF6CB5",name:"ULTRA"},
    {a:"#6C7BFF",b:"#B2B8FF",name:"ICE"}
  ];

  const rarityTheme = {
    common:["#547087","#B6D0E0"],
    rare:["#3F61FF","#74D6FF"],
    epic:["#8B35FF","#E36CFF"],
    legendary:["#FF6B2C","#FFD05A"],
    mythic:["#FFD21F","#FFF5A1"]
  };

  function defs(a,b,uid){
    return `<defs>
      <linearGradient id="g${uid}" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>
      <radialGradient id="r${uid}"><stop stop-color="${b}" stop-opacity=".35"/><stop offset="1" stop-color="${a}" stop-opacity="0"/></radialGradient>
      <filter id="blur${uid}"><feGaussianBlur stdDeviation="22"/></filter>
      <filter id="glow${uid}"><feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>`;
  }

  function base(kind,label,a,b,body,seed){
    const uid = `${hash(label+kind+seed)}`;
    const safe = esc(label).slice(0,25);
    return enc(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 460">
      ${defs(a,b,uid)}
      <rect width="640" height="460" rx="42" fill="#070A12"/>
      <circle cx="105" cy="55" r="190" fill="url(#r${uid})" filter="url(#blur${uid})"/>
      <circle cx="555" cy="420" r="190" fill="url(#r${uid})" filter="url(#blur${uid})"/>
      <path d="M30 355C140 260 185 425 310 345S505 270 620 350" fill="none" stroke="${b}" stroke-opacity=".12" stroke-width="2"/>
      <rect x="30" y="30" width="580" height="400" rx="34" fill="url(#g${uid})" opacity=".045" stroke="${b}" stroke-opacity=".45"/>
      <g opacity=".8"><circle cx="92" cy="100" r="4" fill="#fff"/><circle cx="528" cy="82" r="3" fill="#fff"/><circle cx="492" cy="344" r="5" fill="#fff"/><circle cx="145" cy="380" r="3" fill="${b}"/></g>
      ${body}
      <text x="320" y="389" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif" font-size="25" font-weight="900" letter-spacing="1">${safe}</text>
      <text x="320" y="414" text-anchor="middle" fill="${b}" font-family="Arial,sans-serif" font-size="10" font-weight="800" letter-spacing="3">VLDST • ${kind.toUpperCase()}</text>
    </svg>`);
  }

  function caseArt(label, seed=1){
    const t = themes[(hash(label)+seed) % themes.length];
    const variants = [
      `<path d="M148 160h344l-25 178H173z" fill="#0B0E19" stroke="url(#gX)" stroke-width="9"/><path d="M148 160l46-54h252l46 54" fill="#15192B" stroke="${t.b}" stroke-width="7"/><rect x="210" y="188" width="220" height="106" rx="24" fill="url(#gX)" opacity=".16"/><circle cx="320" cy="241" r="30" fill="#090C16" stroke="${t.b}" stroke-width="7"/><path d="M320 219v44M298 241h44" stroke="#fff" stroke-width="5" stroke-linecap="round"/>`,
      `<rect x="145" y="142" width="350" height="210" rx="38" fill="#0A0D18" stroke="url(#gX)" stroke-width="10"/><path d="M145 204h350M214 142v210M426 142v210" stroke="${t.b}" stroke-opacity=".45" stroke-width="5"/><path d="M195 245l45-45 45 45 55-68 64 68 36-34" fill="none" stroke="url(#gX)" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>`,
      `<path d="M320 113l151 75-44 174H213l-44-174z" fill="#0B0E18" stroke="url(#gX)" stroke-width="9"/><path d="M320 113v249M169 188h302" stroke="${t.b}" stroke-opacity=".35" stroke-width="5"/><circle cx="320" cy="246" r="60" fill="url(#gX)" opacity=".22"/><path d="M320 206l14 29 32 4-23 22 7 31-30-16-30 16 7-31-23-22 32-4z" fill="url(#gX)"/>`,
      `<rect x="150" y="145" width="340" height="205" rx="32" fill="#0A0D18" stroke="url(#gX)" stroke-width="9"/><path d="M183 184h274M183 224h274M183 264h274M183 304h274" stroke="${t.b}" stroke-opacity=".3" stroke-width="4"/><g fill="url(#gX)"><circle cx="215" cy="184" r="10"/><circle cx="215" cy="224" r="10"/><circle cx="215" cy="264" r="10"/><circle cx="215" cy="304" r="10"/></g><path d="M260 176l60 40 60-40M260 216l60 40 60-40M260 256l60 40 60-40" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="5"/>`,
      `<path d="M320 110l126 74v130l-126 74-126-74V184z" fill="#0B0E18" stroke="url(#gX)" stroke-width="9"/><path d="M320 110v278M194 184l126 76 126-76M194 314l126-54 126 54" fill="none" stroke="${t.b}" stroke-opacity=".38" stroke-width="5"/><circle cx="320" cy="260" r="45" fill="url(#gX)" opacity=".28"/>`
    ];
    let body = variants[(hash(label)+seed) % variants.length].replaceAll("gX",`g${hash(label+"case"+seed)}`);
    return base("CASE",label,t.a,t.b,body,seed);
  }

  function itemArt(label, rarity="common", seed=1){
    const rt = rarityTheme[rarity] || rarityTheme.common;
    const h = hash(label + seed);
    const a = rt[0], b = rt[1], uid = hash(label+rarity+seed);
    const v = h % 16;
    const bodies = [
      `<path d="M319 105l31 82 86 5-67 54 23 84-73-47-73 47 23-84-67-54 86-5z" fill="url(#g${uid})" filter="url(#glow${uid})"/>`,
      `<circle cx="320" cy="235" r="100" fill="#0C1120" stroke="url(#g${uid})" stroke-width="10"/><path d="M320 155v160M240 235h160" stroke="${b}" stroke-width="8"/><circle cx="320" cy="235" r="25" fill="url(#g${uid})"/>`,
      `<path d="M214 306l40-135 64 55 64-55 40 135z" fill="url(#g${uid})"/><path d="M214 306h228M254 171l64 55 64-55" fill="none" stroke="#fff" stroke-opacity=".65" stroke-width="5"/>`,
      `<path d="M235 150h170v168H235z" rx="25" fill="#0D1220" stroke="url(#g${uid})" stroke-width="9"/><path d="M270 194h100M270 236h70M270 278h100" stroke="${b}" stroke-width="9" stroke-linecap="round"/>`,
      `<path d="M300 115h40l25 80 70 24-56 39 18 82-77-47-77 47 18-82-56-39 70-24z" fill="url(#g${uid})"/><circle cx="320" cy="225" r="30" fill="#090C16"/>`,
      `<path d="M200 290l62-148 58 65 58-65 62 148z" fill="none" stroke="url(#g${uid})" stroke-width="14" stroke-linejoin="round"/><path d="M232 290h176" stroke="${b}" stroke-width="8"/>`,
      `<circle cx="320" cy="235" r="91" fill="#0C1020" stroke="url(#g${uid})" stroke-width="10"/><path d="M320 160l20 55 59 5-45 38 15 58-49-31-49 31 15-58-45-38 59-5z" fill="url(#g${uid})"/>`,
      `<rect x="210" y="150" width="220" height="170" rx="38" fill="#0C1020" stroke="url(#g${uid})" stroke-width="10"/><path d="M250 235h140M320 165v140" stroke="${b}" stroke-width="7"/><circle cx="270" cy="235" r="20" fill="url(#g${uid})"/><circle cx="370" cy="235" r="20" fill="url(#g${uid})"/>`,
      `<path d="M320 110l95 45v80c0 55-41 98-95 120-54-22-95-65-95-120v-80z" fill="#0B101D" stroke="url(#g${uid})" stroke-width="10"/><path d="M320 153v150M260 205h120" stroke="${b}" stroke-width="8"/>`,
      `<path d="M238 312V188l82-62 82 62v124z" fill="#0C1020" stroke="url(#g${uid})" stroke-width="9"/><path d="M270 222h100v62H270z" fill="url(#g${uid})" opacity=".25"/><circle cx="320" cy="253" r="17" fill="${b}"/>`,
      `<path d="M320 108l32 72 80 9-61 52 20 79-71-43-71 43 20-79-61-52 80-9z" fill="none" stroke="url(#g${uid})" stroke-width="12"/><circle cx="320" cy="240" r="28" fill="url(#g${uid})"/>`,
      `<path d="M215 310l34-148 71 46 71-46 34 148" fill="#0C1020" stroke="url(#g${uid})" stroke-width="9"/><path d="M248 244h144M269 203l51 36 51-36" fill="none" stroke="${b}" stroke-width="7"/>`,
      `<circle cx="255" cy="235" r="53" fill="url(#g${uid})" opacity=".8"/><circle cx="385" cy="235" r="53" fill="url(#g${uid})" opacity=".55"/><path d="M275 235h90M320 180v110" stroke="#fff" stroke-width="7" stroke-linecap="round"/>`,
      `<path d="M320 115l105 90-105 145-105-145z" fill="#0B101D" stroke="url(#g${uid})" stroke-width="10"/><path d="M260 210h120M278 250h84M296 290h48" stroke="${b}" stroke-width="8" stroke-linecap="round"/>`,
      `<rect x="205" y="170" width="230" height="130" rx="65" fill="#0C1020" stroke="url(#g${uid})" stroke-width="10"/><circle cx="270" cy="235" r="32" fill="url(#g${uid})"/><circle cx="370" cy="235" r="32" fill="url(#g${uid})"/><path d="M300 235h40" stroke="#fff" stroke-width="8"/>`
    ];
    return base("ITEM",label,a,b,bodies[v],seed);
  }

  function simple(kind,label,palette,icon){
    const t = themes[palette % themes.length], uid = hash(kind+label);
    const body = `<circle cx="320" cy="220" r="112" fill="url(#g${uid})" opacity=".16"/><g transform="translate(320 220) scale(1.05)">${icon}</g>`;
    return base(kind,label,t.a,t.b,body,uid);
  }



  window.VLDST_ASSETS = {
    hash,
    case:(label,seed=1)=>caseArt(label,seed),
    item:(label,rarity="common",seed=1)=>itemArt(label,rarity,seed),
    premium:(label="PREMIUM")=>simple("PREMIUM",label,5,`<path d="M-120 0l35-85 85 62 85-62 35 85-120 70z" fill="#FFE66D" stroke="#fff" stroke-width="6"/><circle cx="0" cy="0" r="25" fill="#0B0E18"/>`),
    boost:(label="BOOST")=>simple("BOOST",label,1,`<path d="M30-125L-72 10h60l-25 100L75-45H5z" fill="#5BE7FF" stroke="#fff" stroke-width="6"/>`),
    game:(label="VLDST RUSH")=>simple("GAME",label,0,`<rect x="-125" y="-60" width="250" height="120" rx="34" fill="#10162A" stroke="#D45CFF" stroke-width="8"/><circle cx="-62" cy="0" r="22" fill="#D45CFF"/><path d="M-62-14v28M-76 0h28" stroke="#fff" stroke-width="5"/><circle cx="65" cy="-18" r="9" fill="#FF5C81"/><circle cx="88" cy="12" r="9" fill="#5BE7FF"/>`),
    task:(label="TASK")=>simple("TASK",label,4,`<rect x="-100" y="-115" width="200" height="230" rx="28" fill="#10172A" stroke="#59E6FF" stroke-width="8"/><path d="M-55-50l18 18 40-45M-55 12l18 18 40-45M-55 74l18 18 40-45" fill="none" stroke="#59E6FF" stroke-width="9" stroke-linecap="round"/><path d="M35-45h45M35 17h45M35 79h45" stroke="#fff" stroke-width="7" stroke-linecap="round"/>`),
    ref:(label="REFERRALS")=>simple("REF",label,2,`<circle cx="-50" cy="-38" r="32" fill="#FF5CA8"/><circle cx="50" cy="-38" r="32" fill="#A95CFF"/><path d="M-108 80c10-55 48-72 58-72s48 17 58 72M-8 80c10-55 48-72 58-72s48 17 58 72" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round"/>`),
    fallback:()=>itemArt("VLDST", "common", 999)
  };
})();
