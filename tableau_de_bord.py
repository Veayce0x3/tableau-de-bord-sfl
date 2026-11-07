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
  <section id="bonus"></section>
  <section id="ressources"></section>
  <section id="echanges"></section>
  <section id="compteurs"></section>
  <section id="cycles"></section>
</main>
<script>
const D = /*__DATA__*/null;
let FARM;try{FARM=localStorage.getItem("farm")}catch(e){}
if(!D.farms.some(f=>f.id===FARM))FARM=D.farms[0].id;
function setFarm(id){const f=D.farms.find(x=>x.id===id);FARM=id;D.trades=f.trades;D.counters=f.counters;try{localStorage.setItem("farm",id)}catch(e){}}
setFarm(FARM);
const TABS=[["apercu","Aperçu"],["objectifs","Objectifs"],["vente","Vente"],["rentabilite","Rentabilité"],["nft","NFT"],["bonusgrp","Bonus et compétences"],["ressources","Une ressource"],["histgrp","Historique"]];
const GROUPS={bonusgrp:[["bonus","🧮 Mes bonus"],["skills","🎓 Compétences"]],histgrp:[["historique","📈 Gains"],["echanges","🔁 Échanges"],["compteurs","💳 Mon compte"],["cycles","📅 Saisons et cycles passés"]]};
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
function show(id){const grp=Object.keys(GROUPS).find(g=>g===id||GROUPS[g].some(x=>x[0]===id));let sub=id;
 if(grp&&grp===id){try{sub=localStorage.getItem("sub_"+grp)}catch(e){};if(!GROUPS[grp].some(x=>x[0]===sub))sub=GROUPS[grp][0][0];}
 if(grp){try{localStorage.setItem("sub_"+grp,sub)}catch(e){}}
 let sn=document.getElementById("subnav");if(!sn){sn=document.createElement("div");sn.id="subnav";sn.className="controls";sn.style.margin="0 0 12px";document.querySelector("main").prepend(sn);}
 sn.innerHTML=grp?GROUPS[grp].map(([k,l])=>`<button class="chip ${k===sub?"on":""}" data-sub="${k}">${l}</button>`).join(""):"";sn.style.display=grp?"":"none";
 sn.querySelectorAll("[data-sub]").forEach(b=>b.onclick=()=>show(b.dataset.sub));
 document.querySelectorAll("section").forEach(s=>s.classList.toggle("on",s.id===sub));nav.querySelectorAll("button").forEach(b=>b.classList.toggle("on",b.dataset.id===(grp||id)));try{localStorage.setItem("tab",grp||id)}catch(e){};render(sub);}
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
 if(id==="bonus")return bonusTab();
 if(id==="ressources")return ressources();
 if(id==="echanges")return echanges();
 if(id==="compteurs")return compteurs();
 if(id==="cycles")return cyclesTab();
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
 ${(()=>{const R=(D.stock||[]).filter(r=>r.price&&r.stock).map(r=>({n:nm(r.n),v:r.stock*r.price*0.925})),N=((D.nft||{}).rows||[]).filter(r=>r.owned&&r.price).map(r=>({n:r.n,v:r.price*0.925}));
  const vr=sum(R,x=>x.v),vn=sum(N,x=>x.v),top=[...R,...N].sort((a,b)=>b.v-a.v).slice(0,6);
  return `<details class="card"><summary style="cursor:pointer"><b>ℹ️ Informations : ce que vaut ton inventaire (${fr(vr+vn)} FLW)</b></summary><div class="hero" style="margin:8px 0 0"><div><div class="l">Total (si tu vendais tout, après taxe)</div><div class="big">${fr(vr+vn)} FLW</div></div><div><div class="l">📦 Ressources</div><div class="big" style="font-size:22px">${fr(vr)} FLW</div></div><div><div class="l">🧾 NFT à bonus (prix plancher)</div><div class="big" style="font-size:22px">${fr(vn)} FLW</div></div></div>
  <p class="plain">Ce qui pèse le plus : ${top.map(x=>`<b>${x.n}</b> ${fr(x.v)}`).join(" · ")}.</p><div class="sub">Prix du marché du jour − 7,5 % de taxe. Seuls les NFT à bonus sont comptés, au prix plancher (le moins cher en vente) ; les objets de déco et les coins ne sont pas comptés. C'est une valeur indicative : vendre beaucoup d'un coup ferait baisser le prix.</div></details>`})()}
 <div class="card"><h2>📈 Courbe de tes gains (cumul, comme un cours de bourse)</h2><div class="controls" id="cum_per">${[["7","7 jours"],["30","1 mois"],["tout",STARTFR?"Depuis le "+STARTFR.slice(0,5):"Depuis le début"]].map(([k,l])=>`<button class="chip" data-k="${k}">${l}</button>`).join("")}</div><div class="chart"><canvas id="c_cum"></canvas></div><div class="sub" id="cum_note"></div></div>
 <div class="card"><h2>Ton état global (marché, après la taxe de 7,5 %)</h2><div class="scroll"><table class="matrix">
  <tr><th></th>${T.map(([k,l])=>`<th>${l}</th>`).join("")}</tr>
  ${row("💰 Gagné (ventes − achats)",x=>x.net,v=>v>=0?"pos":"neg")}
  ${row("📤 Ventes",x=>x.v,()=> "pos")}
  ${row("📥 Achats",x=>-x.ac,()=> "neg")}
  ${row("🧾 Taxe payée",x=>-x.tax,()=> "neg")}
  <tr><th>Nombre d'échanges</th>${T.map(([k,l,x])=>`<td>${x.n}</td>`).join("")}</tr>
 </table></div><div class="sub">Les gains sont comptés à partir du ${first} (ton premier jour de suivi). Les échanges plus anciens restent dans Historique et Échanges.</div></div>
 <div class="card"><h2>📊 Tes ressources</h2>
 <div class="controls"><button class="chip on" id="mode_ferme">🌾 Ma ferme (récolté / utilisé)</button><button class="chip" id="mode_marche">🏪 Le marché (vendu / acheté)</button></div>
 <div class="controls" id="res_per"></div>
 <div id="pane_ferme"><div id="rj_tab"></div><div class="sub">Comme SFL Tool : stock en fin de journée − stock en début de journée, sans tes achats et ventes sur le marché. <b>Gagné</b> = ce que tu as récolté, miné, collecté… <b>Utilisé</b> = ce que tu as consommé (outils, nourriture, cuisine, bâtiments…). Valeur au prix du marché après taxe. Les jours sans relevé ne sont pas comptés.</div></div>
 <div id="pane_marche" style="display:none"><div class="scroll" id="res_tab"></div></div></div>
 <div class="card"><h2>Gagné par jour (30 derniers jours)</h2><div class="chart"><canvas id="c_ap"></canvas></div></div>
 <div class="card"><h2>⚠️ Ventes à plus de 10 % sous le prix du marché (30 jours)</h2><div id="warn"></div></div>`;
 const drawRes=k=>{const d=PERIODS.find(p=>p[0]===k)[2];const rows=byResource(tradesFor(d));
  document.getElementById("res_tab").innerHTML=rows.length?`<table><tr><th>Ressource</th><th>Vendu</th><th>Prix moyen de vente</th><th>Total ventes</th><th>Acheté</th><th>Prix moyen d'achat</th><th>Total achats</th><th>Gagné</th><th>Prix du marché</th></tr>
  ${(()=>{const tv=sum(rows,r=>r.vs),tb=sum(rows,r=>r.gb),tn=tv-tb;return `<tr style="background:var(--card2,rgba(127,127,127,.12))"><td><b>🧮 TOTAL</b></td><td></td><td></td><td class="pos"><b>${sg(tv)}</b></td><td></td><td></td><td class="neg"><b>${sg(-tb)}</b></td><td class="${tn>=0?"pos":"neg"}"><b>${sg(tn)}</b></td><td></td></tr>`})()}
  ${rows.map(r=>`<tr><td>${nm(r.n)}</td><td>${r.qs?fr(r.qs,0):"—"}</td><td>${r.qs?fp(r.gs/r.qs):"—"}</td><td class="pos">${r.qs?sg(r.vs):"—"}</td><td>${r.qb?fr(r.qb,0):"—"}</td><td>${r.qb?fp(r.gb/r.qb):"—"}</td><td class="neg">${r.qb?sg(-r.gb):"—"}</td><td class="${r.net>=0?"pos":"neg"}"><b>${sg(r.net)}</b></td><td>${fp(D.now[r.n])}</td></tr>`).join("")}</table>
  <div class="sub">Prix moyens avant taxe. « Total ventes » est après la taxe de 7,5 %.</div>`:`<div class="empty">Aucun échange sur cette période.</div>`;};
 const drawRJ=k=>{const X=((D.nft||{}).ressources||{})[k],el=document.getElementById("rj_tab");
  if(!X||!X.jours){el.innerHTML='<div class="empty">Pas encore de données pour cette période.</div>';return;}
  const g=sum(X.gagne,r=>r.v),u=sum(X.utilise,r=>r.v);
  const tb=(L,c)=>L.length?`<table><tr><th style="text-align:left">Ressource</th><th>Quantité</th><th>Valeur (FLW)</th></tr>${L.map(r=>`<tr><td style="text-align:left">${nm(r.n)}</td><td class="${c}">${sg(r.q)}</td><td class="${c}">${sg(r.v)}</td></tr>`).join("")}</table>`:'<div class="empty">Rien.</div>';
  el.innerHTML=`<div class="hero" style="margin:8px 0"><div><div class="l">➕ Gagné</div><div class="big pos">${sg(g)} FLW</div></div><div><div class="l">➖ Utilisé</div><div class="big neg">${sg(u)} FLW</div></div><div><div class="l">= Bilan (${X.jours} jour${X.jours>1?"s":""})</div><div class="big ${g+u>=0?"pos":"neg"}">${sg(g+u)} FLW</div></div></div>
  <div class="grid2" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px"><div><h3>➕ Gagné</h3><div class="scroll">${tb(X.gagne,"pos")}</div></div><div><h3>➖ Utilisé</h3><div class="scroll">${tb(X.utilise,"neg")}</div></div></div>`;};
 let RM="ferme";try{RM=localStorage.getItem("res_mode")||"ferme"}catch(e){}
 const drawResCard=()=>{const ferme=RM==="ferme";document.getElementById("mode_ferme").classList.toggle("on",ferme);document.getElementById("mode_marche").classList.toggle("on",!ferme);
  document.getElementById("pane_ferme").style.display=ferme?"":"none";document.getElementById("pane_marche").style.display=ferme?"none":"";
  const P=ferme?[["1","Aujourd'hui"],["7","7 jours"],["30","30 jours"]]:PERIODS.map(([k,l])=>[k==="jour"?"1":k,l]);
  let cur;try{cur=localStorage.getItem("res_per")||"1"}catch(e){cur="1"};if(!P.some(x=>x[0]===cur))cur="1";
  document.getElementById("res_per").innerHTML=P.map(([k,l])=>`<button class="chip ${k===cur?"on":""}" data-k="${k}">${l}</button>`).join("");
  document.querySelectorAll("#res_per .chip").forEach(x=>x.onclick=()=>{try{localStorage.setItem("res_per",x.dataset.k)}catch(e){};drawResCard();});
  if(ferme)drawRJ(cur);else drawRes(cur==="1"?"jour":cur);};
 document.getElementById("mode_ferme").onclick=()=>{RM="ferme";try{localStorage.setItem("res_mode",RM)}catch(e){};drawResCard();};
 document.getElementById("mode_marche").onclick=()=>{RM="marche";try{localStorage.setItem("res_mode",RM)}catch(e){};drawResCard();};
 drawResCard();
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
 const SZ=(D.nft||{}).saison,SFR={spring:"🌸 Printemps",summer:"☀️ Été",autumn:"🍂 Automne",winter:"❄️ Hiver"};
 const CY=(D.nft||{}).cycle;
 const cycleCard=CY&&CY.nfts.length?`<div><h2>📅 Bilan du cycle complet (${CY.partiel?"de l'"+(SFR[CY.saison_debut]||"").replace(/^\S+ /,"").toLowerCase()+" à l'hiver":"printemps → hiver"})</h2>
  <div class="sub">Une année du jeu = 4 saisons d'une semaine. Un retard pris une saison peut se rattraper la suivante : ce bilan te dit où tu en es sur tout le cycle, depuis le ${CY.debut.split("-").reverse().join("/")}${CY.partiel?" (cycle partiel : l'outil a commencé à suivre en cours d'année)":""}.</div>
  <div class="scroll"><table><tr><th style="text-align:left">NFT</th><th>Objectif sur tout le cycle</th><th>Ce que tu devrais avoir fait à ce jour</th><th>Fait</th><th style="text-align:left">Où tu en es</th></tr>
  ${CY.nfts.map(o=>{const d=o.fait!=null?o.fait-o.attendu:null,f=v=>fr(v,o.total<40?1:0);return `<tr><td style="text-align:left"><b>${o.nft}</b></td><td>${f(o.total)} ${o.unite}</td><td>${f(o.attendu)}</td><td>${o.fait!=null?f(o.fait):"—"}</td><td style="text-align:left" class="${d==null?"":d>=0?"pos":"neg"}">${d==null?"au prochain relevé":d>=0?"✅ en avance de "+f(d)+" "+o.unite:"⏳ en retard de "+f(-d)+" "+o.unite}${o.fait!=null?`<div class="why">il te reste ${f(Math.max(0,o.total-o.fait))} ${o.unite} à faire d'ici la fin de l'hiver</div>`:""}</td></tr>`}).join("")}</table></div></div>`:"";
 const AM=((D.nft||{}).rows||[]).filter(r=>r.owned&&r.amorti).sort((a,b)=>(a.amorti.mois??1e9)-(b.amorti.mois??1e9));
 const amoCard=AM.length?`<details class="card" open><summary style="cursor:pointer"><b>💳 Quand tes NFT seront remboursés</b> <span class="msum">${AM.filter(r=>r.amorti.reste<=0).length}/${AM.length} payés</span></summary>
  <div class="sub">Comme si tu les avais achetés le ${AM[0].amorti.debut.split("-").reverse().join("/")} (premier jour de suivi), au prix de ce jour-là. Chaque jour, l'outil ajoute ce que le NFT t'a rapporté avec ta production réelle. Plus tu produis, plus vite il est payé.</div>
  ${AM.map(r=>`<div class="goal ${r.amorti.reste<=0?"ok":""}"><div class="gchk">${r.amorti.reste<=0?"✅":"💳"}</div><div class="gtxt"><div class="gt"><b>${r.n}</b> : ${r.amorti.reste<=0?"remboursé ! Tout ce qu'il rapporte maintenant est du bénéfice.":`reste ${fr(r.amorti.reste)} FLW à rembourser${r.amorti.mois!=null?" · ≈ "+fr(r.amorti.mois,0)+" mois à ton rythme ("+fr(r.an_pct,0)+" %/an)":""}`}</div><div class="bar"><span style="width:${r.amorti.pct}%"></span></div><div class="why">${fr(r.amorti.fait)} / ${fr(r.amorti.prix)} FLW (${fr(r.amorti.pct,0)} %)</div></div></div>`).join("")}</details>`:"";
 const saisonCard=SZ?`<div class="card"><h2>🗓️ Objectifs de la saison : ${SFR[SZ.nom]||SZ.nom}</h2>
  <div class="controls">${["spring","summer","autumn","winter"].map(k=>`<span class="chip ${k===SZ.nom?"on":""}">${SFR[k]}</span>`).join(" → ")} </div><div class="controls"><button class="chip on" id="sz_btn">📆 Objectifs de cette saison</button><button class="chip" id="cy_btn">📅 Bilan du cycle complet</button></div>
  <div id="sz_pane">
  <div class="sub">Le cycle recommence chaque printemps. Pour chaque NFT que tu possèdes : ce qu'il faut faire <b>cette saison</b> pour qu'il te rapporte au moins 35 %/an. Suivi avec tes vrais compteurs depuis le ${SZ.debut.split("-").reverse().join("/")}${SZ.partielle?" (saison déjà commencée quand l'outil a commencé à la suivre : objectif indicatif)":""}.</div>
  ${(SZ.objectifs||[]).map(o=>{const pct=o.cible&&o.fait!=null?Math.min(100,o.fait/o.cible*100):0,ok=o.cible&&o.fait!=null&&o.fait>=o.cible;
   return `<div class="goal ${ok?"ok":""}"><div class="gchk">${o.cible==null?"💤":ok?"✅":"⬜"}</div><div class="gtxt"><div class="gt"><b>${o.nft}</b> : ${o.cible==null?o.texte:"faire au moins "+o.texte}</div><div class="why">🎁 ${o.quoi}${(()=>{const r=((D.nft||{}).rows||[]).find(x=>x.n===o.nft);return r&&r.an_pct?` · ℹ️ à ton rythme actuel : <b>${fr(r.an_pct,0)} %/an</b>${r.an_pct>35?" (bien au-dessus du minimum de 35 %)":""}`:""})()}</div>${o.cible!=null?`<div class="bar"><span style="width:${pct}%"></span></div><div class="why">${o.fait!=null?fr(o.fait,o.cible<20?1:0)+" / "+fr(o.cible,o.cible<20?1:0)+" ("+fr(pct,0)+" %)":"progression visible au prochain relevé"}</div>`:""}</div></div>`}).join("")||'<div class="empty">Aucun NFT à bonus chiffrable dans ton inventaire.</div>'}</div><div id="cy_pane" style="display:none">${cycleCard||'<div class="empty">Bilan disponible au prochain relevé.</div>'}</div></div>`:"";
 if(!G.length){el.innerHTML=saisonCard+amoCard+'<details class="card"><summary style="cursor:pointer"><b>🎯 Conseils selon ton objectif principal</b></summary>'+conseilCard()+'</details><div class="card"><h2>📝 Ma liste d\'objectifs</h2><div class="controls"><input id="obj_new" placeholder="Écris un objectif…" style="flex:1"><button class="chip" id="obj_add">➕ Ajouter</button></div></div>';const ob=document.getElementById("obj_add");if(ob)ob.onclick=()=>{const v=document.getElementById("obj_new").value.trim();if(v)postObj({action:"add",titre:v});};bindConseil();bindSz();return;}
 G.forEach((g,i)=>g._i=i);
 const done=G.filter(g=>g.fait).length,pct=Math.round(done/G.length*100);
 const groups={};G.forEach(g=>{(groups[g.groupe||"Autres"]=groups[g.groupe||"Autres"]||[]).push(g)});
 const nftLeft=sum(G.filter(g=>g.type==="nft"&&!g.fait&&g.prix),g=>g.prix);
 el.innerHTML=saisonCard+amoCard+`<details class="card"><summary style="cursor:pointer"><b>🎯 Conseils selon ton objectif principal</b></summary>${conseilCard()}</details><details class="card"><summary style="cursor:pointer"><b>📝 Ma liste d'objectifs (achats, compétences, niveau…)</b></summary><div class="controls" style="margin:8px 0"><input id="obj_new" placeholder="Écris un objectif : « augmenter la porcherie », « acheter Rocky the Mole », « niveau 100 », « prochain agrandissement »…" style="flex:1;min-width:240px"><button class="chip" id="obj_add">➕ Ajouter</button></div><div class="sub">L'outil comprend les bâtiments (porcherie, grange, poulailler + niveau), les NFT, les compétences, les niveaux et l'agrandissement, et calcule ce qu'il te manque. Le reste devient un objectif à cocher toi-même.</div><div class="hero"><div><div class="l">Objectifs validés</div><div class="big">${done} / ${G.length}</div><div class="bar"><span style="width:${pct}%"></span></div></div>
  <div><div class="l">NFT encore à acheter</div><div class="big">${fr(nftLeft)} FLW</div><div class="l">au prix du jour</div></div></div>
 ${Object.entries(groups).map(([n,a])=>`<div class="card"><h2>${n} <span class="msum">${a.filter(g=>g.fait).length}/${a.length}</span></h2>
  ${a.map(g=>`<div class="goal ${g.fait?"ok":""}"><div class="gchk">${g.fait?"✅":"⬜"}</div><div class="gtxt"><div class="gt">${g.titre}</div>${g.info?`<div class="why">${g.info}</div>`:""}${g.note?`<div class="why">ℹ️ ${g.note}</div>`:""}</div>
   <div class="gcost"><button class="chip" title="Marquer fait / pas fait" data-obj-fait="${g._i}">${g.fait?"↩️":"✅"}</button> <button class="chip" title="Enlever" data-obj-del="${g._i}">🗑️</button><br>${g.type==="nft"&&!g.fait&&g.prix?`<b>${fr(g.prix)}</b> FLW`:g.cout_restant!=null&&!g.fait?`<b>${fr(g.cout_restant)}</b> FLW<div class="why">en ressources manquantes (sur ${fr(g.cout_total)})</div>`:""}</div></div>`).join("")}</div>`).join("")}
 <div class="sub">Validés automatiquement à chaque relevé : NFT achetés ou vendus, compétences, niveau, objectifs de la semaine. Les autres se cochent avec le bouton ✅. Coûts au prix du marché du jour (coins au taux du jour, huile ≈ 0,10).</div></details>`;
 bindConseil();
 bindSz();
 const ob=document.getElementById("obj_add");if(ob)ob.onclick=()=>{const v=document.getElementById("obj_new").value.trim();if(v)postObj({action:"add",titre:v});};
}
function bindSz(){const a=document.getElementById("sz_btn"),b=document.getElementById("cy_btn");if(!a)return;const set=c=>{a.classList.toggle("on",!c);b.classList.toggle("on",c);document.getElementById("cy_pane").style.display=c?"":"none";document.getElementById("sz_pane").style.display=c?"none":"";};a.onclick=()=>set(false);b.onclick=()=>set(true);}
function postObj(body){if(!location.protocol.startsWith("http")){alert("Pour modifier tes objectifs, ouvre le tableau de bord avec l'appli « Ferme SFL » (ou « Lancer le relevé »).");return;}
 fetch("/objectifs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(r=>r.json()).then(j=>{if(!j.ok){alert(j.message);return;}
  const rb=document.getElementById("refresh");if(rb){rb.textContent="⏳ Mise à jour des objectifs…";rb.disabled=true;}
  fetch("/actualiser",{method:"POST"}).finally(()=>location.reload());}).catch(()=>alert("Le serveur ne répond pas. Relance l'appli « Ferme SFL »."));}
