/*
  Generates slides/step-slides.pptx — the slides that carry the code students
  type, in the same grammar as the Workshop 3 deck: green STEP kicker, verbatim
  code panel, violet READ IT AS card, amber callout, green checkpoint strip.

    node slides/generate-step-slides.js

  These are ADDED to the live Google Slides deck (File -> Import slides), not a
  replacement for it. Where each one goes is in FACILITATOR.md.

  The code on these slides is copied verbatim from lab/solutions/gray.cu and
  lab/solutions/blur.cu at build time, so the slide and the notebook can't drift.
*/
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// ---- Workshop 3 visual system ------------------------------------------
const C = {
  canvas: "0E1119", ink: "ECEEF2", body: "A7B0BC", faint: "6B7480",
  violet: "8B80F9", amber: "F5B301", green: "46D07E", blue: "5A9DFF",
  panel: "0A0C12", border: "272C38",
  violetCard: "1B1A33", violetBorder: "6C63D9",
  greenStrip: "0F2A1C", amberCard: "2A2210",
};
const F = { sans: "Arial", mono: "Courier New" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const W = 13.333, M = 0.85;

// ---- pull the code straight from the solutions ---------------------------
const SOL = (f) => fs.readFileSync(path.join(__dirname, "..", "lab", "solutions", f), "utf8");
const gray = SOL("gray.cu");
const blur = SOL("blur.cu");

function between(src, startRe, endRe) {
  const lines = src.split("\n");
  const a = lines.findIndex((l) => startRe.test(l));
  if (a < 0) throw new Error("start not found: " + startRe);
  let b = lines.length;
  for (let i = a + 1; i < lines.length; i++) if (endRe.test(lines[i])) { b = i; break; }
  return lines.slice(a, b);
}
function stripTrailing(lines) {
  while (lines.length && lines[lines.length - 1].trim() === "") lines.pop();
  return lines;
}
const dedent = (lines) => {
  const ind = Math.min(...lines.filter((l) => l.trim()).map((l) => l.match(/^ */)[0].length));
  return lines.map((l) => l.slice(ind));
};

// Trailing comments come off for the slides - the READ IT AS card does that job,
// and the comments make lines too wide for a projector.
const noComments = (lines) => lines.map((l) => l.replace(/\s+\/\/.*$/, ""));

const grayKernel = noComments(stripTrailing(between(gray, /^__global__/, /^\/\/ -{10,}/)));
// The kernel's signature line is already in the student's cell; they type the body.
const grayBody = dedent(stripTrailing(grayKernel.slice(1, -1)));
const blurKernelFull = noComments(stripTrailing(between(blur, /^__global__/, /^\/\/ -{10,}/)));

// For Build 2 the student changes only what's INSIDE `if (col < w && row < h)`,
// so that's all the slide shows. Pull that body out of the solution.
const ifAt = blurKernelFull.findIndex((l) => /if \(col < w && row < h\)/.test(l));
if (ifAt < 0) throw new Error("blur kernel: bounds-check line not found");
const blurBody = dedent(stripTrailing(blurKernelFull.slice(ifAt + 1, -2)))  // drop `}` of if and of fn
  .filter((l) => l.trim() !== "");                                          // blank lines cost height
const block = (marker) => noComments(dedent(stripTrailing(
  between(gray, new RegExp("// " + marker + " "), /^\s*$|^\s*\/\/ (STEP|setup)|^\}/))
  .filter((l) => !/^\s*\/\/ (STEP|setup)/.test(l))));
const stepLines = (n) => block("STEP " + n);
const setupLines = block("setup");

// ---- primitives ----------------------------------------------------------
function slide() {
  const s = pres.addSlide();
  s.background = { color: C.canvas };
  // the pixel-grid mark, top-left
  const cells = [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [0, 2], [2, 2]];
  cells.forEach(([cx, cy]) => {
    s.addShape(pres.ShapeType.rect, {
      x: M + cx * 0.13, y: 0.45 + cy * 0.13, w: 0.1, h: 0.1,
      fill: { color: C.violet }, line: { color: C.violet, width: 0 },
    });
  });
  return s;
}

