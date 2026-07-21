const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.3 x 7.5

// ---- Palette: GPU / AI night theme (ties to the blur image) ----
const BG="0B1020", CARD="151B2E", LINE="2A3350", CODE="060912",
      GREEN="76B900" /*GPU green*/, CYAN="22D3EE", PURPLE="A78BFA",
      W="EAF0FB", MUT="8A93A8", AMBER="F5B301", RED="F87171";
const HEAD="Arial", BODY="Calibri", MONO="Courier New";
const COLAB="https://colab.research.google.com/github/daryl-888/Workshop2/blob/main/blur.ipynb";

function bg(s){ s.background={color:BG}; }
function kicker(s,txt,col){ s.addText(txt,{x:0.7,y:0.55,w:11.9,h:0.35,fontFace:MONO,
  fontSize:13,color:col||GREEN,charSpacing:2,bold:true,margin:0}); }
function title(s,txt,y){ s.addText(txt,{x:0.7,y:y||0.9,w:11.9,h:0.9,fontFace:HEAD,
  fontSize:34,bold:true,color:W,margin:0}); }
// small "grid of threads" motif = parallelism
function threadGrid(s,x,y,n,cell,gap,col){
  for(let r=0;r<n;r++)for(let c=0;c<n;c++)
    s.addShape(p.ShapeType.rect,{x:x+c*(cell+gap),y:y+r*(cell+gap),w:cell,h:cell,
      fill:{color:col||GREEN},line:{type:"none"}});
}
function codeCard(s,x,y,w,h,lines,fs){
  fs=fs||12.5;
  s.addShape(p.ShapeType.roundRect,{x,y,w,h,rectRadius:0.06,fill:{color:CODE},line:{color:LINE,width:1}});
  const rt=lines.map(ln=>({text:ln.t,options:{color:ln.c||W,fontFace:MONO,fontSize:fs,
    bold:!!ln.b,italic:!!ln.i,breakLine:true}}));
  s.addText(rt,{x:x+0.22,y:y+0.18,w:w-0.44,h:h-0.34,align:"left",valign:"top",margin:0,
    lineSpacingMultiple:1.05});
}
function card(s,x,y,w,h,fill){ s.addShape(p.ShapeType.roundRect,{x,y,w,h,rectRadius:0.07,
  fill:{color:fill||CARD},line:{color:LINE,width:1}}); }

// =============================================================
// 1 — TITLE
// =============================================================
let s=p.addSlide(); bg(s);
kicker(s,"WORKSHOP 2  ·  FROM ZERO TO GPU",GREEN);
threadGrid(s,0.7,1.28,4,0.1,0.04,GREEN);
s.addText("Why GPUs Run\nthe World's AI",{x:0.7,y:2.0,w:9,h:2.2,fontFace:HEAD,fontSize:54,
  bold:true,color:W,lineSpacingMultiple:0.98,margin:0});
s.addText("You'll blur an image on a real GPU — then see how that exact trick powers ChatGPT.",
  {x:0.72,y:4.35,w:8.6,h:0.7,fontFace:BODY,fontSize:19,color:MUT,margin:0});
s.addText([
  {text:"one thread per pixel",options:{color:GREEN,bold:true}},
  {text:"   →   ",options:{color:MUT}},
  {text:"one thread per number",options:{color:CYAN,bold:true}},
  {text:"   →   ",options:{color:MUT}},
  {text:"a trillion at once",options:{color:PURPLE,bold:true}}],
  {x:0.72,y:5.15,w:11,h:0.5,fontFace:MONO,fontSize:15,margin:0});
s.addNotes("Hook: the chip you'll use today is the same kind that runs ChatGPT. Recap Workshop 1 (Linux). Today: your code on a real GPU, then why that pattern is the engine of modern AI. Have students switch Colab to T4 GPU now.");

// =============================================================
// 2 — RECAP + TODAY  (real before/after image)
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"WHERE WE ARE");
title(s,"Last time: a Linux tool. Today: a GPU.");
s.addImage({path:"blur_before_after.png",x:0.7,y:2.05,w:8.2,h:2.68});
s.addText("Before  →  after: your kernel blurs every pixel in parallel.",
  {x:0.7,y:4.8,w:8.2,h:0.4,fontFace:BODY,fontSize:13,italic:true,color:MUT,margin:0});
