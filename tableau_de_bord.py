"""Génère tableau_de_bord.html : un fichier à ouvrir dans le navigateur.

Les données sont intégrées dans la page (aucun serveur). Seule la librairie
de graphiques est chargée depuis internet (cdnjs).
"""
import json
from datetime import datetime
from pathlib import Path


def _slim(trades):
    return [{"t": t["at"], "s": bool(t["sold"]), "n": t["name"], "q": t.get("quantity") or 0,
             "g": t.get("gross") or 0, "net": t.get("net") or 0} for t in trades]


def build_dashboard(root: Path, farms, price_history, watch, names_fr, prices_now, costs=None, cost_hist=None, stock=None, goals=None, start=None, nft=None):
    data = {
        "generatedAt": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "farms": [{"id": f["id"], "nom": f["nom"], "trades": _slim(f["trades"]), "counters": f["counters"]}
                  for f in farms],
        "trades": [],
        "counters": [],
        "prices": price_history,
        "costs": costs or [],
        "costHist": cost_hist or [],
        "stock": stock or [],
        "goals": goals or [],
        "start": start,
        "nft": nft or {"rows": [], "prod": {}},
        "watch": watch,
        "names": names_fr,
        "now": {k: v for k, v in prices_now.items() if isinstance(v, (int, float))},
    }
    html = TEMPLATE.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    out = root / "tableau_de_bord.html"
    out.write_text(html, encoding="utf-8")
    return out