function kicker(s, text) {
  s.addText(text, {
    x: M + 0.7, y: 0.42, w: 9, h: 0.4, fontFace: F.mono, fontSize: 13,
    color: C.green, charSpacing: 3, bold: true, isTextBox: true, margin: 0,
  });
}

function title(s, text, size = 34) {
  s.addText(text, {
    x: M, y: 0.95, w: W - 2 * M, h: 0.8, fontFace: F.sans, fontSize: size, bold: true,
    color: C.ink, isTextBox: true, margin: 0,
  });
}

function codePanel(s, lines, o) {
  s.addShape(pres.ShapeType.rect, {
    x: o.x, y: o.y, w: o.w, h: o.h,
    fill: { color: C.panel }, line: { color: C.border, width: 1 },
  });
  // tokens to highlight: anything CUDA-specific gets the green
  const runs = [];
  lines.forEach((ln, i) => {
    const parts = ln.split(/(cudaMalloc|cudaMemcpy|cudaFree|cudaMemcpyHostToDevice|cudaMemcpyDeviceToHost|__global__|<<<|>>>|dim3|blockIdx\.[xy]|blockDim\.[xy]|threadIdx\.[xy]|checkKernel|BLUR_SIZE)/g);
    parts.forEach((p) => {
      if (!p) return;
      const cuda = /^(cuda|__global__|<<<|>>>|dim3|blockIdx|blockDim|threadIdx|checkKernel|BLUR_SIZE)/.test(p);
      const comment = /^\s*\/\//.test(p) || (ln.indexOf("//") >= 0 && ln.indexOf(p) >= ln.indexOf("//"));
      runs.push({ text: p, options: { color: comment ? C.faint : cuda ? C.green : C.ink } });
    });
    if (i < lines.length - 1) runs.push({ text: "\n", options: {} });
  });
  s.addText(runs, {
    x: o.x + 0.22, y: o.y + 0.18, w: o.w - 0.44, h: o.h - 0.36,
    fontFace: F.mono, fontSize: o.size ?? 12, valign: "top",
    isTextBox: true, margin: 0, lineSpacingMultiple: 1.12,
  });
}

function readCard(s, lines, o) {
  s.addShape(pres.ShapeType.rect, {
    x: o.x, y: o.y, w: o.w, h: o.h,
    fill: { color: C.violetCard }, line: { color: C.violetBorder, width: 1.25 },
  });
  s.addText("READ IT AS", {
    x: o.x + 0.28, y: o.y + 0.22, w: o.w - 0.5, h: 0.3, fontFace: F.sans, fontSize: 12,
    bold: true, color: C.violet, charSpacing: 2, isTextBox: true, margin: 0,
  });
  s.addText(lines.map((t, i) => ({ text: t, options: { breakLine: i < lines.length - 1,
    paraSpaceAfter: 5 } })), {
    x: o.x + 0.28, y: o.y + 0.6, w: o.w - 0.5, h: o.h - 0.8, fontFace: F.sans,
    fontSize: o.size ?? 14.5, color: C.ink, valign: "top", isTextBox: true, margin: 0,
    lineSpacingMultiple: 1.15,
  });
}

function callout(s, text, o) {
  s.addShape(pres.ShapeType.rect, {
    x: o.x, y: o.y, w: o.w, h: o.h,
    fill: { color: C.amberCard }, line: { color: C.amber, width: 1.25 },
  });
  s.addText("!", {
    x: o.x + 0.25, y: o.y, w: 0.4, h: o.h, fontFace: F.sans, fontSize: 22, bold: true,
    color: C.amber, valign: "middle", isTextBox: true, margin: 0,
  });
  s.addText(text, {
    x: o.x + 0.75, y: o.y, w: o.w - 1.0, h: o.h, fontFace: F.sans, fontSize: 13.5,
    color: C.ink, valign: "middle", isTextBox: true, margin: 0, lineSpacingMultiple: 1.15,
  });
}