document.addEventListener("click",e=>{const t=e.target.closest("[data-obj-nft]");if(t){const n=decodeURIComponent(t.dataset.objNft);if(confirm("Ajouter « Acheter "+n+" » à tes objectifs ?"))postObj({action:"add",type:"nft",nom:n,titre:"Acheter "+n,groupe:"NFT à acheter"});}
 const d=e.target.closest("[data-obj-del]");if(d&&confirm("Enlever cet objectif ?"))postObj({action:"del",index:+d.dataset.objDel});
 const f=e.target.closest("[data-obj-fait]");if(f)postObj({action:"fait",index:+f.dataset.objFait});});
const BUTS=[["flower","💰 Gagner plus de Flower (rendement)"],["niveau","⭐ Monter de niveau"],["agrandir","🏡 Agrandir la ferme"],["equilibre","⚖️ Un peu de tout"]];
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
 }else if(b==="equilibre"){
  const t=buys[0];if(t)li.push(`🛒 <b>Un achat rentable</b> : ${t.n} (${fr(t.price)} FLW, ${fr(t.an_pct,0)} %/an).`);
  li.push(`🎯 <b>Garde une réserve</b> de bois, pierre, fer et or pour ton prochain bâtiment ou agrandissement (voir « Ma liste d'objectifs »).`);
  li.push(`⭐ <b>XP sans perdre de Flower</b> : cuisine avec tes propres cultures, surtout les plats qui servent aux livraisons.`);
  const al=(D.stock||[]).filter(r=>r.alert);if(al.length)li.push(`⚠️ <b>Ne vends pas trop bas</b> : ${al.map(r=>nm(r.n)).join(", ")}.`);
  li.push(`✅ <b>Chaque semaine</b> : finis dans le vert et remplis les objectifs de saison de tes NFT (en haut).`);
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
  li.push(`📝 Écris « prochain agrandissement » dans « Ma liste d'objectifs » (➕ Ajouter) : l'outil calcule ce qu'il te manque et combien ça coûterait au marché.`);
 }
 return li.length?li.map(x=>`<p class="plain">${x}</p>`).join(""):'<div class="empty">Rien à signaler 👍</div>';
}
function skillsTab(){
 const el=document.getElementById("skills"),K=(D.nft||{}).skills;
 if(!K){el.innerHTML='<div class="card empty">Compétences indisponibles (sfl.world n\'a pas répondu). Réessaie avec Actualiser.</div>';return;}
 const R=K.rows,own=R.filter(r=>r.owned),by=n=>R.find(r=>r.n===n);
 const weak=K.faibles.map(by).filter(Boolean),plan=(K.plan||[]).map(by).filter(Boolean);
 const pow=own.filter(r=>r.par_util!=null).sort((a,b)=>b.jour-a.jour);
 const earn=own.filter(r=>r.par_util==null&&r.jour!=null&&r.jour>0.001).sort((a,b)=>b.jour-a.jour);
 const lock=own.filter(r=>r.bloquant&&!earn.includes(r)&&!pow.includes(r));
 const other=own.filter(r=>!earn.includes(r)&&!pow.includes(r)&&!lock.includes(r));
 const tips=[];
 if(K.libres>0)tips.push(`🎁 <b>${K.libres} point(s) à placer maintenant.</b>`);
 if(pow.length)tips.push(`⚡ <b>Active tes pouvoirs dès qu'ils sont prêts</b> : ${pow.map(r=>`${r.n} (+${fp(r.par_util)} FLW à chaque fois)`).join(" · ")}. Ensemble ≈ +${fr(sum(pow,r=>r.jour)*30)} FLW/mois si tu n'en rates aucun.`);
 if(plan.length&&K.plan_gain>0.05)tips.push(`🔄 <b>Au prochain reset</b> : lâche ${weak.map(r=>r.n).join(", ")} (${K.plan_points} points qui rapportent peu ou pas de Flower) et prends <b>${plan.map(r=>r.n).join(", ")}</b> → <b>+${fr(K.plan_gain*30)} FLW/mois</b>.`);
 else if(weak.length)tips.push(`✅ <b>Rien d'important à changer au reset.</b> Les compétences qui rapportent peu (${weak.map(r=>r.n).join(", ")}) n'ont pas de meilleur remplaçant rentable pour ta ferme : garde-les si elles te font gagner du temps.`);
 if(lock.length)tips.push(`🔒 <b>Ne les enlève pas</b>, elles débloquent les compétences fortes de leur arbre : ${lock.map(r=>r.n).join(", ")}.`);
 const row=r=>`<tr><td style="text-align:left;min-width:200px"><b>${r.n}</b>${r.rang>1?` <span class="why">rang ${r.rang}</span>`:""}<div class="why">🎁 ${r.effet}</div></td><td>${r.arbre}</td><td>${r.points}</td><td class="${r.jour>0.001?"pos":r.jour<0?"neg":""}">${r.jour!=null?sg(r.jour*30)+" /mois":"—"}</td><td style="text-align:left">${r.verdict}</td></tr>`;
 const tab=(t,L,d)=>L.length?`<div class="card"><h2>${t}</h2>${d?`<div class="sub">${d}</div>`:""}<div class="scroll"><table><tr><th style="text-align:left">Compétence et ce qu’elle fait</th><th>Arbre</th><th>Points</th><th>Rapporte</th><th style="text-align:left">Verdict</th></tr>${L.map(row).join("")}</table></div></div>`:"";
 const others=R.filter(r=>!r.owned&&(r.jour||0)>0.001).sort((a,b)=>(b.par_point||0)-(a.par_point||0)).slice(0,12);
 el.innerHTML=(/^pas encore/.test((D.nft||{}).source||"")?`<div class="card"><p class="plain">⚠️ <b>Ta ferme n'a pas pu être lue</b> : les gains ci-dessous sont approximatifs. Réessaie 🔄 Actualiser.</p></div>`:"")+
 `<div class="hero"><div><div class="l">Niveau ${K.niveau}</div><div class="big">${K.utilises} pts</div><div class="l">utilisés · ${K.libres} libre(s)</div></div></div>
 <div class="card"><h2>💡 Ce que je te conseille</h2>${tips.map(t=>`<p class="plain">${t}</p>`).join("")}</div>
 ${totauxCard()}
 ${tab("💰 Celles qui te rapportent",earn,"Classées de celle qui rapporte le plus à celle qui rapporte le moins, avec ta ferme actuelle.")}
 ${tab("⚡ Tes pouvoirs à activer",pow,"Ils ne rapportent que si tu les actives. Gain par mois si tu les utilises à chaque fois qu'ils sont prêts.")}
 ${tab("🔒 Celles qui débloquent un palier",lock,"Elles rapportent peu, mais les enlever bloquerait les compétences fortes de leur arbre.")}
 ${tab("🖐️ Les autres (confort, coins, nourriture, XP)",other,"Pas de gain direct en Flower : elles font gagner du temps, des coins, de l'XP ou changent la nourriture des animaux.")}
 ${tab("🛒 Compétences qui rapporteraient le plus si tu les prenais",others,"Les plus rentables par point, avec ta ferme actuelle. « 🔒 » = il faut d'abord plus de points dans l'arbre.")}
 <div class="card"><h2>🌳 Tes arbres</h2><div class="scroll"><table><tr><th>Arbre</th><th>Points</th><th>Palier atteint</th><th>Palier 2 à</th><th>Palier 3 à</th></tr>${K.arbres.map(a=>`<tr><td>${a.arbre}</td><td>${a.points}</td><td><b>${a.palier}</b></td><td>${a.seuil2} pts</td><td>${a.seuil3} pts</td></tr>`).join("")}</table></div>
 <div class="sub">Gains calculés avec ta ferme (rochers, arbres, champs, animaux) et tes habitudes, aux prix du jour, sur l'effet de base (rang 1). Les pouvoirs ne comptent pas la nourriture des animaux.</div></div>`;
}
function sliderHTML(r){const c=r.pot.cur,mx=Math.max(c.max,c.actu)*1.0,st=mx>50?1:0.1;
 return `<div class="sim" style="margin-top:6px;padding:8px;border:1px dashed var(--line,#ccc);border-radius:8px" data-sim="${encodeURIComponent(JSON.stringify({c,price:r.price,base:r.jour}))}">
  <div><b>🎚️ Et si je faisais…</b> <span class="sim_v"></span> ${c.unite}</div>
  <input type="range" min="0" max="${mx.toFixed(1)}" step="${st}" value="${c.actu.toFixed(1)}" style="width:100%">
  <div class="sim_out"></div></div>`;}