card(s,9.15,2.05,3.45,2.68);
s.addText([
  {text:"The plan\n",options:{bold:true,color:W,fontSize:16,breakLine:true,paraSpaceAfter:8}},
  {text:"1  Blur an image on a GPU (lab)\n",options:{color:GREEN,breakLine:true,paraSpaceAfter:6}},
  {text:"2  See it's really matrix math\n",options:{color:CYAN,breakLine:true,paraSpaceAfter:6}},
  {text:"3  That math = every LLM",options:{color:PURPLE}}],
  {x:9.4,y:2.28,w:3.0,h:2.3,fontFace:BODY,fontSize:15,valign:"top",margin:0});
s.addNotes("Bridge from WS1. Today is lecture-heavy with a short lab in the middle. The image is the actual output of the kernel they'll complete.");

// =============================================================
// 3 — THE PATTERN: one thread per output element
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"THE BIG IDEA");
title(s,"One thread per output element");
s.addText("A GPU doesn't do one big job fast. It does the SAME tiny job on thousands of pieces of data at the same time.",
  {x:0.72,y:1.95,w:6.3,h:1.1,fontFace:BODY,fontSize:18,color:MUT,margin:0});
s.addText([
  {text:"For the blur:  ",options:{color:W,bold:true}},
  {text:"one thread is handed one pixel. It averages that pixel's neighbours and writes the result. Millions of threads, one per pixel, all at once.",options:{color:MUT}}],
  {x:0.72,y:3.15,w:6.3,h:1.6,fontFace:BODY,fontSize:16,margin:0});
s.addText("Remember this sentence — the whole workshop is it, scaled up.",
  {x:0.72,y:5.2,w:6.3,h:0.6,fontFace:BODY,fontSize:14,italic:true,color:GREEN,margin:0});
// big grid of pixel-threads
card(s,7.7,1.95,4.9,4.4);
threadGrid(s,8.55,2.45,9,0.3,0.07,CYAN);
s.addText("each square = one pixel = one thread",{x:7.7,y:5.95,w:4.9,h:0.35,align:"center",
  fontFace:MONO,fontSize:12,color:MUT,margin:0});
s.addNotes("Core mental model. Data parallelism. The grid is a picture of a launch: one thread per cell, all running the same kernel simultaneously.");

// =============================================================
// 4 — CPU vs GPU
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"WHY A GPU AT ALL");
title(s,"A few geniuses vs a stadium of students");
// CPU card
card(s,0.7,2.05,5.85,4.2);
s.addText("CPU",{x:1.0,y:2.3,w:5,h:0.5,fontFace:HEAD,bold:true,fontSize:22,color:W,margin:0});
s.addText("A few very fast cores",{x:1.0,y:2.85,w:5,h:0.4,fontFace:BODY,fontSize:15,color:MUT,margin:0});
threadGrid(s,1.0,3.5,2,0.5,0.15,AMBER);
s.addText([{text:"~8–64 ",options:{color:AMBER,bold:true,fontSize:26}},
  {text:"powerful cores.\nGreat at one complicated task at a time.",options:{color:MUT,fontSize:14}}],
  {x:2.6,y:3.5,w:3.7,h:1.5,fontFace:BODY,valign:"top",margin:0});
// GPU card
card(s,6.75,2.05,5.85,4.2);
s.addText("GPU",{x:7.05,y:2.3,w:5,h:0.5,fontFace:HEAD,bold:true,fontSize:22,color:GREEN,margin:0});
s.addText("Thousands of simple cores",{x:7.05,y:2.85,w:5,h:0.4,fontFace:BODY,fontSize:15,color:MUT,margin:0});
threadGrid(s,7.05,3.5,6,0.16,0.06,GREEN);
s.addText([{text:"~2,560 ",options:{color:GREEN,bold:true,fontSize:26}},
  {text:"cores on a Colab T4.\nGreat at the same simple sum, a million times.",options:{color:MUT,fontSize:14}}],
  {x:8.5,y:3.5,w:3.8,h:1.5,fontFace:BODY,valign:"top",margin:0});