function checkpoint(s, text, y = 6.35) {
  s.addShape(pres.ShapeType.rect, {
    x: M, y: y, w: W - 2 * M, h: 0.62,
    fill: { color: C.greenStrip }, line: { color: C.green, width: 1.25 },
  });
  s.addText("✓  " + text, {
    x: M + 0.3, y: y, w: W - 2 * M - 0.5, h: 0.62, fontFace: F.sans, fontSize: 15,
    bold: true, color: C.green, valign: "middle", isTextBox: true, margin: 0,
  });
}

function insertTag(s, where) {
  // Where this slide goes in the live deck. Faint, bottom-right, delete after import.
  s.addText("insert: " + where, {
    x: W - M - 6, y: 7.24, w: 6, h: 0.22, fontFace: F.mono, fontSize: 8,
    color: C.faint, align: "right", isTextBox: true, margin: 0,
  });
}

/* The standard STEP layout: code left, read-card right, optional callout and strip. */
function stepSlide(o) {
  const s = slide();
  kicker(s, o.kicker);
  title(s, o.title);
  // Fixed rhythm on every slide: code + read card from y=1.95; the amber callout
  // always at 5.25; the green checkpoint strip always at 6.35. The read card is
  // sized independently of the code panel so short code never squeezes it.
  const CALLOUT_Y = 5.25;
  const codeH = o.codeH ?? 3.0;
  const codeW = o.codeW ?? 7.15;
  const readH = o.readH ?? (o.callout ? CALLOUT_Y - 0.3 - 1.95 : Math.max(codeH, 2.6));
  codePanel(s, o.code, { x: M, y: 1.95, w: codeW, h: codeH, size: o.codeSize });
  readCard(s, o.read, { x: M + codeW + 0.3, y: 1.95, w: W - 2 * M - codeW - 0.3, h: readH,
    size: o.readSize });
  if (o.callout) {
    callout(s, o.callout, { x: M, y: CALLOUT_Y, w: W - 2 * M, h: 0.85 });
  }
  if (o.checkpoint) checkpoint(s, o.checkpoint, o.checkpointY);
  insertTag(s, o.where);
  s.addNotes(o.notes);
  return s;
}