function simUpdate(box){const d=JSON.parse(decodeURIComponent(box.dataset.sim)),c=d.c,x=+box.querySelector("input").value;
 const g=Math.max(0,d.base+(x-c.actu)*c.gain_u),an=g*365/d.price*100,mo=g>0.0001?d.price/g/30:null;
 const note=mo==null?"🔴 Pas rentable":mo<12?"🟢 Très rentable":mo<24?"🟡 Correct":mo<36?"🟠 Moyen":"🔴 Pas rentable";
 box.querySelector(".sim_v").textContent=fr(x,x<20?1:0);
 let t=`→ <b>${note}</b> · ${fr(an,0)} %/an · ${mo!=null?"remboursé en "+fr(mo,0)+" mois":"jamais remboursé"} · +${fr(g*30)} FLW/mois`;
 if(c.alt&&x!==c.actu){const dx=x-c.actu,ech=dx*c.echange_u*30,net=(x-c.actu)*c.gain_u*30+ech;
  t+=`<br>🔄 ${dx>0?"Ces champs seraient pris sur ton "+c.alt:"Ces champs repasseraient en "+c.alt} : ${ech>=0?"tu y gagnes":"tu y perds"} <b>${fr(Math.abs(ech))} FLW/mois</b> en valeur de récolte (${c.culture} contre ${c.alt}, tes bonus sur le ${c.alt} compris).<br>➡️ <b>Bilan pour toute ta ferme : ${sg(net)} FLW/mois.</b>`;}
 box.querySelector(".sim_out").innerHTML=t;}