TEMPLATE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;550;650;750&display=swap" rel="stylesheet">
<title>Tableau de bord SFL</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{
  --bg:#f6f4ee;--card:#ffffff;--ink:#22201b;--muted:#6f6a5f;--line:#e4dfd3;
  --accent:#3f7d4e;--accent-soft:#e3efe5;--sell:#3f7d4e;--buy:#c0602f;--warn:#b5482b;--market:#5a6fb0;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#181a17;--card:#22251f;--ink:#ecebe4;--muted:#a3a194;--line:#353a31;
  --accent:#7cc38d;--accent-soft:#2a3a2d;--sell:#7cc38d;--buy:#e8955f;--warn:#ef7d5e;--market:#93a6e6;}}
:root[data-theme="dark"]{
  --bg:#181a17;--card:#22251f;--ink:#ecebe4;--muted:#a3a194;--line:#353a31;
  --accent:#7cc38d;--accent-soft:#2a3a2d;--sell:#7cc38d;--buy:#e8955f;--warn:#ef7d5e;--market:#93a6e6;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Inter",system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
header{padding:22px 16px 6px;max-width:1100px;margin:auto}
h1{font-size:24px;margin:0;letter-spacing:-.02em}
.sub{color:var(--muted);font-size:13px}
nav{display:flex;gap:6px;flex-wrap:wrap;max-width:1100px;margin:8px auto 0;padding:0 16px}
nav{position:sticky;top:0;z-index:5;background:var(--bg);padding-top:8px;padding-bottom:8px}
nav button{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:8px 15px;border-radius:999px;cursor:pointer;font-size:14px;font-weight:550}
nav button.on{background:var(--accent);border-color:var(--accent);color:#fff}
main{max-width:1100px;margin:auto;padding:12px 16px 40px}
section{display:none}section.on{display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:14px}
.kpi,.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;box-shadow:0 1px 2px rgba(0,0,0,.04),0 4px 14px rgba(0,0,0,.04)}
.hero{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:14px;padding:18px;border-radius:18px;background:linear-gradient(135deg,var(--accent-soft),var(--card));border:1px solid var(--line)}
.hero .l{color:var(--muted);font-size:12.5px}.hero .big{font-size:30px;font-weight:750;letter-spacing:-.02em}
.badge{display:inline-block;padding:3px 9px;border-radius:999px;font-size:12.5px;font-weight:600;white-space:nowrap}
.badge.good{background:color-mix(in srgb,var(--sell) 18%,transparent);color:var(--sell)}
.badge.mid{background:color-mix(in srgb,var(--muted) 15%,transparent);color:var(--muted)}
.badge.wait{background:color-mix(in srgb,#d99a2b 20%,transparent);color:#b07812}
.badge.keep{background:color-mix(in srgb,var(--market) 18%,transparent);color:var(--market)}
.badge.bad{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}
.chart.big{height:380px}
.ticker{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 16px;margin:6px 0 10px}
.tname{font-size:15px;color:var(--muted);font-weight:600;width:100%}.tprice{font-size:34px;font-weight:750;letter-spacing:-.02em}.tunit{font-size:13px;color:var(--muted);font-weight:500}
.tchg{font-size:16px;font-weight:650}.tmeta{width:100%;color:var(--muted);font-size:12.5px}
details summary{cursor:pointer}
.plain{margin:6px 0;line-height:1.55}
.bar{height:8px;border-radius:99px;background:var(--line);margin-top:8px;overflow:hidden}.bar span{display:block;height:100%;background:var(--accent)}
.goal{display:flex;gap:12px;align-items:flex-start;padding:10px 4px;border-bottom:1px solid var(--line)}.goal:last-child{border-bottom:0}
.goal.ok .gt{color:var(--muted);text-decoration:line-through}.gchk{font-size:20px;line-height:1.2}.gtxt{flex:1}.gt{font-weight:600}.gcost{text-align:right;white-space:nowrap}
.month{border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin-bottom:8px;background:var(--card)}
.month summary{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline;list-style:none}.month summary::-webkit-details-marker{display:none}
.msum{color:var(--muted);font-size:13px}.mbody{margin-top:8px}
.why{color:var(--muted);font-size:11.5px;white-space:normal;max-width:260px;margin-top:2px}
tr:hover td{background:color-mix(in srgb,var(--accent) 5%,transparent)}
.kpi .l{color:var(--muted);font-size:12px}.kpi .v{font-size:22px;font-weight:650;margin-top:2px;font-variant-numeric:tabular-nums}
.card{margin-bottom:14px}.card h2{font-size:15px;margin:0 0 10px}
.pos{color:var(--sell)}.neg{color:var(--buy)}.warn{color:var(--warn)}
table{width:100%;border-collapse:collapse;font-size:13.5px;font-variant-numeric:tabular-nums}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;font-size:12px}
.scroll{overflow-x:auto}
.controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
select,input{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:6px 8px;font-size:14px}
.chart{position:relative;height:300px}
.empty{color:var(--muted);font-style:italic;padding:8px 0}
.chip{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:5px 12px;border-radius:999px;cursor:pointer;font-size:13px}.chip.on{background:var(--accent-soft);border-color:var(--accent);color:var(--accent);font-weight:600}
.matrix th{text-align:left}.matrix td{text-align:center}.bub{display:inline-block;min-width:96px;padding:8px 10px;border-radius:12px;background:var(--accent-soft);font-size:18px;font-weight:650}.bub.neg{background:color-mix(in srgb,var(--buy) 14%,transparent)}
.theme{float:right;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:4px 8px;cursor:pointer}
</style>
</head>
<body>
<header>
  <button class="theme" id="theme" title="Clair / sombre">◐</button><button class="theme" id="refresh" style="margin-right:6px">🔄 Actualiser</button>
  <h1>🌻 Tableau de bord Sunflower Land</h1>
  <div class="sub" id="gen"></div>
  <div class="controls" id="farmbox" style="margin-top:8px;display:none"><label>Ferme <select id="farm"></select></label></div>
</header>
<nav id="tabs"></nav>
<main>
  <section id="apercu"></section>
  <section id="historique"></section>
  <section id="objectifs"></section>
  <section id="vente"></section>
  <section id="rentabilite"></section>
  <section id="nft"></section>
  <section id="skills"></section>
  <section id="ressources"></section>
  <section id="echanges"></section>
  <section id="compteurs"></section>
</main>
<script>
const D = /*__DATA__*/null;
let FARM;try{FARM=localStorage.getItem("farm")}catch(e){}
if(!D.farms.some(f=>f.id===FARM))FARM=D.farms[0].id;
function setFarm(id){const f=D.farms.find(x=>x.id===id);FARM=id;D.trades=f.trades;D.counters=f.counters;try{localStorage.setItem("farm",id)}catch(e){}}
setFarm(FARM);
const TABS=[["apercu","Aperçu"],["objectifs","Objectifs"],["vente","Vente"],["rentabilite","Rentabilité"],["nft","NFT"],["skills","Compétences"],["ressources","Une ressource"],["historique","Historique"],["echanges","Échanges"],["compteurs","Compteurs"]];
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const fr=(x,d=2)=>x==null||isNaN(x)?"—":x.toLocaleString("fr-FR",{minimumFractionDigits:d,maximumFractionDigits:d});
const fp=x=>x==null?"—":fr(x,x>=10?2:4);
const sg=x=>{if(Math.abs(x)<0.005)return fr(0);return (x>0?"+":"")+fr(x)};
const nm=n=>D.names[n]||n;
const day=t=>new Date(t).toISOString().slice(0,10);
const charts={};
function alpha(c,a){c=c.trim();if(c.startsWith("#")){const n=parseInt(c.slice(1).length===3?c.slice(1).split("").map(x=>x+x).join(""):c.slice(1),16);return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`;}return c;}
function zeroSplit(ctx){const ch=ctx.chart,a=ch.chartArea,y=ch.scales&&ch.scales.y;const g0=css("--sell"),r0=css("--buy");if(!a||!y)return g0;
 let t=(y.getPixelForValue(0)-a.top)/(a.bottom-a.top);t=Math.min(1,Math.max(0,t));const g=ch.ctx.createLinearGradient(0,a.top,0,a.bottom);
 g.addColorStop(0,g0);g.addColorStop(t,g0);g.addColorStop(t,r0);g.addColorStop(1,r0);return g;}
function areaGrad(ctx,color){const g=ctx.chart.ctx.createLinearGradient(0,0,0,ctx.chart.height||300);g.addColorStop(0,alpha(color,.35));g.addColorStop(1,alpha(color,0));return g;}
function chart(id,cfg){if(charts[id])charts[id].destroy();if(!window.Chart){document.getElementById(id).parentElement.innerHTML='<div class="empty">Graphique indisponible (pas de connexion internet).</div>';return;}charts[id]=new Chart(document.getElementById(id),cfg);}
const baseOpts=()=>({responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},
  plugins:{legend:{labels:{color:css("--ink")}}},
  scales:{x:{ticks:{color:css("--muted")},grid:{color:css("--line")}},y:{ticks:{color:css("--muted")},grid:{color:css("--line")}}}});

const fsel=document.getElementById("farm");D.farms.forEach(f=>{const o=document.createElement("option");o.value=f.id;o.textContent=f.nom+" · #"+f.id;fsel.appendChild(o);});fsel.value=FARM;if(D.farms.length>1)document.getElementById("farmbox").style.display="flex";document.querySelector("h1").textContent="🌻 "+D.farms.find(f=>f.id===FARM).nom+" — tableau de bord";document.title=D.farms[0].nom+" — SFL";
function updGen(){document.getElementById("gen").textContent="Mis à jour le "+D.generatedAt+" · "+D.trades.length+" échanges enregistrés · "+D.prices.length+" relevé(s) de prix";}
updGen();fsel.onchange=()=>{setFarm(fsel.value);updGen();render(document.querySelector("section.on").id);};
const nav=document.getElementById("tabs");
TABS.forEach(([id,l],i)=>{const b=document.createElement("button");b.textContent=l;b.onclick=()=>show(id);b.dataset.id=id;nav.appendChild(b);});
function show(id){document.querySelectorAll("section").forEach(s=>s.classList.toggle("on",s.id===id));nav.querySelectorAll("button").forEach(b=>b.classList.toggle("on",b.dataset.id===id));try{localStorage.setItem("tab",id)}catch(e){};render(id);}
document.getElementById("theme").onclick=()=>{const r=document.documentElement;const cur=r.dataset.theme||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");r.dataset.theme=cur==="dark"?"light":"dark";try{localStorage.setItem("theme",r.dataset.theme)}catch(e){};render(document.querySelector("section.on").id);};
try{const t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}catch(e){}
const rb=document.getElementById("refresh");
rb.onclick=async()=>{
 if(!location.protocol.startsWith("http")){alert("Pour actualiser depuis ce bouton, ouvre le tableau de bord avec « Lancer le relevé » (il démarre un petit serveur sur ton ordinateur).\n\nTu peux aussi simplement relancer « Lancer le relevé ».");return;}
 rb.disabled=true;rb.textContent="⏳ Relevé en cours… (jusqu'à 1 min)";
 try{const r=await fetch("/actualiser",{method:"POST"});const j=await r.json();
  if(j.ok){rb.textContent="✅ À jour";setTimeout(()=>location.reload(),600);}else{alert("Actualisation impossible : "+j.message);rb.textContent="🔄 Actualiser";rb.disabled=false;}}
 catch(e){alert("Le serveur ne répond pas. Relance « Lancer le relevé ».");rb.textContent="🔄 Actualiser";rb.disabled=false;}
};

function sum(arr,f){return arr.reduce((a,x)=>a+f(x),0)}
const START=D.start?new Date(D.start+"T00:00:00").getTime():0;const STARTFR=D.start?D.start.split("-").reverse().join("/"):"";
function GT(){return D.trades.filter(t=>t.t>=START)}
function inLast(days){const lim=Math.max(START,Date.now()-days*864e5);return D.trades.filter(t=>t.t>=lim)}
function periodKey(t,kind){const d=new Date(t);if(kind==="jour")return d.toISOString().slice(0,10);
  if(kind==="mois")return d.toISOString().slice(0,7);
  const x=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate()));const wd=(x.getUTCDay()+6)%7;x.setUTCDate(x.getUTCDate()-wd);return "Sem. du "+x.toISOString().slice(0,10);}
function groups(kind){const m={};D.trades.forEach(t=>{const k=periodKey(t.t,kind);m[k]=m[k]||{v:0,a:0,n:0,items:{}};if(t.s)m[k].v+=t.net;else m[k].a+=-t.net;m[k].n++;m[k].items[t.n]=(m[k].items[t.n]||0)+t.net;});return Object.entries(m).sort((a,b)=>a[0]<b[0]?-1:1);}

function render(id){
 if(id==="apercu")return apercu();
 if(id==="historique")return historique();
 if(id==="objectifs")return objectifs();
 if(id==="vente")return vente();
 if(id==="rentabilite")return rentabilite();
 if(id==="nft")return nftTab();
 if(id==="skills")return skillsTab();
 if(id==="ressources")return ressources();
 if(id==="echanges")return echanges();
 if(id==="compteurs")return compteurs();
}

const PERIODS=[["jour","Aujourd'hui",1],["7","7 jours",7],["30","30 jours",30],["tout",STARTFR?"Depuis le "+STARTFR.slice(0,5):"Depuis le début",null]];
function tradesFor(p){if(p===null)return GT();if(p===1){const d=new Date();d.setHours(0,0,0,0);return GT().filter(t=>t.t>=d.getTime());}return inLast(p);}
function totals(a){const v=sum(a.filter(t=>t.s),t=>t.net),ac=-sum(a.filter(t=>!t.s),t=>t.net),tax=sum(a.filter(t=>t.s),t=>t.g-t.net);return {v,ac,net:v-ac,tax,n:a.length};}
function byResource(a){const m={};a.forEach(t=>{const r=m[t.n]=m[t.n]||{qs:0,gs:0,vs:0,qb:0,gb:0};if(t.s){r.qs+=t.q;r.gs+=t.g;r.vs+=t.net;}else{r.qb+=t.q;r.gb+=t.g;}});
 return Object.entries(m).map(([n,r])=>({n,...r,net:r.vs-r.gb})).sort((x,y)=>Math.abs(y.net)-Math.abs(x.net));}
function apercu(){
 const T=PERIODS.map(([k,l,d])=>[k,l,totals(tradesFor(d))]);
 const first=STARTFR||(D.trades.length?new Date(D.trades[0].t).toLocaleDateString("fr-FR"):"—");
 const row=(label,f,cls)=>`<tr><th>${label}</th>${T.map(([k,l,x])=>{const v=f(x);return `<td><div class="bub ${cls?cls(v):""}">${sg(v)}</div></td>`}).join("")}</tr>`;
 let per;try{per=localStorage.getItem("per")}catch(e){};if(!PERIODS.some(p=>p[0]===per))per="30";
 const wk=totals(tradesFor(7)),td=totals(tradesFor(1));
 document.getElementById("apercu").innerHTML=
 `<div class="hero"><div><div class="l">Cette semaine</div><div class="big ${wk.net>=0?"pos":"neg"}">${sg(wk.net)} FLW</div></div>
  <div><div class="l">Aujourd'hui</div><div class="big ${td.net>=0?"pos":"neg"}">${sg(td.net)} FLW</div></div>
  <div><div class="l">Objectif</div><div class="big" style="font-size:20px">${wk.net>=0?"✅ Dans le vert":"⚠️ Dans le rouge"} cette semaine</div></div></div>
 <div class="card"><h2>📈 Courbe de tes gains (cumul, comme un cours de bourse)</h2><div class="controls" id="cum_per">${[["7","7 jours"],["30","1 mois"],["tout",STARTFR?"Depuis le "+STARTFR.slice(0,5):"Depuis le début"]].map(([k,l])=>`<button class="chip" data-k="${k}">${l}</button>`).join("")}</div><div class="chart"><canvas id="c_cum"></canvas></div><div class="sub" id="cum_note"></div></div>
 <div class="card"><h2>Ton état global (marché, après la taxe de 7,5 %)</h2><div class="scroll"><table class="matrix">
  <tr><th></th>${T.map(([k,l])=>`<th>${l}</th>`).join("")}</tr>
  ${row("💰 Gagné (ventes − achats)",x=>x.net,v=>v>=0?"pos":"neg")}
  ${row("📤 Ventes",x=>x.v,()=> "pos")}
  ${row("📥 Achats",x=>-x.ac,()=> "neg")}
  ${row("🧾 Taxe payée",x=>-x.tax,()=> "neg")}
  <tr><th>Nombre d'échanges</th>${T.map(([k,l,x])=>`<td>${x.n}</td>`).join("")}</tr>
 </table></div><div class="sub">Les gains sont comptés à partir du ${first} (ton nouveau départ, réglable avec <code>date_depart</code> dans <code>ma_ferme.json</code>). Les échanges plus anciens restent dans Historique et Échanges.</div></div>
 <div class="card"><h2>Détail par ressource</h2><div class="controls" id="per_chips">${PERIODS.map(([k,l])=>`<button class="chip ${k===per?"on":""}" data-k="${k}">${l}</button>`).join("")}</div><div class="scroll" id="res_tab"></div></div>
 <div class="card"><h2>Gagné par jour (30 derniers jours)</h2><div class="chart"><canvas id="c_ap"></canvas></div></div>
 <div class="card"><h2>⚠️ Ventes à plus de 10 % sous le prix du marché (30 jours)</h2><div id="warn"></div></div>`;
 const drawRes=k=>{const d=PERIODS.find(p=>p[0]===k)[2];const rows=byResource(tradesFor(d));
  document.getElementById("res_tab").innerHTML=rows.length?`<table><tr><th>Ressource</th><th>Vendu</th><th>Prix moyen de vente</th><th>Total ventes</th><th>Acheté</th><th>Prix moyen d'achat</th><th>Total achats</th><th>Gagné</th><th>Prix du marché</th></tr>
  ${(()=>{const tv=sum(rows,r=>r.vs),tb=sum(rows,r=>r.gb),tn=tv-tb;return `<tr style="background:var(--card2,rgba(127,127,127,.12))"><td><b>🧮 TOTAL</b></td><td></td><td></td><td class="pos"><b>${sg(tv)}</b></td><td></td><td></td><td class="neg"><b>${sg(-tb)}</b></td><td class="${tn>=0?"pos":"neg"}"><b>${sg(tn)}</b></td><td></td></tr>`})()}
  ${rows.map(r=>`<tr><td>${nm(r.n)}</td><td>${r.qs?fr(r.qs,0):"—"}</td><td>${r.qs?fp(r.gs/r.qs):"—"}</td><td class="pos">${r.qs?sg(r.vs):"—"}</td><td>${r.qb?fr(r.qb,0):"—"}</td><td>${r.qb?fp(r.gb/r.qb):"—"}</td><td class="neg">${r.qb?sg(-r.gb):"—"}</td><td class="${r.net>=0?"pos":"neg"}"><b>${sg(r.net)}</b></td><td>${fp(D.now[r.n])}</td></tr>`).join("")}</table>
  <div class="sub">Prix moyens avant taxe. « Total ventes » est après la taxe de 7,5 %.</div>`:`<div class="empty">Aucun échange sur cette période.</div>`;};
 document.querySelectorAll("#per_chips .chip").forEach(b=>b.onclick=()=>{document.querySelectorAll("#per_chips .chip").forEach(x=>x.classList.toggle("on",x===b));try{localStorage.setItem("per",b.dataset.k)}catch(e){};drawRes(b.dataset.k);});
 drawRes(per);
 const m=inLast(30);const agg={};m.filter(t=>t.s).forEach(t=>{agg[t.n]=agg[t.n]||{q:0,g:0};agg[t.n].q+=t.q;agg[t.n].g+=t.g;});
 const warn=Object.entries(agg).map(([n,a])=>{const u=a.g/a.q,mk=D.now[n];return {n,u,mk,gap:mk?(u-mk)/mk*100:null,lost:mk&&u<mk?(mk-u)*a.q*0.925:0}}).filter(x=>x.gap!=null&&x.gap<-10).sort((a,b)=>b.lost-a.lost);
 document.getElementById("warn").innerHTML=warn.length?`<table><tr><th>Ressource</th><th>Ton prix moyen</th><th>Marché aujourd'hui</th><th>Écart</th><th>Manque à gagner</th></tr>${warn.map(x=>`<tr><td>${nm(x.n)}</td><td>${fp(x.u)}</td><td>${fp(x.mk)}</td><td class="warn">${fr(x.gap,0)} %</td><td class="warn">${fr(x.lost)}</td></tr>`).join("")}</table>`:`<div class="empty">Aucune 👍</div>`;
 const drawCum=k=>{let cp=k;try{localStorage.setItem("cumper",k)}catch(e){};document.querySelectorAll("#cum_per .chip").forEach(b=>b.classList.toggle("on",b.dataset.k===k));
  let gall=groups("jour").filter(x=>!D.start||x[0]>=D.start);if(k!=="tout"){const lim=new Date(Date.now()-(+k)*864e5).toISOString().slice(0,10);gall=gall.filter(x=>x[0]>=lim);}
  let acc=0;const cum=gall.map(x=>acc+=x[1].v-x[1].a);
  document.getElementById("cum_note").textContent=gall.length?`Sur la période : ${sg(acc)} FLW (part de 0 au début de la période).`+(k==="tout"?` Compté depuis le ${STARTFR||gall[0][0].split("-").reverse().join("/")}.`:""):"Pas d'échange sur la période.";
  chart("c_cum",{type:"line",data:{labels:gall.map(x=>x[0].slice(8)+"/"+x[0].slice(5,7)),datasets:[{label:"Gain cumulé (FLW)",data:cum,borderColor:zeroSplit,fill:{target:"origin",above:alpha(css("--sell"),.22),below:alpha(css("--buy"),.25)},pointBackgroundColor:cum.map(v=>v<0?css("--buy"):css("--sell")),pointBorderColor:cum.map(v=>v<0?css("--buy"):css("--sell")),tension:.3,pointRadius:3,borderWidth:2.5}]},options:Object.assign(baseOpts(),{plugins:{legend:{display:false}}})});};
 document.querySelectorAll("#cum_per .chip").forEach(b=>b.onclick=()=>drawCum(b.dataset.k));
 let cp0;try{cp0=localStorage.getItem("cumper")}catch(e){};drawCum(["7","30","tout"].includes(cp0)?cp0:"30");
 const g=groups("jour").slice(-30);
 chart("c_ap",{type:"bar",data:{labels:g.map(x=>x[0].slice(8)+"/"+x[0].slice(5,7)),datasets:[{label:"Gagné",data:g.map(x=>x[1].v-x[1].a),backgroundColor:g.map(x=>x[1].v-x[1].a>=0?css("--sell"):css("--buy"))}]},options:baseOpts()});
}

function historique(){
 const el=document.getElementById("historique");let kind;try{kind=localStorage.getItem("hk")}catch(e){};if(!["jour","semaine","mois"].includes(kind))kind="jour";
 el.innerHTML=`<div class="card"><div class="controls" id="hk">${[["jour","Par jour"],["semaine","Par semaine"],["mois","Par mois"]].map(([k,l])=>`<button class="chip ${k===kind?"on":""}" data-k="${k}">${l}</button>`).join("")}</div><div class="chart"><canvas id="c_hist"></canvas></div></div><div class="card scroll" id="h_tab"></div>`;
 const draw=k=>{const g=groups(k);
  document.getElementById("h_tab").innerHTML=g.length?`<table><tr><th>Période</th><th>Ventes</th><th>Achats</th><th>Gagné</th><th>Échanges</th></tr>${g.slice().reverse().map(([p,x])=>`<tr><td>${p}</td><td class="pos">${sg(x.v)}</td><td class="neg">${sg(-x.a)}</td><td class="${x.v-x.a>=0?"pos":"neg"}"><b>${sg(x.v-x.a)}</b></td><td>${x.n}</td></tr>`).join("")}</table>`:'<div class="empty">Pas encore de données.</div>';
  chart("c_hist",{type:"bar",data:{labels:g.map(x=>x[0]),datasets:[{type:"line",label:"Gagné",data:g.map(x=>x[1].v-x[1].a),borderColor:css("--ink"),backgroundColor:css("--ink"),tension:.25},{label:"Ventes",data:g.map(x=>x[1].v),backgroundColor:css("--sell")},{label:"Achats",data:g.map(x=>-x[1].a),backgroundColor:css("--buy")}]},options:baseOpts()});};
 document.querySelectorAll("#hk .chip").forEach(b=>b.onclick=()=>{document.querySelectorAll("#hk .chip").forEach(x=>x.classList.toggle("on",x===b));try{localStorage.setItem("hk",b.dataset.k)}catch(e){};draw(b.dataset.k);});
 draw(kind);
}

function objectifs(){
 const el=document.getElementById("objectifs"),G=D.goals;
 if(!G.length){el.innerHTML=conseilCard()+'<div class="card empty">Aucun objectif détaillé. Ajoute-les dans objectifs.json.</div>';bindConseil();return;}
 const done=G.filter(g=>g.fait).length,pct=Math.round(done/G.length*100);
 const groups={};G.forEach(g=>{(groups[g.groupe||"Autres"]=groups[g.groupe||"Autres"]||[]).push(g)});
 const nftLeft=sum(G.filter(g=>g.type==="nft"&&!g.fait&&g.prix),g=>g.prix);
 el.innerHTML=conseilCard()+`<div class="hero"><div><div class="l">Objectifs validés</div><div class="big">${done} / ${G.length}</div><div class="bar"><span style="width:${pct}%"></span></div></div>
  <div><div class="l">NFT encore à acheter</div><div class="big">${fr(nftLeft)} FLW</div><div class="l">au prix du jour</div></div></div>
 ${Object.entries(groups).map(([n,a])=>`<div class="card"><h2>${n} <span class="msum">${a.filter(g=>g.fait).length}/${a.length}</span></h2>
  ${a.map(g=>`<div class="goal ${g.fait?"ok":""}"><div class="gchk">${g.fait?"✅":"⬜"}</div><div class="gtxt"><div class="gt">${g.titre}</div>${g.info?`<div class="why">${g.info}</div>`:""}${g.note?`<div class="why">ℹ️ ${g.note}</div>`:""}</div>
   <div class="gcost">${g.type==="nft"&&!g.fait&&g.prix?`<b>${fr(g.prix)}</b> FLW`:g.cout_restant!=null&&!g.fait?`<b>${fr(g.cout_restant)}</b> FLW<div class="why">en ressources manquantes (sur ${fr(g.cout_total)})</div>`:""}</div></div>`).join("")}</div>`).join("")}
 <div class="sub">Validés automatiquement à chaque relevé : NFT achetés ou vendus, compétences, niveau, objectifs de la semaine. Les autres (« manuel ») se cochent dans <code>objectifs.json</code> en mettant <code>"fait": true</code>. Coûts au prix du marché du jour (coins au taux de 1 525, huile ≈ 0,10).</div>`;
 bindConseil();
}
const BUTS=[["flower","💰 Gagner plus de Flower (rendement)"],["niveau","⭐ Monter de niveau"],["agrandir","🏡 Agrandir la ferme"]];
function getBut(){let b;try{b=localStorage.getItem("but")}catch(e){};return BUTS.some(x=>x[0]===b)?b:(D.but||"flower");}
function conseilCard(){const b=getBut();return `<div class="card"><h2>🎯 Ton objectif principal</h2><div class="controls" id="but_chips">${BUTS.map(([k,l])=>`<button class="chip ${k===b?"on":""}" data-k="${k}">${l}</button>`).join("")}</div><div id="conseils">${conseils(b)}</div><div class="sub">Conseils calculés par l'outil à chaque relevé, avec ta production et les prix du jour.</div></div>`;}
function bindConseil(){document.querySelectorAll("#but_chips .chip").forEach(x=>x.onclick=()=>{try{localStorage.setItem("but",x.dataset.k)}catch(e){};document.querySelectorAll("#but_chips .chip").forEach(y=>y.classList.toggle("on",y===x));document.getElementById("conseils").innerHTML=conseils(x.dataset.k);});}
function conseils(b){
 const N=(D.nft||{}).rows||[],li=[];
 const buys=N.filter(r=>!r.owned&&!r.xp&&r.an_pct>=35&&r.jour>0.001).sort((a,b)=>b.an_pct-a.an_pct);
 const xpOwned=N.filter(r=>r.owned&&r.xp);
 if(b==="flower"){
  if(buys.length){const t=buys.slice(0,3);li.push(`🛒 <b>Meilleurs NFT à acheter</b> : ${t.map(r=>`<b>${r.n}</b> (${fr(r.price)} FLW → +${fp(r.jour)}/jour, ${fr(r.an_pct,0)} %/an, remboursé en ~${fr(r.rembourse_jours/30,0)} mois)`).join(" · ")}. Total : ${fr(sum(t,r=>r.price))} FLW pour +${fr(sum(t,r=>r.mois))} FLW/mois.`);}
  if(xpOwned.length)li.push(`💤 <b>À vendre</b> (ne rapportent que de l'XP) : ${xpOwned.map(r=>`${r.n} (~${fr(r.price)} FLW)`).join(", ")} → ${fr(sum(xpOwned,r=>r.price))} FLW à réinvestir.`);
  const al=(D.stock||[]).filter(r=>r.alert);if(al.length)li.push(`⚠️ <b>Tu vends trop bas</b> : ${al.map(r=>nm(r.n)).join(", ")} → regarde le « prix mini conseillé » dans l'onglet Vente.`);
  const bad=(D.costs||[]).filter(r=>r.cycle&&r.marge<0);if(bad.length)li.push(`🐄 <b>À perte</b> : ${bad.map(r=>r.item).join(", ")} (${bad.map(r=>fp(r.marge)).join(" / ")} par cycle). Ne les nourris que si une bounty les attend.`);
  const tr=(D.costs||[]).filter(r=>r.trade);if(tr.length)li.push(`🐷 <b>Cochons</b> : échange chaque cochon contre ses poils au niveau 10 (+${fp(tr[0].marge)} FLW chacun) ou 15 (+${fp(tr[1]?tr[1].marge:0)}), puis rachète-en un.`);
  const neg=(D.costs||[]).filter(r=>!r.cycle&&!r.trade&&r.marge<0);if(neg.length)li.push(`⛏️ <b>Produire coûte plus que vendre</b> : ${neg.map(r=>nm(r.item)).join(", ")} → ne les vends pas, garde-les pour tes outils (ou achète-les moins cher que ton coût).`);
 }else if(b==="niveau"){
  const xpAll=N.filter(r=>r.xp);
  li.push(`⭐ <b>NFT d'XP</b> : ${xpAll.map(r=>`${r.n} ${r.xp} — ${r.owned?"✅ tu l'as, garde-le":r.price?`${fr(r.price)} FLW`:"prix inconnu"}`).join(" · ")}.`);
  li.push(`🍳 L'XP vient surtout de la <b>cuisine</b> : cuisine avec tes propres cultures (pas achetées), en priorité les plats qui servent aussi aux livraisons.`);
  li.push(`💡 Monter de niveau donne des points de compétence : vise ceux qui rapportent des ressources (voir onglet Rentabilité), pas ceux qui donnent des coins si tu en as assez.`);
 }else{
  const keep=["Wood","Stone","Iron","Gold","Crimstone","Obsidian","Oil"];const st=(D.stock||[]).filter(r=>keep.includes(r.n));
  li.push(`🏡 <b>Garde tes matériaux</b> : un agrandissement demande surtout du bois, de la pierre, du fer et de l'or. Ne vends pas ces ressources tant que l'agrandissement n'est pas fait.`);
  if(st.length)li.push(`📦 Tu as : ${st.map(r=>`${nm(r.n)} ${fr(r.stock,0)}`).join(" · ")}.`);
  const mines=N.filter(r=>!r.xp&&/Mole|Golem|Nugget|Idol|Turtle|Beaver|Totem|Wendy|Peckster/.test(r.n)&&!r.owned&&r.an_pct>=35);
  if(mines.length)li.push(`⛏️ NFT qui produisent ces matériaux et restent rentables : ${mines.map(r=>`<b>${r.n}</b> (${fr(r.an_pct,0)} %/an)`).join(", ")}.`);
  li.push(`📝 Ajoute ton prochain agrandissement dans <code>objectifs.json</code> avec ses ressources : l'outil calcule ce qu'il te manque et combien ça coûterait au marché.`);
 }
 return li.length?li.map(x=>`<p class="plain">${x}</p>`).join(""):'<div class="empty">Rien à signaler 👍</div>';
}
function skillsTab(){
 const el=document.getElementById("skills"),K=(D.nft||{}).skills;
 if(!K){el.innerHTML='<div class="card empty">Compétences indisponibles (sfl.world n\'a pas répondu). Réessaie avec Actualiser.</div>';return;}
 const R=K.rows,own=R.filter(r=>r.owned),by=n=>R.find(r=>r.n===n);
 const best=K.meilleurs.map(by).filter(Boolean),weak=K.faibles.map(by).filter(Boolean);
 const ptsWeak=sum(weak,r=>r.points);
 const tips=[];
 if(K.libres>0)tips.push(`🎁 <b>Tu as ${K.libres} point(s) à placer.</b> ${best.length?"Meilleur choix : "+best.slice(0,3).map(r=>`<b>${r.n}</b> (${r.arbre}, ${r.points} pt → +${fp(r.jour)}/jour)`).join(", "):""}`);
 else tips.push(`✅ Tous tes points sont placés (${K.utilises} / ${K.niveau}).`);
 if(weak.length)tips.push(`🔄 <b>Au prochain reset</b>, ces compétences rapportent peu ou pas de Flower et ne bloquent rien : ${weak.map(r=>`${r.n} (${r.points} pt)`).join(", ")} → <b>${ptsWeak} point(s)</b> récupérables. Garde celles de confort si le temps gagné compte pour toi.`);
 if(best.length)tips.push(`📈 <b>Où les remettre</b> (les plus rentables par point, accessibles) : ${best.map(r=>`<b>${r.n}</b> (${r.arbre}, ${r.points} pt, +${fp(r.jour)}/jour)`).join(" · ")}.`);
 const lock=own.filter(r=>r.bloquant);if(lock.length)tips.push(`🔒 <b>À ne pas enlever</b> (elles débloquent le palier supérieur de leur arbre) : ${lock.map(r=>r.n).join(", ")}.`);
 const neg=own.filter(r=>r.jour!=null&&r.jour<0);if(neg.length)tips.push(`⚠️ <b>Te coûtent plus qu'elles ne rapportent</b> : ${neg.map(r=>r.n).join(", ")}.`);
 const row=r=>`<tr><td style="text-align:left;min-width:190px"><b>${r.n}</b>${r.rang>1?` <span class="why">rang ${r.rang}</span>`:""}<div class="why">🎁 ${r.effet}</div></td><td>${r.arbre}</td><td>${r.palier}</td><td>${r.points}</td><td>${r.type}</td><td class="${r.jour>0.001?"pos":r.jour<0?"neg":""}">${r.jour!=null?sg(r.jour):"—"}</td><td style="text-align:left">${r.verdict}</td></tr>`;
 const head=`<tr><th style="text-align:left">Compétence et ce qu’elle fait</th><th>Arbre</th><th>Palier</th><th>Points</th><th>Type</th><th>Gain / jour</th><th style="text-align:left">Verdict</th></tr>`;
 const others=R.filter(r=>!r.owned&&(r.jour||0)>0.001).sort((a,b)=>(b.par_point||0)-(a.par_point||0));
 el.innerHTML=(/^pas encore/.test((D.nft||{}).source||"")?`<div class="card"><p class="plain">⚠️ <b>Estimation provisoire</b> : tes compétences sont bien les tiennes, mais les gains en Flower utilisent une ferme type tant que ta production n'est pas mesurée (3 jours de relevés).</p></div>`:"")+`<div class="hero"><div><div class="l">Niveau et points</div><div class="big">${K.niveau}</div><div class="l">${K.utilises} points utilisés · ${K.libres} libre(s)</div></div><div><div class="l">Tes compétences chiffrables rapportent</div><div class="big pos">+${fr(K.total_jour*30)} FLW/mois</div><div class="l">+${fp(K.total_jour)} par jour (estimation)</div></div></div>
 <div class="card"><h2>💡 Conseils pour optimiser</h2>${tips.map(t=>`<p class="plain">${t}</p>`).join("")}</div>
 <div class="card"><h2>🌳 Tes arbres</h2><div class="scroll"><table><tr><th>Arbre</th><th>Points (paliers 1-2)</th><th>Palier atteint</th><th>Palier 2 à</th><th>Palier 3 à</th></tr>${K.arbres.map(a=>`<tr><td>${a.arbre}</td><td>${a.points}</td><td><b>${a.palier}</b></td><td>${a.seuil2} pts</td><td>${a.seuil3} pts</td></tr>`).join("")}</table></div></div>
 <div class="card"><h2>🧾 Tes compétences</h2><div class="scroll"><table>${head}${own.map(row).join("")}</table></div></div>
 <div class="card"><h2>🛒 Compétences qui rapporteraient des Flower (les plus rentables par point d'abord)</h2><div class="scroll"><table>${head}${others.map(row).join("")||'<tr><td colspan="7" class="empty">Rien de chiffrable à ajouter.</td></tr>'}</table></div>
 <div class="sub">Gains estimés avec ta production par jour (onglet NFT, en bas) et les prix du jour. Effets en anglais, tels qu'écrits dans le jeu. Le gain est calculé sur l'effet de base (rang 1). Les bonus de vitesse comptent pour moitié (la nuit, tu ne récoltes pas). « — » = effet qu'on ne peut pas chiffrer en Flower (confort, coins, XP, nourriture).</div></div>`;
}
function nftTab(){
 const el=document.getElementById("nft"),N=(D.nft||{}).rows||[],P=(D.nft||{}).prod||{};
 const own=N.filter(r=>r.owned),buy=N.filter(r=>!r.owned);
 const ownDay=sum(own,r=>r.jour),ownVal=sum(own,r=>r.price||0);
 const row=r=>`<tr><td style="text-align:left;min-width:190px"><b>${r.n}</b>${r.wearable?' <span class="why">(vêtement)</span>':""}<div class="why">🎁 ${r.effet||""}</div></td><td>${r.price?fr(r.price):"—"}</td><td class="${r.jour>0.001?"pos":""}">${r.xp?"XP":"+"+fp(r.jour)}</td><td>${r.xp?"—":"+"+fr(r.mois)}</td><td class="${r.cls}"><b>${r.an_pct!=null&&!r.xp?fr(r.an_pct,0)+" %":"—"}</b></td><td>${r.rembourse_jours?fr(r.rembourse_jours/30,0)+" mois":"—"}</td><td style="text-align:left"><span class="${r.cls}">${r.verdict}</span><div class="why">Calcul : ${r.why}</div></td></tr>`;
 const head=`<tr><th style="text-align:left">NFT et ce qu’il fait</th><th>Prix (FLW)</th><th>Gain / jour</th><th>Gain / mois</th><th>Rendement / an</th><th>Remboursé en</th><th style="text-align:left">Verdict</th></tr>`;
 el.innerHTML=(/^pas encore/.test((D.nft||{}).source||"")?`<div class="card"><p class="plain">⚠️ <b>Estimation provisoire</b> : ta production n'est pas encore mesurée (il faut 3 jours de relevés). En attendant, les gains sont calculés avec une ferme type et peuvent ne pas correspondre à ta ferme (ex. un NFT de fer alors que tu n'as presque pas de fer).</p></div>`:"")+`<div class="hero"><div><div class="l">Tes NFT à bonus rapportent</div><div class="big pos">+${fr(ownDay*30)} FLW/mois</div><div class="l">+${fp(ownDay)} par jour</div></div><div><div class="l">Ils valent (prix plancher)</div><div class="big">${fr(ownVal)} FLW</div><div class="l">soit ${ownVal?fr(ownDay*365/ownVal*100,0):"—"} %/an en moyenne</div></div></div>
 <div class="card"><h2>🧾 Tes NFT</h2><div class="sub">Rendement / an = ce qu'il rapporte en un an ÷ son prix. Un NFT reste à toi et se revend : au-dessus de ~35-40 %/an, c'est un bon placement.</div><div class="scroll"><table>${head}${own.map(row).join("")||'<tr><td colspan="7" class="empty">Aucun NFT à bonus détecté.</td></tr>'}</table></div></div>
 <div class="card"><h2>🛒 NFT que tu pourrais acheter (du plus rentable au moins rentable)</h2><div class="scroll"><table>${head}${buy.sort((a,b)=>(b.an_pct||-1)-(a.an_pct||-1)).map(row).join("")}</table></div></div>
 <div class="card"><h2>⚙️ Calculé avec ta production par jour</h2><p class="plain">${/^pas encore/.test((D.nft||{}).source||"")?"⚠️ <b>Production "+D.nft.source+".</b> Les gains des NFT et des compétences ne sont pas encore ceux de TA ferme : ils deviennent justes après 3 jours de relevés (l'outil mesure ce que tu produis chaque jour).":"✅ Production "+((D.nft||{}).source||"")+"."}</p><p class="plain">Pierre ${fr(P.Stone,0)} · Fer ${fr(P.Iron,0)} · Or ${fr(P.Gold,0)} · Crimstone ${fr(P.Crimstone,1)} · Bois ${fr(P.Wood,0)} coups/jour · ${fr(P.cycles_vaches,0)} cycles de vaches · ${fr(P.cycles_poules,0)} cycles de poules · champs/jour : ${Object.entries(P.recoltes||{}).map(([k,v])=>nm(k)+" "+fr(v,0)).join(", ")}.</p><div class="sub">Si ta ferme est différente, règle ces nombres dans <code>ma_ferme.json</code> → <code>"ma_production"</code>. Les vêtements (Milk Apron…) ne sont pas détectés : ajoute-les dans <code>"nft_possedes"</code>. Effets des NFT tirés du code du jeu ; prix plancher du jour. Les bonus de vitesse comptent pour moitié (la nuit, tu ne récoltes pas).</div></div>`;
}

const SIG={vendre:["🟢","Bon moment pour vendre","good"],normal:["⚪","Prix normal","mid"],attendre:["🟠","Attends si tu peux","wait"],garder:["🔵","À garder","keep"],cout:["🔴","Sous ton coût","bad"]};
function venteTable(rows,showKeep){return `<table><tr><th>Ressource</th><th style="text-align:left">Conseil</th><th>En stock</th>${showKeep?"<th>Réserve</th>":""}<th>Vendable</th><th>Prix du marché</th><th>Prix mini conseillé</th><th>Valeur vendable</th></tr>
 ${rows.map(r=>{const g=SIG[r.sig];return `<tr><td><b>${nm(r.n)}</b></td><td style="text-align:left"><span class="badge ${g[2]}">${g[0]} ${g[1]}</span><div class="why">${r.txt}</div>${r.alert?`<div class="why warn">⚠️ ${r.alert}</div>`:""}</td><td>${fr(r.stock,0)}</td>${showKeep?`<td>${r.keep?fr(r.keep,0):"—"}</td>`:""}<td><b>${fr(r.sellable,0)}</b></td><td>${fp(r.price)}</td><td>${fp(r.floor)}</td><td class="pos">${fr(r.value)}</td></tr>`}).join("")}</table>`;}
function vente(){
 const el=document.getElementById("vente");const S=D.stock;
 if(!S.length){el.innerHTML='<div class="card empty">Pas de stock vendable trouvé.</div>';return;}
 let vf;try{vf=localStorage.getItem("vf")}catch(e){};if(!["tout","vendre","normal","attendre","garder","cout"].includes(vf))vf="tout";
 const keepF=r=>vf==="tout"||r.sig===vf;
 const sale0=S.filter(r=>r.role==="vente"),farm0=S.filter(r=>r.role==="ferme"&&r.sellable>0),other0=S.filter(r=>r.role==="autre"&&r.value>=0.5);
 const sale=sale0.filter(keepF),farm=farm0.filter(keepF),other=other0.filter(keepF);
 const v=a=>sum(a,r=>r.value);const alerts=S.filter(r=>r.alert);
 const cnt=k=>S.filter(r=>(r.role!=="ferme"||r.sellable>0)&&(k==="tout"||r.sig===k)).length;
 el.innerHTML=`<div class="hero"><div><div class="l">🏷️ À vendre (ce que tu produis pour vendre)</div><div class="big pos">${fr(v(sale))} FLW</div></div>
  <div><div class="l">🌾 Surplus de ta ferme</div><div class="big">${fr(v(farm))} FLW</div><div class="l">au-delà de tes réserves</div></div>
  <div><div class="l">⚠️ Ventes récentes trop basses</div><div class="big ${alerts.length?"warn":""}" style="font-size:20px">${alerts.map(r=>nm(r.n)).join(", ")||"Aucune 👍"}</div></div></div>
 <div class="card"><div class="controls" id="vf">${[["tout","Tout"],["vendre","🟢 Bon moment pour vendre"],["normal","⚪ Prix normal"],["attendre","🟠 Attendre"],["garder","🔵 À garder"],["cout","🔴 Sous le coût"]].map(([k,l])=>`<button class="chip ${k===vf?"on":""}" data-k="${k}">${l} (${cnt(k)})</button>`).join("")}</div>
 <div class="controls"><input id="v_q" list="v_list" placeholder="🔎 Chercher une ressource de ton stock (ex. Pierre)" style="flex:1;min-width:220px;font-size:15px;padding:9px 12px"><datalist id="v_list">${S.map(r=>`<option value="${nm(r.n)}">`).join("")}</datalist></div><div id="v_res"></div></div>
 <div class="card"><h2>🏷️ Ce que tu produis pour vendre</h2><div class="scroll">${sale.length?venteTable(sale,false):'<div class="empty">Rien dans ce filtre.</div>'}</div></div>
 <div class="card"><h2>🌾 Pour ta ferme — seulement le surplus</h2><div class="sub">Tu les produis pour nourrir tes animaux ou fabriquer tes outils. Ne vends que ce qui dépasse ta réserve.</div><div class="scroll">${farm.length?venteTable(farm,true):'<div class="empty">Rien dans ce filtre.</div>'}</div></div>
 ${other.length?`<details class="card"><summary><b>Autres ressources en stock (${other.length})</b> · ${fr(v(other))} FLW</summary><div class="scroll" style="margin-top:10px">${venteTable(other,false)}</div></details>`:""}
 <div class="sub" id="v_note">Classement réglable dans <code>ma_ferme.json</code> : « a_vendre », « pour_ma_ferme », « stock_a_garder ». Le conseil compare le prix du jour aux 7 derniers jours (plus précis après ~5 jours d'historique) et à ton coût de production.</div>`;
 document.querySelectorAll("#vf .chip").forEach(b=>b.onclick=()=>{try{localStorage.setItem("vf",b.dataset.k)}catch(e){};vente();});
 const q=document.getElementById("v_q");
 q.oninput=()=>{const t=q.value.trim().toLowerCase();const out=document.getElementById("v_res");
  if(!t){out.innerHTML="";return;}
  const hit=S.filter(r=>nm(r.n).toLowerCase().includes(t)||r.n.toLowerCase().includes(t));
  out.innerHTML=hit.length?`<div class="scroll" style="margin-top:8px">${venteTable(hit,true)}</div>`:'<div class="empty">Pas dans ton stock vendable.</div>';};
}

function rentabilite(){
 const el=document.getElementById("rentabilite");const C=D.costs;
 const m=inLast(30);const sold={};m.filter(t=>t.s).forEach(t=>{sold[t.n]=sold[t.n]||{q:0,g:0};sold[t.n].q+=t.q;sold[t.n].g+=t.g;});
 const res=C.filter(r=>!r.cycle&&!r.trade),cyc=C.filter(r=>r.cycle),trd=C.filter(r=>r.trade);
 const real=res.map(r=>{const x=sold[r.item];if(!x)return null;const unet=x.g/x.q*0.925;return {item:r.item,q:x.q,unet,cost:r.cout,profit:x.q*(unet-r.cout)}}).filter(Boolean).sort((a,b)=>b.profit-a.profit);
 const realTot=sum(real,x=>x.profit);
 const cls=v=>v>=0?"pos":"neg";const pctm=r=>r.cout>0?fr(r.marge/r.cout*100,0)+" %":"—";
 el.innerHTML=`<div class="hero"><div><div class="l">💡 Ton bénéfice réel sur tes ventes (30 jours)</div><div class="big ${realTot>=0?"pos":"neg"}">${sg(realTot)} FLW</div><div class="l">ce que tu as vendu, moins la taxe et ce que t'a coûté sa production</div></div></div>
 <div class="card"><h2>💬 En clair (30 derniers jours)</h2>${real.length?`<p class="plain">${real[0].profit>0?`👍 Ce qui te rapporte le plus : <b>${nm(real[0].item)}</b> (${sg(real[0].profit)} FLW).`:""} ${real.filter(x=>x.profit<0).length?`👎 À revoir : <b>${real.filter(x=>x.profit<0).map(x=>nm(x.item)).join(", ")}</b> (vendu moins cher que ce que ça coûte à produire).`:"Tout ce que tu as vendu était rentable."}</p>
 <div class="scroll"><table><tr><th></th><th>Ressource</th><th>Quantité vendue</th><th>Prix net / unité</th><th>Coût / unité</th><th>Pour 100 vendues</th><th>Gagné au total</th></tr>
 ${real.map(x=>`<tr><td>${x.profit>=0?"✅":"❌"}</td><td><b>${nm(x.item)}</b></td><td>${fr(x.q,0)}</td><td>${fp(x.unet)}</td><td>${fp(x.cost)}</td><td class="${cls(x.profit)}">${sg((x.unet-x.cost)*100)}</td><td class="${cls(x.profit)}"><b>${sg(x.profit)} FLW</b></td></tr>`).join("")}
 </table></div>`:'<div class="empty">Pas de vente de ressource produite sur 30 jours.</div>'}</div>
 <div class="card"><h2>Coût de production d'une unité vs prix de vente (prix du jour)</h2>
 <div class="sub">Coût = outils (coins au taux de 1 FLW = 1 525 coins + ressources au prix du marché) ÷ ce que rapporte une action. Vente nette = prix du marché − 7,5 % de taxe. Rendements réglables dans <code>ma_ferme.json</code>.</div>
 <div class="scroll"><table><tr><th>Ressource</th><th>Coût / unité</th><th>dont coins</th><th>dont ressources</th><th>Vente nette / unité</th><th>Marge / unité</th><th>Marge</th><th>Ton prix de vente moyen (30 j)</th><th>Ta marge réelle</th><th>Recette</th></tr>
 ${res.map(r=>{const s=sold[r.item];const u=s?s.g/s.q*0.925:null;return `<tr><td>${nm(r.item)}</td><td>${fp(r.cout)}</td><td>${fp(r.cout_coins)}</td><td>${fp(r.cout_matieres)}</td><td>${fp(r.vente_nette)}</td><td class="${cls(r.marge)}"><b>${fp(r.marge)}</b></td><td class="${cls(r.marge)}">${pctm(r)}</td><td>${u!=null?fp(u):"—"}</td><td class="${u!=null?cls(u-r.cout):""}">${u!=null?fp(u-r.cout):"—"}</td><td style="text-align:left;color:var(--muted)">${r.detail}</td></tr>`}).join("")}
 </table></div></div>
 <div class="card"><h2>Animaux : marge par cycle (prix du jour, 2 caresses par cycle)</h2><div class="scroll"><table><tr><th>Animal</th><th>Coût de la nourriture</th><th>Production vendue (nette)</th><th>Marge par cycle</th><th>Détail</th></tr>
 ${cyc.map(r=>`<tr><td>${r.item}</td><td>${fp(r.cout)}</td><td>${fp(r.vente_nette)}</td><td class="${cls(r.marge)}"><b>${fp(r.marge)}</b></td><td style="text-align:left;color:var(--muted)">${r.detail}</td></tr>`).join("")}
 </table></div><div class="sub">Poules : production de base du jeu, sans tes bonus d'œufs (le vrai gain est un peu plus haut). Cochons : sans les poils, voir ci-dessous.</div></div>
 <div class="card"><h2>🐷 Échanger un cochon contre ses poils</h2><div class="scroll"><table><tr><th>Quand</th><th>Poils vendus (net)</th><th>Nouveau cochon</th><th>Gain par cochon</th><th>Pour tes 6 cochons</th></tr>
 ${trd.map(r=>`<tr><td>${r.item}</td><td>${fp(r.vente_nette)}</td><td>${fp(r.cout)}</td><td class="${cls(r.marge)}"><b>${sg(r.marge)} FLW</b></td><td class="${cls(r.marge)}"><b>${sg(r.marge*6)} FLW</b></td></tr>`).join("")}
 </table></div><div class="sub">En plus des truffes produites pendant la montée. Prix du poil au jour du relevé.</div></div>
 <div class="card"><h2>Évolution du coût de production</h2><div class="controls"><select id="cost_sel">${res.map(r=>`<option value="${r.item}">${nm(r.item)}</option>`).join("")}</select></div><div class="chart"><canvas id="c_cost"></canvas></div></div>`;
 const draw=()=>{const it=document.getElementById("cost_sel").value;const H=D.costHist;const mk={};D.prices.forEach(p=>mk[p.date]=p.prices[it]);
  chart("c_cost",{type:"line",data:{labels:H.map(h=>h.date),datasets:[{label:"Coût de production",data:H.map(h=>h.couts[it]??null),borderColor:css("--buy"),backgroundColor:css("--buy"),spanGaps:true},{label:"Vente nette",data:H.map(h=>mk[h.date]!=null?mk[h.date]*0.925:null),borderColor:css("--sell"),backgroundColor:css("--sell"),spanGaps:true}]},options:baseOpts()});};
 document.getElementById("cost_sel").onchange=draw;draw();
}

function ressources(){
 const el=document.getElementById("ressources");
 const all=new Set();Object.values(D.watch).forEach(a=>a.forEach(i=>all.add(i)));D.trades.forEach(t=>all.add(t.n));D.prices.forEach(p=>Object.keys(p.prices).forEach(k=>all.add(k)));
 const opts=[...all].filter(o=>D.prices.some(p=>p.prices[o]!=null)||D.trades.some(t=>t.n===o)).sort((a,b)=>nm(a).localeCompare(nm(b)));
 const quick=["Stone","Crimstone","Gold","Milk","Leather","Truffle","Pig Bristles","Iron","Wood","Barley","Wheat"].filter(q=>opts.includes(q));
 let sel;try{sel=localStorage.getItem("res")}catch(e){};if(!sel||!opts.includes(sel))sel="Stone";
 let per;try{per=localStorage.getItem("rper")}catch(e){};if(!per)per="90";
 el.innerHTML=`<div class="card"><div class="controls" id="r_quick">${quick.map(q=>`<button class="chip ${q===sel?"on":""}" data-k="${q}">${nm(q)}</button>`).join("")}
 <select id="r_sel">${opts.map(o=>`<option value="${o}" ${o===sel?"selected":""}>${nm(o)}</option>`).join("")}</select></div>
 <div class="ticker" id="r_head"></div>
 <div class="controls" id="r_per">${[["7","1 sem."],["30","1 mois"],["90","3 mois"],["180","6 mois"],["99999","Tout"]].map(([k,l])=>`<button class="chip ${k===per?"on":""}" data-k="${k}">${l}</button>`).join("")}</div>
 <div class="chart big"><canvas id="c_res"></canvas></div>
 <div class="sub">📈 Ligne : prix du marché chaque jour (un point par relevé). 🟢 ronds : tes ventes (prix moyen du jour). 🔺 : tes achats. Pointillés rouges : ce que te coûte la production d'une unité.</div></div>
 <div class="card scroll"><h2>Tes échanges sur cette ressource</h2><div id="r_tab"></div></div>`;
 const draw=()=>{const item=sel,days=+per;try{localStorage.setItem("res",item);localStorage.setItem("rper",per)}catch(e){}
  document.getElementById("r_sel").value=item;document.querySelectorAll("#r_quick .chip").forEach(b=>b.classList.toggle("on",b.dataset.k===item));
  const lim=Date.now()-days*864e5,limDay=new Date(lim).toISOString().slice(0,10);
  const ph=D.prices.filter(p=>p.date>=limDay&&p.prices[item]!=null);
  const tr=D.trades.filter(t=>t.n===item&&t.t>=lim);
  const labels=[...new Set([...ph.map(p=>p.date),...tr.map(t=>day(t.t))])].sort();
  const mk={};ph.forEach(p=>mk[p.date]=p.prices[item]);
  const cost={};D.costHist.forEach(h=>{if(h.couts[item]!=null)cost[h.date]=h.couts[item]});
  const sold={},bought={};tr.forEach(t=>{const d=day(t.t),o=t.s?sold:bought;o[d]=o[d]||{q:0,g:0};o[d].q+=t.q;o[d].g+=t.g;});
  const avg=o=>labels.map(d=>o[d]?o[d].g/o[d].q:null);
  const vals=ph.map(p=>p.prices[item]);const first=vals[0],now=D.now[item]??vals[vals.length-1];
  const ch=first&&now?(now-first)/first*100:null;const up=ch==null||ch>=0;
  document.getElementById("r_head").innerHTML=`<div class="tname">${nm(item)}</div><div class="tprice">${fp(now)} <span class="tunit">FLW / unité</span></div>
   <div class="tchg ${up?"pos":"neg"}">${ch==null?"":(up?"▲ ":"▼ ")+fr(Math.abs(ch),1)+" % sur la période"}</div>
   <div class="tmeta">Plus bas ${vals.length?fp(Math.min(...vals)):"—"} · Plus haut ${vals.length?fp(Math.max(...vals)):"—"} · ${vals.length} jour(s) de cours${D.costs.find(c=>c.item===item)?" · Coût de production "+fp(D.costs.find(c=>c.item===item).cout):""}</div>`;
  const col=up?css("--sell"):css("--buy");
  chart("c_res",{type:"line",data:{labels,datasets:[
   {label:"Prix du marché",data:labels.map(d=>mk[d]??null),borderColor:col,backgroundColor:c=>areaGrad(c,col),fill:true,spanGaps:true,tension:.25,pointRadius:labels.length>40?0:3,borderWidth:2.5},
   {label:"Tes ventes",data:avg(sold),borderColor:css("--sell"),backgroundColor:css("--sell"),spanGaps:true,tension:.25,borderWidth:2,pointRadius:6},
   {label:"Tes achats",data:avg(bought),borderColor:css("--buy"),backgroundColor:css("--buy"),spanGaps:true,tension:.25,borderWidth:2,borderDash:[6,4],pointRadius:7,pointStyle:"triangle"},
   {label:"Coût de production",data:labels.map(d=>cost[d]??null),borderColor:css("--warn"),borderDash:[6,5],pointRadius:0,spanGaps:true,fill:false,borderWidth:1.5}]},options:baseOpts()});
  document.getElementById("r_tab").innerHTML=tr.length?`<table><tr><th>Date</th><th>Type</th><th>Quantité</th><th>Prix unitaire</th><th>Marché ce jour</th><th>Net (FLW)</th></tr>${tr.slice().reverse().map(t=>`<tr><td>${new Date(t.t).toLocaleString("fr-FR",{dateStyle:"short",timeStyle:"short"})}</td><td>${t.s?"Vente":"Achat"}</td><td>${fr(t.q,0)}</td><td>${fp(t.g/t.q)}</td><td>${fp(mk[day(t.t)])}</td><td class="${t.net>=0?"pos":"neg"}">${sg(t.net)}</td></tr>`).join("")}</table>`:`<div class="empty">Aucun échange sur la période.</div>`;
  if(vals.length<3)document.getElementById("r_head").insertAdjacentHTML("beforeend",'<div class="tmeta">ℹ️ La courbe se remplit avec un point par jour de relevé : elle deviendra parlante dans quelques jours.</div>');
 };
 document.querySelectorAll("#r_quick .chip").forEach(b=>b.onclick=()=>{sel=b.dataset.k;draw();});
 document.getElementById("r_sel").onchange=e=>{sel=e.target.value;draw();};
 document.querySelectorAll("#r_per .chip").forEach(b=>b.onclick=()=>{per=b.dataset.k;document.querySelectorAll("#r_per .chip").forEach(x=>x.classList.toggle("on",x===b));draw();});
 draw();
}

function echanges(){
 const el=document.getElementById("echanges");
 el.innerHTML=`<div class="card"><div class="controls"><input id="e_q" placeholder="🔎 Filtrer une ressource (ex. Pierre)"><select id="e_t"><option value="">Achats et ventes</option><option value="v">Ventes</option><option value="a">Achats</option></select></div><div id="e_tab"></div></div>`;
 const MOIS=["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"];
 const open=new Set();
 const draw=()=>{const q=document.getElementById("e_q").value.toLowerCase(),ty=document.getElementById("e_t").value;
  const rows=D.trades.filter(t=>(!q||t.n.toLowerCase().includes(q)||nm(t.n).toLowerCase().includes(q))&&(!ty||(ty==="v")===t.s));
  const by={};rows.forEach(t=>{const k=new Date(t.t).toISOString().slice(0,7);(by[k]=by[k]||[]).push(t)});
  const keys=Object.keys(by).sort().reverse();if(!open.size&&keys.length)open.add(keys[0]);
  document.getElementById("e_tab").innerHTML=keys.length?keys.map(k=>{const a=by[k],v=sum(a.filter(t=>t.s),t=>t.net),ac=-sum(a.filter(t=>!t.s),t=>t.net);const[y,m]=k.split("-");
   return `<details class="month" data-k="${k}" ${open.has(k)?"open":""}><summary><b>📁 ${MOIS[+m-1]} ${y}</b><span class="msum">${a.length} échanges · ventes <span class="pos">${sg(v)}</span> · achats <span class="neg">${sg(-ac)}</span> · gagné <b class="${v-ac>=0?"pos":"neg"}">${sg(v-ac)}</b></span></summary><div class="scroll mbody"></div></details>`}).join(""):'<div class="empty">Aucun échange.</div>';
  const fill=d=>{const a=by[d.dataset.k].slice().reverse();d.querySelector(".mbody").innerHTML=`<table><tr><th>Date</th><th>Ressource</th><th>Type</th><th>Quantité</th><th>Prix à l'unité</th><th>Net (FLW)</th></tr>${a.map(t=>`<tr><td>${new Date(t.t).toLocaleString("fr-FR",{dateStyle:"short",timeStyle:"short"})}</td><td>${nm(t.n)}</td><td>${t.s?"Vente":"Achat"}</td><td>${fr(t.q,0)}</td><td>${fp(t.g/t.q)}</td><td class="${t.net>=0?"pos":"neg"}">${sg(t.net)}</td></tr>`).join("")}</table>`;};
  document.querySelectorAll("#e_tab details").forEach(d=>{if(d.open)fill(d);d.addEventListener("toggle",()=>{if(d.open){open.add(d.dataset.k);fill(d)}else{open.delete(d.dataset.k);d.querySelector(".mbody").innerHTML=""}})});
 };
 document.getElementById("e_q").oninput=draw;document.getElementById("e_t").onchange=draw;draw();
}

function compteurs(){
 const c=D.counters,el=document.getElementById("compteurs");
 el.innerHTML=`<div class="card"><h2>Compteurs du jeu dans le temps</h2><div class="chart"><canvas id="c_cpt"></canvas></div></div>
 <div class="card scroll"><table><tr><th>Date</th><th>Solde</th><th>Coins</th><th>Déposé</th><th>Retiré</th><th>Dépensé en jeu</th><th>Frais gems</th></tr>${c.slice().reverse().map(x=>`<tr><td>${x.date}</td><td>${fr(x.solde)}</td><td>${fr(x.coins,0)}</td><td>${fr(x.deposited)}</td><td>${fr(x.withdrawn)}</td><td>${fr(x.spent)}</td><td>${fr(x.gemFees)}</td></tr>`).join("")}</table></div>`;
 chart("c_cpt",{type:"line",data:{labels:c.map(x=>x.date),datasets:[{label:"Solde Flower",data:c.map(x=>x.solde),borderColor:css("--sell"),backgroundColor:css("--sell")},{label:"Retiré (cumul)",data:c.map(x=>x.withdrawn),borderColor:css("--market"),backgroundColor:css("--market")},{label:"Dépensé en jeu (cumul)",data:c.map(x=>x.spent),borderColor:css("--buy"),backgroundColor:css("--buy")}]},options:baseOpts()});
}

let start="apercu";try{start=localStorage.getItem("tab")||"apercu"}catch(e){}
show(TABS.some(t=>t[0]===start)?start:"apercu");
</script>
</body>
</html>
"""