s.addText("Blur, matrix multiply, and LLMs are all \"the same simple sum, a million times.\"",
  {x:0.7,y:6.45,w:12,h:0.5,fontFace:BODY,fontSize:15,italic:true,color:CYAN,margin:0,align:"center"});
s.addNotes("The stadium analogy is the keeper. CPU = a few brilliant mathematicians; GPU = a stadium of students each doing one arithmetic problem. For repetitive parallel math, the stadium wins by orders of magnitude.");

// =============================================================
// 5 — THE BLUR KERNEL (their code)
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"THE CODE YOU'LL FINISH");
title(s,"The blur kernel: runs once per pixel");
codeCard(s,0.7,2.0,7.5,4.5,[
 {t:"__global__", c:PURPLE},
 {t:"void blurKernel(uchar* out, uchar* in, int w, int h){", c:W},
 {t:"  // which pixel is THIS thread?", c:MUT},
 {t:"  int col = blockIdx.x*blockDim.x + threadIdx.x;", c:GREEN},
 {t:"  int row = blockIdx.y*blockDim.y + threadIdx.y;", c:GREEN},
 {t:"  if(col<w && row<h){", c:W},
 {t:"    // average the neighbourhood...", c:MUT},
 {t:"    int idx = (curRow*w + curCol)*3;", c:CYAN},
 {t:"    rVal += in[idx+0]; ...", c:W},
 {t:"    out[outIdx] = rVal / pixels;", c:W},
 {t:"  }", c:W},
 {t:"}", c:W}],13);
card(s,8.4,2.0,4.2,4.5);
s.addText([
  {text:"Read it as:\n",options:{bold:true,color:W,fontSize:16,breakLine:true,paraSpaceAfter:8}},
  {text:"\"I am one thread. I figure out my pixel from my position in the grid, average its neighbours, and write one output pixel.\"\n\n",options:{color:MUT,fontSize:15,breakLine:true}},
  {text:"That ",options:{color:MUT,fontSize:15}},
  {text:"idx = (row*w + col)",options:{color:CYAN,fontFace:MONO,fontSize:13}},
  {text:" — flat, row-major indexing — comes back in 3 slides.",options:{color:MUT,fontSize:15}}],
  {x:8.65,y:2.25,w:3.7,h:4.0,fontFace:BODY,valign:"top",margin:0});
s.addNotes("Show the real kernel (trimmed). Emphasize the index math and 'one thread = one pixel'. Foreshadow that matrix multiply uses the identical indexing.");

// =============================================================
// 6 — ZOOM OUT: matrix multiply
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"ZOOM OUT ONE STEP",CYAN);
title(s,"From \"average neighbours\" to \"dot products\"");
s.addText("Matrix multiply C = A × B: each output cell is a row of A times a column of B — multiply pairs, add them up. A 'dot product'.",
  {x:0.72,y:1.95,w:11.8,h:0.8,fontFace:BODY,fontSize:17,color:MUT,margin:0});
// A
const gx=1.2, gy=3.1, cs=0.62;
s.addText("A (a row)",{x:gx,y:gy-0.5,w:2.5,h:0.35,fontFace:BODY,fontSize:13,color:MUT,margin:0});
for(let c=0;c<4;c++){ s.addShape(p.ShapeType.rect,{x:gx+c*cs,y:gy,w:cs-0.06,h:cs-0.06,
  fill:{color:c<4?CARD:CARD},line:{color:GREEN,width:c>=0?1.5:1}});
  s.addText("a"+(c+1),{x:gx+c*cs,y:gy,w:cs-0.06,h:cs-0.06,align:"center",valign:"middle",fontFace:MONO,fontSize:12,color:GREEN,margin:0}); }