/* ═══════════════════════════════════ 0. what in_d is (before STEP 1) */
{
  const s = slide();
  kicker(s, "BEFORE STEP 1 · DEVICE POINTERS");
  title(s, "What in_d actually is");

  codePanel(s, ["unsigned char *in_d, *out_d;     // will hold addresses in GPU memory"],
    { x: M, y: 1.95, w: W - 2 * M, h: 0.7, size: 13 });

  // CPU box
  const by = 2.95, bh = 2.2;
  s.addShape(pres.ShapeType.rect, { x: M, y: by, w: 4.6, h: bh,
    fill: { color: C.panel }, line: { color: C.border, width: 1 } });
  s.addText("CPU memory", { x: M + 0.25, y: by + 0.15, w: 3, h: 0.3, fontFace: F.mono,
    fontSize: 11, color: C.amber, charSpacing: 2, isTextBox: true, margin: 0 });
  s.addShape(pres.ShapeType.rect, { x: M + 0.35, y: by + 0.7, w: 3.9, h: 0.75,
    fill: { color: C.canvas }, line: { color: C.amber, width: 1 } });
  s.addText([{ text: "in_d", options: { color: C.ink, bold: true } },
             { text: "  =  0x7f3a2c000000", options: { color: C.body } }], {
    x: M + 0.5, y: by + 0.7, w: 3.7, h: 0.75, fontFace: F.mono, fontSize: 13,
    valign: "middle", isTextBox: true, margin: 0 });
  s.addText("a variable that lives HERE — just a number", { x: M + 0.35, y: by + 1.55,
    w: 3.9, h: 0.4, fontFace: F.sans, fontSize: 12, color: C.body, isTextBox: true, margin: 0 });

  // arrow
  s.addShape(pres.ShapeType.line, { x: M + 4.75, y: by + 1.07, w: 2.55, h: 0,
    line: { color: C.violet, width: 2, endArrowType: "triangle" } });
  s.addText("…points at…", { x: M + 4.75, y: by + 0.65, w: 2.55, h: 0.35, fontFace: F.sans,
    fontSize: 11, color: C.violet, align: "center", isTextBox: true, margin: 0 });

  // GPU box
  const gx = M + 7.45;
  s.addShape(pres.ShapeType.rect, { x: gx, y: by, w: W - M - gx, h: bh,
    fill: { color: C.panel }, line: { color: C.border, width: 1 } });
  s.addText("GPU memory", { x: gx + 0.25, y: by + 0.15, w: 3, h: 0.3, fontFace: F.mono,
    fontSize: 11, color: C.green, charSpacing: 2, isTextBox: true, margin: 0 });
  s.addShape(pres.ShapeType.rect, { x: gx + 0.35, y: by + 0.7, w: W - M - gx - 0.7, h: 0.75,
    fill: { color: "10241A" }, line: { color: C.green, width: 1 } });
  s.addText("7,372,800 bytes — the photo will go here", { x: gx + 0.5, y: by + 0.7,
    w: W - M - gx - 1.0, h: 0.75, fontFace: F.sans, fontSize: 13, color: C.ink,
    valign: "middle", isTextBox: true, margin: 0 });
  s.addText("…memory THERE, which the CPU cannot read", { x: gx + 0.35, y: by + 1.55,
    w: W - M - gx - 0.7, h: 0.4, fontFace: F.sans, fontSize: 12, color: C.body,
    isTextBox: true, margin: 0 });

  callout(s, "You can pass in_d around, print it, hand it to CUDA calls. " +
             "The one thing you must never do is follow it from the CPU — in_d[0] kills the program.",
    { x: M, y: 5.45, w: W - 2 * M, h: 0.85 });
  insertTag(s, "after your Build 1 divider, first");
  s.addNotes(
    "30 seconds. This exists so cudaMalloc(&in_d, ...) on the next slide isn't " +
    "mysterious.\n\n" +
    "in_d is an ordinary variable in ordinary CPU memory. What's special is its " +
    "VALUE: an address on the other machine. The CPU can carry that number around " +
    "and hand it to CUDA, and CUDA knows what to do with it. The CPU itself " +
    "cannot dereference it.\n\n" +
    "If asked why it's declared but not set: that's what STEP 1 does."
  );
}

/* ═══════════════════════════════════ STEP 1 */
stepSlide({
  kicker: "STEP 1 · cudaMalloc", title: "Ask the GPU for memory",
  code: [...setupLines, "", ...stepLines(1)],
  codeH: 2.5, codeSize: 13,
  read: [
    "loadImage / makeImage — the photo into CPU memory, and an empty picture the same size. Helpers from lab/gpulab.h, not CUDA.",
    "&in_d — the address OF our variable, so cudaMalloc can write the GPU address into it.",
    "img.bytes — how many: 1920 × 1280 × 3 = 7,372,800.",
    "Twice: one block for the photo, one for the result.",
  ],
  callout: "Why the &? cudaMalloc has to hand you back an address. A C function can't change " +
           "your variable unless you give it the variable's location — so you pass &in_d, not in_d.",
  where: "after the device-pointer slide",
  notes:
    "Type both lines. Say the & out loud every time - 'the address of in_d'.\n\n" +
    "Concept: cudaMalloc = malloc, but the memory is on the GPU and the CPU can't touch it.\n" +
    "Expected: nothing visible yet.\n" +
    "Pause: on the &. This is the single most-asked-about character in the session.\n" +
    "Stumble: writing cudaMalloc(in_d, ...) without the &. It compiles with a warning " +
    "and then STEP 2 fails with 'a CUDA call BEFORE the launch failed'.\n" +
    "Recovery: the greyscale lifebelt cell.",
});

