/* Deepfake Forensics Platform — hackathon pitch deck generator (pptxgenjs).
   Dark premium theme, native-shape diagrams, real screenshots/charts, speaker notes.
   Run: node build_deck.js  ->  Deepfake_Forensics_Pitch.pptx                        */
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.defineLayout({ name: "W", width: 13.333, height: 7.5 });
p.layout = "W";
p.author = "Team";
p.company = "Deepfake Forensics Platform";
p.title = "Multimodal Deepfake Detection & Media Forensics Platform";
p.theme = { headFontFace: "Calibri", bodyFontFace: "Calibri" };

// ---------- palette ----------
const BG="0B0F1A", PANEL="151D30", PANEL2="1E2740", STROKE="2A3556",
      INK="E6EAF2", MUTED="9AA4B8", TEAL="2DD4BF", TEALD="14B8A6",
      BLUE="60A5FA", AMBER="F59E0B", RED="F87171", GREEN="34D399", VIOLET="A78BFA";
const HEAD="Calibri", BODY="Calibri", MONO="Courier New";
const W=13.333, H=7.5, M=0.6;

// ---------- helpers ----------
function bg(s, fill=BG){ s.background={color:fill}; }
function rr(s,x,y,w,h,o={}){ s.addShape(p.ShapeType.roundRect,{x,y,w,h,rectRadius:o.r??0.1,
  fill:o.fill?{color:o.fill}:{color:PANEL}, line:o.line===null?{type:"none"}:{color:o.line||STROKE,width:o.lw||1},
  shadow:o.shadow?{type:"outer",color:"000000",opacity:0.35,blur:8,offset:3,angle:90}:undefined }); }
function rect(s,x,y,w,h,fill,line=null){ s.addShape(p.ShapeType.rect,{x,y,w,h,fill:{color:fill},
  line:line?{color:line,width:1}:{type:"none"}}); }
function tx(s,text,o){ s.addText(text,Object.assign({isTextBox:true,margin:0,fontFace:BODY,color:INK,
  fontSize:14,valign:"top",align:"left"},o)); }
function kicker(s,text){ tx(s,text,{x:M,y:0.42,w:11,h:0.3,fontSize:12,bold:true,color:TEAL,charSpacing:2}); }
function title(s,text){ tx(s,text,{x:M,y:0.72,w:W-1.2,h:0.9,fontSize:30,bold:true,color:INK,fontFace:HEAD}); }
function foot(s,n){ tx(s,"Deepfake Forensics Platform",{x:M,y:H-0.42,w:6,h:0.3,fontSize:9,color:MUTED});
  tx(s,String(n).padStart(2,"0"),{x:W-1.1,y:H-0.42,w:0.5,h:0.3,fontSize:9,color:MUTED,align:"right"}); }
function chevron(s,x,y,color=TEAL){ s.addShape(p.ShapeType.triangle,{x,y,w:0.22,h:0.2,rotate:90,
  fill:{color},line:{type:"none"}}); }
function node(s,x,y,w,h,label,sub,o={}){ rr(s,x,y,w,h,{fill:o.fill||PANEL2,line:o.line||STROKE,r:0.08,shadow:true});
  tx(s,label,{x:x+0.1,y:y+h/2-(sub?0.34:0.16),w:w-0.2,h:0.34,fontSize:o.fs||12.5,bold:true,
    color:o.tc||INK,align:"center",fontFace:HEAD});
  if(sub) tx(s,sub,{x:x+0.1,y:y+h/2+0.02,w:w-0.2,h:0.3,fontSize:9.5,color:o.sc||MUTED,align:"center"}); }
function bullets(s,items,o){ s.addText(items.map((it,i)=>({text:typeof it==="string"?it:it.t,
  options:{bullet:{code:"2022",indent:14},color:(typeof it==="object"&&it.c)||INK,breakLine:true,
  paraSpaceAfter:(o&&o.gap)??8,fontSize:(o&&o.fs)||13.5,bold:typeof it==="object"&&it.b}})),
  Object.assign({isTextBox:true,margin:0,fontFace:BODY,valign:"top",x:M,y:1.8,w:6,h:5},o)); }
function card(s,x,y,w,h,head,body,o={}){ rr(s,x,y,w,h,{fill:o.fill||PANEL,line:o.line||STROKE,r:0.1,shadow:true});
  if(o.tag){ rr(s,x+0.22,y+0.22,0.34,0.34,{fill:o.tagfill||TEALD,line:null,r:0.06});
    tx(s,o.tag,{x:x+0.22,y:y+0.24,w:0.34,h:0.3,fontSize:13,bold:true,color:"06231F",align:"center",fontFace:HEAD}); }
  const hx = o.tag ? x+0.7 : x+0.24;
  tx(s,head,{x:hx,y:y+0.22,w:w-(hx-x)-0.22,h:0.4,fontSize:o.hfs||15,bold:true,color:o.hc||INK,fontFace:HEAD});
  if(body) tx(s,body,{x:x+0.24,y:y+0.72,w:w-0.48,h:h-0.9,fontSize:o.bfs||11.5,color:o.bc||MUTED,
    lineSpacingMultiple:1.05}); }
function slide(sectionTitle){ const s=p.addSlide(); bg(s); return s; }

// =====================================================================
// SLIDE 1 — TITLE
// =====================================================================
(function(){ const s=slide();
  rect(s,0,0,W,H,BG);
  // subtle panel on right with screenshot
  rr(s,8.3,1.5,4.4,4.5,{fill:PANEL,line:STROKE,r:0.12,shadow:true});
  s.addImage({path:"assets/02_results.jpg",x:8.5,y:1.7,w:4.0,h:2.26,rounding:true});
  tx(s,"Live product — forensic assessment dashboard",{x:8.5,y:4.05,w:4.0,h:0.6,fontSize:10,color:MUTED,align:"center"});
  s.addImage({path:"assets/roc_curves.png",x:9.1,y:4.5,w:2.8,h:2.3,rounding:true});
  // shield mark
  rr(s,M,0.7,0.7,0.7,{fill:"0E3B34",line:TEALD,r:0.12});
  tx(s,"◆",{x:M,y:0.78,w:0.7,h:0.5,fontSize:24,color:TEAL,align:"center"});
  kicker(s,"AI/ML & DEEP LEARNING HACKATHON  ·  PROBLEM 02");
  tx(s,"Multimodal Deepfake\nDetection & Media\nForensics Platform",{x:M,y:1.95,w:7.6,h:2.3,fontSize:34,bold:true,color:INK,fontFace:HEAD,lineSpacingMultiple:1.0});
  tx(s,"Catching fakes across image, video and audio — with evidence, not guesswork.",
     {x:M,y:3.95,w:7.4,h:0.7,fontSize:15,italic:true,color:TEAL});
  rr(s,M,4.95,7.3,1.15,{fill:PANEL,line:STROKE,r:0.1});
  tx(s,"TEAM",{x:M+0.25,y:5.1,w:2,h:0.3,fontSize:10,bold:true,color:MUTED,charSpacing:2});
  tx(s,"[Your Team Name]  ·  [Member 1]  ·  [Member 2]  ·  [Member 3]",
     {x:M+0.25,y:5.42,w:6.8,h:0.4,fontSize:14,bold:true,color:INK});
  tx(s,"github.com/harshsingh0120/-Multimodal-Deepfake-Detection-and-Media-Forensics-Platform",
     {x:M,y:6.25,w:7.4,h:0.3,fontSize:10,color:MUTED,fontFace:MONO});
  foot(s,1);
  s.addNotes("Welcome. We built the Multimodal Deepfake Detection & Media Forensics Platform for Problem 02. "+
   "In one line: upload an image, video or audio clip and get back a structured, explainable report on how likely it is to be manipulated — across every modality, not just one. "+
   "I'll take you from the problem, to how it works, the exact technologies and why we chose them, our honest measured results, and the impact. Note our guiding principle you'll see throughout: we report EVIDENCE of potential manipulation, never definitive proof.");
})();