s.addText("×",{x:gx+4*cs+0.05,y:gy,w:0.4,h:cs,align:"center",valign:"middle",fontFace:HEAD,bold:true,fontSize:22,color:W,margin:0});
// B column
const bx=gx+4*cs+0.55;
s.addText("B (a col)",{x:bx,y:gy-0.5,w:2,h:0.35,fontFace:BODY,fontSize:13,color:MUT,margin:0});
for(let r=0;r<4;r++){ s.addShape(p.ShapeType.rect,{x:bx,y:gy+r*cs,w:cs-0.06,h:cs-0.06,
  fill:{color:CARD},line:{color:CYAN,width:1.5}});
  s.addText("b"+(r+1),{x:bx,y:gy+r*cs,w:cs-0.06,h:cs-0.06,align:"center",valign:"middle",fontFace:MONO,fontSize:12,color:CYAN,margin:0}); }
s.addText("=",{x:bx+cs+0.1,y:gy,w:0.4,h:cs,align:"center",valign:"middle",fontFace:HEAD,bold:true,fontSize:22,color:W,margin:0});
// result cell
const rx=bx+cs+0.65;
s.addShape(p.ShapeType.rect,{x:rx,y:gy,w:cs-0.06,h:cs-0.06,fill:{color:PURPLE},line:{type:"none"}});
s.addText("C",{x:rx,y:gy,w:cs-0.06,h:cs-0.06,align:"center",valign:"middle",fontFace:HEAD,bold:true,fontSize:16,color:BG,margin:0});
codeCard(s,rx+0.9,gy-0.15,5.2,1.5,[
 {t:"C = a1*b1 + a2*b2", c:W},
 {t:"      + a3*b3 + a4*b4", c:W},
 {t:"one output cell, one thread", c:GREEN,i:true}],13);
s.addText("One output cell = one dot product = one thread's job. Sound familiar?",
  {x:0.72,y:5.7,w:12,h:0.5,fontFace:BODY,fontSize:16,italic:true,color:CYAN,margin:0});
s.addNotes("Generalize the blur: instead of averaging a neighbourhood, each output element is a sum of products (dot product). Still one independent value per output cell.");

// =============================================================
// 7 — SAME SHAPE: matmul kernel
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"YOUR OWN MATMUL KERNEL",CYAN);
title(s,"Same launch. Same indexing. Bigger idea.");
codeCard(s,0.7,2.0,7.7,4.4,[
 {t:"__global__", c:PURPLE},
 {t:"void MatrixMul(float* M, float* N,", c:W},
 {t:"               float* P, int width){", c:W},
 {t:"  int col = blockIdx.x*blockDim.x+threadIdx.x;", c:GREEN},
 {t:"  if(col < width){", c:W},
 {t:"    for(int i=0;i<width;++i){", c:W},
 {t:"      float sum = 0;", c:W},
 {t:"      for(int k=0;k<width;++k)", c:W},
 {t:"        sum += M[i*width+k]*N[k*width+col];", c:CYAN},
 {t:"      P[i*width+col] = sum;   // one cell", c:W},
 {t:"    }", c:W},
 {t:"  }", c:W},
 {t:"}", c:MUT}],12.5);
card(s,8.6,2.0,4.0,4.4);
s.addText([
  {text:"Notice:\n",options:{bold:true,color:W,fontSize:16,breakLine:true,paraSpaceAfter:8}},
  {text:"• ",options:{color:GREEN,fontSize:15}},
  {text:"same thread-index line as the blur\n",options:{color:MUT,fontSize:14,breakLine:true,paraSpaceAfter:6}},
  {text:"• ",options:{color:GREEN,fontSize:15}},
  {text:"same ",options:{color:MUT,fontSize:14}},
  {text:"i*width+k",options:{color:CYAN,fontFace:MONO,fontSize:12}},
  {text:" row-major math\n",options:{color:MUT,fontSize:14,breakLine:true,paraSpaceAfter:6}},
  {text:"• ",options:{color:GREEN,fontSize:15}},
  {text:"one thread → one output cell\n\n",options:{color:MUT,fontSize:14,breakLine:true,paraSpaceAfter:8}},
  {text:"It's the blur pattern, doing math instead of averaging.",options:{color:CYAN,fontSize:14,italic:true}}],
  {x:8.85,y:2.25,w:3.5,h:4.0,fontFace:BODY,valign:"top",margin:0});
s.addNotes("From matmul/Ch3exercises.cu. The point: it's structurally identical to the blur they just wrote. Same indexing, same one-thread-per-output launch.");

