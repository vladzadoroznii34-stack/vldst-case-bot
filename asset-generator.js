// VLDST CASE — CODE ASSETS
// Все "картинки" проекта генерируются кодом как SVG.
// Никаких PNG/JPG/WebP/SVG-файлов для кейсов, предметов и магазина не требуется.

const THEMES = {
  neon:["#00E5FF","#8B5CFF","#090615"],
  core:["#4D8DFF","#9D5CFF","#080F24"],
  pulse:["#43FF9B","#39A7FF","#061A18"],
  aura:["#FF74F2","#714DFF","#170A27"],
  void:["#FF3ED1","#612DFF","#160519"],
  overdrive:["#FFC247","#FF4C62","#211005"],
  rift:["#5DF3FF","#704CFF","#061426"]
};

const RARITY = {
  COMMON:"#8D98A8",
  RARE:"#38A8FF",
  EPIC:"#A55CFF",
  LEGENDARY:"#FFB52F",
  MYTHIC:"#FF39D4"
};

const esc = s => String(s ?? "")
  .replaceAll("&","&amp;").replaceAll("<","&lt;")
  .replaceAll(">","&gt;").replaceAll('"',"&quot;");

function hash(s){
  let h=2166136261;
  for(const c of String(s)){h^=c.charCodeAt(0);h=Math.imul(h,16777619)}
  return h>>>0;
}
function rng(seed){
  let x=hash(seed);
  return ()=>{x+=0x6D2B79F5;let t=x;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296}
}

function svgShell(title, subtitle, a, b, bg, body){
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>
    <radialGradient id="r"><stop stop-color="${a}" stop-opacity=".45"/><stop offset="1" stop-color="${bg}" stop-opacity="0"/></radialGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="640" height="640" rx="52" fill="${bg}"/>
  <circle cx="80" cy="80" r="210" fill="url(#r)"/>
  <circle cx="580" cy="560" r="230" fill="url(#r)"/>
  ${body}
  <rect x="24" y="24" width="592" height="592" rx="40" fill="none" stroke="url(#g)" stroke-opacity=".55" stroke-width="3"/>
  <text x="42" y="548" fill="#fff" font-family="Arial,sans-serif" font-weight="900" font-size="25">${esc(title)}</text>
  <text x="42" y="580" fill="#BEB8CE" font-family="Arial,sans-serif" font-size="16">${esc(subtitle)}</text>
  </svg>`;
}

export function caseSvg(c){
  const [a,b,bg]=THEMES[c.theme]||THEMES.core;
  const r=rng(`case:${c.id}:${c.name}`);
  const particles=Array.from({length:28},()=>`<circle cx="${30+r()*580}" cy="${30+r()*470}" r="${2+r()*7}" fill="${a}" opacity="${.12+r()*.45}"/>`).join("");
  const rings=[0,1,2].map(i=>`<circle cx="320" cy="285" r="${115+i*38}" fill="none" stroke="url(#g)" stroke-width="${i===0?5:2}" opacity="${.8-i*.2}"/>`).join("");
  const box=`<g filter="url(#glow)">
    <rect x="175" y="160" width="290" height="235" rx="34" fill="#0D0A17" stroke="url(#g)" stroke-width="7"/>
    <path d="M175 215h290M235 160v235M405 160v235" stroke="url(#g)" stroke-width="5" opacity=".65"/>
    <rect x="278" y="248" width="84" height="84" rx="20" fill="url(#g)"/>
    <path d="M320 263v54M293 290h54" stroke="#fff" stroke-width="8" stroke-linecap="round"/>
  </g>`;
  return svgShell(`#${c.id} ${c.name}`,"VLDST CASE • DROP",a,b,bg,particles+rings+box);
}

export function itemSvg(i){
  const a=RARITY[i.rarity]||"#A55CFF";
  const b=RARITY[i.rarity]==="#FF39D4"?"#612DFF":"#5C4BFF";
  const bg="#08070F", r=rng(`item:${i.id}:${i.name}`);
  const particles=Array.from({length:24},()=>`<circle cx="${30+r()*580}" cy="${30+r()*470}" r="${1+r()*6}" fill="${a}" opacity="${.1+r()*.5}"/>`).join("");
  const rarity=esc(i.rarity);
  const initials=String(i.name).replace(/[^A-Za-zА-Яа-я0-9]/g,"").slice(0,3).toUpperCase();
  const crystal=`<g filter="url(#glow)">
    <polygon points="320,120 430,215 395,380 320,455 245,380 210,215" fill="url(#g)" opacity=".9"/>
    <polygon points="320,145 390,220 360,350 320,405 280,350 250,220" fill="#0C0A15" opacity=".65"/>
    <path d="M320 145v260M250 220h140M280 350h80" stroke="#fff" opacity=".35" stroke-width="4"/>
    <text x="320" y="300" text-anchor="middle" fill="#fff" font-family="Arial" font-weight="900" font-size="36">${esc(initials)}</text>
  </g>`;
  return svgShell(`#${i.id} ${i.name}`,`${rarity} • VLDST DROP`,a,b,bg,particles+crystal);
}

export function shopSvg(p){
  const a=p.kind==="premium"?"#FFD35A":p.kind==="boost"?"#46F5FF":"#A75CFF";
  const b=p.kind==="premium"?"#FF7A3D":p.kind==="boost"?"#4C63FF":"#FF3FCB";
  const icon=p.kind==="premium"?"★":p.kind==="boost"?"⚡":"◆";
  const body=`<g filter="url(#glow)">
    <circle cx="320" cy="275" r="128" fill="#0C0915" stroke="url(#g)" stroke-width="8"/>
    <circle cx="320" cy="275" r="92" fill="url(#g)" opacity=".92"/>
    <text x="320" y="310" text-anchor="middle" fill="#fff" font-family="Arial" font-size="105" font-weight="900">${icon}</text>
  </g>`;
  return svgShell(p.title,p.subtitle||"VLDST STAR SHOP",a,b,"#08070F",body);
}

export function gameSvg(){
  return svgShell("VLDST REACTOR","MINI GAME • SCORE FOR COINS","#44F0FF","#9C4DFF","#070812",
    `<g filter="url(#glow)"><circle cx="320" cy="290" r="150" fill="#0B0A15" stroke="url(#g)" stroke-width="9"/>
    <circle cx="320" cy="290" r="105" fill="none" stroke="url(#g)" stroke-width="4" opacity=".8"/>
    <circle cx="320" cy="290" r="48" fill="url(#g)"/>
    <path d="M320 185v55M425 290h-55M320 395v-55M215 290h55" stroke="#fff" stroke-width="7" stroke-linecap="round"/></g>`);
}