// =====================================================================
// SLIDE 2 — INTRODUCTION
// =====================================================================
(function(){ const s=slide(); kicker(s,"INTRODUCTION"); title(s,"What we are building");
  tx(s,"A media-verification web platform. You give it a photo, a video, or an audio clip; it runs forensic analysis across every modality present, fuses the evidence with a calibrated confidence, and returns a clear, explainable report plus a downloadable PDF.",
     {x:M,y:1.7,w:12.1,h:1.0,fontSize:15,color:INK,lineSpacingMultiple:1.1});
  const y=3.0,w=3.86,h=3.3,g=0.25;
  card(s,M,y,w,h,"What it is",
    "A browser app + analysis engine. Upload media, get a forensic assessment. No installation for the end user — it runs in the browser against our server.",{tag:"1"});
  card(s,M+w+g,y,w,h,"What it does",
    "Scores four signals — image, video (temporal), audio (voice) and lip-sync — flags suspicious frames and audio segments, draws heatmaps, and writes a PDF report.",{tag:"2",tagfill:BLUE});
  card(s,M+2*(w+g),y,w,h,"Who benefits",
    "Journalists and fact-checkers verifying viral media; bank fraud teams catching voice clones; and trust-&-safety analysts triaging reports at scale.",{tag:"3",tagfill:VIOLET});
  foot(s,2);
  s.addNotes("The platform is a web app with an analysis engine behind it. A user uploads any image, video, or audio file. "+
   "It does not just say fake/real — it breaks the decision into four forensic signals, shows where and why it is suspicious with heatmaps and flagged timestamps, and produces a shareable PDF. "+
   "Three audiences benefit directly: journalists and fact-checkers, bank fraud teams facing voice-cloning, and trust-and-safety analysts who must triage large volumes of reported media.");
})();