// =============================================================
// 8 — MEMORY: coalesced
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"ONE SPEED SECRET");
title(s,"GPUs love neighbours reading neighbours");
s.addText("When threads read memory that sits side-by-side, the hardware grabs it all in one trip. Jump around, and it takes many trips. This is 'coalesced' access — a big part of GPU speed.",
  {x:0.72,y:1.95,w:11.8,h:1.1,fontFace:BODY,fontSize:17,color:MUT,margin:0});
card(s,0.7,3.3,5.85,2.9);
s.addText("Coalesced ✓",{x:1.0,y:3.55,w:5,h:0.4,fontFace:HEAD,bold:true,fontSize:18,color:GREEN,margin:0});
for(let i=0;i<6;i++) s.addShape(p.ShapeType.rect,{x:1.0+i*0.75,y:4.15,w:0.66,h:0.66,fill:{color:GREEN},line:{type:"none"}});
s.addText("threads 1-6 read memory 1-6, in order → one fetch",
  {x:1.0,y:5.0,w:5.3,h:0.9,fontFace:BODY,fontSize:14,color:MUT,margin:0});
card(s,6.75,3.3,5.85,2.9);
s.addText("Scattered ✗",{x:7.05,y:3.55,w:5,h:0.4,fontFace:HEAD,bold:true,fontSize:18,color:RED,margin:0});
const order=[0,3,1,5,2,4];
for(let i=0;i<6;i++) s.addShape(p.ShapeType.rect,{x:7.05+order[i]*0.75,y:4.15,w:0.66,h:0.66,fill:{color:RED},line:{type:"none"}});
s.addText("threads read all over the place → many slow fetches",
  {x:7.05,y:5.0,w:5.3,h:0.9,fontFace:BODY,fontSize:14,color:MUT,margin:0});
s.addText("(This is why your Ch3 column kernel beats the row kernel.)",
  {x:0.7,y:6.55,w:12,h:0.4,fontFace:BODY,fontSize:13,italic:true,color:MUT,margin:0,align:"center"});
s.addNotes("Keep light — one analogy: grabbing a whole shelf row in one reach vs walking back and forth. Callback to their own coalesced-vs-not notes in Ch3exercises.cu.");

// =============================================================
// 9 — WHERE LLMs LIVE
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"THE PAYOFF",PURPLE);
title(s,"An LLM is (mostly) matrix multiplies");
const steps=[
  {t:"Words → numbers",d:"tokens become vectors",c:CYAN},
  {t:"Q, K, V",d:"3 matrix multiplies",c:GREEN},
  {t:"Attention",d:"Q·Kᵀ, then × V — matmuls",c:GREEN},
  {t:"Feed-forward",d:"the biggest matmuls",c:GREEN},
  {t:"Next word",d:"one more matmul",c:PURPLE}];
let sx=0.7, sw=2.3, sgap=0.15, sy=2.4, sh=2.5;
steps.forEach((st,i)=>{
  const x=sx+i*(sw+sgap);
  card(s,x,sy,sw,sh);
  s.addShape(p.ShapeType.rect,{x:x+0.25,y:sy+0.3,w:0.5,h:0.5,fill:{color:st.c},line:{type:"none"}});
  s.addText(String(i+1),{x:x+0.25,y:sy+0.3,w:0.5,h:0.5,align:"center",valign:"middle",fontFace:HEAD,bold:true,fontSize:18,color:BG,margin:0});
  s.addText(st.t,{x:x+0.22,y:sy+1.0,w:sw-0.44,h:0.7,fontFace:HEAD,bold:true,fontSize:15,color:W,margin:0});
  s.addText(st.d,{x:x+0.22,y:sy+1.65,w:sw-0.44,h:0.7,fontFace:BODY,fontSize:13,color:MUT,margin:0,valign:"top"});
  if(i<4) s.addText("→",{x:x+sw-0.02,y:sy+0.9,w:0.2,h:0.5,align:"center",valign:"middle",fontFace:HEAD,bold:true,fontSize:18,color:MUT,margin:0});
});
s.addText("Almost every box above is the same one-thread-per-output-cell matmul you just met.",
  {x:0.7,y:5.4,w:12,h:0.6,fontFace:BODY,fontSize:17,italic:true,color:PURPLE,margin:0,align:"center"});