document.addEventListener("input",e=>{const b=e.target.closest(".sim");if(b)simUpdate(b);});
document.addEventListener("toggle",e=>{const b=e.target.querySelector&&e.target.querySelector(".sim");if(b)simUpdate(b);},true);
function nftTab(){
 const el=document.getElementById("nft"),N=(D.nft||{}).rows||[],P=(D.nft||{}).prod||{};
 const own=N.filter(r=>r.owned),buy=N.filter(r=>!r.owned);
 const ownDay=sum(own,r=>r.jour),ownVal=sum(own,r=>r.price||0);
 const row=r=>`<tr><td style="text-align:left;min-width:190px">${!r.owned&&r.price?`<button class="chip" title="En faire un objectif" data-obj-nft="${encodeURIComponent(r.n)}">🎯</button> `:""}<b>${r.n}</b>${r.wearable?' <span class="why">(vêtement)</span>':""}<div class="why">🎁 ${r.effet||""}</div></td><td>${r.price?fr(r.price):"—"}</td><td class="${r.jour>0.001?"pos":""}">${r.xp?"XP":"+"+fp(r.jour)}</td><td>${r.xp?"—":"+"+fr(r.mois)}</td><td class="${r.cls}"><b>${r.an_pct!=null&&!r.xp?fr(r.an_pct,0)+" %":"—"}</b></td><td>${r.rembourse_jours?fr(r.rembourse_jours/30,0)+" mois":"—"}</td><td style="text-align:left;min-width:280px">${r.pas_pour_toi&&!r.owned?`<div><b>🚫 Pas pour toi</b> : ${r.pas_pour_toi}.</div>`:""}${r.note&&!(r.pas_pour_toi&&!r.owned)?`<div><b>${r.note}</b>${r.an_pct!=null?` · ${fr(r.an_pct,0)} %/an`:""}${r.rembourse_jours?` · remboursé en ${fr(r.rembourse_jours/30,0)} mois`:""}${r.jour>0.001?` · +${fr(r.mois)} FLW/mois`:""}</div>`:""}
  ${r.pot?`<div class="why">👉 ${r.pot.actuel}</div>`:""}
  ${r.pot&&r.pot.opt&&r.an_max!=null?(r.an_max>(r.an_pct||0)*1.15?`<div class="why">💡 Jusqu'à <b>${fr(r.an_max,0)} %/an</b>${r.mois_max?` (remboursé en ${fr(r.mois_max,0)} mois)`:""} ${r.pot.opt}</div>`:`<div class="why">✅ Tu en tires déjà presque tout.</div>`):""}
  ${r.amorti?`<div><b>💳 Amorti ${fr(r.amorti.pct,0)} %</b> (${fr(r.amorti.fait)} / ${fr(r.amorti.prix)} FLW) · reste ${fr(r.amorti.reste)} FLW${r.amorti.mois!=null?` ≈ ${fr(r.amorti.mois,0)} mois à ton rythme`:""}</div><div class="bar"><span style="width:${r.amorti.pct}%"></span></div>`:""}${r.note?"":`<span class="${r.cls}">${r.verdict}</span>`}<details><summary class="why" style="cursor:pointer">ℹ️ détail du calcul</summary><div class="why">${r.note?r.verdict+" · ":""}${r.why}</div></details></td></tr>`;
 const SK=[["n","NFT et ce qu’il fait"],["price","Prix (FLW)"],["jour","Gain / jour"],["mois","Gain / mois"],["an_pct","Rendement / an"],["rembourse_jours","Remboursé en"],[null,"Verdict"]];
 const head=`<tr>${SK.map(([k,l],i)=>`<th ${k?`data-sort="${k}" style="cursor:pointer;user-select:none;${i===0?"text-align:left":""}" title="Clique pour trier"`:'style="text-align:left"'}>${l}<span class="sarr"></span></th>`).join("")}</tr>`;
 let SORT={k:null,dir:0};
 const sorter=(a,b)=>{if(!SORT.k)return (b.chiffrable-a.chiffrable)||((b.an_pct??-1)-(a.an_pct??-1));const va=a[SORT.k],vb=b[SORT.k];
  if(SORT.k==="n")return SORT.dir*a.n.localeCompare(b.n);if(va==null&&vb==null)return 0;if(va==null)return 1;if(vb==null)return -1;return SORT.dir*(va-vb);};
 const bindSort=()=>document.querySelectorAll("#nft th[data-sort]").forEach(th=>{th.onclick=()=>{const k=th.dataset.sort;
  if(SORT.k!==k)SORT={k,dir:1};else if(SORT.dir===1)SORT={k,dir:-1};else SORT={k:null,dir:0};
  document.querySelectorAll("#nft th[data-sort] .sarr").forEach(x=>x.textContent="");if(SORT.k)document.querySelectorAll(`#nft th[data-sort="${SORT.k}"] .sarr`).forEach(x=>x.textContent=SORT.dir>0?" ▲":" ▼");
  drawOwn();draw();};});
 el.innerHTML=(/^pas encore/.test((D.nft||{}).source||"")?`<div class="card"><p class="plain">⚠️ <b>Ta ferme n'a pas pu être lue</b> (sfl.world n'a pas répondu). Les conseils d'achat sont masqués pour ne pas te conseiller un NFT inutile. Réessaie 🔄 Actualiser dans quelques minutes.</p></div>`:"")+`<div class="hero"><div><div class="l">Tes NFT à bonus rapportent</div><div class="big pos">+${fr(ownDay*30)} FLW/mois</div><div class="l">+${fp(ownDay)} par jour</div></div><div><div class="l">Ils valent (prix plancher)</div><div class="big">${fr(ownVal)} FLW</div><div class="l">soit ${ownVal?fr(ownDay*365/ownVal*100,0):"—"} %/an en moyenne</div></div></div>
 <div class="card"><h2>🧾 Tes NFT</h2><div class="sub">Rendement / an = ce qu'il rapporte en un an ÷ son prix. Un NFT reste à toi et se revend : au-dessus de ~35-40 %/an, c'est un bon placement.</div><div class="scroll"><table>${head}<tbody id="own_rows"></tbody></table></div></div>
 ${(()=>{const T=buy.filter(r=>r.price&&!r.pas_pour_toi&&r.note&&/🟢|🟡/.test(r.note)).sort((a,b)=>(b.an_pct||0)-(a.an_pct||0)).slice(0,8);
  return `<div class="card"><h2>🏆 Le top pour ta ferme</h2><div class="sub">Les NFT en vente qui te rapporteraient le plus, avec tes compétences, tes bonus, ce que tu produis vraiment et tes habitudes. Seulement ceux remboursés en moins de 2 ans. Change chaque jour selon les prix et ta façon de jouer.</div>
  ${T.length?`<div class="scroll"><table><tr><th style="text-align:left">NFT</th><th>Prix</th><th>Note</th><th>Rendement</th><th>Remboursé en</th><th style="text-align:left">Pourquoi</th></tr>${T.map(r=>`<tr><td style="text-align:left"><button class="chip" title="En faire un objectif" data-obj-nft="${encodeURIComponent(r.n)}">🎯</button> <b>${r.n}</b><div class="why">🎁 ${r.effet}</div></td><td>${fr(r.price)}</td><td>${r.note}</td><td><b>${fr(r.an_pct,0)} %/an</b></td><td>${fr(r.rembourse_jours/30,0)} mois</td><td style="text-align:left" class="why">${r.pot?r.pot.actuel:""}</td></tr>`).join("")}</table></div>`:'<div class="empty">Aucun NFT en vente ne se rembourse en moins de 2 ans avec ta façon de jouer actuelle.</div>'}</div>`;})()}
 <div class="card"><h2>🛒 Tous les NFT en vente, comparés à ta ferme</h2>
 <div class="controls" style="flex-wrap:wrap;gap:8px;align-items:center">
  <span>Prix de</span><input id="nf_min" type="number" min="0" step="10" style="width:90px"> <span>à</span><input id="nf_max" type="number" min="0" step="50" style="width:90px"><span>FLW</span>
  ${[[0,200],[200,1000],[1000,3000],[0,0]].map(([a,b])=>`<button class="chip" data-min="${a}" data-max="${b}">${b?a+" – "+b:"Tous"}</button>`).join("")}
  <label style="white-space:nowrap"><input type="checkbox" id="nf_ok"> Seulement ceux qui rapportent</label>
  <input id="nf_q" type="search" placeholder="Chercher un NFT…" style="min-width:160px">
 </div>
 <div class="sub" id="nf_count"></div>
 <div class="scroll"><table>${head}<tbody id="nf_rows"></tbody></table></div>
 <div class="sub">Triés du plus rentable au moins rentable pour TA ferme actuelle. « Effet non chiffrable » = bonus qui ne se mesure pas en Flower (marks, cuisine, pêche, confort…) : l'effet est quand même indiqué.</div></div>
 <div class="card"><h2>⚙️ Calculé avec ta production par jour</h2><p class="plain">${/^pas encore/.test((D.nft||{}).source||"")?"⚠️ <b>Production "+D.nft.source+".</b> Les gains des NFT et des compétences ne sont pas encore ceux de TA ferme : ils deviennent justes après 3 jours de relevés (l'outil mesure ce que tu produis chaque jour).":"✅ Production "+((D.nft||{}).source||"")+"."}</p><p class="plain">Pierre ${fr(P.Stone,0)} · Fer ${fr(P.Iron,0)} · Or ${fr(P.Gold,0)} · Crimstone ${fr(P.Crimstone,1)} · Bois ${fr(P.Wood,0)} coups/jour · ${fr(P.cycles_vaches,0)} cycles de vaches · ${fr(P.cycles_poules,0)} cycles de poules · champs/jour : ${Object.entries(P.recoltes||{}).map(([k,v])=>nm(k)+" "+fr(v,0)).join(", ")}.</p><div class="sub">Tout est lu automatiquement sur ta ferme à chaque relevé : rochers, arbres, champs, vaches, poules, vêtements portés (toi et tes Farm Hands), compétences, rendements et ton rythme réel. Effets des NFT tirés du code du jeu ; prix plancher du jour. Bonus de vitesse des cultures comptés à 100 % (si tes champs ne restent jamais vides) ; ceux des animaux à 50 % (la nuit, tu ne ramasses pas).</div></div>`;
 let F={min:0,max:200,ok:false,q:""};try{F=Object.assign(F,JSON.parse(localStorage.getItem("nf")||"{}"))}catch(e){}
 const mn=document.getElementById("nf_min"),mx=document.getElementById("nf_max"),ok=document.getElementById("nf_ok"),q=document.getElementById("nf_q");
 mn.value=F.min||0;mx.value=F.max||"";ok.checked=!!F.ok;q.value=F.q||"";
 const draw=()=>{F={min:+mn.value||0,max:+mx.value||0,ok:ok.checked,q:q.value.trim().toLowerCase()};try{localStorage.setItem("nf",JSON.stringify(F))}catch(e){}
  const L=buy.filter(r=>r.price&&r.price>=F.min&&(!F.max||r.price<=F.max)&&(!F.ok||(r.jour>0.001&&!r.xp))&&(!F.q||r.n.toLowerCase().includes(F.q)||(r.effet||"").toLowerCase().includes(F.q)))
   .sort(sorter);
  document.getElementById("nf_rows").innerHTML=L.map(row).join("")||'<tr><td colspan="7" class="empty">Aucun NFT dans cette tranche de prix.</td></tr>';
  document.getElementById("nf_count").textContent=`${L.length} NFT entre ${fr(F.min,0)} et ${F.max?fr(F.max,0):"∞"} FLW · ${L.filter(r=>r.jour>0.001&&r.an_pct>=35).length} rentables pour ta ferme (≥ 35 %/an)`;
  document.querySelectorAll("#nft .chip[data-min]").forEach(b=>b.classList.toggle("on",+b.dataset.min===F.min&&+b.dataset.max===F.max));};
 [mn,mx,ok].forEach(x=>x.onchange=draw);q.oninput=draw;mn.oninput=draw;mx.oninput=draw;
 document.querySelectorAll("#nft .chip[data-min]").forEach(b=>b.onclick=()=>{mn.value=b.dataset.min;mx.value=+b.dataset.max||"";draw();});
 const drawOwn=()=>{document.getElementById("own_rows").innerHTML=[...own].sort(sorter).map(row).join("")||'<tr><td colspan="7" class="empty">Aucun NFT à bonus détecté.</td></tr>';};
 bindSort();drawOwn();draw();
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
 <div class="sub" id="v_note">Le conseil compare le prix du jour aux 7 derniers jours (plus précis après ~5 jours d'historique) et à ton coût de production.</div>`;
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
 const bonV=res.filter(r=>r.marge>0).sort((a,b)=>b.marge/b.cout-a.marge/a.cout),malV=res.filter(r=>r.marge<0);
 const anim=cyc.slice().sort((a,b)=>b.marge-a.marge),perte=anim.filter(r=>r.marge<0);
 const bref=`<div class="card"><h2>📌 En bref</h2>
  <p class="plain">✅ <b>Rentable à produire pour vendre</b> : ${bonV.slice(0,5).map(r=>`${nm(r.item)} (se vend ${fr(r.vente_nette/r.cout,0)} fois ce qu’il te coûte)`).join(", ")||"rien pour l'instant"}.</p>
  ${malV.length?`<p class="plain">❌ <b>Te coûte plus cher à produire qu'il ne se vend</b> : ${malV.map(r=>nm(r.item)).join(", ")} → garde-le pour ta ferme, ne le vends pas.</p>`:""}
  <p class="plain">🐄 <b>Animaux</b> : le plus rentable par cycle est « ${anim[0]?anim[0].item:"—"} » (${anim[0]?sg(anim[0].marge):"—"} FLW).${perte.length?` À perte : ${perte.map(r=>r.item).join(", ")}.`:""}</p>
  ${trd.length?`<p class="plain">🐷 <b>Cochons</b> : les échanger contre leurs poils rapporte ${sg(trd[0].marge)} FLW chacun au niveau 10 et ${sg(trd[1]?trd[1].marge:0)} au niveau 15.</p>`:""}
  <div class="sub">Les tableaux détaillés sont ci-dessous (clique pour les ouvrir).</div></div>`;
 el.innerHTML=bref+`<div class="hero"><div><div class="l">💡 Ton bénéfice réel sur tes ventes (30 jours)</div><div class="big ${realTot>=0?"pos":"neg"}">${sg(realTot)} FLW</div><div class="l">ce que tu as vendu, moins la taxe et ce que t'a coûté sa production</div></div></div>
 <div class="card"><h2>💬 En clair (30 derniers jours)</h2>${real.length?`<p class="plain">${real[0].profit>0?`👍 Ce qui te rapporte le plus : <b>${nm(real[0].item)}</b> (${sg(real[0].profit)} FLW).`:""} ${real.filter(x=>x.profit<0).length?`👎 À revoir : <b>${real.filter(x=>x.profit<0).map(x=>nm(x.item)).join(", ")}</b> (vendu moins cher que ce que ça coûte à produire).`:"Tout ce que tu as vendu était rentable."}</p>
 <div class="scroll"><table><tr><th></th><th>Ressource</th><th>Quantité vendue</th><th>Prix net / unité</th><th>Coût / unité</th><th>Pour 100 vendues</th><th>Gagné au total</th></tr>
 ${real.map(x=>`<tr><td>${x.profit>=0?"✅":"❌"}</td><td><b>${nm(x.item)}</b></td><td>${fr(x.q,0)}</td><td>${fp(x.unet)}</td><td>${fp(x.cost)}</td><td class="${cls(x.profit)}">${sg((x.unet-x.cost)*100)}</td><td class="${cls(x.profit)}"><b>${sg(x.profit)} FLW</b></td></tr>`).join("")}
 </table></div>`:'<div class="empty">Pas de vente de ressource produite sur 30 jours.</div>'}</div>
 <details class="card"><summary style="cursor:pointer"><b>🧾 Détail : coût de production d'une unité vs prix de vente</b></summary>
 <div class="sub">Coût = outils (coins au taux du jour de SFL Tool + ressources au prix du marché) ÷ ce que rapporte une action. Vente nette = prix du marché − 7,5 % de taxe. Rendements lus sur ta ferme.</div>
 <div class="scroll"><table><tr><th>Ressource</th><th>Coût / unité</th><th>dont coins</th><th>dont ressources</th><th>Vente nette / unité</th><th>Marge / unité</th><th>Marge</th><th>Ton prix de vente moyen (30 j)</th><th>Ta marge réelle</th><th>Recette</th></tr>
 ${res.map(r=>{const s=sold[r.item];const u=s?s.g/s.q*0.925:null;return `<tr><td>${nm(r.item)}</td><td>${fp(r.cout)}</td><td>${fp(r.cout_coins)}</td><td>${fp(r.cout_matieres)}</td><td>${fp(r.vente_nette)}</td><td class="${cls(r.marge)}"><b>${fp(r.marge)}</b></td><td class="${cls(r.marge)}">${pctm(r)}</td><td>${u!=null?fp(u):"—"}</td><td class="${u!=null?cls(u-r.cout):""}">${u!=null?fp(u-r.cout):"—"}</td><td style="text-align:left;color:var(--muted)">${r.detail}</td></tr>`}).join("")}
 </table></div></details>
 <details class="card"><summary style="cursor:pointer"><b>🐄 Détail : animaux, marge par cycle</b></summary><h2 style="display:none">Animaux : marge par cycle (prix du jour, 2 caresses par cycle)</h2><div class="scroll"><table><tr><th>Animal</th><th>Coût de la nourriture</th><th>Production vendue (nette)</th><th>Marge par cycle</th><th>Détail</th></tr>
 ${cyc.map(r=>`<tr><td>${r.item}</td><td>${fp(r.cout)}</td><td>${fp(r.vente_nette)}</td><td class="${cls(r.marge)}"><b>${fp(r.marge)}</b></td><td style="text-align:left;color:var(--muted)">${r.detail}</td></tr>`).join("")}
 </table></div><div class="sub">Poules : production de base du jeu, sans tes bonus d'œufs (le vrai gain est un peu plus haut). Cochons : sans les poils, voir ci-dessous.</div></details>
 <div class="card"><h2>🐷 Échanger un cochon contre ses poils</h2><div class="scroll"><table><tr><th>Quand</th><th>Poils vendus (net)</th><th>Nouveau cochon</th><th>Gain par cochon</th><th>Pour 3 cochons</th><th>Pour 6</th><th>Pour 9</th></tr>
 ${trd.map(r=>`<tr><td>${r.item}</td><td>${fp(r.vente_nette)}</td><td>${fp(r.cout)}</td><td class="${cls(r.marge)}"><b>${sg(r.marge)} FLW</b></td><td class="${cls(r.marge)}">${sg(r.marge*3)}</td><td class="${cls(r.marge)}"><b>${sg(r.marge*6)}</b></td><td class="${cls(r.marge)}">${sg(r.marge*9)}</td></tr>`).join("")}
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
 if(!c.length){el.innerHTML='<div class="card empty">Pas encore de relevé.</div>';return;}
 const L=c[c.length-1],F=c[0],d=k=>(L[k]||0)-(F[k]||0);
 const net=(L.withdrawn||0)-(L.deposited||0);
 el.innerHTML=`<div class="hero"><div><div class="l">💰 Flower sur ton compte</div><div class="big">${fr(L.solde)}</div></div>
  <div><div class="l">📥 Déposés (depuis le début)</div><div class="big" style="font-size:22px">${fr(L.deposited)}</div></div>
  <div><div class="l">📤 Retirés (depuis le début)</div><div class="big" style="font-size:22px">${fr(L.withdrawn)}</div></div></div>
 <div class="card"><h2>💳 Ton compte en clair</h2>
  <p class="plain">Tu as <b>déposé ${fr(L.deposited)} FLW</b> et <b>retiré ${fr(L.withdrawn)} FLW</b> depuis le début : ${net>=0?`tu as déjà récupéré <b class="pos">${fr(net)} FLW de plus</b> que ce que tu as mis.`:`il te reste <b class="neg">${fr(-net)} FLW</b> à récupérer pour rentrer dans tes frais.`}</p>
  <p class="plain">Dans le jeu (hors marché) tu as <b>dépensé ${fr(L.spent)} FLW</b> au total, dont <b>${fr(L.gemFees)} FLW en gems</b>.</p>
  <p class="plain">Depuis le ${F.date.split("-").reverse().join("/")} (premier relevé) : solde ${sg(d("solde"))} · déposé ${sg(d("deposited"))} · retiré ${sg(d("withdrawn"))} · dépensé en jeu ${sg(d("spent"))} · gems ${sg(d("gemFees"))}.</p></div>
 ${(()=>{const usd=L.flower_usd,M=[];for(let i=1;i<c.length;i++){const a=c[i-1],b=c[i],r=b.flower_usd||usd;
   const dd=(b.deposited||0)-(a.deposited||0),dw=(b.withdrawn||0)-(a.withdrawn||0);
   if(dd>0.01)M.push({d:b.date,t:"📥 Dépôt",q:dd,r});if(dw>0.01)M.push({d:b.date,t:"📤 Retrait",q:dw,r});}
  if(!usd)return "";const $=v=>fr(v)+" $";
  return `<div class="card"><h2>💵 En dollars (USDC)</h2>
  <p class="plain">Cours du Flower aujourd'hui : <b>1 FLW = ${fr(usd,4)} $</b>.</p>
  <p class="plain">Ton solde de ${fr(L.solde)} FLW vaut <b>≈ ${$(L.solde*usd)}</b>.</p>
  <p class="plain">Avant le suivi (jusqu'au ${F.date.split("-").reverse().join("/")}), les cours de l'époque ne sont pas connus : au cours d'aujourd'hui, tes ${fr(F.deposited)} FLW déposés vaudraient ≈ ${$(F.deposited*usd)} et tes ${fr(F.withdrawn)} FLW retirés ≈ ${$(F.withdrawn*usd)}.</p>
  ${M.length?`<div class="scroll"><table><tr><th>Date</th><th>Mouvement</th><th>Flower</th><th>Cours ce jour-là</th><th>En dollars</th></tr>${M.slice().reverse().map(m=>`<tr><td>${m.d.split("-").reverse().join("/")}</td><td>${m.t}</td><td>${fr(m.q)}</td><td>${fr(m.r,4)} $</td><td><b>${$(m.q*m.r)}</b></td></tr>`).join("")}</table></div>
   <p class="plain">Depuis le début du suivi : déposé <b>${$(sum(M.filter(m=>m.t.includes("Dépôt")),m=>m.q*m.r))}</b> · retiré <b>${$(sum(M.filter(m=>m.t.includes("Retrait")),m=>m.q*m.r))}</b>.</p>`:`<div class="sub">À partir de maintenant, chaque dépôt et chaque retrait sera noté ici avec le cours du Flower du jour, pour savoir ce qu'il t'a coûté ou rapporté en dollars.</div>`}</div>`;})()}
 <div class="card scroll"><table><tr><th>Date</th><th>Solde Flower</th><th>Déposé</th><th>Retiré</th><th>Dépensé en jeu</th><th>Frais gems</th><th>Cours FLW</th></tr>${c.slice().reverse().map(x=>`<tr><td>${x.date.split("-").reverse().join("/")}</td><td>${fr(x.solde)}</td><td>${fr(x.deposited)}</td><td>${fr(x.withdrawn)}</td><td>${fr(x.spent)}</td><td>${fr(x.gemFees)}</td><td>${x.flower_usd?fr(x.flower_usd,4)+" $":"—"}</td></tr>`).join("")}</table>
 <div class="sub">Chiffres de ton compte relevés chaque jour (SFL Tool). « Dépensé en jeu » = Flower utilisés dans le jeu hors marché (gems, achats en boutique…).</div></div>`;
}
function totauxCard(){
 const T=(D.nft||{}).totaux||[];
 return T.length?`<div class="card"><h2>🧮 Le total de tes bonus, ressource par ressource</h2><div class="scroll"><table><tr><th style="text-align:left">Ressource</th><th>Grâce aux NFT</th><th>Grâce aux compétences</th><th>Total en plus à chaque action</th><th>Multiplicateur</th><th>Temps de repousse</th><th style="text-align:left">Chances</th><th style="text-align:left">Détail (d'où vient chaque bonus)</th></tr>
  ${T.map(x=>`<tr><td style="text-align:left"><b>${x.nom}</b></td><td>${x.add_nft?sg(x.add_nft):"—"}</td><td>${x.add_comp?sg(x.add_comp):"—"}</td><td class="${x.add>0?"pos":x.add<0?"neg":""}"><b>${x.add?sg(x.add):"—"}</b></td><td>${x.mult!==1?"×"+fr(x.mult,2):"—"}</td><td>${x.temps!==1?"×"+fr(x.temps,2)+" ("+fr((1-x.temps)*100,0)+" % plus rapide)":"—"}</td><td style="text-align:left">${x.chances.join(" · ")||"—"}</td><td style="text-align:left;color:var(--muted);font-size:12px">${x.lignes.map(l=>"• "+l).join("<br>")}</td></tr>`).join("")}</table></div>
  <div class="sub">NFT <b>et</b> compétences additionnés. Ex. pierre « +0,85 » = à chaque coup de pioche, tu gagnes 0,85 pierre de plus que sans aucun bonus (+0,25 des NFT, +0,60 des compétences, Ferrous Favor enlevant 0,5). Temps de repousse ×0,8 = tes rochers reviennent 20 % plus vite. Les compétences sont comptées à leur effet de base (rang 1) ; les vêtements portés (toi et tes Farm Hands) sont lus automatiquement. Un total à 0 avec des lignes (ex. plumes) = un bonus et un malus qui s'annulent.</div></div>`:"";
}
function cyclesTab(){
 const el=document.getElementById("cycles"),SP=(D.nft||{}).saisons_passees||[],CP=(D.nft||{}).cycles_passes||[];
 const SFR={spring:"🌸 Printemps",summer:"☀️ Été",autumn:"🍂 Automne",winter:"❄️ Hiver"},dt=d=>d.split("-").reverse().join("/");
 const cyc=CP.slice().reverse().map(c=>{const ok=c.nfts.filter(o=>o.fait!=null&&o.fait>=o.total).length;return `<div class="card"><h2>📅 Cycle du ${dt(c.debut)} au ${dt(c.fin)} <span class="msum">${ok}/${c.nfts.length} réussis</span></h2>${c.partiel?'<div class="sub">Cycle partiel (suivi commencé en cours d\'année).</div>':""}
  <div class="scroll"><table><tr><th style="text-align:left">NFT</th><th>Objectif du cycle</th><th>Fait</th><th style="text-align:left">Résultat</th></tr>${c.nfts.map(o=>{const f=v=>fr(v,o.total<40?1:0);return `<tr><td style="text-align:left"><b>${o.nft}</b></td><td>${f(o.total)} ${o.unite}</td><td>${o.fait!=null?f(o.fait):"—"}</td><td style="text-align:left" class="${o.fait>=o.total?"pos":"neg"}">${o.fait>=o.total?"✅ réussi":"❌ manqué de "+f(o.total-o.fait)+" "+o.unite}</td></tr>`}).join("")}</table></div></div>`;}).join("");
 const sai=SP.slice().reverse().map(z=>{const L=(z.objectifs||[]).filter(o=>o.cible);const ok=L.filter(o=>o.fait>=o.cible).length;return `<details class="card"><summary style="cursor:pointer"><b>${SFR[z.saison]||z.saison}</b> du ${dt(z.debut)} au ${dt(z.fin)} <span class="msum">${ok}/${L.length} réussis</span></summary><div class="scroll"><table><tr><th style="text-align:left">NFT</th><th>Objectif</th><th>Fait</th><th></th></tr>${L.map(o=>`<tr><td style="text-align:left">${o.nft}</td><td>${o.texte}</td><td>${o.fait!=null?fr(o.fait,o.cible<20?1:0):"—"}</td><td>${o.fait>=o.cible?"✅":"❌"}</td></tr>`).join("")}</table></div></details>`;}).join("");
 el.innerHTML=(cyc||sai)?cyc+(sai?`<div class="card"><h2>🗓️ Saisons passées</h2><div class="sub">Clique sur une saison pour voir le détail.</div></div>`+sai:""):'<div class="card empty">Aucune saison terminée pour l\'instant. Le bilan de chaque saison sera rangé ici automatiquement à la fin de la saison, et celui du cycle complet à chaque nouveau printemps.</div>';
}
function bonusTab(){
 const el=document.getElementById("bonus"),N=((D.nft||{}).rows||[]).filter(r=>r.owned),K=(((D.nft||{}).skills||{}).rows||[]).filter(r=>r.owned);
 const CAT=[["⛏️ Mines",/stone|iron|gold|crimstone|mineral|pierre|fer\b|\bor\b|pioche|rocher|obsidian/i],["🌲 Bois",/wood|tree|bois|arbre|axe/i],["🌾 Cultures",/crop|plot|wheat|corn|kale|barley|cultur|champ|blé|maïs|orge|chou|seed|harvest/i],["🐄 Animaux",/cow|chicken|pig|sheep|milk|leather|egg|feather|wool|truffle|vache|poule|lait|cuir|œuf|plume|animal|feed/i],["🍎 Fruits et serre",/fruit|apple|orange|banana|tomato|lemon|grape|olive|rice|greenhouse|blueberry/i],["⭐ XP et cuisine",/xp|cook|meal|food|cuisine/i],["🎣 Pêche, abeilles, fleurs",/fish|reel|bee|honey|flower|lotus/i]];
 const cat=t=>{for(const[c,re]of CAT)if(re.test(t))return c;return "✨ Autres"};
 const G={};
 N.forEach(r=>{const c=cat(r.n+" "+(r.effet||""));(G[c]=G[c]||[]).push({src:"🧾 NFT",n:r.n,e:r.effet||"",g:r.xp?null:r.jour})});
 K.forEach(r=>{const c=cat(r.arbre+" "+r.effet);(G[c]=G[c]||[]).push({src:"🎓 Compétence",n:r.n+(r.rang>1?` (rang ${r.rang})`:""),e:r.effet,g:r.jour})});
 const order=[...CAT.map(x=>x[0]),"✨ Autres"].filter(c=>G[c]);
 const tot=sum(N,r=>r.xp?0:r.jour)+sum(K,r=>r.jour||0);
 const tcard=totauxCard();
 el.innerHTML=tcard+`<div class="hero"><div><div class="l">Tous tes bonus</div><div class="big">${N.length+K.length}</div><div class="l">${N.length} NFT · ${K.length} compétences</div></div></div>
 ${order.map(c=>`<div class="card"><h2>${c} <span class="msum">${G[c].length}</span></h2><div class="scroll"><table><tr><th style="text-align:left">Bonus</th><th>Source</th><th style="text-align:left">Effet</th><th>Rapporte</th></tr>${G[c].sort((a,b)=>(b.g||0)-(a.g||0)).map(x=>`<tr><td style="text-align:left"><b>${x.n}</b></td><td>${x.src}</td><td style="text-align:left;color:var(--muted)">${x.e}</td><td class="${x.g>0.001?"pos":""}">${x.g!=null&&x.g>0.001?sg(x.g*30)+" /mois":"—"}</td></tr>`).join("")}</table></div></div>`).join("")}
 <div class="sub">Résumé à titre d'information. NFT lus dans ton inventaire et compétences lues sur ta ferme à chaque relevé : un NFT acheté ou vendu apparaît ou disparaît au relevé suivant. « — » = effet qui ne se chiffre pas en Flower.</div>`;
}

let start="apercu";try{start=localStorage.getItem("tab")||"apercu"}catch(e){}
show(TABS.some(t=>t[0]===start)?start:"apercu");
</script>
</body>
</html>
"""
