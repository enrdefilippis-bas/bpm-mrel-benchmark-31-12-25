<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MREL Peer Benchmark — 31-12-2025</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#061629;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1f2937;display:flex;min-height:100vh}
/* SIDEBAR */
.sidebar{width:264px;min-width:264px;background:#13315c;color:#fff;padding:24px 20px;box-shadow:2px 0 8px rgba(0,0,0,.2);display:flex;flex-direction:column;gap:0}
.sidebar h1{font-size:18px;color:#fff;margin-bottom:4px}
.sidebar .subtitle{color:#9aa4b1;font-size:11px;margin-bottom:20px}
.sidebar .meta{color:#9aa4b1;font-size:11px;margin-bottom:20px}
.section-title{color:#9aa4b1;font-size:10px;letter-spacing:.1em;text-transform:uppercase;margin:20px 0 8px}
.nav-link{display:block;padding:8px 10px;margin:2px 0;color:#e6ecf2;text-decoration:none;border-radius:4px;font-size:13px;cursor:pointer;border:none;background:none;width:100%;text-align:left}
.nav-link:hover{background:rgba(255,255,255,.06)}
.nav-link.active{background:rgba(230,168,23,.16);color:#f3c96a;border-left:3px solid #e6a817;padding-left:7px}
.control-label{color:#e6ecf2;font-size:12px;margin:12px 0 6px}
select,input[type=range]{width:100%;background:#0b2545;color:#e6ecf2;border:1px solid #4a6a8a;border-radius:4px;padding:6px 10px;font-size:12px;font-family:inherit;cursor:pointer}
select:focus{outline:none;border-color:#e6a817}
.radio-group{display:flex;flex-direction:column;gap:4px}
.radio-group label{color:#e6ecf2;font-size:12px;display:flex;align-items:center;gap:6px;cursor:pointer}
/* MAIN */
.main{flex:1;padding:28px 36px;background:#f5f7fa;overflow-x:auto}
.page{display:none}.page.active{display:block}
.page-header{margin-bottom:20px}
.page-header h2{color:#0b2545;font-size:22px;margin-bottom:4px}
.page-header p{color:#5b6572;font-size:13px}
/* CARDS */
.card{background:#fff;border-radius:6px;padding:20px 24px;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:16px}
.card h3{color:#0b2545;font-size:15px;margin-bottom:4px}
.card .caption{color:#5b6572;font-size:12px;margin-bottom:14px}
/* BADGE GRID */
.badge-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:16px}
.badge{background:#fff;border-radius:6px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.badge .b-label{color:#5b6572;font-size:11px;letter-spacing:.05em;text-transform:uppercase;margin-bottom:2px}
.badge .b-value{color:#0b2545;font-size:20px;font-weight:700;line-height:1.2}
.badge .b-sub{color:#5b6572;font-size:11px;margin-top:2px}
.badge.bpm .b-value{color:#c0362c}
/* CONTROLS ROW */
.ctrl-row{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:12px}
.ctrl-row label{font-size:12px;color:#5b6572}
.ctrl-row select{width:auto;min-width:180px}
/* TWO-COLS */
.two-col{display:flex;gap:16px;flex-wrap:wrap}
.two-col>div{flex:1;min-width:0}
/* META */
.meta-line{color:#5b6572;font-size:11px;font-style:italic;margin-top:6px}
/* Per-page sidebar filter panels */
.page-filters{margin-top:0}
</style>
</head>
<body>
<div class="sidebar">
  <h1>MREL Benchmark</h1>
  <div class="subtitle">BPM vs peer banks · EBA Pillar 3</div>
  <div class="meta" id="meta-line">Loading…</div>

  <div class="section-title">Pages</div>
  <button class="nav-link active" onclick="showPage('universe',this)">Universe</button>
  <button class="nav-link" onclick="showPage('cushion',this)">Cushion</button>
  <button class="nav-link" onclick="showPage('composition',this)">Composition</button>
  <button class="nav-link" onclick="showPage('maturity',this)">Maturity</button>
  <button class="nav-link" onclick="showPage('creditor',this)">Creditor rank</button>

  <div class="section-title">Filters</div>
  <div class="control-label">Peer set</div>
  <select id="peer-set" onchange="refreshAll()">
    <option value="c1">Italian peers — CdA cluster 1</option>
    <option value="c2">EU peers — CdA cluster 2</option>
    <option value="both">Cluster 1 + 2 (tutti)</option>
  </select>

  <!-- Per-page filter panels — only one visible at a time -->
  <div id="filters-universe" class="page-filters">
    <div class="control-label">Highlight</div>
    <div class="radio-group">
      <label><input type="radio" name="univ-highlight" value="peer" checked onchange="renderUniverse()"> CdA peer set</label>
      <label><input type="radio" name="univ-highlight" value="country" onchange="renderUniverse()"> Country</label>
    </div>
  </div>

  <div id="filters-cushion" class="page-filters" style="display:none">
    <div class="control-label">Metrica cushion</div>
    <select id="cushion-metric" onchange="renderCushion()">
      <option value="mrel_ex">MREL % TREA vs req (ex-CBR)</option>
      <option value="mrel_with">MREL % TREA vs OCR (with-CBR)</option>
      <option value="subord_ex">Subord % TREA vs req (ex-CBR)</option>
      <option value="subord_with">Subord % TREA vs req+CBR</option>
      <option value="tem">MREL % TEM vs req TEM</option>
      <option value="subord_ratio">Subordination ratio</option>
    </select>
  </div>

  <div id="filters-composition" class="page-filters" style="display:none">
    <div class="control-label">View</div>
    <div class="radio-group">
      <label><input type="radio" name="comp-mode" value="pct" checked onchange="renderComposition()"> 100% mix</label>
      <label><input type="radio" name="comp-mode" value="eur" onchange="renderComposition()"> €bn absolute</label>
    </div>
    <div class="control-label">Sort by</div>
    <select id="comp-sort" onchange="renderComposition()">
      <option value="subord_share">Subordination share</option>
      <option value="own_funds_share">Own funds share</option>
      <option value="senior_share">Senior share</option>
      <option value="total">Total stack (€)</option>
      <option value="name">Bank name (A→Z)</option>
    </select>
  </div>

  <div id="filters-maturity" class="page-filters" style="display:none">
    <div class="control-label">Sort by</div>
    <select id="mat-sort" onchange="renderMaturity()">
      <option value="s1_2y">1–2y share</option>
      <option value="s2_5y">2–5y share</option>
      <option value="s5_10y">5–10y share</option>
      <option value="s10y">10y+ share</option>
      <option value="sperp">Perpetual share</option>
      <option value="total">Total eligible (€)</option>
      <option value="name">Bank name (A→Z)</option>
    </select>
  </div>

  <div id="filters-creditor" class="page-filters" style="display:none">
    <div class="control-label">View</div>
    <select id="crd-mode" onchange="renderCreditor()">
      <option value="pct">100% mix</option>
      <option value="eur">€bn assoluto</option>
    </select>
    <div class="control-label">Sort by</div>
    <select id="crd-sort" onchange="renderCreditor()">
      <option value="total_desc">Total eligible (€ desc)</option>
      <option value="senior">Senior share (Rank 1)</option>
      <option value="subord">Deep-subord share (Rank ≥ 4)</option>
      <option value="name">Bank name (A→Z)</option>
    </select>
  </div>
</div>

<div class="main">
  <!-- UNIVERSE PAGE -->
  <div id="page-universe" class="page active">
    <div class="page-header">
      <h2>Universe — Full EU Pillar 3 population</h2>
      <p>Ogni punto = una banca con disclosure MREL nel Pillar 3 EBA (+ PDF). Asse X: TREA assoluto (scala log). Asse Y: MREL/TREA capacity. BPM in rosso, peer set CdA in blu scuro, altri in grigio. Ref: 31-12-2025.</p>
    </div>
    <div class="card">
      <div id="universe-chart" style="min-height:500px"></div>
      <div class="meta-line">Fonte: EBA Pillar 3 cell-level export (p3mreldata_2025q4.xlsx) + manual entries da PDF. 25 banche con TREA ≥ 12bn e MREL/TREA disponibili al 31-12-2025 (escluse banche con TREA < 12bn).</div>
    </div>
  </div>

  <!-- CUSHION PAGE -->
  <div id="page-cushion" class="page">
    <div class="page-header">
      <h2>Cushion — MREL capacity vs requirement</h2>
      <p>Barre per banca con capacità (blu) e requisito (marker ambra). BPM evidenziato in rosso. Ref date: 31-12-2025.</p>
    </div>
    <div class="badge-grid" id="cushion-badges"></div>
    <div class="card">
      <div id="cushion-chart-title" class="caption"></div>
      <div id="cushion-chart" style="min-height:420px"></div>
    </div>
  </div>

  <!-- COMPOSITION PAGE -->
  <div id="page-composition" class="page">
    <div class="page-header">
      <h2>Composition — MREL stack by instrument class</h2>
      <p>Stacked bar per classe strumento. Fonte: TLAC1 (K_91.00). BPM evidenziato.</p>
    </div>
    <div class="card">
      <div class="meta-line">Fonte: K_91.00 (TLAC1) col c0010 (MREL). I totali possono differire da KM2 per deduzioni pre-cap.</div>
      <div id="comp-chart" style="min-height:420px"></div>
    </div>
  </div>

  <!-- MATURITY PAGE -->
  <div id="page-maturity" class="page">
    <div class="page-header">
      <h2>Maturity — residual-maturity profile</h2>
      <p>Heatmap delle quote per bucket di maturity. Più scuro = quota maggiore. Fonte: K_97.00 col c0050.</p>
    </div>
    <div class="card">
      <div class="meta-line">Nota: BPER e Bank of Ireland non disponibili in questo template (Pillar 3 Q4 2025 usa TLAC3b / non ancora pubblicato).</div>
      <div id="mat-chart" style="min-height:380px"></div>
    </div>
  </div>

  <!-- CREDITOR RANK PAGE -->
  <div id="page-creditor" class="page">
    <div class="page-header">
      <h2>Creditor ranking — MREL stack by insolvency rank</h2>
      <p>Stacked bar per insolvency rank. Rank 1 = più senior (pagato per primo). Fonte: K_97.00 / TLAC3.</p>
    </div>
    <div class="card">
      <div class="meta-line">Nota: ICCREA, Cassa Centrale, Bank of Ireland non disponibili (Pillar 3 Q4 2025 non ancora pubblicato).</div>
      <div id="crd-chart" style="min-height:420px"></div>
    </div>
  </div>
</div>

<script>
const DATA=__DASHBOARD_DATA__;
</script>
<script>
// ─── THEME ──────────────────────────────────────────────────────────────────
const NAVY="#0b2545",NAVY_DEEP="#061629",STEEL="#4a6a8a",MIST="#e6ecf2";
const AMBER="#e6a817",AMBER_SOFT="#f3c96a",RED="#c0362c";
const GREY400="#9aa4b1",GREY600="#5b6572",GREY200="#d5dae0",WHITE="#ffffff";
const BPM_COLOR=RED, PEER_COLOR=STEEL, REQ_COLOR=AMBER;
const FONT="Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif";

const LAYOUT_BASE={
  paper_bgcolor:WHITE, plot_bgcolor:WHITE,
  font:{family:FONT,color:"#1f2937",size:12},
  title:{font:{family:FONT,color:NAVY,size:15},x:0},
  hoverlabel:{bgcolor:NAVY,bordercolor:NAVY,font:{family:FONT,color:WHITE,size:12}},
  xaxis:{gridcolor:GREY200,zerolinecolor:GREY200},
  yaxis:{gridcolor:GREY200,zerolinecolor:GREY200},
  margin:{l:220,r:24,t:90,b:40},
};

// ─── PEER FILTER ──────────────────────────────────────────────────────────
function activeLeis(){
  const v=document.getElementById("peer-set").value;
  if(v==="c1") return new Set(DATA.cluster1_leis);
  if(v==="c2") return new Set(DATA.cluster2_leis);
  return new Set([...DATA.cluster1_leis,...DATA.cluster2_leis]);
}

function filterKM2(){
  const leis=activeLeis();
  return DATA.km2.filter(d=>leis.has(d.lei));
}

// ─── HELPERS ────────────────────────────────────────────────────────────
function fmt(v,u){
  if(v===null||v===undefined||isNaN(v)) return "—";
  if(u==="%") return (v*100).toFixed(2)+"%";
  if(u==="pp") return (v>0?"+":"")+(v*100).toFixed(2)+" pp";
  if(u==="€bn") return "€"+(v/1e9).toFixed(1)+"bn";
  return v;
}
function plotlyConfig(){return{displayModeBar:false};}

// ─── NAVIGATION ─────────────────────────────────────────────────────────
const PAGE_FILTER_MAP={universe:"filters-universe",cushion:"filters-cushion",composition:"filters-composition",maturity:"filters-maturity",creditor:"filters-creditor"};

function showPage(id,btn){
  document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
  document.querySelectorAll(".nav-link").forEach(b=>b.classList.remove("active"));
  document.getElementById("page-"+id).classList.add("active");
  btn.classList.add("active");
  // Show only the relevant sidebar filter panel
  Object.entries(PAGE_FILTER_MAP).forEach(([page,filterId])=>{
    const el=document.getElementById(filterId);
    if(el) el.style.display=(page===id)?"block":"none";
  });
  // lazy render
  if(id==="universe") renderUniverse();
  if(id==="cushion") renderCushion();
  if(id==="composition") renderComposition();
  if(id==="maturity") renderMaturity();
  if(id==="creditor") renderCreditor();
}

function refreshAll(){
  renderUniverse();
  renderCushion();
  renderComposition();
  renderMaturity();
  renderCreditor();
  buildBadges();
}

// ─── META LINE ──────────────────────────────────────────────────────────
document.getElementById("meta-line").textContent=
  DATA.km2.length+" banks · Ref: 31-12-2025";

// ─── UNIVERSE PAGE ───────────────────────────────────────────────────────
function renderUniverse(){
  const highlightMode=document.querySelector("input[name=univ-highlight]:checked").value;
  const rows=DATA.universe;
  if(!rows||!rows.length){Plotly.purge("universe-chart");return;}

  // Split into groups for layered rendering (others → peers C2 → peers C1 → BPM)
  const others=rows.filter(d=>!d.is_bpm&&!d.is_peer);
  const peersC2=rows.filter(d=>d.is_peer&&d.cluster==="c2");
  const peersC1=rows.filter(d=>d.is_peer&&d.cluster==="c1");
  const bpm=rows.filter(d=>d.is_bpm);

  function hoverText(d){
    const name=d.name.length>40?d.name.substring(0,38)+"…":d.name;
    return `<b>${name}</b><br>Country: ${d.country}<br>TREA: €${d.trea_bn.toFixed(1)}bn<br>MREL/TREA: ${(d.mrel_pct_trea*100).toFixed(2)}%`;
  }

  // Percentile annotation lines (universe median)
  const mrelVals=rows.map(d=>d.mrel_pct_trea).sort((a,b)=>a-b);
  const univMedian=mrelVals[Math.floor(mrelVals.length/2)];

  const traces=[];

  // --- Others (grey) ---
  traces.push({
    type:"scatter",mode:"markers",name:"EU universe (other)",
    x:others.map(d=>d.trea_bn),y:others.map(d=>d.mrel_pct_trea*100),
    marker:{size:7,color:GREY400,opacity:0.55,line:{width:0}},
    text:others.map(hoverText),hovertemplate:"%{text}<extra></extra>",
  });

  // --- Peer Cluster 2 (steel blue) ---
  traces.push({
    type:"scatter",mode:"markers+text",name:"Cluster 2 — EU peer",
    x:peersC2.map(d=>d.trea_bn),y:peersC2.map(d=>d.mrel_pct_trea*100),
    marker:{size:11,color:STEEL,opacity:0.9,
      line:{width:1.2,color:NAVY},symbol:"circle"},
    text:peersC2.map(d=>{
      const short=d.name.replace("Banco de Sabadell, S.A.","Sabadell")
                        .replace("AIB Group plc","AIB")
                        .replace("Belfius Bank","Belfius");
      return short;
    }),
    textposition:peersC2.map(d=>{
      if(d.name.includes("Sabadell")) return "top right";
      if(d.name.includes("AIB")) return "top left";
      return "top center";
    }),
    textfont:{color:STEEL,size:10},
    customdata:peersC2.map(hoverText),
    hovertemplate:"%{customdata}<extra></extra>",
  });

  // --- Peer Cluster 1 (navy) ---
  traces.push({
    type:"scatter",mode:"markers+text",name:"Cluster 1 — ITA peer",
    x:peersC1.map(d=>d.trea_bn),y:peersC1.map(d=>d.mrel_pct_trea*100),
    marker:{size:11,color:NAVY,opacity:0.9,
      line:{width:1.2,color:NAVY},symbol:"circle"},
    text:peersC1.map(d=>{
      return d.name.replace("Intesa Sanpaolo S.p.A.","Intesa")
                   .replace("UniCredit S.p.A.","UniCredit")
                   .replace("Banca Monte dei Paschi di Siena S.p.A.","MPS")
                   .replace("Mediobanca - Banca di Credito Finanziario S.p.A.","Mediobanca");
    }),
    textposition:peersC1.map(d=>{
      if(d.name.includes("Intesa")) return "top right";
      if(d.name.includes("UniCredit")) return "bottom left";
      if(d.name.includes("Mediobanca")) return "top left";
      return "top center";
    }),
    textfont:{color:NAVY,size:10},
    customdata:peersC1.map(hoverText),
    hovertemplate:"%{customdata}<extra></extra>",
  });

  // --- BPM (red diamond) ---
  if(bpm.length){
    const b=bpm[0];
    traces.push({
      type:"scatter",mode:"markers+text",name:"Banco BPM",
      x:[b.trea_bn],y:[b.mrel_pct_trea*100],
      marker:{size:16,color:BPM_COLOR,symbol:"diamond",
        line:{width:2,color:"white"}},
      text:["BPM"],textposition:"middle right",
      textfont:{color:BPM_COLOR,size:13,family:FONT},
      customdata:[hoverText(b)],
      hovertemplate:"%{customdata}<extra></extra>",
    });
  }

  // Median reference line annotation
  const shapes=[{
    type:"line",xref:"paper",yref:"y",
    x0:0,x1:1,y0:univMedian*100,y1:univMedian*100,
    line:{color:AMBER,width:1.5,dash:"dot"},
  }];
  const annotations=[{
    xref:"paper",yref:"y",x:1.01,y:univMedian*100,
    text:`Median<br>${(univMedian*100).toFixed(1)}%`,
    showarrow:false,font:{size:10,color:AMBER},
    xanchor:"left",
  }];

  Plotly.react("universe-chart",traces,{
    ...LAYOUT_BASE,
    title:{text:"Own funds and eligible liabilities as % of TREA — 31-12-2025 (25 banks)",
           font:{family:FONT,color:NAVY,size:14},x:0},
    xaxis:{
      title:"Total Risk Exposure Amount (TREA, €bn) — log scale",
      type:"log",
      tickformat:",.0f",
      tickvals:[0.1,0.5,1,5,10,50,100,500,1000],
      ticktext:["0.1","0.5","1","5","10","50","100","500","1000"],
      gridcolor:GREY200,zerolinecolor:GREY200,
    },
    yaxis:{
      title:"Own funds and eligible liabilities as % of TREA",
      tickformat:".0%",
      tickvals:[15,20,25,30,35,40,45,50,55,60,65,70],
      ticktext:["15%","20%","25%","30%","35%","40%","45%","50%","55%","60%","65%","70%"],
      gridcolor:GREY200,
    },
    margin:{l:80,r:80,t:90,b:60},
    showlegend:true,
    legend:{orientation:"h",y:1.16,x:0,xanchor:"left",yanchor:"bottom",
            font:{size:11},bgcolor:"rgba(255,255,255,0.85)"},
    shapes:shapes,
    annotations:annotations,
    height:520,
  },plotlyConfig());
}

// ─── CUSHION PAGE ────────────────────────────────────────────────────────
const CUSHION_SPECS={
  mrel_ex:{cap:"mrel_pct_trea",req:"mrel_requirement_trea_ex_cbr",
    title:"MREL % TREA — capacity vs MREL requirement (ex-CBR)",reqLbl:"Req ex-CBR"},
  mrel_with:{cap:"mrel_pct_trea",req:"mrel_requirement_trea_with_cbr",
    title:"MREL % TREA — capacity vs OCR threshold (MREL + CBR)",reqLbl:"OCR (MREL+CBR)"},
  subord_ex:{cap:"subord_pct_trea",req:"mrel_subord_requirement_trea_ex_cbr",
    title:"Subordination % TREA — capacity vs subord requirement (ex-CBR)",reqLbl:"Subord req ex-CBR"},
  subord_with:{cap:"subord_pct_trea",req:"mrel_subord_requirement_trea_with_cbr",
    title:"Subordination % TREA — capacity vs subord req + CBR",reqLbl:"Subord req+CBR"},
  tem:{cap:"mrel_pct_tem",req:"mrel_requirement_tem",
    title:"MREL % TEM — capacity vs TEM requirement",reqLbl:"Req TEM"},
  subord_ratio:{cap:"subordination_ratio",req:null,
    title:"Subordination ratio — subordinated share of total MREL stack",reqLbl:null},
};

function renderCushion(){
  const metric=document.getElementById("cushion-metric").value;
  const spec=CUSHION_SPECS[metric];
  const rows=filterKM2().filter(d=>d[spec.cap]!==null).sort((a,b)=>a[spec.cap]-b[spec.cap]);
  if(!rows.length){Plotly.purge("cushion-chart");return;}

  const labels=rows.map(d=>d.name);
  const caps=rows.map(d=>d[spec.cap]);
  const reqs=spec.req?rows.map(d=>d[spec.req]):null;
  const colors=rows.map(d=>d.is_bpm?BPM_COLOR:PEER_COLOR);

  const hover=rows.map((d,i)=>{
    const c=caps[i], r=reqs?reqs[i]:null;
    let h=`<b>${d.name}</b><br>Capacity: ${fmt(c,"%")}`;
    if(r!==null&&r!==undefined) h+=`<br>${spec.reqLbl}: ${fmt(r,"%")}<br>Surplus: ${fmt(c-r,"pp")}`;
    return h;
  });

  const traces=[{
    type:"bar",orientation:"h",y:labels,x:caps,
    marker:{color:colors},name:"Capacity",
    hovertext:hover,hoverinfo:"text",hoverlabel:{namelength:-1},
  }];

  if(reqs){
    const rFilt=reqs.map((r,i)=>r!==null?r:null);
    traces.push({
      type:"scatter",mode:"markers",orientation:"h",
      y:labels.filter((_,i)=>rFilt[i]!==null),
      x:rFilt.filter(r=>r!==null),
      marker:{symbol:"line-ns",size:18,color:AMBER,line:{color:AMBER,width:3}},
      name:spec.reqLbl,hovertemplate:spec.reqLbl+": %{x:.2%}<extra></extra>",
    });
  }

  const h=Math.max(380,22*rows.length+140);
  Plotly.react("cushion-chart",traces,{
    ...LAYOUT_BASE,
    title:{text:spec.title,font:{family:FONT,color:NAVY,size:14},x:0},
    xaxis:{...LAYOUT_BASE.xaxis,tickformat:".0%",title:""},
    yaxis:{automargin:true},
    showlegend:true,legend:{orientation:"h",y:1.18,x:1,xanchor:"right",yanchor:"bottom",bgcolor:"rgba(255,255,255,0.85)"},
    height:h,
  },plotlyConfig());
  document.getElementById("cushion-chart-title").textContent="";
  buildBadges();
}

// ─── BADGES ──────────────────────────────────────────────────────────────
function buildBadges(){
  const rows=filterKM2();
  const bpm=rows.find(d=>d.is_bpm);
  const peers=rows.filter(d=>!d.is_bpm);
  if(!bpm){document.getElementById("cushion-badges").innerHTML="";return;}

  const med_mrel=median(peers.map(d=>d.mrel_pct_trea).filter(v=>v!==null));
  const med_subord=median(peers.map(d=>d.subord_pct_trea).filter(v=>v!==null));

  const badges=[
    {lbl:"BPM MREL % TREA",val:fmt(bpm.mrel_pct_trea,"%"),sub:"capacity",cls:"bpm"},
    {lbl:"Cushion vs MREL (ex-CBR)",val:fmt(bpm.mrel_surplus_trea_ex_cbr_pp,"pp"),sub:"vs "+fmt(bpm.mrel_requirement_trea_ex_cbr,"%")+" req",cls:"bpm"},
    {lbl:"Cushion vs OCR (with-CBR)",val:fmt(bpm.mrel_surplus_trea_with_cbr_pp,"pp"),sub:"M-MDA breach se < 0",cls:"bpm"},
    {lbl:"BPM Subord % TREA",val:fmt(bpm.subord_pct_trea,"%"),sub:"vs peer median "+fmt(med_subord,"%"),cls:"bpm"},
    {lbl:"Peer median MREL % TREA",val:fmt(med_mrel,"%"),sub:"n="+peers.filter(d=>d.mrel_pct_trea!==null).length+" banche",cls:""},
    {lbl:"BPM MREL % TEM",val:fmt(bpm.mrel_pct_tem,"%"),sub:"capacity su TEM",cls:"bpm"},
  ];
  document.getElementById("cushion-badges").innerHTML=badges.map(b=>`
    <div class="badge ${b.cls}">
      <div class="b-label">${b.lbl}</div>
      <div class="b-value">${b.val}</div>
      <div class="b-sub">${b.sub}</div>
    </div>`).join("");
}

function median(arr){
  if(!arr.length) return null;
  const s=[...arr].sort((a,b)=>a-b);
  const m=Math.floor(s.length/2);
  return s.length%2?s[m]:(s[m-1]+s[m])/2;
}

// ─── COMPOSITION PAGE ────────────────────────────────────────────────────
const COMP_COLORS={"CET1":"#0b2545","AT1":"#2a4d7a","T2":"#4a6a8a","Subord EL":"#e6a817","Senior EL":"#f3c96a"};
const COMP_CLASSES=[
  {key:"cet1",label:"CET1"},
  {key:"at1",label:"AT1"},
  {key:"tier2",label:"T2"},
  {key:"subord_el",label:"Subord EL"},
  {key:"senior_el",label:"Senior EL"},
];

function renderComposition(){
  const leis=activeLeis();
  const mode=document.querySelector("input[name=comp-mode]:checked").value;
  const sortKey=document.getElementById("comp-sort").value;
  let rows=DATA.comp.filter(d=>leis.has(d.lei));
  if(!rows.length){Plotly.purge("comp-chart");return;}

  rows=rows.map(d=>{
    const own=(d.cet1||0)+(d.at1||0)+(d.tier2||0);
    const subord=own+(d.subord_el||0);
    return{...d,
      own_funds_share:d.total?own/d.total:0,
      subord_share:d.total?subord/d.total:0,
      senior_share:d.total?(d.senior_el||0)/d.total:0};
  });

  if(sortKey==="name") rows.sort((a,b)=>b.name.localeCompare(a.name));
  else if(sortKey==="total") rows.sort((a,b)=>a.total-b.total);
  else rows.sort((a,b)=>a[sortKey]-b[sortKey]);

  const labels=rows.map(d=>d.name);
  const totals=rows.map(d=>d.total||1);
  const traces=COMP_CLASSES.map(cls=>{
    const vals=rows.map(d=>d[cls.key]||0);
    const xs=mode==="pct"?vals.map((v,i)=>v/totals[i]):vals.map(v=>v/1e9);
    const hover=rows.map((d,i)=>{
      const v=vals[i],t=totals[i];
      return mode==="pct"
        ?`<b>${d.name}</b><br>${cls.label}: ${(v/t*100).toFixed(1)}% (€${(v/1e9).toFixed(2)}bn)`
        :`<b>${d.name}</b><br>${cls.label}: €${(v/1e9).toFixed(2)}bn (${(v/t*100).toFixed(1)}%)`;
    });
    return{type:"bar",orientation:"h",y:labels,x:xs,name:cls.label,
      marker:{color:COMP_COLORS[cls.label]},hovertext:hover,hoverinfo:"text"};
  });

  Plotly.react("comp-chart",traces,{
    ...LAYOUT_BASE,barmode:"stack",
    title:{text:"MREL stack composition — 31-12-2025",font:{family:FONT,color:NAVY,size:14},x:0},
    xaxis:{...LAYOUT_BASE.xaxis,
      title:mode==="pct"?"Share of MREL stack":"MREL stack (€bn)",
      tickformat:mode==="pct"?".0%":".1f",
      range:mode==="pct"?[0,1]:undefined},
    yaxis:{automargin:true},
    showlegend:true,
    legend:{orientation:"h",y:1.18,x:1,xanchor:"right",yanchor:"bottom",bgcolor:"rgba(255,255,255,0.85)"},
    height:Math.max(380,26*rows.length+170),
  },plotlyConfig());
}

// ─── MATURITY PAGE ────────────────────────────────────────────────────────
const BUCKET_KEYS=["s1_2y","s2_5y","s5_10y","s10y","sperp"];
const BUCKET_LBLS=["1–2y","2–5y","5–10y","10y+","Perpetual"];
const BUCKET_AMT =["b1_2y","b2_5y","b5_10y","b10y","perp"];

function renderMaturity(){
  const leis=activeLeis();
  const sortKey=document.getElementById("mat-sort").value;
  let rows=DATA.mat.filter(d=>leis.has(d.lei));
  if(!rows.length){Plotly.purge("mat-chart");return;}

  if(sortKey==="name") rows.sort((a,b)=>b.name.localeCompare(a.name));
  else if(sortKey==="total") rows.sort((a,b)=>a.total-b.total);
  else rows.sort((a,b)=>(a[sortKey]||0)-(b[sortKey]||0));

  const labels=rows.map(d=>d.name);
  const matrix=rows.map(d=>BUCKET_KEYS.map(k=>d[k]||0));
  const matrixT=BUCKET_KEYS.map((_,j)=>rows.map((_,i)=>matrix[i][j]));

  const hover=rows.map((d,i)=>BUCKET_KEYS.map((k,j)=>{
    const s=(d[k]||0)*100,a=(d[BUCKET_AMT[j]]||0)/1e9;
    return `<b>${d.name}</b><br>${BUCKET_LBLS[j]}: ${s.toFixed(1)}% (€${a.toFixed(2)}bn)`;
  }));
  const hoverT=BUCKET_KEYS.map((_,j)=>rows.map((_,i)=>hover[i][j]));

  const trace={
    type:"heatmap",
    z:matrixT,
    x:labels,
    y:BUCKET_LBLS,
    colorscale:[[0,"#eef3f7"],[0.15,"#b9c7d7"],[0.35,"#7e96b1"],[0.6,"#3f5a7a"],[0.85,"#1c2f4a"],[1,"#0b2545"]],
    zmin:0,zmax:1,
    colorbar:{tickformat:".0%",title:{text:"Share"}},
    hovertext:hoverT,hoverinfo:"text",
    transpose:false,
  };

  // Reformat as rows=banks, cols=buckets (Plotly heatmap: z[i][j] = row i col j)
  const z=rows.map(d=>BUCKET_KEYS.map(k=>d[k]||0));
  const hoverXY=rows.map((d,i)=>BUCKET_KEYS.map((k,j)=>{
    const s=(d[k]||0)*100,a=(d[BUCKET_AMT[j]]||0)/1e9;
    return `<b>${d.name}</b><br>${BUCKET_LBLS[j]}: ${s.toFixed(1)}% (€${a.toFixed(2)}bn)`;
  }));

  const traceH={
    type:"heatmap",
    z:z, x:BUCKET_LBLS, y:labels,
    colorscale:[[0,"#eef3f7"],[0.15,"#b9c7d7"],[0.35,"#7e96b1"],[0.6,"#3f5a7a"],[0.85,"#1c2f4a"],[1,"#0b2545"]],
    zmin:0,zmax:1,
    colorbar:{tickformat:".0%",title:{text:"Share"}},
    hovertext:hoverXY,hoverinfo:"text",
  };

  // BPM marker
  const bpmRow=rows.find(d=>d.is_bpm);
  const extraTraces=[];
  if(bpmRow){
    extraTraces.push({
      type:"scatter",mode:"markers+text",
      x:[BUCKET_LBLS[BUCKET_LBLS.length-1]],y:[bpmRow.name],
      marker:{size:12,color:RED,symbol:"diamond"},
      text:["BPM"],textposition:"middle right",
      textfont:{color:RED,size:11},hoverinfo:"skip",showlegend:false,
    });
  }

  Plotly.react("mat-chart",[traceH,...extraTraces],{
    ...LAYOUT_BASE,
    title:{text:"Maturity profile — 31-12-2025",font:{family:FONT,color:NAVY,size:14},x:0},
    xaxis:{title:"Residual maturity bucket",side:"top",gridcolor:GREY200},
    yaxis:{automargin:true,gridcolor:GREY200},
    margin:{l:240,r:60,t:80,b:40},
    height:Math.max(420,28*rows.length+160),showlegend:false,
  },plotlyConfig());
}

// ─── CREDITOR RANK PAGE ──────────────────────────────────────────────────
const RANK_COLORS_MAP={
  1:"#7d96b0",2:"#627e9a",3:"#4a6a8a",4:"#3e5772",
  5:"#d8a946",6:"#e6a817",7:"#d69516",8:"#c0362c",9:"#a82f26",10:"#8b271f"
};
function rankColor(r){return RANK_COLORS_MAP[r]||"#7a7a7a";}

function renderCreditor(){
  const leis=activeLeis();
  const mode=document.getElementById("crd-mode").value;
  const sortKey=document.getElementById("crd-sort").value;
  let rows=DATA.crd.filter(d=>leis.has(d.lei));
  if(!rows.length){Plotly.purge("crd-chart");return;}

  rows=rows.map(d=>{
    const total=Object.values(d.ranks).reduce((s,v)=>s+(v||0),0)||1;
    const r1=d.ranks[1]||0;
    const subord=(d.ranks[4]||0)+(d.ranks[5]||0)+(d.ranks[6]||0)+(d.ranks[7]||0)+(d.ranks[8]||0)+(d.ranks[9]||0)+(d.ranks[10]||0);
    return{...d,total,r1_share:r1/total,subord_share:subord/total};
  });

  if(sortKey==="name") rows.sort((a,b)=>b.name.localeCompare(a.name));
  else if(sortKey==="total_desc") rows.sort((a,b)=>a.total-b.total);
  else if(sortKey==="senior") rows.sort((a,b)=>a.r1_share-b.r1_share);
  else if(sortKey==="subord") rows.sort((a,b)=>a.subord_share-b.subord_share);

  const allRanks=[...new Set(rows.flatMap(d=>Object.keys(d.ranks).map(Number)))].sort((a,b)=>a-b);
  const labels=rows.map(d=>d.name);

  const traces=allRanks.map(rank=>{
    const vals=rows.map(d=>d.ranks[rank]||0);
    const totals=rows.map(d=>d.total);
    const xs=mode==="pct"?vals.map((v,i)=>v/totals[i]):vals.map(v=>v/1e9);
    const hover=rows.map((d,i)=>{
      const v=vals[i],t=totals[i];
      return mode==="pct"
        ?`<b>${d.name}</b><br>Rank ${rank}: ${(v/t*100).toFixed(1)}% (€${(v/1e9).toFixed(2)}bn)`
        :`<b>${d.name}</b><br>Rank ${rank}: €${(v/1e9).toFixed(2)}bn (${(v/t*100).toFixed(1)}%)`;
    });
    return{type:"bar",orientation:"h",y:labels,x:xs,name:`Rank ${rank}`,
      marker:{color:rankColor(rank)},hovertext:hover,hoverinfo:"text"};
  });

  Plotly.react("crd-chart",traces,{
    ...LAYOUT_BASE,barmode:"stack",
    title:{text:"Creditor ranking — MREL stack by insolvency rank (31-12-2025)",font:{family:FONT,color:NAVY,size:14},x:0},
    xaxis:{...LAYOUT_BASE.xaxis,
      title:mode==="pct"?"Share of MREL stack":"MREL stack (€bn)",
      tickformat:mode==="pct"?".0%":".1f",
      range:mode==="pct"?[0,1]:undefined},
    yaxis:{automargin:true},
    showlegend:true,
    legend:{orientation:"h",y:1.18,x:1,xanchor:"right",yanchor:"bottom",bgcolor:"rgba(255,255,255,0.85)"},
    height:Math.max(380,26*rows.length+140),
  },plotlyConfig());
}

// ─── INIT ────────────────────────────────────────────────────────────────
renderUniverse();
renderCushion();
renderComposition();
</script>
</body>
</html>