s.addNotes("The transformer pipeline, labelled by operation. Don't teach transformer internals deeply — just show that the heavy lifting is matmul after matmul, the exact kernel shape they now understand.");

// =============================================================
// 10 — BY THE NUMBERS
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"BY THE NUMBERS",AMBER);
title(s,"Why not just use a CPU?");
const stats=[
  {big:"~2,560",lab:"cores on a Colab T4 GPU\n(a CPU has tens)",c:GREEN},
  {big:"~1–3 TB/s",lab:"GPU memory bandwidth\n(CPU: ~0.05–0.1 TB/s)",c:CYAN},
  {big:"billions",lab:"of multiply-adds per word\nan LLM generates",c:PURPLE}];
let tx=0.7, tw=3.9, tgap=0.3, ty=2.4, th=3.0;
stats.forEach((st,i)=>{
  const x=tx+i*(tw+tgap);
  card(s,x,ty,tw,th);
  s.addText(st.big,{x:x+0.2,y:ty+0.4,w:tw-0.4,h:1.0,align:"center",fontFace:HEAD,bold:true,fontSize:44,color:st.c,margin:0});
  s.addText(st.lab,{x:x+0.2,y:ty+1.7,w:tw-0.4,h:1.1,align:"center",valign:"top",fontFace:BODY,fontSize:15,color:MUT,margin:0});
});
s.addText("Thousands of workers + memory fed fast enough to keep them busy. That combination is what a CPU can't match — and what LLMs need.",
  {x:0.7,y:5.75,w:12,h:0.7,fontFace:BODY,fontSize:15,italic:true,color:AMBER,margin:0,align:"center"});
s.addText("Figures are approximate and illustrative; exact numbers vary by chip.",
  {x:0.7,y:6.55,w:12,h:0.35,fontFace:BODY,fontSize:11,color:MUT,margin:0,align:"center"});
s.addNotes("Some real numbers, framed as orders of magnitude. T4 = 2,560 CUDA cores (they'll use a T4). GPU HBM bandwidth ~TB/s vs CPU ~tens of GB/s. Keep it honest: approximate.");

// =============================================================
// 11 — WHY GPU WINS FOR LLMs
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"PUTTING IT TOGETHER",PURPLE);
title(s,"Three reasons the GPU runs AI");
const rs=[
  {h:"Massive parallelism",d:"Thousands of threads do independent matmul cells at once — exactly the blur pattern.",c:GREEN},
  {h:"Huge memory bandwidth",d:"Weights are enormous; the GPU streams them fast enough to keep all those cores fed.",c:CYAN},
  {h:"Tensor cores",d:"Modern GPUs have hardware built to do one thing: small matrix multiplies, insanely fast.",c:PURPLE}];
let ry=2.35;
rs.forEach(r=>{
  card(s,0.7,ry,11.9,1.2);
  s.addShape(p.ShapeType.rect,{x:1.0,y:ry+0.32,w:0.55,h:0.55,fill:{color:r.c},line:{type:"none"}});
  s.addText(r.h,{x:1.8,y:ry+0.2,w:4.3,h:0.8,fontFace:HEAD,bold:true,fontSize:19,color:W,valign:"middle",margin:0});
  s.addText(r.d,{x:6.1,y:ry+0.2,w:6.3,h:0.8,fontFace:BODY,fontSize:15,color:MUT,valign:"middle",margin:0});
  ry+=1.35;
});
s.addNotes("Summary of the 'why'. Tensor cores = specialized matmul units — the hardware doubling-down on the exact operation LLMs are made of.");

// =============================================================
// 12 — FULL CIRCLE
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"FULL CIRCLE");
title(s,"You already wrote the pattern");
const chain=[
  {t:"Blur",d:"one thread\nper pixel",c:GREEN},
  {t:"Matmul",d:"one thread\nper cell",c:CYAN},
  {t:"Attention",d:"one thread\nper score",c:PURPLE},
  {t:"ChatGPT",d:"millions of\nthreads",c:AMBER}];
