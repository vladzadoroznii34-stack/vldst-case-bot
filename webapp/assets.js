/* ============================================================
   VLDST CASE — ARTWORK V4
   Все изображения генерируются внутри JS как SVG data-uri.
   Никаких PNG/JPG/WebP для встроенной графики не требуется.
   ============================================================ */
(function(){
  "use strict";

  const enc = s => "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(s);
  const esc = v => String(v ?? "").replace(/[&<>"]/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"
  }[c]));
  const hash = v => {
    let h = 2166136261;
    for (const c of String(v ?? "VLDST")) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
    return Math.abs(h >>> 0);
  };

  const themes = [
    {key:"FIRE",     a:"#ff2417", b:"#ffd21f", dark:"#42070b", icon:"knife",   title:"VLDST FIRE",    sub:"INFERNO"},
    {key:"NEON",     a:"#9b32ff", b:"#35e7ff", dark:"#18083f", icon:"katana",  title:"VLDST NEON",    sub:"NIGHT CITY"},
    {key:"CYBER",    a:"#087cff", b:"#48ffe0", dark:"#061c35", icon:"pistol",  title:"VLDST CYBER",   sub:"PROTOCOL"},
    {key:"GOLD",     a:"#ff9d00", b:"#fff09a", dark:"#3b2200", icon:"crown",   title:"VLDST GOLD",    sub:"ROYAL DROP"},
    {key:"VOID",     a:"#692cff", b:"#ff3ea5", dark:"#1a0738", icon:"dragon",  title:"VLDST VOID",    sub:"DARK MATTER"},
    {key:"ICE",      a:"#24bfff", b:"#d8fbff", dark:"#052a3d", icon:"orb",     title:"VLDST ICE",     sub:"FROZEN CORE"},
    {key:"BLOOD",    a:"#b40020", b:"#ff5570", dark:"#2c030d", icon:"blade",   title:"VLDST BLOOD",   sub:"RED PROTOCOL"},
    {key:"GALAXY",   a:"#6d4aff", b:"#ff67db", dark:"#10082d", icon:"galaxy",  title:"VLDST GALAXY",  sub:"STARFALL"}
  ];

  const rarities = {
    common:    ["#526b82","#d2e5f5"],
    rare:      ["#3f63ff","#62ddff"],
    epic:      ["#8d35ff","#ee74ff"],
    legendary: ["#ff642b","#ffd25a"],
    mythic:    ["#ffc400","#fff6a0"]
  };

  function defs(a,b,id,dark="#070910"){
    return `<defs>
      <linearGradient id="g${id}" x1="0" y1="0" x2="1" y2="1">
        <stop stop-color="${a}"/><stop offset="1" stop-color="${b}"/>
      </linearGradient>
      <linearGradient id="metal${id}" x1="0" y1="0" x2="0" y2="1">
        <stop stop-color="#25060b"/><stop offset=".45" stop-color="${a}"/><stop offset="1" stop-color="#23040a"/>
      </linearGradient>
      <linearGradient id="steel${id}" x1="0" y1="0" x2="1" y2="1">
        <stop stop-color="#ffffff"/><stop offset=".18" stop-color="#aeb8c9"/>
        <stop offset=".48" stop-color="#161b28"/><stop offset=".75" stop-color="#f8fbff"/><stop offset="1" stop-color="#59647a"/>
      </linearGradient>
      <radialGradient id="orb${id}">
        <stop stop-color="${b}" stop-opacity=".8"/><stop offset=".35" stop-color="${a}" stop-opacity=".28"/>
        <stop offset="1" stop-color="${dark}" stop-opacity="0"/>
      </radialGradient>
      <filter id="blur${id}"><feGaussianBlur stdDeviation="24"/></filter>
      <filter id="glow${id}">
        <feGaussianBlur stdDeviation="6" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>`;
  }

  function particles(a,b,id,n=28){
    let out="";
    for(let i=0;i<n;i++){
      const x=30+hash(id+"x"+i)%580, y=35+hash(id+"y"+i)%335;
      const r=1+hash(id+"r"+i)%3;
      const op=(.25+(hash(id+"o"+i)%7)/10).toFixed(2);
      out += `<circle cx="${x}" cy="${y}" r="${r}" fill="${i%2?a:b}" opacity="${op}"/>`;
    }
    return out;
  }

  function caseObject(kind,a,b,id){
    if(kind==="knife") return `<g filter="url(#glow${id})" transform="rotate(-12 320 200)">
      <path d="M105 207Q185 135 395 154L535 187 390 213 165 220Z" fill="url(#steel${id})" stroke="#fff" stroke-width="3"/>
      <path d="M392 155l78 32-73 26-25-18z" fill="#151924" stroke="${b}" stroke-width="5"/>
      <path d="M346 160l48 50" stroke="${a}" stroke-width="6"/>
    </g>`;
    if(kind==="katana") return `<g filter="url(#glow${id})" transform="rotate(-17 320 200)">
      <path d="M72 203Q230 145 500 161q28 2 43 18-15 15-43 16L145 219Z" fill="url(#steel${id})" stroke="#fff" stroke-width="3"/>
      <rect x="55" y="190" width="92" height="25" rx="9" fill="#10141f" stroke="${a}" stroke-width="5"/>
      <path d="M120 193l44 22M140 187l45 22M160 181l45 22" stroke="${b}" stroke-width="4"/>
    </g>`;
    if(kind==="pistol") return `<g filter="url(#glow${id})" transform="rotate(-8 320 210)">
      <path d="M125 174h285l62 34-65 31H274l-34 82h-70l20-82-51-21z" fill="#111725" stroke="${b}" stroke-width="7"/>
      <rect x="195" y="145" width="180" height="32" rx="10" fill="#31394d"/>
      <path d="M268 232l51 13-26 74h-66z" fill="#090d16" stroke="${a}" stroke-width="6"/>
      <circle cx="392" cy="205" r="8" fill="#fff"/>
    </g>`;
    if(kind==="crown") return `<g filter="url(#glow${id})">
      <path d="M172 146l82 62 66-105 66 105 82-62-24 153H196Z" fill="url(#g${id})" stroke="#fff" stroke-width="5"/>
      <circle cx="254" cy="205" r="10" fill="#fff"/><circle cx="320" cy="103" r="10" fill="#fff"/><circle cx="386" cy="205" r="10" fill="#fff"/>
    </g>`;
    if(kind==="orb") return `<g filter="url(#glow${id})">
      <circle cx="320" cy="210" r="92" fill="#09121e" stroke="url(#g${id})" stroke-width="15"/>
      <path d="M260 250Q320 120 380 250M245 210h150M320 125v170" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="5"/>
      <circle cx="320" cy="210" r="24" fill="url(#g${id})"/>
    </g>`;
    if(kind==="blade") return `<g filter="url(#glow${id})" transform="rotate(-24 320 210)">
      <path d="M120 235L455 125l60 30-310 137Z" fill="url(#steel${id})" stroke="#fff" stroke-width="4"/>
      <path d="M225 275l95-45 42 45-88 50z" fill="#121624" stroke="${a}" stroke-width="6"/>
    </g>`;
    if(kind==="galaxy") return `<g filter="url(#glow${id})">
      <path d="M320 90c72 0 138 56 138 126s-66 126-138 126-138-56-138-126S248 90 320 90Z" fill="url(#g${id})" opacity=".82"/>
      <path d="M205 244q115-155 230-70" fill="none" stroke="#fff" stroke-width="7" stroke-opacity=".75"/>
      <circle cx="290" cy="190" r="9" fill="#fff"/><circle cx="362" cy="220" r="7" fill="#fff"/><circle cx="337" cy="155" r="5" fill="#fff"/>
    </g>`;
    return `<g filter="url(#glow${id})">
      <path d="M320 75c-80 28-128 81-107 145 13 39 43 63 83 77l24 55 24-55c40-14 70-38 83-77 21-64-27-117-107-145Z" fill="url(#g${id})" stroke="#fff" stroke-width="5"/>
      <path d="M235 145l55 20-34 31M405 145l-55 20 34 31" fill="none" stroke="#fff" stroke-width="7"/>
      <circle cx="282" cy="196" r="8" fill="#fff"/><circle cx="358" cy="196" r="8" fill="#fff"/>
    </g>`;
  }

  function crate(t,id,label){
    return `<g filter="url(#glow${id})">
      <path d="M104 272h432l-20 112H124Z" fill="url(#metal${id})" stroke="${t.b}" stroke-width="5"/>
      <path d="M134 272h372l-25-64H159Z" fill="${t.dark}" stroke="${t.a}" stroke-width="5"/>
      <path d="M122 311h396M115 355h410" stroke="#fff" stroke-opacity=".18" stroke-width="4"/>
      <path d="M155 272v112M225 272v112M415 272v112M485 272v112" stroke="#17040a" stroke-width="10" opacity=".8"/>
      <rect x="264" y="306" width="112" height="58" rx="13" fill="#19060b" stroke="${t.b}" stroke-width="5"/>
      <text x="320" y="343" text-anchor="middle" fill="#fff" font-size="20" font-weight="1000" font-family="Arial">VLDST</text>
      <path d="M155 272l31-64h268l31 64" fill="none" stroke="${t.b}" stroke-width="5"/>
    </g>
    <text x="320" y="414" text-anchor="middle" fill="#fff" font-family="Arial" font-size="25" font-weight="1000" letter-spacing="2">${esc(label).slice(0,25)}</text>`;
  }

  function caseArt(label,seed=1){
    const s=String(label||"VLDST CASE").toUpperCase();
    let t=themes.find(x=>s.includes(x.key)) || themes[(hash(label)+seed)%themes.length];
    const id=hash(label+"|case|"+seed);
    return enc(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 460">
      ${defs(t.a,t.b,id,t.dark)}
      <rect width="640" height="460" rx="42" fill="#020307"/>
      <circle cx="130" cy="110" r="210" fill="url(#orb${id})" filter="url(#blur${id})"/>
      <circle cx="520" cy="310" r="220" fill="url(#orb${id})" filter="url(#blur${id})"/>
      ${particles(t.a,t.b,id)}
      <ellipse cx="320" cy="390" rx="250" ry="28" fill="${t.a}" opacity=".22" filter="url(#blur${id})"/>
      ${caseObject(t.icon,t.a,t.b,id)}
      ${crate(t,id,t.title)}
      <text x="320" y="54" text-anchor="middle" fill="${t.b}" font-family="Arial" font-size="11" font-weight="900" letter-spacing="5">VLDST CASE • ${t.sub}</text>
    </svg>`);
  }

  const itemKinds = {
    blade: `<path d="M115 270Q210 150 470 170l55 35-95 50-260 30Z" fill="url(#gID)" stroke="#fff" stroke-opacity=".75" stroke-width="4"/><path d="M360 235l95 20-48 70-85-48Z" fill="#0c111c" stroke="url(#gID)" stroke-width="8"/>`,
    pistol: `<path d="M135 178h270l65 37-62 34H275l-32 85h-68l18-85-58-22Z" fill="#111726" stroke="url(#gID)" stroke-width="9"/><rect x="205" y="145" width="160" height="34" rx="9" fill="#30394e"/><circle cx="385" cy="207" r="8" fill="#fff"/>`,
    helmet: `<path d="M190 310V220q0-105 130-105t130 105v90h-72v-50h-116v50Z" fill="#0d1422" stroke="url(#gID)" stroke-width="12"/><path d="M228 235h184" stroke="#fff" stroke-opacity=".55" stroke-width="8"/><path d="M270 135l50-24 50 24" fill="none" stroke="#fff" stroke-width="6"/>`,
    gem: `<path d="M320 90l125 85-45 150-80 55-80-55-45-150Z" fill="url(#gID)" stroke="#fff" stroke-opacity=".75" stroke-width="5"/><path d="M195 175h250M320 90v290M250 175l70 90 70-90" fill="none" stroke="#fff" stroke-opacity=".6" stroke-width="5"/>`,
    mask: `<path d="M170 180q150-95 300 0v95q-45 80-105 35l-45-42-45 42q-60 45-105-35Z" fill="#0b111c" stroke="url(#gID)" stroke-width="12"/><circle cx="255" cy="228" r="19" fill="url(#gID)"/><circle cx="385" cy="228" r="19" fill="url(#gID)"/>`,
    crown: `<path d="M165 150l82 65 73-112 73 112 82-65-22 165H187Z" fill="url(#gID)" stroke="#fff" stroke-width="5"/><circle cx="247" cy="216" r="9" fill="#fff"/><circle cx="320" cy="104" r="9" fill="#fff"/><circle cx="393" cy="216" r="9" fill="#fff"/>`,
    orb: `<circle cx="320" cy="220" r="112" fill="#08111d" stroke="url(#gID)" stroke-width="16"/><path d="M238 270Q320 115 402 270M225 220h190M320 120v200" fill="none" stroke="#fff" stroke-opacity=".6" stroke-width="6"/><circle cx="320" cy="220" r="27" fill="url(#gID)"/>`,
    coin: `<circle cx="320" cy="220" r="120" fill="url(#gID)" stroke="#fff" stroke-width="7"/><circle cx="320" cy="220" r="90" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="5"/><text x="320" y="250" text-anchor="middle" fill="#fff" font-size="82" font-family="Arial" font-weight="1000">V</text>`,
    dragon: `<path d="M320 100q-85 30-115 105 20 45 75 40l40 85 40-85q55 5 75-40-30-75-115-105Z" fill="url(#gID)" stroke="#fff" stroke-width="5"/><path d="M245 180l-65-30 38 70M395 180l65-30-38 70" fill="none" stroke="#fff" stroke-width="7"/><circle cx="285" cy="200" r="8" fill="#fff"/><circle cx="355" cy="200" r="8" fill="#fff"/>`
  };

  function chooseItemKind(label,seed){
    const s=String(label||"").toLowerCase();
    if(/нож|knife|blade|меч|sword|катан|blade|клинок/.test(s)) return "blade";
    if(/пист|gun|pistol|smg|rifle|ак|deagle|glock/.test(s)) return "pistol";
    if(/шлем|helmet|armor|брон|маска|mask/.test(s)) return s.includes("маск")||s.includes("mask") ? "mask" : "helmet";
    if(/корон|crown|king|royal/.test(s)) return "crown";
    if(/дракон|dragon|phoenix|феникс/.test(s)) return "dragon";
    if(/крист|gem|diamond|алмаз/.test(s)) return "gem";
    if(/монет|coin|coin|золот/.test(s)) return "coin";
    if(/сфер|orb|ядр|core|energy/.test(s)) return "orb";
    return Object.keys(itemKinds)[hash(label+"|"+seed)%Object.keys(itemKinds).length];
  }

  function itemArt(label,rarityName="common",seed=1){
    const r=rarities[String(rarityName).toLowerCase()]||rarities.common;
    const id=hash(label+"|"+rarityName+"|"+seed), kind=chooseItemKind(label,seed);
    const shape=itemKinds[kind].replaceAll("gID",`g${id}`);
    return enc(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 460">
      ${defs(r[0],r[1],id)}
      <rect width="640" height="460" rx="42" fill="#04060b"/>
      <circle cx="320" cy="215" r="195" fill="url(#orb${id})" filter="url(#blur${id})"/>
      ${particles(r[0],r[1],id,20)}
      <g filter="url(#glow${id})">${shape}</g>
      <text x="320" y="398" text-anchor="middle" fill="#fff" font-family="Arial" font-size="23" font-weight="1000">${esc(label).slice(0,27)}</text>
      <text x="320" y="423" text-anchor="middle" fill="${r[1]}" font-family="Arial" font-size="11" font-weight="900" letter-spacing="4">VLDST • ${String(rarityName).toUpperCase()}</text>
    </svg>`);
  }

  function serviceArt(kind,label,a,b,icon){
    const id=hash(kind+"|"+label);
    return enc(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 460">
      ${defs(a,b,id)}
      <rect width="640" height="460" rx="42" fill="#04060b"/>
      <circle cx="320" cy="205" r="195" fill="url(#orb${id})" filter="url(#blur${id})"/>
      ${particles(a,b,id,22)}
      <g transform="translate(320 205)" filter="url(#glow${id})">${icon}</g>
      <text x="320" y="398" text-anchor="middle" fill="#fff" font-family="Arial" font-size="24" font-weight="1000">${esc(label).slice(0,27)}</text>
      <text x="320" y="423" text-anchor="middle" fill="${b}" font-family="Arial" font-size="11" font-weight="900" letter-spacing="4">VLDST • ${kind}</text>
    </svg>`);
  }

  window.VLDST_ASSETS = {
    hash,
    case:(label,seed=1)=>caseArt(label,seed),
    item:(label,rarity="common",seed=1)=>itemArt(label,rarity,seed),
    premium:(label="PREMIUM")=>serviceArt("PREMIUM",label,"#ffad21","#fff3a1",`<path d="M-125-60l70 55 55-100 55 100 70-55-18 145h-232Z" fill="#ffd84a" stroke="#fff" stroke-width="7"/><circle cx="0" cy="20" r="28" fill="#151827"/>`),
    boost:(label="BOOST")=>serviceArt("BOOST",label,"#22c7ff","#b8f8ff",`<path d="M45-135L-65 0h62l-32 120L82-50H8Z" fill="#59e7ff" stroke="#fff" stroke-width="7"/>`),
    game:(label="VLDST RUSH")=>serviceArt("GAME",label,"#8c3dff","#ff6bda",`<rect x="-135" y="-75" width="270" height="150" rx="35" fill="#11172a" stroke="#d45cff" stroke-width="9"/><circle cx="-65" cy="0" r="26" fill="#d45cff"/><path d="M-65-18v36M-83 0h36" stroke="#fff" stroke-width="6"/><circle cx="60" cy="-22" r="11" fill="#ff5d80"/><circle cx="90" cy="22" r="11" fill="#5be7ff"/>`),
    task:(label="TASKS")=>serviceArt("MISSIONS",label,"#00c78a","#8affd0",`<rect x="-105" y="-125" width="210" height="250" rx="28" fill="#10182a" stroke="#59e6ff" stroke-width="8"/><path d="M-62-58l20 20 44-50M-62 12l20 20 44-50M-62 82l20 20 44-50" fill="none" stroke="#59e6ff" stroke-width="10" stroke-linecap="round"/><path d="M34-52h48M34 18h48M34 88h48" stroke="#fff" stroke-width="7" stroke-linecap="round"/>`),
    ref:(label="REFERRALS")=>serviceArt("INVITE",label,"#ff3d86","#bd69ff",`<circle cx="-54" cy="-40" r="34" fill="#ff5ca8"/><circle cx="54" cy="-40" r="34" fill="#a95cff"/><path d="M-116 92c10-62 52-82 62-82s52 20 62 82M-8 92c10-62 52-82 62-82s52 20 62 82" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/>`),
    inventory:(label="INVENTORY")=>serviceArt("LOOT",label,"#7139ff","#5be7ff",`<path d="M-105-60h210l-25 190H-80Z" fill="#121827" stroke="#8f58ff" stroke-width="8"/><path d="M-70-60q70-100 140 0" fill="none" stroke="#5be7ff" stroke-width="10"/><circle cx="0" cy="32" r="28" fill="url(#gID)"/>`),
    fallback:()=>itemArt("VLDST ITEM","common",999)
  };

  /* Поддержка вызова из консоли для быстрой проверки:
     VLDST_ASSETS.case("VLDST FIRE")
     VLDST_ASSETS.item("Огненный клинок","legendary")
  */
})();