/* ═══════════════════════════════════ STEP 2 */
stepSlide({
  kicker: "STEP 2 · cudaMemcpy →", title: "Ship the photo across",
  code: stepLines(2), codeH: 1.4, codeSize: 13,
  read: [
    "Destination first. Then source. Like assignment: in_d = img.data.",
    "img.bytes — how many, same as before.",
    "cudaMemcpyHostToDevice — which way. Host is the CPU, device is the GPU.",
  ],
  readSize: 14,
  callout: "Destination comes FIRST — most people expect source first. Swap them, or get the direction " +
           "wrong, and the copy fails; you'll hear about it as 'a CUDA call BEFORE the launch failed'.",
  where: "after STEP 1",
  notes:
    "One line, four arguments. Read them left to right as: where to, where from, how much, which way.\n\n" +
    "Concept: the GPU can't see img.data. This is the moment the photo physically moves.\n" +
    "Expected: nothing visible yet.\n" +
    "Pause: 'host' and 'device' - say it once, then use CPU and GPU.\n" +
    "Stumble: cudaMemcpyDeviceToHost here, or arguments swapped. Both produce the " +
    "'BEFORE the launch' message from the check, which names STEP 1 and 2.\n" +
    "Recovery: lifebelt cell.",
});

/* ═══════════════════════════════════ STEP 3 · launch */
stepSlide({
  kicker: "STEP 3 · THE LAUNCH", title: "Decide how many threads, then go",
  code: stepLines(3),
  codeH: 2.0, codeSize: 12.5, codeW: 7.5,
  read: [
    "block = 16 × 16 = 256 threads, in a square tile.",
    "grid = how many tiles: (1920+15)/16 = 120 across, (1280+15)/16 = 80 down.",
    "120 × 80 × 256 = 2,457,600 threads. One per pixel.",
    "<<<how many tiles, how big>>>, then the ordinary arguments.",
  ],
  readSize: 13,
  callout: "+15 then /16 rounds UP. Integer division rounds down: a 1930-wide photo would give 120 " +
           "tiles and silently lose its last 10 columns. Rounding up is why the kernel needs its if.",
  where: "after STEP 2",
  notes:
    "Three lines plus the given checkKernel. This is the slide to slow down on for the maths.\n\n" +
    "Concept: you don't write a loop, you say how many. dim3 is just a struct of three ints.\n" +
    "Expected: nothing visible yet - the kernel is still empty.\n" +
    "Pause: do the arithmetic out loud. 1920/16, 1280/16, times 256. Land on 2,457,600.\n" +
    "Stumble: forgetting the second dim3, or writing <<<block, grid>>> the wrong way round " +
    "(it runs, wrong picture). dim3 block(32,32) is 1024 - the max; bigger fails to launch.\n" +
    "checkKernel: 'the launch is fire-and-forget; this line waits and asks if it worked.' " +
    "Don't go deeper today.",
});

/* ═══════════════════════════════════ STEP 3 · kernel (greyscale) */
stepSlide({
  kicker: "STEP 3 · THE KERNEL", title: "What one thread does with its one pixel",
  code: ["// the body of imageKernel - its signature line is already in the cell",
         ...grayBody],
  codeH: 3.5, codeSize: 11.5, codeW: 7.6,
  read: [
    "Which pixel am I? blockIdx × blockDim + threadIdx, once across, once down.",
    "Am I on the picture? Rounding up made spare threads; they sit still.",
    "Where does my pixel live? (row × w + col) × 3 — bytes, not pixels.",
    "Then the only line that's about grey.",
  ],
  readSize: 13.5,
  where: "after STEP 3 · the launch",
  notes:
    "About eight real lines. Type the three 'every kernel' lines first and say so - " +
    "col, row, if. Then the address. Then the grey mix.\n\n" +
    "Concept: this runs 2.4 million times, each copy with different blockIdx/threadIdx.\n" +
    "Pause: after the if - 'this is the price of rounding up on the last slide.'\n" +
    "Stumble: (col * w + row) - row and col swapped. Threads run off the end of the " +
    "picture and the check says 'outside the picture... this one is in the kernel'.\n" +
    "Don't derive 0.21/0.72/0.07 - 'eyes see green most, blue least'.",
});