// =====================================================================
// SLIDE 3 — PROBLEM
// =====================================================================
(function(){ const s=slide(); kicker(s,"THE PROBLEM"); title(s,"Deepfakes are cheap, convincing, and hard to catch");
  bullets(s,[
    {t:"Fake video, cloned voice and manipulated images now enable fraud, impersonation and misinformation at scale.",b:false},
    {t:"Single-modality detectors fail: attackers combine a fake face with synthetic audio, and compression erases the very artifacts a detector relies on.",b:false},
    {t:"Most tools are black boxes — a yes/no with no evidence a human analyst can check or defend.",b:false},
    {t:"They also overfit to one generator and collapse on media made by a different, unseen model.",b:false},
  ],{x:M,y:1.75,w:6.7,h:3.6,fs:14,gap:12});
  // examples column
  rr(s,7.6,1.75,5.1,4.6,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
  tx(s,"REAL-WORLD EXAMPLES",{x:7.85,y:1.95,w:4.6,h:0.3,fontSize:11,bold:true,color:TEAL,charSpacing:1});
  const ex=[["Voice-clone CEO fraud","A cloned executive voice authorises a fraudulent wire transfer over the phone."],
    ["Fabricated public figures","A convincing fake video of a leader spreads before it can be debunked."],
    ["Manipulated KYC selfies","A face-swapped or synthetic selfie defeats identity verification at a bank."]];
  let yy=2.4; ex.forEach(([a,b])=>{ rr(s,7.85,yy,4.6,1.18,{fill:PANEL2,line:STROKE,r:0.08});
    tx(s,a,{x:8.05,y:yy+0.14,w:4.2,h:0.35,fontSize:13,bold:true,color:INK});
    tx(s,b,{x:8.05,y:yy+0.5,w:4.2,h:0.6,fontSize:10.5,color:MUTED,lineSpacingMultiple:1.03}); yy+=1.33; });
  foot(s,3);
  s.addNotes("The core problem: deepfakes are now cheap and convincing. The key insight from the problem statement is that SINGLE-modality detectors fail — attackers mix a fake face with cloned audio, or simply compress the file to hide artifacts. "+
   "On top of that, most tools are black boxes that can't justify their answer, and they overfit to one generator. "+
   "Concretely this looks like voice-clone CEO fraud authorising wire transfers, fabricated videos of public figures, and face-swapped KYC selfies defeating bank onboarding. The people who must catch these — journalists, banks, platforms — currently lack an explainable, multimodal tool.");
})();

// =====================================================================
// SLIDE 4 — MOTIVATION & SOCIAL IMPACT
// =====================================================================
(function(){ const s=slide(); kicker(s,"MOTIVATION & SOCIAL IMPACT"); title(s,"Why this problem matters");
  card(s,M,1.75,6.0,2.25,"Trust is the target",
    "Deepfakes don't just fool individuals — they erode shared trust in what we see and hear. When any clip can be dismissed as fake, real evidence loses its power too. Fast, explainable verification protects that trust.",{tag:"!",tagfill:AMBER,hc:INK});
  card(s,M,4.15,6.0,2.2,"Real financial and safety harm",
    "Voice-clone and face-swap fraud cause direct financial loss and enable harassment and disinformation. Giving front-line reviewers a triage tool reduces harm before it spreads.",{tag:"$",tagfill:GREEN,hc:INK});
  rr(s,7.0,1.75,5.7,4.6,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
  tx(s,"WHO BENEFITS",{x:7.25,y:1.95,w:5,h:0.3,fontSize:11,bold:true,color:TEAL,charSpacing:1});
  const rows=[["Journalists & fact-checkers","Verify footage/photos before publishing"],
    ["Bank fraud teams","Catch voice-cloning in KYC and support calls"],
    ["Trust & safety analysts","Triage reported media at scale"],
    ["Everyday citizens","Benefit from a less polluted information space"]];
  let yy=2.45; rows.forEach(([a,b])=>{ rr(s,7.25,yy,5.2,0.86,{fill:PANEL2,line:STROKE,r:0.07});
    tx(s,a,{x:7.45,y:yy+0.12,w:4.8,h:0.32,fontSize:13,bold:true,color:INK});
    tx(s,b,{x:7.45,y:yy+0.46,w:4.8,h:0.32,fontSize:10.5,color:MUTED}); yy+=0.97; });
  foot(s,4);
  s.addNotes("We chose this problem because the target is trust itself. Deepfakes erode the shared ability to believe what we see and hear — and once everything can be dismissed as fake, genuine evidence is devalued too. "+
   "There is concrete harm: financial fraud, harassment, disinformation. Our social contribution is to put a fast, explainable triage tool in the hands of the people who must verify media — journalists, banks, platforms — and, through them, protect ordinary citizens from a polluted information space.");
})();

// =====================================================================
// SLIDE 5 — PROPOSED SOLUTION
// =====================================================================
(function(){ const s=slide(); kicker(s,"OUR SOLUTION"); title(s,"One tool, every modality, with the reasoning shown");
  // mini pipeline strip
  const y=1.7,h=0.95,w=2.2,g=0.42; let x=M;
  const steps=[["Upload","image · video · audio"],["Analyse","4 forensic branches"],["Fuse","+ calibrated confidence"],["Report","verdict · heatmaps · PDF"]];
  steps.forEach((st,i)=>{ node(s,x,y,w,h,st[0],st[1],{fill:PANEL2}); if(i<3) chevron(s,x+w+0.1,y+h/2-0.1); x+=w+g; });
  // functionalities
  const items=[
    ["Per-modality risk scores","Separate image, video, audio and lip-sync scores — plus one fused overall score."],
    ["Explainable evidence","Every score lists the exact indicators that fired, with a contribution for each."],
    ["Localisation","ELA & frequency heatmaps, flagged suspicious frames (thumbnails) and audio segments."],
    ["Calibrated confidence","Temperature scaling keeps confidence honest; cross-modal disagreement is penalised."],
    ["Downloadable PDF report","A shareable forensic record an analyst can attach to a case."],
    ["Responsible wording","Always 'evidence of potential manipulation' — never a definitive judgement."]];
  const cw=3.86,ch=1.5,gg=0.25; let cx=M,cy=3.1,col=0;
  items.forEach((it,i)=>{ card(s,cx,cy,cw,ch,it[0],it[1],{hfs:13.5,bfs:10.8}); col++;
    if(col===3){col=0;cx=M;cy+=ch+0.22;} else cx+=cw+gg; });
  foot(s,5);
  s.addNotes("Our solution is a single pipeline: Upload, Analyse across four branches, Fuse with calibrated confidence, and Report. "+
   "The functionalities that matter: separate per-modality scores plus one fused score; explainable evidence where every score names the indicators behind it; localisation via heatmaps and flagged frames/segments; calibrated confidence so we're not over-sure; a downloadable PDF; and responsible wording throughout. "+
   "This directly answers the problem: it's multimodal, it's explainable, and it's honest about uncertainty.");
})();

// =====================================================================
// SLIDE 6 — SYSTEM ARCHITECTURE
// =====================================================================
(function(){ const s=slide(); kicker(s,"SYSTEM ARCHITECTURE"); title(s,"How the components fit together");
  // Frontend
  node(s,M,2.2,2.5,1.5,"Frontend","React + Vite + TS\n+ Tailwind (browser)",{fill:PANEL2,fs:14});
  chevron(s,M+2.5+0.12,2.85);
  // API
  node(s,3.5,2.2,2.5,1.5,"REST API","FastAPI + Uvicorn\n/api/analyze · /report",{fill:"13332E",line:TEALD,fs:14,tc:TEAL});
  chevron(s,3.5+2.5+0.12,2.85);
  // Pipeline box containing analyzers
  rr(s,7.0,1.95,5.7,3.9,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
  tx(s,"ANALYSIS PIPELINE (orchestrator)",{x:7.2,y:2.08,w:5.3,h:0.3,fontSize:11,bold:true,color:TEAL,charSpacing:1});
  const an=[["Image","ELA · FFT · noise"],["Video","temporal · optical flow"],["Audio","MFCC · spectral"],["Lip-sync","mouth ↔ audio"]];
  let ax=7.2,ay=2.45; an.forEach((a,i)=>{ node(s,ax,ay,2.6,0.72,a[0],a[1],{fill:PANEL2,fs:12});
    ax+= (i%2===0)?2.75:-2.75; if(i%2===1) ay+=0.82; });
  node(s,7.2,4.2,5.3,0.62,"Late Fusion + Temperature Calibration","",{fill:"2A2140",line:VIOLET,fs:12.5,tc:VIOLET});
  node(s,7.2,4.95,5.3,0.62,"Report Generator  (JSON + PDF)","",{fill:PANEL2,fs:12.5});
  // optional plugin
  rr(s,M,4.15,5.6,1.7,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
  tx(s,"OPTIONAL — trained-model plugin",{x:M+0.2,y:4.28,w:5.2,h:0.3,fontSize:11,bold:true,color:AMBER,charSpacing:1});
  tx(s,"Pre-trained Vision Transformer (Hugging Face) loaded via PyTorch + Transformers. Downloaded, not trained here. Falls back to the forensic engine when absent.",
     {x:M+0.2,y:4.62,w:5.2,h:1.1,fontSize:11,color:MUTED,lineSpacingMultiple:1.05});
  // data-flow note
  tx(s,"Data flow: browser → HTTPS/JSON upload → pipeline routes to the branches that apply → scores fused & calibrated → JSON + PDF returned. Stateless: no database; media processed transiently.",
     {x:M,y:6.35,w:12.1,h:0.7,fontSize:11,italic:true,color:MUTED});
  foot(s,6);
  s.addNotes("Architecture left-to-right. The React frontend in the browser sends the uploaded file over HTTPS to our FastAPI REST API. "+
   "The API hands it to the analysis pipeline — the orchestrator — which routes the media to the branches that apply: image, video, audio, lip-sync. Those scores go into late fusion with temperature calibration, then the report generator emits JSON and a PDF. "+
   "Optionally, a pre-trained Vision Transformer from Hugging Face can replace the image branch's score — it's downloaded, not trained by us, and the system falls back to the forensic engine if it's absent. "+
   "Important: the system is stateless. There is no database; uploaded media is processed transiently and not persisted.");
})();

// =====================================================================
// SLIDE 7 — TECHNOLOGY STACK
// =====================================================================
(function(){ const s=slide(); kicker(s,"TECHNOLOGY STACK"); title(s,"Every technology, and what it does");
  const groups=[
    ["Languages",TEAL,[["Python 3.12","Backend + all analysis & ML"],["TypeScript","Typed frontend logic"]]],
    ["Frontend",BLUE,[["React 18 + Vite","Fast SPA dashboard"],["Tailwind CSS","Consistent responsive styling"]]],
    ["Backend",TEAL,[["FastAPI + Uvicorn","Typed async REST API + auto-docs"],["python-multipart","Handles file uploads"]]],
    ["Vision & Audio",GREEN,[["OpenCV","ELA, FFT, optical flow, faces"],["librosa","Spectrogram, MFCC, flatness"],["scikit-image / SciPy / NumPy","Image & signal math"]]],
    ["ML / Models",VIOLET,[["scikit-learn","Metrics + logistic fusion"],["PyTorch + Transformers (opt.)","Load pre-trained ViT"]]],
    ["Reporting & Media",AMBER,[["ReportLab","Downloadable PDF reports"],["imageio-ffmpeg","Bundled ffmpeg (audio demux)"],["Matplotlib","Evaluation charts"]]],
  ];
  const cw=3.86,chh=2.5,gx=0.25,gy=0.25; let gx0=M,gy0=1.75,c=0;
  groups.forEach((g)=>{ const x=gx0+(c%3)*(cw+gx), y=gy0+Math.floor(c/3)*(chh+gy);
    rr(s,x,y,cw,chh,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
    rr(s,x+0.22,y+0.2,0.22,0.22,{fill:g[1],line:null,r:0.05});
    tx(s,g[0],{x:x+0.55,y:y+0.17,w:cw-0.7,h:0.32,fontSize:13.5,bold:true,color:INK,fontFace:HEAD});
    let yy=y+0.62; g[2].forEach(([a,b])=>{ tx(s,a,{x:x+0.24,y:yy,w:cw-0.48,h:0.26,fontSize:11.5,bold:true,color:g[1]});
      tx(s,b,{x:x+0.24,y:yy+0.235,w:cw-0.48,h:0.3,fontSize:10,color:MUTED}); yy+=0.56; });
    c++; });
  foot(s,7);
  s.addNotes("Our stack, grouped. Python 3.12 runs all backend and analysis; TypeScript types the frontend. "+
   "Frontend: React 18 + Vite for a fast single-page dashboard, Tailwind for consistent styling. Backend: FastAPI — typed, async, with automatic API docs — plus python-multipart for uploads. "+
   "Vision & audio: OpenCV is our computer-vision workhorse (ELA, FFT, optical flow, face detection); librosa handles audio features; scikit-image/SciPy/NumPy do the math. "+
   "ML: scikit-learn for metrics and the logistic fusion; PyTorch + Transformers OPTIONALLY load a pre-trained ViT. Reporting: ReportLab for PDFs, imageio-ffmpeg bundles ffmpeg so no system install is needed, Matplotlib for our evaluation charts. "+
   "The 'why' for each is on the next slides, but the theme is: mature, well-supported libraries, no exotic dependencies, no paid services.");
})();

// =====================================================================
// SLIDE 8 — "AI AGENT" / HOW THE AI SYSTEM WORKS (honest reframe)
// =====================================================================
(function(){ const s=slide(); kicker(s,"HOW THE AI SYSTEM WORKS"); title(s,"An autonomous analysis pipeline — not a chatbot");
  // honest banner
  rr(s,M,1.7,12.1,0.9,{fill:"2A2140",line:VIOLET,r:0.1});
  tx(s,[{text:"Honest framing:  ",options:{bold:true,color:VIOLET}},
    {text:"our system is 'agentic' in that it receives input, decides which tools to run, runs them, and returns a reasoned decision. It is NOT an LLM chatbot — there is no language model, no prompts, no conversation.",options:{color:INK}}],
    {x:M+0.25,y:1.85,w:11.6,h:0.65,fontSize:12.5,isTextBox:true,margin:0,valign:"middle",lineSpacingMultiple:1.03});
  // flow
  const y=3.1,h=1.3,w=2.15,g=0.33; let x=M;
  const flow=[["1 · Receive","Media uploaded via the API"],
    ["2 · Understand","Detect type; demux frames & audio"],
    ["3 · Decide","Route to the branches that apply"],
    ["4 · Act (tools)","Run analyzers / ViT model"],
    ["5 · Respond","Fuse, calibrate, write report"]];
  flow.forEach((f,i)=>{ node(s,x,y,w,h,f[0],f[1],{fill:i===3?"13332E":PANEL2,line:i===3?TEALD:STROKE,fs:13,tc:i===3?TEAL:INK});
    if(i<4) chevron(s,x+w+0.05,y+h/2-0.1); x+=w+g; });
  // chatbot vs agent compare
  rr(s,M,4.95,12.1,1.35,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
  tx(s,"A normal chatbot vs. our analysis agent",{x:M+0.25,y:5.08,w:11,h:0.3,fontSize:12.5,bold:true,color:TEAL});
  tx(s,[{text:"Chatbot: ",options:{bold:true,color:MUTED}},
    {text:"takes text, predicts the next words, returns a sentence.   ",options:{color:INK}},
    {text:"Our agent: ",options:{bold:true,color:TEAL}},
    {text:"takes media, measures physical forensic signals with specialised tools, and returns a structured, evidence-backed decision — reproducible and inspectable.",options:{color:INK}}],
    {x:M+0.25,y:5.45,w:11.6,h:0.8,fontSize:12,isTextBox:true,margin:0,lineSpacingMultiple:1.05});
  foot(s,8);
  s.addNotes("This slide is deliberately honest and will earn credibility with judges. People hear 'AI agent' and assume a chatbot. Ours is agentic in the real sense — it receives input, decides which tools to use, uses them, and returns a reasoned decision — but there is NO language model, no prompts, no conversation. "+
   "The workflow: 1) Receive the media. 2) Understand it — detect type, extract frames and audio. 3) Decide — route to the branches that apply (e.g. skip lip-sync if there's no face or no audio). 4) Act — run the specialised analysis tools and, optionally, the ViT model. 5) Respond — fuse, calibrate, and write the report. "+
   "The contrast at the bottom is the one-liner for judges: a chatbot predicts words; our agent measures physical signals with specialised tools and returns a reproducible, inspectable decision.");
})();

// =====================================================================
// SLIDE 9 — AI / ML IMPLEMENTATION
// =====================================================================
(function(){ const s=slide(); kicker(s,"AI / ML IMPLEMENTATION"); title(s,"Three layers of intelligence — and what we deliberately left out");
  card(s,M,1.75,3.86,3.3,"1 · Interpretable forensic engine",
    "Hand-written signal processing — no training, no GPU. ELA & FFT artifacts, noise/sharpness consistency, temporal flicker, MFCC/spectral audio cues, and a lip-sync correlation. Every output has a formula you can read.",{tag:"◆",tagfill:TEAL,hc:INK,bfs:11});
  card(s,M+4.11,1.75,3.86,3.3,"2 · Pre-trained ViT (optional)",
    "A public Vision Transformer deepfake classifier from Hugging Face, loaded with PyTorch + Transformers. Trained by its authors — we download and run it. Raised real-data AUC from chance to ~0.78.",{tag:"◆",tagfill:BLUE,hc:INK,bfs:11});
  card(s,M+2*4.11,1.75,3.86,3.3,"3 · Learned fusion",
    "A logistic regression combines the branch scores. Cross-validated only for evaluation — not shipped as defaults. Adding the forensic signal lifted fused AUC to ~0.82.",{tag:"◆",tagfill:VIOLET,hc:INK,bfs:11});
  rr(s,M,5.25,12.1,1.1,{fill:"3A1F24",line:RED,r:0.1});
  tx(s,"NOT USED (and why)",{x:M+0.25,y:5.38,w:4,h:0.3,fontSize:11,bold:true,color:RED,charSpacing:1});
  tx(s,"No LLM · no prompt engineering · no RAG · no embeddings or vector database · no function-calling.  Our task is perception (vision + audio signals), not language — so language-model machinery would add cost and opacity without improving detection.",
     {x:M+0.25,y:5.7,w:11.6,h:0.6,fontSize:11.5,color:INK,lineSpacingMultiple:1.04});
  foot(s,9);
  s.addNotes("Our 'AI' is three honest layers. One: an interpretable forensic engine — pure signal-processing math, no training, no GPU; every number has a readable formula. Two: an OPTIONAL pre-trained Vision Transformer from Hugging Face, loaded with PyTorch and Transformers — trained by its authors, we just download and run it; it lifted real-data AUC from chance to about 0.78. Three: a learned logistic-regression fusion, cross-validated for evaluation, which pushed fused AUC to about 0.82. "+
   "The red box is important for a judge expecting RAG and vector databases: we deliberately use NO LLM, no prompts, no RAG, no embeddings, no vector DB, no function-calling — because this is a perception problem, not a language problem. Adding that machinery would add cost and opacity without improving detection. Saying this clearly shows we understand the tools, not just the buzzwords.");
})();

// =====================================================================
// SLIDE 10 — BACKEND
// =====================================================================
(function(){ const s=slide(); kicker(s,"BACKEND IMPLEMENTATION"); title(s,"FastAPI orchestrator + modular analyzers");
  // modules table
  const rows=[[{text:"Module",options:{bold:true,color:"06231F",fill:{color:TEAL}}},{text:"Responsibility",options:{bold:true,color:"06231F",fill:{color:TEAL}}}]];
  [["app/main.py","FastAPI app, routes, CORS, size/type validation"],
   ["utils/media.py","Type detection, frame sampling, ffmpeg audio demux"],
   ["analyzers/*.py","image · video · audio · sync · fusion · model_plugin"],
   ["pipeline.py","Routes media → analyzers → fusion → assembles result"],
   ["report/pdf_report.py","Builds the downloadable PDF (ReportLab)"]].forEach((r,i)=>
    rows.push([{text:r[0],options:{fontFace:MONO,color:TEAL,fill:{color:i%2?PANEL:PANEL2}}},
      {text:r[1],options:{color:INK,fill:{color:i%2?PANEL:PANEL2}}}]));
  s.addTable(rows,{x:M,y:1.75,w:7.0,colW:[2.5,4.5],border:{type:"solid",color:STROKE,pt:1},
    fontFace:BODY,fontSize:11,valign:"middle",rowH:0.52,margin:4});
  // endpoints
  rr(s,7.9,1.75,4.8,4.6,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
  tx(s,"API ENDPOINTS",{x:8.15,y:1.9,w:4.4,h:0.3,fontSize:11,bold:true,color:TEAL,charSpacing:1});
  const eps=[["POST /api/analyze","Upload a file → full JSON assessment"],
    ["GET /api/report/{id}","Download the forensic PDF"],
    ["GET /api/result/{id}","Re-fetch a cached JSON result"],
    ["GET /api/health","Liveness + engine + ffmpeg status"],
    ["GET /api/config","Upload limits & allowed types"]];
  let yy=2.35; eps.forEach(([a,b])=>{ tx(s,a,{x:8.15,y:yy,w:4.4,h:0.28,fontSize:11.5,bold:true,color:INK,fontFace:MONO});
    tx(s,b,{x:8.15,y:yy+0.26,w:4.4,h:0.3,fontSize:10.5,color:MUTED}); yy+=0.78; });
  tx(s,"Request flow:  frontend POSTs the file → validated & saved to a temp dir → pipeline analyses it → JSON returned and a PDF cached by id → temp files deleted.",
     {x:M,y:6.4,w:12.1,h:0.6,fontSize:11,italic:true,color:MUTED});
  foot(s,10);
  s.addNotes("The backend is a FastAPI app. Key modules: main.py holds the routes, CORS, and upload validation; utils/media.py detects the file type, samples video frames, and demuxes audio with the bundled ffmpeg; the analyzers package has one file per branch plus fusion and the optional model plugin; pipeline.py is the orchestrator that routes media through the analyzers to fusion and assembles the result; and report/pdf_report.py builds the PDF. "+
   "Five endpoints: POST /api/analyze is the workhorse — upload returns the full JSON assessment; /api/report/{id} downloads the PDF; /api/result re-fetches a cached result; /health and /config support the UI. "+
   "Request flow: the frontend POSTs the file, we validate and save it to a temp directory, the pipeline analyses it, we return JSON and cache a PDF by id, then delete the temp files — nothing is persisted.");
})();

// =====================================================================
// SLIDE 11 — FRONTEND
// =====================================================================
(function(){ const s=slide(); kicker(s,"FRONTEND IMPLEMENTATION"); title(s,"A clear, responsive React dashboard");
  s.addImage({path:"assets/01_landing.jpg",x:M,y:1.8,w:6.2,h:3.49,rounding:true,shadow:{type:"outer",color:"000000",opacity:0.4,blur:10,offset:4,angle:90}});
  tx(s,"Upload screen — drag & drop, supported types and size shown",{x:M,y:5.35,w:6.2,h:0.3,fontSize:10,color:MUTED,align:"center"});
  const items=[
    ["Stack","React 18 + Vite + TypeScript + Tailwind CSS. Builds to static files the backend can serve."],
    ["Components","Upload panel, staged loader, verdict gauge, per-modality cards, heatmap viewer, flagged-frame gallery."],
    ["Interaction","Drag-and-drop a file → animated progress → results render; a button downloads the PDF."],
    ["How it reaches the backend","The browser sends the file with fetch() to /api/analyze; Vite proxies /api to FastAPI in dev."],
    ["Displaying results","Typed JSON drives the gauge, score bars, evidence bullets, heatmaps and flagged segments."]];
  let yy=1.8; items.forEach(([a,b],i)=>{ rr(s,7.1,yy,5.6,0.86,{fill:PANEL,line:STROKE,r:0.08});
    tx(s,a,{x:7.3,y:yy+0.11,w:5.2,h:0.3,fontSize:12.5,bold:true,color:TEAL});
    tx(s,b,{x:7.3,y:yy+0.42,w:5.2,h:0.4,fontSize:10.3,color:MUTED,lineSpacingMultiple:1.0}); yy+=0.92; });
  foot(s,11);
  s.addNotes("The frontend is a React 18 app built with Vite and TypeScript, styled with Tailwind. It compiles to static files our backend can serve, so the whole thing can run from one server. "+
   "Components include the upload panel, a staged loader, the circular verdict gauge, per-modality cards, a heatmap viewer, and a flagged-frame gallery. "+
   "Interaction is simple: drag-and-drop a file, watch an animated progress indicator, and the results render; one button downloads the PDF. "+
   "It reaches the backend with a standard fetch() POST to /api/analyze — in development Vite proxies /api to FastAPI so there's no CORS friction. The typed JSON response drives every visual element, so the UI and the API never drift apart.");
})();

// =====================================================================
// SLIDE 12 — APIS & EXTERNAL INTEGRATIONS
// =====================================================================
(function(){ const s=slide(); kicker(s,"APIs & EXTERNAL INTEGRATIONS"); title(s,"What talks to what — and no API keys");
  const cards=[
    ["Our REST API (internal)",TEAL,"The FastAPI service the frontend calls. We send a multipart file; we receive a JSON assessment and a PDF. This is the only API in the request path at runtime."],
    ["Hugging Face (build-time)",BLUE,"Public, anonymous download of the pre-trained ViT and the evaluation dataset. No login, no token — used to fetch model weights and test data, not during user requests."],
    ["Bundled ffmpeg",GREEN,"Not a web service — a binary shipped via imageio-ffmpeg. Used locally to demux a video's audio track to WAV so the audio branch can analyse it."]];
  let x=M; cards.forEach(([a,c,b])=>{ rr(s,x,1.8,3.86,2.9,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
    rr(s,x+0.22,2.0,0.22,0.22,{fill:c,line:null,r:0.05});
    tx(s,a,{x:x+0.55,y:1.97,w:3.1,h:0.5,fontSize:13.5,bold:true,color:INK,fontFace:HEAD});
    tx(s,b,{x:x+0.24,y:2.55,w:3.4,h:2.0,fontSize:11.3,color:MUTED,lineSpacingMultiple:1.08}); x+=4.11; });
  rr(s,M,5.0,12.1,1.3,{fill:"3A1F24",line:RED,r:0.1});
  tx(s,"NO SECRETS, NO THIRD-PARTY ACCOUNTS",{x:M+0.25,y:5.13,w:7,h:0.3,fontSize:11,bold:true,color:RED,charSpacing:1});
  tx(s,"There are zero API keys in the project. The core engine calls no external paid service. Everything downloaded (packages, model, dataset) is public and anonymous; the only credentials used in the whole project were the team's own GitHub login to push the code.",
     {x:M+0.25,y:5.45,w:11.6,h:0.8,fontSize:12,color:INK,lineSpacingMultiple:1.05});
  foot(s,12);
  s.addNotes("Integrations, clearly. At runtime there is exactly one API in the path: our own FastAPI service. The frontend sends a multipart file and gets back JSON plus a PDF. "+
   "At build time we touch Hugging Face — a public, anonymous download of the pre-trained ViT and the evaluation dataset. No login, no token, and it is not called during user requests. "+
   "ffmpeg is not a web service; it's a binary bundled through imageio-ffmpeg, used locally to extract a video's audio so the audio branch can run. "+
   "The headline for judges: there are ZERO API keys in this project. The core engine calls no external paid service; everything we downloaded is public; the only credential used anywhere was our own GitHub login to push the code. That also means nothing can leak.");
})();

// =====================================================================
// SLIDE 13 — COMPLETE WORKFLOW
// =====================================================================
(function(){ const s=slide(); kicker(s,"COMPLETE WORKING WORKFLOW"); title(s,"From upload to downloadable report");
  const steps=[["1","User uploads","A photo, video or audio file in the browser."],
    ["2","Validate","Type & size checked; rejected early if unsupported."],
    ["3","Ingest & demux","Sample frames (OpenCV); extract audio (ffmpeg)."],
    ["4","Analyse branches","Image, video, audio and lip-sync run in parallel where they apply."],
    ["5","Fuse & calibrate","Weighted late fusion + temperature scaling → overall score."],
    ["6","Build report","Verdict, evidence, heatmaps, flagged frames/segments, PDF."],
    ["7","Deliver","JSON renders in the UI; PDF available to download."]];
  const w=1.64,h=2.0,g=0.08; let x=M,y=2.2;
  steps.forEach((st,i)=>{ rr(s,x,y,w,h,{fill:i===3?"13332E":PANEL,line:i===3?TEALD:STROKE,r:0.09,shadow:true});
    rr(s,x+w/2-0.26,y+0.18,0.52,0.52,{fill:i===3?TEAL:PANEL2,line:i===3?null:STROKE,r:0.26});
    tx(s,st[0],{x:x+w/2-0.26,y:y+0.27,w:0.52,h:0.36,fontSize:17,bold:true,color:i===3?"06231F":TEAL,align:"center",fontFace:HEAD});
    tx(s,st[1],{x:x+0.1,y:y+0.82,w:w-0.2,h:0.5,fontSize:11.5,bold:true,color:INK,align:"center"});
    tx(s,st[2],{x:x+0.1,y:y+1.3,w:w-0.2,h:0.62,fontSize:9.3,color:MUTED,align:"center",lineSpacingMultiple:1.02});
    if(i<6) chevron(s,x+w+0.0,y+h/2-0.1); x+=w+g; });
  rr(s,M,4.75,12.1,1.55,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
  tx(s,"Edge cases handled along the way",{x:M+0.25,y:4.9,w:8,h:0.3,fontSize:12.5,bold:true,color:TEAL});
  tx(s,"Image with no face → facial checks skipped, noted.   Video with no audio → audio & lip-sync skipped.   Corrupt/oversized/empty file → clear error (HTTP 4xx).   Low-confidence inputs flagged as a limitation, never hidden.",
     {x:M+0.25,y:5.3,w:11.6,h:0.9,fontSize:12,color:INK,lineSpacingMultiple:1.1});
  foot(s,13);
  s.addNotes("End-to-end, a single request: 1) the user uploads a file; 2) we validate type and size and reject bad input early; 3) we ingest — sample frames with OpenCV and demux audio with ffmpeg; 4) the applicable branches analyse the media; 5) scores are fused with weights and temperature-calibrated into one overall score; 6) the report is built with the verdict, evidence, heatmaps and flagged frames/segments; 7) the JSON renders in the UI and the PDF is ready to download. "+
   "Crucially we handle edge cases gracefully: no face means facial checks are skipped and noted; no audio track means audio and lip-sync are skipped; corrupt, oversized or empty files get a clear error; and low-confidence inputs are flagged as a limitation rather than hidden. This robustness is what makes it a working prototype, not a demo that only survives the happy path.");
})();

// =====================================================================
// SLIDE 14 — KEY FEATURES
// =====================================================================
(function(){ const s=slide(); kicker(s,"IMPORTANT FEATURES"); title(s,"What each feature does and how it works");
  const f=[
    ["Per-modality + fused scoring","Each branch outputs an independent 0–1 score; fusion weights them by confidence.","OpenCV · librosa · NumPy"],
    ["Lip-sync consistency","Correlates mouth-openness over time with the audio loudness envelope; mismatch = suspicious.","OpenCV faces + librosa"],
    ["Explainable heatmaps","ELA and FFT overlays show WHERE the image looks edited; spectrogram for audio.","OpenCV + Matplotlib"],
    ["Flagged frames & segments","Highest-scoring frames (with thumbnails) and audio time-ranges are surfaced.","OpenCV · librosa"],
    ["Calibrated confidence","Temperature scaling softens over-confidence; disagreement lowers it.","scikit-learn math"],
    ["Downloadable PDF report","A formatted forensic record with verdict, evidence, heatmaps and limitations.","ReportLab"]];
  const cw=3.86,ch=1.95,gx=0.25,gy=0.22; let c=0;
  f.forEach((it)=>{ const x=M+(c%3)*(cw+gx), y=1.8+Math.floor(c/3)*(ch+gy);
    rr(s,x,y,cw,ch,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
    tx(s,it[0],{x:x+0.24,y:y+0.2,w:cw-0.48,h:0.6,fontSize:13.5,bold:true,color:INK,fontFace:HEAD});
    tx(s,it[1],{x:x+0.24,y:y+0.78,w:cw-0.48,h:0.8,fontSize:10.8,color:MUTED,lineSpacingMultiple:1.05});
    tx(s,it[2],{x:x+0.24,y:y+ch-0.38,w:cw-0.48,h:0.3,fontSize:9.5,bold:true,color:TEAL,fontFace:MONO}); c++; });
  foot(s,14);
  s.addNotes("Six features, each with the mechanism and the tech behind it. Per-modality plus fused scoring: every branch gives a 0–1 score and fusion weights them by confidence. Lip-sync consistency: we correlate how open the mouth is over time with the audio loudness envelope — if they don't move together, that's a red flag, and it's our technically hardest feature. Explainable heatmaps: ELA and FFT overlays show where an image looks edited, plus a spectrogram for audio. Flagged frames and segments: we surface the most suspicious frames with thumbnails and the suspicious audio time-ranges. Calibrated confidence: temperature scaling stops the system being over-sure, and disagreement between branches lowers confidence. And the downloadable PDF: a formatted record with verdict, evidence, heatmaps and limitations. Each is built from mature libraries — OpenCV, librosa, scikit-learn, ReportLab — not magic.");
})();

// =====================================================================
// SLIDE 15 — SECURITY, RELIABILITY & LIMITATIONS
// =====================================================================
(function(){ const s=slide(); kicker(s,"SECURITY, RELIABILITY & LIMITATIONS"); title(s,"Built to be safe, honest about what it can't do");
  card(s,M,1.75,3.86,4.4,"Security & privacy",
    "• Strict file type & size validation.\n• Uploads processed in a temp dir, then deleted — nothing persisted.\n• No database, no user accounts, no secrets in code.\n• CORS restricted to an allow-list.\n• No code executed from uploaded content.",{tag:"◆",tagfill:GREEN,hc:INK,bfs:11.5});
  card(s,M+4.11,1.75,3.86,4.4,"Reliability",
    "• 32 automated tests (unit, API, robustness) all pass.\n• Graceful handling of no-face, no-audio, corrupt, oversized and empty files.\n• Deterministic analysis → reproducible results.\n• Stateless API scales horizontally with more workers.",{tag:"◆",tagfill:BLUE,hc:INK,bfs:11.5});
  card(s,M+2*4.11,1.75,3.86,4.4,"Limitations (stated openly)",
    "• Scores are indicators, not proof.\n• Heavy compression/resizing can hide artifacts.\n• Generalisation to unseen generators is limited.\n• Face-dependent checks need a visible frontal face.\n• A 'Low' result is not a guarantee of authenticity.",{tag:"!",tagfill:AMBER,hc:INK,bfs:11.5});
  tx(s,"On 'AI hallucinations': there is no generative model in the pipeline, so there is nothing to hallucinate — outputs are deterministic measurements, and the optional ViT returns a bounded probability, not free text.",
     {x:M,y:6.35,w:12.1,h:0.6,fontSize:11,italic:true,color:MUTED});
  foot(s,15);
  s.addNotes("Security and privacy by design: strict type and size validation, uploads processed in a temp directory and then deleted, no database, no accounts, no secrets in code, CORS locked to an allow-list, and we never execute anything from an uploaded file. "+
   "Reliability: 32 automated tests across unit, API and robustness all pass; we handle no-face, no-audio, corrupt, oversized and empty inputs gracefully; analysis is deterministic so results reproduce; and because the API is stateless we scale by adding workers. "+
   "Limitations we state openly — this builds trust: scores are indicators not proof, compression can hide artifacts, generalisation to unseen generators is limited, facial checks need a visible face, and a 'Low' result is not a guarantee of authenticity. "+
   "On hallucinations specifically: there is no generative model, so there is nothing to hallucinate — the outputs are deterministic measurements, and the optional ViT returns a bounded probability, never free text.");
})();

// =====================================================================
// SLIDE 16 — IMPLEMENTATION CHALLENGES
// =====================================================================
(function(){ const s=slide(); kicker(s,"IMPLEMENTATION CHALLENGES"); title(s,"What broke, and how we fixed it");
  const rows=[[{text:"Challenge",options:{bold:true,color:"06231F",fill:{color:TEAL}}},
    {text:"How we solved it",options:{bold:true,color:"06231F",fill:{color:TEAL}}}]];
  [["OpenCV 5.0 removed the face detector & bundled cascades","Pinned the stable OpenCV 4.10 line, which ships CascadeClassifier + the Haar data."],
   ["No system ffmpeg on the machine","Shipped a static ffmpeg binary via imageio-ffmpeg — zero system install needed."],
   ["Pre-trained ViT scored WORSE than chance (AUC 0.22)","Diagnosed a reversed id2label in the model; verified on known-real faces; added a fake-index override → AUC 0.78."],
   ["Interpretable engine was chance-level on real deepfakes","Reported it honestly, then added the trained-model + learned-fusion path to lift accuracy."],
   ["CPU-only, no GPU, large models","Kept the core engine GPU-free; made the ViT an optional, cached, lazy-loaded plugin."]].forEach((r,i)=>
    rows.push([{text:r[0],options:{color:INK,fill:{color:i%2?PANEL:PANEL2},bold:true}},
      {text:r[1],options:{color:MUTED,fill:{color:i%2?PANEL:PANEL2}}}]));
  s.addTable(rows,{x:M,y:1.8,w:12.1,colW:[5.0,7.1],border:{type:"solid",color:STROKE,pt:1},
    fontFace:BODY,fontSize:11.5,valign:"middle",rowH:0.78,margin:6});
  foot(s,16);
  s.addNotes("Real challenges and real fixes — this is where judges test whether you actually built it. One: OpenCV 5.0 had just removed the Haar face detector and its data; we pinned the stable 4.10 line that still ships them. Two: the machine had no ffmpeg, so we bundled a static binary through imageio-ffmpeg — no install needed. "+
   "Three, our favourite: the pre-trained ViT first scored WORSE than chance, AUC 0.22. Instead of shipping it, we diagnosed a reversed id2label in the published model, verified the true orientation on known-real faces, and added a fake-index override — which corrected it to 0.78. Four: our own interpretable engine was chance-level on real deepfakes; we reported that honestly and added the trained-model and learned-fusion path to lift accuracy. Five: with no GPU, we kept the core engine GPU-free and made the ViT an optional, cached, lazily-loaded plugin. "+
   "Every one of these is a debugging story we can walk through live.");
})();

// =====================================================================
// SLIDE 17 — DEMO & SCREENSHOTS
// =====================================================================
(function(){ const s=slide(); kicker(s,"DEMO & SCREENSHOTS"); title(s,"The product, end to end");
  s.addImage({path:"assets/02_results.jpg",x:M,y:1.8,w:7.4,h:4.19,rounding:true,shadow:{type:"outer",color:"000000",opacity:0.4,blur:10,offset:4,angle:90}});
  tx(s,"Verdict dashboard — band, score gauge, confidence, per-modality evidence",{x:M,y:6.05,w:7.4,h:0.3,fontSize:10,color:MUTED,align:"center"});
  s.addImage({path:"assets/03_heatmap.jpg",x:8.25,y:1.8,w:4.45,h:2.52,rounding:true,shadow:{type:"outer",color:"000000",opacity:0.4,blur:10,offset:4,angle:90}});
  tx(s,"ELA heatmap — where the image recompresses differently",{x:8.25,y:4.36,w:4.45,h:0.3,fontSize:10,color:MUTED,align:"center"});
  rr(s,8.25,4.8,4.45,1.5,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
  tx(s,"Live demo flow",{x:8.45,y:4.92,w:4,h:0.3,fontSize:12.5,bold:true,color:TEAL});
  tx(s,"Drag in a sample → staged loader → verdict + evidence + heatmaps → download the PDF. Runs locally at http://localhost:8000.",
     {x:8.45,y:5.26,w:4.05,h:0.95,fontSize:11,color:MUTED,lineSpacingMultiple:1.08});
  foot(s,17);
  s.addNotes("These are real screenshots from the running app. On the left is the verdict dashboard: the band, the circular score gauge, calibrated confidence, and the per-modality cards with their evidence bullets. On the right is an ELA heatmap showing where the image recompresses differently from its surroundings — the kind of localisation an analyst can actually point to. "+
   "In the live demo I'll drag in a sample file, you'll see the staged loader, then the verdict with evidence and heatmaps appear, and finally I'll download the PDF. It all runs locally at localhost:8000 with one command.");
})();

// =====================================================================
// SLIDE 18 — EVALUATION & RESULTS
// =====================================================================
(function(){ const s=slide(); kicker(s,"EVALUATION & RESULTS"); title(s,"Measured honestly on real data — no test-set tuning");
  s.addImage({path:"assets/roc_curves.png",x:M,y:1.8,w:5.0,h:4.1,rounding:true,shadow:{type:"outer",color:"000000",opacity:0.35,blur:8,offset:3,angle:90}});
  // metrics table
  const rows=[[{text:"Detector",options:{bold:true,color:"06231F",fill:{color:TEAL}}},
    {text:"AUC",options:{bold:true,color:"06231F",fill:{color:TEAL},align:"center"}},
    {text:"Accuracy",options:{bold:true,color:"06231F",fill:{color:TEAL},align:"center"}}]];
  [["Interpretable engine","0.27","~50% (chance)",RED],
   ["Pre-trained ViT","0.78","75%",BLUE],
   ["2-model ensemble","0.78","76%",MUTED],
   ["Learned fusion (best)","0.82","78%",GREEN]].forEach((r,i)=>
    rows.push([{text:r[0],options:{color:INK,bold:i===3,fill:{color:i%2?PANEL:PANEL2}}},
      {text:r[1],options:{color:r[3],bold:true,align:"center",fill:{color:i%2?PANEL:PANEL2}}},
      {text:r[2],options:{color:INK,align:"center",fill:{color:i%2?PANEL:PANEL2}}}]));
  s.addTable(rows,{x:5.85,y:1.95,w:6.85,colW:[3.25,1.6,2.0],border:{type:"solid",color:STROKE,pt:1},
    fontFace:BODY,fontSize:12.5,valign:"middle",rowH:0.62,margin:6});
  rr(s,5.85,5.1,6.85,1.2,{fill:PANEL,line:STROKE,r:0.1});
  tx(s,"The honest story",{x:6.05,y:5.22,w:6.4,h:0.3,fontSize:12.5,bold:true,color:TEAL});
  tx(s,"Our hand-coded engine is chance-level alone — but its signal is complementary: fusing it with the ViTs beats either (AUC 0.82, ECE 0.025). Cross-dataset, no tuning on the test set, 237 real/fake faces.",
     {x:6.05,y:5.55,w:6.5,h:0.7,fontSize:11,color:INK,lineSpacingMultiple:1.05});
  foot(s,18);
  s.addNotes("This is the slide that separates us from teams that quote a fake 99%. We built an evaluation harness and measured on real data — 237 real-versus-deepfake faces from a public Hugging Face dataset, cross-dataset, with NO tuning on the test set. "+
   "The ROC curve on the left tells the whole story. Our interpretable engine alone is AUC 0.27 — below the chance diagonal, essentially inverted for this generator, and we report that openly. The pre-trained ViT reaches 0.78. A two-model ensemble doesn't help because the models are correlated. But the learned FUSION of the ViTs with our engine reaches AUC 0.82 and, importantly, a near-perfect calibration error of 0.025. "+
   "The lesson: our 'weak' forensic signal is COMPLEMENTARY — it makes a strong trained model better. That's the whole thesis of a multimodal platform, and we proved it with numbers. We also state the caveats: small sample, cross-validation may share identities, so treat it as directional.");
})();

// =====================================================================
// SLIDE 19 — INNOVATION & COMPETITIVE ADVANTAGE
// =====================================================================
(function(){ const s=slide(); kicker(s,"INNOVATION & COMPETITIVE ADVANTAGE"); title(s,"Why ours is different");
  const f=[
    ["Truly multimodal + cross-modal","Most tools score one modality. We also check whether the modalities AGREE — the lip-sync branch catches audio dubbed over real video, which single-stream detectors miss."],
    ["Explainable by construction","Every score is backed by named indicators and heatmaps. An analyst can defend the result — not just trust a black box."],
    ["Complementary fusion, proven","We measured that a transparent forensic signal lifts a trained model (AUC 0.78 → 0.82). Interpretability AND accuracy, not a trade-off."],
    ["Honest & responsible","Calibrated confidence, 'evidence not proof' wording, and openly reported failure cases — exactly what trust-&-safety work requires."],
    ["Zero lock-in, runs anywhere","No GPU, no paid APIs, no keys, no database. A pluggable slot accepts stronger trained models when available."],
    ["Agentic pipeline","It routes, selects tools, and decides autonomously per file — the right 'agent' shape for a perception task."]];
  const cw=6.0,ch=1.5,gx=0.25,gy=0.22; let c=0;
  f.forEach((it)=>{ const x=M+(c%2)*(cw+gx), y=1.8+Math.floor(c/2)*(ch+gy);
    rr(s,x,y,cw,ch,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
    rr(s,x+0.22,y+0.22,0.3,0.3,{fill:TEALD,line:null,r:0.06});
    tx(s,"✓",{x:x+0.22,y:y+0.24,w:0.3,h:0.28,fontSize:14,bold:true,color:"06231F",align:"center"});
    tx(s,it[0],{x:x+0.66,y:y+0.2,w:cw-0.9,h:0.35,fontSize:13.5,bold:true,color:INK,fontFace:HEAD});
    tx(s,it[1],{x:x+0.24,y:y+0.6,w:cw-0.48,h:0.85,fontSize:10.6,color:MUTED,lineSpacingMultiple:1.05}); c++; });
  foot(s,19);
  s.addNotes("What makes us different. First, we're truly multimodal AND cross-modal — we don't just score each stream, we check whether they AGREE; the lip-sync branch catches audio dubbed over real video, which single-stream detectors miss entirely. Second, we're explainable by construction — named indicators and heatmaps mean an analyst can defend the result. Third, we proved complementary fusion: a transparent signal lifting a trained model from 0.78 to 0.82 — interpretability and accuracy together, not a trade-off. Fourth, we're honest and responsible: calibrated confidence, 'evidence not proof', openly reported failures — exactly what trust-and-safety demands. Fifth, zero lock-in: no GPU, no paid APIs, no keys, no database, plus a pluggable slot for stronger models. And the agentic pipeline shape is the right one for a perception task. Why is an agent useful here? Because the right analysis depends on the file — it must decide which tools to run.");
})();

// =====================================================================
// SLIDE 20 — FUTURE SCOPE
// =====================================================================
(function(){ const s=slide(); kicker(s,"FUTURE SCOPE"); title(s,"Where we take it next");
  const f=[
    ["Fine-tuned & cross-generator models","Train the detectors on FaceForensics++/ASVspoof with identity-disjoint splits to push accuracy well past 0.82."],
    ["Trained audio & video plugins","Drop wav2vec2/AASIST (audio) and video models into the existing plugin slots for end-to-end deep detection."],
    ["Attention-based fusion","Replace late fusion with a learned attention head that weighs modalities per sample."],
    ["Scale & deployment","Containerised workers behind a queue for batch/stream triage; a hosted API for partners."],
    ["Richer localisation","Landmark-based lip-sync and PRNU sensor-fingerprint analysis for finer evidence."],
    ["Case management","Accounts, history and collaboration for analyst teams handling many items."]];
  const cw=6.0,ch=1.42,gx=0.25,gy=0.18; let c=0;
  f.forEach((it)=>{ const x=M+(c%2)*(cw+gx), y=1.75+Math.floor(c/2)*(ch+gy);
    rr(s,x,y,cw,ch,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
    tx(s,it[0],{x:x+0.24,y:y+0.18,w:cw-0.48,h:0.35,fontSize:13.5,bold:true,color:TEAL,fontFace:HEAD});
    tx(s,it[1],{x:x+0.24,y:y+0.56,w:cw-0.48,h:0.8,fontSize:11,color:MUTED,lineSpacingMultiple:1.03}); c++; });
  tx(s,"The architecture was designed for this: every heavy model is an optional, pluggable component.",
     {x:M,y:6.6,w:12.1,h:0.4,fontSize:11.5,italic:true,color:MUTED});
  foot(s,20);
  s.addNotes("Future scope, and note the architecture was designed for it — every heavy model is an optional plugin. First and biggest: fine-tune the detectors on FaceForensics++ and ASVspoof with identity-disjoint, cross-generator splits to push accuracy well past 0.82. Add trained audio and video plugins — wav2vec2 or AASIST for voice, a video model — into the slots that already exist. Upgrade late fusion to a learned attention head. For scale, containerised workers behind a queue for batch and stream triage, and a hosted API for partners. Richer localisation with landmark-based lip-sync and PRNU sensor fingerprints. And case management — accounts, history, collaboration — for analyst teams. None of this requires re-architecting; it slots into what we built.");
})();

// =====================================================================
// SLIDE 21 — CONCLUSION
// =====================================================================
(function(){ const s=slide(); bg(s,BG);
  rr(s,M,1.3,12.1,0.9,{fill:"13332E",line:TEALD,r:0.1});
  tx(s,"CONCLUSION",{x:M+0.3,y:1.5,w:11,h:0.5,fontSize:14,bold:true,color:TEAL,charSpacing:2,valign:"middle"});
  const items=[
    ["The problem","Deepfakes defeat single-modality, black-box detectors and erode public trust."],
    ["Our solution","A multimodal, explainable forensic platform: image + video + audio + lip-sync, fused and calibrated, with a shareable report."],
    ["The technology","FastAPI + OpenCV + librosa + ReportLab, with an optional pre-trained ViT and learned fusion — no GPU, no keys, fully open."],
    ["The proof","32/32 tests pass; measured cross-dataset AUC 0.82 with honest, reported limitations."],
    ["The impact","A practical triage tool for journalists, banks and platforms — protecting trust in what we see and hear."]];
  let yy=2.5; items.forEach(([a,b],i)=>{ rr(s,M,yy,12.1,0.7,{fill:i%2?PANEL:PANEL2,line:STROKE,r:0.08});
    tx(s,a,{x:M+0.25,y:yy+0.12,w:2.6,h:0.45,fontSize:13.5,bold:true,color:TEAL,valign:"middle"});
    tx(s,b,{x:M+3.0,y:yy+0.1,w:8.9,h:0.5,fontSize:12,color:INK,valign:"middle",lineSpacingMultiple:1.0}); yy+=0.78; });
  tx(s,"We don't just claim a number — we show the evidence, the limits, and the reasoning. That's what forensics should be.",
     {x:M,y:6.55,w:12.1,h:0.5,fontSize:14,italic:true,bold:true,color:TEAL,align:"center"});
  foot(s,21);
  s.addNotes("To conclude, the through-line: the problem is that deepfakes defeat single-modality black-box detectors and erode trust. Our solution is a multimodal, explainable forensic platform — image, video, audio and lip-sync, fused and calibrated, with a shareable report. The technology is mature and open — FastAPI, OpenCV, librosa, ReportLab, an optional pre-trained ViT and learned fusion — with no GPU, no keys. The proof is real: all tests pass and we measured a cross-dataset AUC of 0.82 with honest limitations. And the impact is a practical triage tool for the people defending the information space. "+
   "Closing line: we don't just claim a number — we show the evidence, the limits, and the reasoning. That is what forensics should be. Thank you.");
})();

// =====================================================================
// SLIDE 22 — THANK YOU / Q&A
// =====================================================================
(function(){ const s=slide(); bg(s,BG);
  rr(s,M,0.7,0.7,0.7,{fill:"0E3B34",line:TEALD,r:0.12});
  tx(s,"◆",{x:M,y:0.78,w:0.7,h:0.5,fontSize:24,color:TEAL,align:"center"});
  tx(s,"Thank you",{x:M,y:2.1,w:9,h:1.1,fontSize:52,bold:true,color:INK,fontFace:HEAD});
  tx(s,"Multimodal Deepfake Detection & Media Forensics Platform",{x:M,y:3.3,w:11,h:0.6,fontSize:18,color:TEAL,bold:true});
  tx(s,"We'd love your questions.",{x:M,y:3.95,w:9,h:0.5,fontSize:16,italic:true,color:MUTED});
  rr(s,M,4.75,12.1,1.5,{fill:PANEL,line:STROKE,r:0.1,shadow:true});
  tx(s,"TEAM",{x:M+0.25,y:4.92,w:3,h:0.3,fontSize:11,bold:true,color:MUTED,charSpacing:2});
  tx(s,"[Your Team Name]   ·   [Member 1]   ·   [Member 2]   ·   [Member 3]",{x:M+0.25,y:5.25,w:11.5,h:0.4,fontSize:15,bold:true,color:INK});
  tx(s,"github.com/harshsingh0120/-Multimodal-Deepfake-Detection-and-Media-Forensics-Platform",
     {x:M+0.25,y:5.75,w:11.5,h:0.3,fontSize:11,color:TEAL,fontFace:MONO});
  foot(s,22);
  s.addNotes("Thank you — we're happy to take questions. If a judge is quiet, prompt them: would you like to see the live demo, dig into the lip-sync math, or discuss how we measured accuracy honestly? Have the repo open and the local server running at localhost:8000 so you can show anything on request.");
})();

p.writeFile({ fileName: "Deepfake_Forensics_Pitch.pptx" }).then(f=>console.log("WROTE",f));