let cx=1.1, cw=2.5, cgap=0.7, cy=2.7, ch=2.0;
chain.forEach((n,i)=>{
  const x=cx+i*(cw+cgap);
  card(s,x,cy,cw,ch);
  s.addText(n.t,{x:x+0.15,y:cy+0.35,w:cw-0.3,h:0.6,align:"center",fontFace:HEAD,bold:true,fontSize:22,color:n.c,margin:0});
  s.addText(n.d,{x:x+0.15,y:cy+1.05,w:cw-0.3,h:0.8,align:"center",valign:"top",fontFace:MONO,fontSize:13,color:MUT,margin:0});
  if(i<3) s.addText("→",{x:x+cw+0.05,y:cy+0.6,w:0.6,h:0.7,align:"center",valign:"middle",fontFace:HEAD,bold:true,fontSize:30,color:MUT,margin:0});
});
s.addText("Same idea, four scales. Master the smallest one today and the biggest one stops being magic.",
  {x:0.7,y:5.35,w:12,h:0.6,fontFace:BODY,fontSize:17,italic:true,color:W,margin:0,align:"center"});
s.addNotes("The through-line as one picture. This is the slide to leave up during the lab.");

// =============================================================
// 13 — LAB / CLOSER
// =============================================================
s=p.addSlide(); bg(s);
kicker(s,"YOUR TURN");
threadGrid(s,0.7,1.28,4,0.1,0.04,GREEN);
s.addText("Go fill in the blanks.",{x:0.7,y:2.1,w:7.6,h:1.1,fontFace:HEAD,fontSize:46,bold:true,color:W,margin:0});
// Open-in-Colab button (clickable in the .pptx; on-screen call to action)
s.addShape(p.ShapeType.roundRect,{x:8.7,y:2.12,w:3.9,h:0.92,rectRadius:0.11,fill:{color:AMBER},line:{type:"none"},hyperlink:{url:COLAB}});
s.addText([{text:"▶  Open in Colab",options:{hyperlink:{url:COLAB}}}],
  {x:8.7,y:2.12,w:3.9,h:0.92,align:"center",valign:"middle",fontFace:HEAD,bold:true,fontSize:20,color:BG,margin:0});
s.addText("colab.research.google.com/github/daryl-888/Workshop2",
  {x:8.15,y:3.12,w:5.0,h:0.3,align:"center",fontFace:MONO,fontSize:9,color:MUT,margin:0});
codeCard(s,0.7,3.5,7.2,2.9,[
 {t:"# no install, no downloads:",c:MUT},
 {t:"1. click  Open in Colab  (top right)",c:GREEN},
 {t:"2. Runtime -> T4 GPU, then run cells",c:GREEN},
 {t:"   (cell 1 grabs the repo for you)",c:MUT},
 {t:"3. fill the 9 TODO blanks",c:CYAN},
 {t:"4. it compiles & runs on the GPU",c:W},
 {t:"5. watch your image blur",c:PURPLE}],14);
card(s,8.1,3.5,4.5,2.9);
s.addText([
  {text:"9 blanks.\n",options:{bold:true,color:W,fontSize:20,breakLine:true,paraSpaceAfter:8}},
  {text:"Each one is a line you now understand: which pixel am I, where is it in memory, what's the average.\n\n",options:{color:MUT,fontSize:15,breakLine:true}},
  {text:"Stuck? Hints are in the README.",options:{color:GREEN,fontSize:14,italic:true}}],
  {x:8.35,y:3.75,w:4.0,h:2.5,fontFace:BODY,valign:"top",margin:0});
s.addText("When the right-hand image blurs — you just ran your own code on the same kind of chip that runs AI.",
  {x:0.7,y:6.65,w:12,h:0.5,fontFace:BODY,fontSize:14,italic:true,color:CYAN,margin:0,align:"center"});
s.addNotes("Kick off the lab. Leave the full-circle slide (12) or this one up while students work. Reconvene for the numbers/why slides if you front-loaded the lab.");

p.writeFile({fileName:"workshop-2-gpu-llms.pptx"}).then(f=>console.log("WROTE",f));