/* ═══════════════════════════════════ STEP 4 */
stepSlide({
  kicker: "STEP 4 · cudaMemcpy ←", title: "Bring the answer home",
  code: stepLines(4),
  codeH: 1.4, codeSize: 13,
  read: [
    "The same call, reversed. Destination is now the CPU's out.data.",
    "Source is out_d — where the GPU wrote the grey pixels.",
    "cudaMemcpyDeviceToHost — GPU to CPU this time.",
  ],
  readSize: 14,
  callout: "Skip this line and NOTHING crashes. The GPU did the work; the CPU never went to collect it. " +
           "You get a black picture and no error. The check will say 'STEP 4'.",
  where: "after STEP 3 · the kernel",
  notes:
    "Same four arguments in the same order - only the pointers swap sides and the direction flips.\n\n" +
    "Concept: results live on the GPU until you ask. Nothing is automatic.\n" +
    "Pause: on the callout. This silent failure is the one they'll hit for real later.\n" +
    "Stumble: leaving it out, or copying INTO out_d again. Both give black.\n" +
    "saveImage is given - it's file writing, not CUDA.",
});

/* ═══════════════════════════════════ STEP 5 */
stepSlide({
  kicker: "STEP 5 · cudaFree", title: "Give the memory back",
  code: stepLines(5),
  codeH: 1.9, codeSize: 13,
  read: [
    "One cudaFree per cudaMalloc. Nothing collects GPU memory for you.",
    "freeImage is the CPU side — the helper, not CUDA. Then return 0.",
  ],
  readSize: 14,
  checkpoint: "Run the cell, then lab.run().  Expect: ✅ Greyscale, and correct — then lab.show().",
  where: "after STEP 4",
  notes:
    "Two lines. Then RUN.\n\n" +
    "Concept: the GPU's memory is a fixed pool; leak it in a loop and you run out.\n" +
    "Expected: '✅ Greyscale, and correct - all 2,457,600 pixels found themselves in the array.'\n" +
    "Then lab.show() - let them look.\n" +
    "Stumble: forgetting a free doesn't break THIS program. Say so; it breaks the next one.\n" +
    "Recovery: lifebelt. Anyone still broken should paste it now, before Build 2.",
});

/* ═══════════════════════════════════ BUILD 2 · the blur kernel */
// The student copies the ENTIRE function from this slide into student/blur.cu,
// whose main() is already written. Blank lines dropped to fit.
const blurFn = blurKernelFull.filter((l) => l.trim() !== "");
stepSlide({
  kicker: "BUILD 2 · THE KERNEL", title: "New file, same main(). Copy this function.",
  code: blurFn,
  codeH: 4.5, codeSize: 9.2, codeW: 8.2, checkpointY: 6.6,
  read: [
    "student/blur.cu — main() is already there. This goes above it.",
    "col, row, the if — same start as greyscale.",
    "Walk the square around me. Skip neighbours off the picture. Count the ones I used.",
    "Divide by n — what I counted — not by 49.",
  ],
  readSize: 12.5,
  checkpoint: "Run the cell, then lab.run(\"blur\").  Expect: ✅ Blur, edges included — then lab.show().",
  where: "after your Build 2 divider",
  notes: [
    "This whole function gets typed into student/blur.cu, above the main() that is",
    "already written there. Open the cell first and scroll through main(): 'you typed",
    "exactly this twenty minutes ago - only the kernel's name is different.'",
    "",
    "Concept: the host code is a reusable shell. What the GPU DOES lives in the kernel.",
    "Expected: '✅ Blur, and it matches a CPU version exactly - edges included.'",
    "Pause: on 'divide by n'. Ask why not 49. Someone will get it - corners.",
    "Stumble: /49 - the check says 'the outermost 3 pixels are dark'. A greyscale kernel",
    "pasted here by mistake - the check says 'greyscale, not blurred'. Wrong function name -",
    "won't compile; main() calls blurKernel.",
    "Then: BLUR_SIZE 15, re-run. Twenty times the work, same instant.",
  ].join("\n"),
});

const out = path.join(__dirname, "step-slides.pptx");
pres.writeFile({ fileName: out }).then(() => console.log("wrote " + out));
