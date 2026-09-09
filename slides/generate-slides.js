/*
  Generates slides/workshop-2-gpu-llms.pptx

    npm install                 (once, from the repo root)
    python lab/verify.py        (produces build/gray.ppm and build/blur.ppm)
    python slides/make_assets.py
    node slides/generate-slides.js

  Import into Google Slides with File -> Import slides.

  The deck runs ~30 minutes and stops where the live coding starts. Speaker
  notes on every slide. Two conventions used throughout:
      CPU = amber        GPU = green        "put the laptop down" = violet
*/
const pptxgen = require("pptxgenjs");
const path = require("path");

const A = (f) => path.join(__dirname, "assets", f);

const C = {
  ink: "12161C",          // near-black, dark slide background
  panel: "1C232D",        // raised panel on dark
  paper: "F5F7FA",        // light slide background
  card: "FFFFFF",
  text: "12161C",
  textDim: "5C6B7A",
  onDark: "F5F7FA",
  onDarkDim: "97A6B5",
  cpu: "E8A33D",          // amber - the CPU, everywhere
  gpu: "3DDC84",          // green - the GPU, everywhere
  gpuInk: "17853F",       // the same green, dark enough to read on white
  cue: "9B8CFA",          // violet - stop talking, start typing
  line: "DCE3EB",
  // Byte colours for the flat-array diagram. Deliberately NOT amber/green:
  // those two mean CPU and GPU everywhere else in this deck.
  chR: "E98C82", chG: "8AC79B", chB: "8FAAD9",
};

const F = { head: "Arial", body: "Calibri", code: "Courier New" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.author = "From Zero to GPU";
pres.title = "Run Your Code on a GPU";

const W = 13.333, H = 7.5, M = 0.7;

/* ---------------------------------------------------------------- helpers */
function slide(bg) {
  const s = pres.addSlide();
  s.background = { color: bg || C.paper };
  return s;
}

function title(s, txt, opts = {}) {
  s.addText(txt, {
    x: M, y: opts.y ?? 0.45, w: W - 2 * M, h: 0.9,
    fontFace: F.head, fontSize: opts.size ?? 34, bold: true,
    color: opts.color ?? C.text, align: "left", isTextBox: true, margin: 0,
  });
}

function body(s, txt, o = {}) {
  s.addText(txt, {
    x: o.x ?? M, y: o.y ?? 1.5, w: o.w ?? W - 2 * M, h: o.h ?? 1.0,
    fontFace: F.body, fontSize: o.size ?? 16, color: o.color ?? C.textDim,
    align: o.align ?? "left", isTextBox: true, margin: 0,
    lineSpacingMultiple: o.lsm ?? 1.15, bold: o.bold ?? false,
  });
}

function card(s, o) {
  s.addShape(pres.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.09,
    fill: { color: o.fill ?? C.card },
    line: { color: o.stroke ?? C.line, width: 1 },
  });
}

// A small filled circle with a character in it - the repeated motif.
function dot(s, o) {
  s.addShape(pres.ShapeType.ellipse, {
    x: o.x, y: o.y, w: o.d, h: o.d, fill: { color: o.color },
    line: { color: o.color, width: 1 },
  });
  s.addText(o.label, {
    x: o.x, y: o.y, w: o.d, h: o.d, fontFace: F.head,
    fontSize: o.size ?? 13, bold: true, color: o.text ?? C.ink,
    align: "center", valign: "middle", isTextBox: true, margin: 0,
  });
}

function code(s, lines, o) {
  s.addText(lines, {
    x: o.x, y: o.y, w: o.w, h: o.h,
    fontFace: F.code, fontSize: o.size ?? 13, color: o.color ?? C.onDark,
    fill: o.fill ? { color: o.fill } : undefined,
    align: "left", isTextBox: true, margin: o.pad ?? 10,
    lineSpacingMultiple: 1.2,
  });
}

/* A "put the laptop down / pick it up" divider. */
function cueSlide(kicker, heading, lines, notes) {
  const s = slide(C.ink);
  s.addText(kicker, {
    x: M, y: 1.9, w: W - 2 * M, h: 0.4, fontFace: F.head, fontSize: 15,
    bold: true, color: C.cue, charSpacing: 2, isTextBox: true, margin: 0,
  });
  s.addText(heading, {
    x: M, y: 2.35, w: W - 2 * M, h: 1.1, fontFace: F.head, fontSize: 44,
    bold: true, color: C.onDark, isTextBox: true, margin: 0,
  });
  s.addText(lines, {
    x: M, y: 3.6, w: 8.6, h: 1.8, fontFace: F.body, fontSize: 17,
    color: C.onDarkDim, isTextBox: true, margin: 0, lineSpacingMultiple: 1.3,
  });
  s.addNotes(notes);
  return s;
}

/* ══════════════════════════════════════════════════ 1. title */
{
  const s = slide(C.ink);
  s.addText("Run Your Code on a GPU", {
    x: M, y: 2.5, w: 11, h: 1.2, fontFace: F.head, fontSize: 54, bold: true,
    color: C.onDark, isTextBox: true, margin: 0,
  });
  s.addText("From Zero to GPU  ·  Session 2", {
    x: M, y: 1.95, w: 11, h: 0.4, fontFace: F.head, fontSize: 14, bold: true,
    color: C.gpu, charSpacing: 3, isTextBox: true, margin: 0,
  });
  s.addText("In one hour you will write a program that changes a photo\nusing 2,457,600 threads at the same time.", {
    x: M, y: 3.85, w: 9.5, h: 1.0, fontFace: F.body, fontSize: 19,
    color: C.onDarkDim, isTextBox: true, margin: 0, lineSpacingMultiple: 1.3,
  });
  s.addNotes(
    "Welcome back. Last time: you built a tool on a Linux machine.\n\n" +
    "Today is different - today your code runs on a completely different " +
    "processor, and you'll see a photo change because of it.\n\n" +
    "Housekeeping: get Colab open and switch the runtime to T4 GPU NOW, " +
    "before we start talking. The first GPU allocation is slow and I want it " +
    "out of the way."
  );
}

/* ══════════════════════════════════════════════════ 2. the hook */
{
  const s = slide(C.ink);
  title(s, "Why does everyone want these chips?", { color: C.onDark, y: 1.1 });
  s.addText("Every answer ChatGPT gives you is\nthousands of GPU cores doing simple sums.", {
    x: M, y: 2.3, w: 11.5, h: 1.6, fontFace: F.head, fontSize: 32, bold: true,
    color: C.gpu, isTextBox: true, margin: 0, lineSpacingMultiple: 1.2,
  });
  s.addText("By the end of the hour you'll have written that same kind of code — " +
            "the same shape, on a much smaller problem — and you'll know exactly " +
            "why it has to be a GPU and not the processor you normally use.", {
    x: M, y: 4.25, w: 10.5, h: 1.3, fontFace: F.body, fontSize: 17,
    color: C.onDarkDim, isTextBox: true, margin: 0, lineSpacingMultiple: 1.3,
  });
  s.addNotes(
    "This is the promise for the hour. Don't oversell - be specific: the " +
    "SHAPE of what they write today is the shape of what runs a model.\n\n" +
    "Don't explain how yet. That's the payoff at the end, and it lands much " +
    "harder once they've written the code."
  );
}

/* ══════════════════════════════════════════════════ 3. the analogy */
{
  const s = slide();
  title(s, "A CPU and a GPU are good at opposite things");

  card(s, { x: M, y: 1.55, w: 5.75, h: 4.3 });
  dot(s, { x: M + 0.45, y: 1.95, d: 0.62, color: C.cpu, label: "CPU" , size: 11});
  s.addText("Four brilliant mathematicians", {
    x: M + 0.45, y: 2.8, w: 4.9, h: 0.5, fontFace: F.head, fontSize: 20,
    bold: true, color: C.text, isTextBox: true, margin: 0,
  });
  body(s, "Give them anything — a hard problem, a weird problem, a problem that " +
          "changes halfway through — and they'll work it out, fast, one step " +
          "after another.\n\nAsk them to do a million tiny sums and they'll be " +
          "there all afternoon.", {
    x: M + 0.45, y: 3.35, w: 4.9, h: 2.2, size: 15,
  });

  card(s, { x: 7.05, y: 1.55, w: 5.6, h: 4.3 });
  dot(s, { x: 7.5, y: 1.95, d: 0.62, color: C.gpu, label: "GPU", size: 11 });
  s.addText("A stadium of students", {
    x: 7.5, y: 2.8, w: 4.7, h: 0.5, fontFace: F.head, fontSize: 20,
    bold: true, color: C.text, isTextBox: true, margin: 0,
  });
  body(s, "Each one can do exactly one small sum, and not quickly.\n\n" +
          "But there are thousands of them, and if you can hand every single " +
          "person their own sum at the same moment, they finish together — in " +
          "the time it takes to do one.", {
    x: 7.5, y: 3.35, w: 4.7, h: 2.2, size: 15,
  });

  body(s, "Today's job — “make every pixel in this photo grey” — is two and a half million tiny identical sums.", {
    x: M, y: 6.15, w: W - 2 * M, h: 0.5, size: 16, bold: true, color: C.text,
  });
  s.addNotes(
    "Spend real time here. This analogy carries the whole session.\n\n" +
    "The key move is 'identical and independent'. The stadium only wins when " +
    "every person can start immediately without waiting for anyone else's " +
    "answer. If sum #2 needs the result of sum #1, the stadium is useless and " +
    "the mathematicians win.\n\n" +
    "Ask the room: which of these is 'add up these million numbers'? (Trick " +
    "question - it's partly sequential. Don't dwell, just plant it.)"
  );
}

/* ══════════════════════════════════════════════════ 4. the numbers */
{
  const s = slide();
  title(s, "The same trade, in numbers");

  const rows = [
    ["How many cores", "8 – 16", "Thousands"],
    ["Speed of one core", "Very fast", "Fairly slow"],
    ["Best at", "Anything, in order", "One job, a million times"],
    ["Memory", "Your RAM", "Its own, separate"],
  ];

  s.addText("", { x: M, y: 1.5, w: 0.1, h: 0.1, isTextBox: true }); // spacer
  const y0 = 1.75, rh = 0.86;

  s.addText("CPU", { x: 5.5, y: 1.25, w: 3.4, h: 0.4, fontFace: F.head, fontSize: 15,
    bold: true, color: C.cpu, align: "center", isTextBox: true, margin: 0 });
  s.addText("GPU", { x: 9.1, y: 1.25, w: 3.5, h: 0.4, fontFace: F.head, fontSize: 15,
    bold: true, color: C.gpu, align: "center", isTextBox: true, margin: 0 });

  rows.forEach((r, i) => {
    const y = y0 + i * rh;
    if (i % 2 === 0) {
      s.addShape(pres.ShapeType.rect, {
        x: M, y: y - 0.06, w: W - 2 * M, h: rh - 0.06,
        fill: { color: "ECF0F5" }, line: { color: "ECF0F5", width: 0 },
      });
    }
    s.addText(r[0], { x: M + 0.2, y: y, w: 4.4, h: rh - 0.2, fontFace: F.body,
      fontSize: 16, color: C.textDim, valign: "middle", isTextBox: true, margin: 0 });
    s.addText(r[1], { x: 5.5, y: y, w: 3.4, h: rh - 0.2, fontFace: F.head,
      fontSize: 17, bold: true, color: C.text, align: "center", valign: "middle",
      isTextBox: true, margin: 0 });
    s.addText(r[2], { x: 9.1, y: y, w: 3.5, h: rh - 0.2, fontFace: F.head,
      fontSize: 17, bold: true, color: C.text, align: "center", valign: "middle",
      isTextBox: true, margin: 0 });
  });

  body(s, "That last row is the one that catches everybody out.", {
    x: M, y: 5.6, w: 11, h: 0.5, size: 17, bold: true, color: C.text,
  });
  s.addNotes(
    "Move quickly through the first three rows - they're just the analogy made " +
    "concrete.\n\nStop hard on the last row. Separate memory is the thing that " +
    "makes CUDA code look the way it does, and if they don't get it now, every " +
    "cudaMemcpy in the build will look like pointless bureaucracy.\n\n" +
    "Next slide is entirely about that row."
  );
}

/* ══════════════════════════════════════════════════ 5. two memories */
{
  const s = slide();
  title(s, "The catch: the GPU cannot see your data");

  // CPU side
  card(s, { x: M, y: 1.75, w: 4.55, h: 3.1, fill: "FDF4E5", stroke: "F0D9AC" });
  s.addText("CPU", { x: M + 0.3, y: 2.0, w: 2, h: 0.4, fontFace: F.head,
    fontSize: 14, bold: true, color: C.cpu, isTextBox: true, margin: 0 });
  s.addText("your photo\nlives here", { x: M + 0.3, y: 2.55, w: 3.9, h: 1.0,
    fontFace: F.head, fontSize: 20, bold: true, color: C.text, isTextBox: true,
    margin: 0, lineSpacingMultiple: 1.15 });
  body(s, "Ordinary memory. Your program can read and write it whenever it likes.", {
    x: M + 0.3, y: 3.7, w: 3.9, h: 1.0, size: 14 });

  // GPU side
  card(s, { x: 8.1, y: 1.75, w: 4.55, h: 3.1, fill: "E9FBF1", stroke: "A9E9C6" });
  s.addText("GPU", { x: 8.4, y: 2.0, w: 2, h: 0.4, fontFace: F.head,
    fontSize: 14, bold: true, color: "1F9E5C", isTextBox: true, margin: 0 });
  s.addText("its own memory,\ncompletely separate", { x: 8.4, y: 2.55, w: 3.9, h: 1.0,
    fontFace: F.head, fontSize: 20, bold: true, color: C.text, isTextBox: true,
    margin: 0, lineSpacingMultiple: 1.15 });
  body(s, "Thousands of cores can read this at once. Your CPU cannot touch it at all.", {
    x: 8.4, y: 3.7, w: 3.9, h: 1.0, size: 14 });

  // arrows between
  s.addShape(pres.ShapeType.line, {
    x: 5.45, y: 2.65, w: 2.55, h: 0,
    line: { color: C.textDim, width: 2, endArrowType: "triangle" },
  });
  s.addText("copy over", { x: 5.45, y: 2.2, w: 2.55, h: 0.4, fontFace: F.body,
    fontSize: 13, color: C.textDim, align: "center", isTextBox: true, margin: 0 });

  s.addShape(pres.ShapeType.line, {
    x: 5.45, y: 3.75, w: 2.55, h: 0,
    line: { color: C.textDim, width: 2, beginArrowType: "triangle" },
  });
  s.addText("copy back", { x: 5.45, y: 3.9, w: 2.55, h: 0.4, fontFace: F.body,
    fontSize: 13, color: C.textDim, align: "center", isTextBox: true, margin: 0 });

  body(s, "Two machines in one box, with a cable between them. Nothing the GPU does " +
          "is visible to you until you ask for it back — and that copying is not free. " +
          "We'll measure it later.", {
    x: M, y: 5.35, w: 11.5, h: 1.0, size: 16, color: C.text,
  });
  s.addNotes(
    "The single most useful mental picture in the session. Draw it in the air " +
    "if you have to.\n\n" +
    "Emphasise: this isn't a rule someone invented, it's physical. They're " +
    "different chips with different memory attached.\n\n" +
    "Foreshadow the race: 'hold onto the fact that those two arrows cost time. " +
    "At the end we'll find out that they cost MORE time than the actual work.'"
  );
}

/* ══════════════════════════════════════════════════ 6. the five steps */
{
  const s = slide(C.ink);
  title(s, "So every CUDA program does these five things", { color: C.onDark });
  body(s, "Leave this on the screen. Every program we write today has exactly this skeleton.", {
    y: 1.4, size: 15, color: C.onDarkDim,
  });

  const steps = [
    ["1", "Ask the GPU for memory", "cudaMalloc(&in_d, bytes);"],
    ["2", "Copy your data over", "cudaMemcpy(in_d, img, bytes, cudaMemcpyHostToDevice);"],
    ["3", "Run your code there", "myKernel<<<grid, block>>>(out_d, in_d, w, h);"],
    ["4", "Copy the answer back", "cudaMemcpy(out, out_d, bytes, cudaMemcpyDeviceToHost);"],
    ["5", "Give the memory back", "cudaFree(in_d);"],
  ];

  steps.forEach((st, i) => {
    const y = 2.05 + i * 0.92;
    dot(s, { x: M, y: y + 0.05, d: 0.5, color: i === 2 ? C.gpu : C.panel,
             label: st[0], text: i === 2 ? C.ink : C.onDark, size: 14 });
    s.addText(st[1], { x: M + 0.75, y: y, w: 3.5, h: 0.6, fontFace: F.head,
      fontSize: 16, bold: true, color: C.onDark, valign: "middle",
      isTextBox: true, margin: 0 });
    code(s, st[2], { x: M + 4.35, y: y + 0.02, w: 7.6, h: 0.58,
      size: 12, color: i === 2 ? C.gpu : C.onDarkDim, fill: C.panel });
  });

  s.addNotes(
    "This is the reference slide. Genuinely leave it up while you code, or " +
    "duplicate it and come back to it.\n\n" +
    "Point out that step 3 is the only one that's interesting, and it's the " +
    "only one they'll write today. Steps 1, 2, 4, 5 are already typed in the " +
    "notebook and never change between the two programs.\n\n" +
    "'Host' = CPU, 'device' = GPU. That's why it says HostToDevice. Say it once " +
    "so the constant names stop looking cryptic."
  );
}

/* ══════════════════════════════════════════════════ 7. threads in blocks */
{
  const s = slide();
  title(s, "You don't write a loop. You say how many.");
  body(s, "You ask for a number of threads, and they all start at once. But they arrive " +
          "in fixed-size groups called blocks — so a thread has to work out which piece " +
          "of the job is actually its own.", { y: 1.35, h: 0.8, size: 16 });

  // three blocks of four threads
  const bx = [1.15, 5.0, 8.85], bw = 3.3, by = 2.55;
  bx.forEach((x, b) => {
    card(s, { x: x, y: by, w: bw, h: 1.5, fill: "ECF0F5", stroke: C.line });
    s.addText("block " + b, { x: x, y: by + 0.1, w: bw, h: 0.32, fontFace: F.head,
      fontSize: 12, bold: true, color: C.textDim, align: "center",
      isTextBox: true, margin: 0 });
    for (let t = 0; t < 4; t++) {
      const tx = x + 0.22 + t * 0.73;
      s.addShape(pres.ShapeType.roundRect, {
        x: tx, y: by + 0.55, w: 0.62, h: 0.72, rectRadius: 0.06,
        fill: { color: C.gpu }, line: { color: "2FBF6F", width: 1 },
      });
      s.addText(String(t), { x: tx, y: by + 0.55, w: 0.62, h: 0.32,
        fontFace: F.body, fontSize: 10, color: "0E5A33", align: "center",
        isTextBox: true, margin: 0 });
      s.addText(String(b * 4 + t), { x: tx, y: by + 0.8, w: 0.62, h: 0.42,
        fontFace: F.head, fontSize: 16, bold: true, color: C.ink,
        align: "center", isTextBox: true, margin: 0 });
    }
  });

  s.addText([
    { text: "small number", options: { bold: true, color: C.text } },
    { text: " = threadIdx.x, my seat inside my block          ", options: {} },
    { text: "large number", options: { bold: true, color: C.text } },
    { text: " = the one we actually want: 0 to 11, once each", options: {} },
  ], { x: M, y: 4.2, w: 11.9, h: 0.35, fontFace: F.body, fontSize: 13,
    color: C.textDim, align: "center", isTextBox: true, margin: 0 });

  code(s, "int col = blockIdx.x * blockDim.x + threadIdx.x;", {
    x: M, y: 4.75, w: 11.9, h: 0.62, size: 18, color: C.onDark, fill: C.ink, pad: 12,
  });
  body(s, "“Skip past all the blocks in front of me, then add my own seat.”  " +
          "Do it once for across (x) and once for down (y), and a thread knows its pixel.", {
    y: 5.6, size: 16, color: C.text, h: 0.8,
  });
  s.addNotes(
    "THE most important slide before the build. They are about to type this " +
    "exact line twice and I want it to be familiar, not magic.\n\n" +
    "Walk the diagram: green boxes are threads, small number is threadIdx, big " +
    "number is what we compute. Note 0..11 with no gaps and no repeats - that's " +
    "the whole requirement. Two threads with the same number would fight over " +
    "one pixel; a missing number means a pixel nobody colours.\n\n" +
    "The cinema analogy works well: row number times seats per row, plus your " +
    "seat.\n\nDon't explain WHY blocks exist (shared memory, scheduling). Not " +
    "today. If asked: 'the hardware hands work out in groups, and there are " +
    "clever things you can do within a group - that's session three.'"
  );
}

/* ══════════════════════════════════════════════════ 8. flat array */
{
  const s = slide();
  title(s, "And a photo is just one long line of numbers");
  body(s, "There is no grid in memory. Every row is laid end to end, and every pixel " +
          "is three bytes: red, green, blue.", { y: 1.35, h: 0.6, size: 16 });

  // Two rows of two pixels, each pixel three bytes. Bytes are coloured by
  // channel, which is both accurate and keeps amber/green meaning CPU/GPU.
  const sx = M, sy = 2.55, cw = 0.44, pw = cw * 3, gap = 0.55;
  const letters = ["R", "G", "B"];
  const chFill = [C.chR, C.chG, C.chB];

  [0, 1].forEach((rowIdx) => {
    const rx = sx + rowIdx * (2 * pw + gap);

    s.addText("row " + rowIdx, {
      x: rx, y: sy - 0.45, w: 2 * pw, h: 0.32, fontFace: F.head, fontSize: 12,
      bold: true, color: C.textDim, align: "center", isTextBox: true, margin: 0,
    });
    s.addShape(pres.ShapeType.line, {
      x: rx, y: sy - 0.1, w: 2 * pw, h: 0,
      line: { color: C.line, width: 2 },
    });

    [0, 1].forEach((pixIdx) => {
      const px = rx + pixIdx * pw;
      for (let i = 0; i < 3; i++) {
        const cx = px + i * cw;
        s.addShape(pres.ShapeType.rect, {
          x: cx, y: sy, w: cw, h: 0.72,
          fill: { color: chFill[i] }, line: { color: "FFFFFF", width: 2 },
        });
        s.addText(letters[i], {
          x: cx, y: sy, w: cw, h: 0.72, fontFace: F.body, fontSize: 12,
          color: C.ink, align: "center", valign: "middle", isTextBox: true, margin: 0,
        });
      }
      s.addText("pixel (" + rowIdx + "," + pixIdx + ")", {
        x: px, y: sy + 0.78, w: pw, h: 0.28, fontFace: F.body, fontSize: 11,
        color: C.textDim, align: "center", isTextBox: true, margin: 0,
      });
    });
  });

  const endX = sx + 2 * (2 * pw + gap) - gap + 0.15;
  s.addText("…", { x: endX, y: sy, w: 0.6, h: 0.72, fontFace: F.head,
    fontSize: 22, color: C.textDim, valign: "middle", isTextBox: true, margin: 0 });
  s.addText("rows just keep going, end to end", {
    x: endX + 0.55, y: sy + 0.18, w: 4.2, h: 0.4, fontFace: F.body, fontSize: 12,
    color: C.textDim, valign: "middle", isTextBox: true, margin: 0,
  });

  code(s, "int i = (row * width + col) * 3;", {
    x: M, y: 3.85, w: 11.9, h: 0.62, size: 18, color: C.onDark, fill: C.ink, pad: 12,
  });

  card(s, { x: M, y: 4.72, w: 11.9, h: 1.55 });
  body(s, "“Skip whole rows to get to my row, walk along to my column, " +
          "then times three because each pixel is three bytes.”\n\n" +
          "Then i + 0 is red, i + 1 is green, i + 2 is blue. Get row and col the " +
          "wrong way round here and threads read each other's pixels — it's the " +
          "classic mistake, and you'll see it if it happens.", {
    x: M + 0.3, y: 4.97, w: 11.3, h: 1.2, size: 15, color: C.text,
  });
  s.addNotes(
    "Second of the two lines they're about to type. Same treatment: make it " +
    "familiar now so typing it isn't mysterious.\n\n" +
    "The 'times three' is worth a beat - beginners often forget the picture is " +
    "bytes, not pixels.\n\n" +
    "Mention the row/col swap deliberately. When someone does it in the build " +
    "(someone always does), the notebook says exactly that, and they'll " +
    "remember hearing it."
  );
}

/* ══════════════════════════════════════════════════ 9. the one idea */
{
  const s = slide(C.ink);
  s.addText("The whole idea, in five words", {
    x: M, y: 2.0, w: 11, h: 0.5, fontFace: F.head, fontSize: 15, bold: true,
    color: C.gpu, charSpacing: 2, isTextBox: true, margin: 0,
  });
  s.addText("One thread per\noutput element.", {
    x: M, y: 2.6, w: 11, h: 2.0, fontFace: F.head, fontSize: 52, bold: true,
    color: C.onDark, isTextBox: true, margin: 0, lineSpacingMultiple: 1.1,
  });
  s.addText("One pixel, one thread. Two and a half million of them, all at the same moment.\n" +
            "Hold onto this sentence — we're going to use it three times today.", {
    x: M, y: 4.9, w: 11, h: 1.0, fontFace: F.body, fontSize: 18,
    color: C.onDarkDim, isTextBox: true, margin: 0, lineSpacingMultiple: 1.3,
  });
  s.addNotes(
    "Say it, then make them say it. It is the thread that ties the pixel work " +
    "to the LLM payoff at the end.\n\n" +
    "Three uses: one thread per PIXEL (today's build), one thread per NUMBER in " +
    "a matrix multiply, and that's what a language model is made of.\n\n" +
    "Short slide. Don't linger - go and build something."
  );
}

/* ══════════════════════════════════════════════════ 10. what we're building */
{
  const s = slide();
  title(s, "What we're about to build");

  s.addImage({ path: A("before.jpg"), x: M, y: 1.5, w: 3.85, h: 2.57 });
  s.addImage({ path: A("gray.jpg"), x: 4.74, y: 1.5, w: 3.85, h: 2.57 });
  s.addImage({ path: A("crop_blur.jpg"), x: 9.48, y: 1.5, w: 2.57, h: 2.57 });

  const caps = [
    [M, "the photo", "1920 x 1280 = 2,457,600 pixels"],
    [4.74, "program 1 — greyscale", "each pixel mixes its own colours"],
    [9.48, "program 2 — blur", "each pixel averages its neighbours\n(zoomed in, or you'd never see it)"],
  ];
  caps.forEach(([x, h1, h2]) => {
    s.addText(h1, { x: x, y: 4.2, w: 3.85, h: 0.35, fontFace: F.head, fontSize: 15,
      bold: true, color: C.text, isTextBox: true, margin: 0 });
    s.addText(h2, { x: x, y: 4.55, w: 3.85, h: 0.6, fontFace: F.body, fontSize: 13,
      color: C.textDim, isTextBox: true, margin: 0, lineSpacingMultiple: 1.2 });
  });

  card(s, { x: M, y: 5.25, w: 11.9, h: 1.15 });
  body(s, "Two programs — but the five steps never change between them. " +
          "The only thing we rewrite is what a single thread does once it knows which pixel it owns.", {
    x: M + 0.3, y: 5.5, w: 11.3, h: 0.7, size: 16, color: C.text,
  });
  s.addNotes(
    "Show them the destination before they start typing. It matters - people " +
    "type with more confidence when they know what it's for.\n\n" +
    "The third image is a CROP, say so, otherwise the blur looks weak. At full " +
    "size a 7-pixel blur on a 1920-wide photo is genuinely hard to see on a " +
    "projector.\n\n" +
    "Set the expectation for the build: 'the second program will feel almost " +
    "free, because we only change the middle.'"
  );
}

/* ══════════════════════════════════════════════════ 11-13. the cues */
cueSlide("LAPTOPS OPEN", "Build 1 — greyscale",
  "Notebook section 2. The bottom of the cell is already written — that's the five steps.\n\n" +
  "We write the kernel at the top together. About eight lines.\n\n" +
  "If you lose the thread: open the 🛟 cell underneath, copy it, and you're back with us.",
  "~8 minutes.\n\n" +
  "Type in this order, saying why:\n" +
  "  col  -> 'which column do I own'\n" +
  "  row  -> 'same again, downwards'\n" +
  "  if   -> 'we asked for more threads than pixels; leftovers sit still'\n" +
  "  i    -> 'the flat address, from the slide'\n" +
  "  the weighted sum -> 'and THIS is the only line that's about grey'\n\n" +
  "When you run it, point at the line printing 2,457,600 threads. That number " +
  "is the moment the room gets it.\n\n" +
  "Then show the picture. Let them enjoy it.\n\n" +
  "Do NOT stop for individual typos. Point at the lifebelt cell and keep going."
);

cueSlide("KEEP THEM OPEN", "Build 2 — blur",
  "Notebook section 3. Scroll to the bottom of the cell first: it is identical to last time.\n\n" +
  "Only the kernel changes — walk the square around me, add up the neighbours, divide.\n\n" +
  "Watch for the edges: a corner pixel has fewer neighbours than a middle one.",
  "~10 minutes.\n\n" +
  "Open by scrolling to the bottom of the cell and saying 'look - nothing down " +
  "here changed. Same five steps, same launch.' That's the lesson, not an aside.\n\n" +
  "The two for-loops are the only genuinely new thing. Say 'radius three means " +
  "a seven by seven square'.\n\n" +
  "Dwell on dividing by n rather than 49 - it's the one real gotcha, and if " +
  "someone gets it wrong the check literally says 'the middle is right but the " +
  "edges are dark'.\n\n" +
  "After it runs: point at the BOTTOM row of the figure, the zoomed crop.\n\n" +
  "Then: everyone change BLUR_SIZE to 15 and re-run. Twenty times the work, " +
  "still instant. That lands harder than anything you can say."
);

cueSlide("NOTHING TO TYPE", "How fast was that, really?",
  "Notebook section 4. The same blur, done twice — once as an ordinary loop on the CPU, once on the GPU.\n\n" +
  "Two numbers to watch: how much faster the blur itself was, and how much faster it was once you count the copying.",
  "~5 minutes. Just run it.\n\n" +
  "Get them to read the two speedup numbers out loud before you explain.\n\n" +
  "Then make the point: the blur itself is hundreds of times faster, but " +
  "counting the copying it's far less - because most of the GPU's time went on " +
  "moving bytes, not computing.\n\n" +
  "That's the two-memories slide coming back to bite. And it's the answer to " +
  "'why does everyone care whether a model FITS on the GPU' - the weights get " +
  "loaded on once and left there.\n\n" +
  "Numbers vary by machine. On a T4 expect the CPU around 1-3 seconds and the " +
  "kernel in single-digit milliseconds."
);

/* ══════════════════════════════════════════════════ 14. blur -> matmul */
{
  const s = slide();
  title(s, "Now the payoff: it's the same program");
  body(s, "Multiplying two matrices is the same shape of code you just wrote. " +
          "Only the arithmetic in the middle is different.", { y: 1.3, h: 0.5, size: 16 });

  card(s, { x: M, y: 2.0, w: 5.75, h: 3.5, fill: "FFFFFF" });
  s.addText("your blur", { x: M + 0.3, y: 2.2, w: 4, h: 0.35, fontFace: F.head,
    fontSize: 14, bold: true, color: C.gpuInk, isTextBox: true, margin: 0 });
  code(s, "col = blockIdx.x*blockDim.x + threadIdx.x;\n" +
          "row = blockIdx.y*blockDim.y + threadIdx.y;\n\n" +
          "if (col < w && row < h) {\n\n" +
          "    for (neighbours around me)\n" +
          "        total += pixel value;\n\n" +
          "    out[...] = total / count;\n}", {
    x: M + 0.3, y: 2.6, w: 5.15, h: 2.7, size: 11.5, color: C.text });

  card(s, { x: 7.05, y: 2.0, w: 5.6, h: 3.5, fill: "FFFFFF" });
  s.addText("a matrix multiply", { x: 7.35, y: 2.2, w: 4, h: 0.35, fontFace: F.head,
    fontSize: 14, bold: true, color: C.gpuInk, isTextBox: true, margin: 0 });
  code(s, "col = blockIdx.x*blockDim.x + threadIdx.x;\n" +
          "row = blockIdx.y*blockDim.y + threadIdx.y;\n\n" +
          "if (col < w && row < h) {\n\n" +
          "    for (k across the row/column)\n" +
          "        total += A[..] * B[..];\n\n" +
          "    out[...] = total;\n}", {
    x: 7.35, y: 2.6, w: 5.0, h: 2.7, size: 11.5, color: C.text });

  body(s, "Same “which one am I”. Same bounds check. Same loop that adds things up. " +
          "One thread per output number — for the second time today.", {
    x: M, y: 5.7, w: 11.9, h: 0.8, size: 16, color: C.text, bold: true,
  });
  s.addNotes(
    "Put the two side by side and let them look for a few seconds before you " +
    "say anything. The recognition is the point.\n\n" +
    "This is use #2 of 'one thread per output element'.\n\n" +
    "Don't teach matrix multiplication properly. All they need: each output " +
    "number is a sum of products, and every output number can be worked out " +
    "independently of the others. That's the only property that matters."
  );
}

/* ══════════════════════════════════════════════════ 15. matmul -> LLM */
{
  const s = slide();
  title(s, "And a language model is mostly matrix multiplies");

  const items = [
    ["Turning words into numbers", "a matrix multiply"],
    ["Working out which words matter to each other", "two matrix multiplies"],
    ["The big layers in between", "the largest matrix multiplies of all"],
  ];
  items.forEach((it, i) => {
    const y = 1.7 + i * 1.12;
    card(s, { x: M, y: y, w: 11.9, h: 0.95 });
    dot(s, { x: M + 0.3, y: y + 0.22, d: 0.5, color: C.gpu, label: String(i + 1), size: 14 });
    s.addText(it[0], { x: M + 1.0, y: y, w: 6.6, h: 0.95, fontFace: F.body,
      fontSize: 16, color: C.text, valign: "middle", isTextBox: true, margin: 0 });
    s.addText(it[1], { x: 8.0, y: y, w: 4.3, h: 0.95, fontFace: F.head,
      fontSize: 15, bold: true, color: C.textDim, align: "right",
      valign: "middle", isTextBox: true, margin: 0 });
  });

  card(s, { x: M, y: 5.2, w: 11.9, h: 1.3, fill: "E9FBF1", stroke: "A9E9C6" });
  body(s, "Producing ONE word means billions of these little sums — every one of them " +
          "independent, every one of them a “one thread per output number” job. " +
          "Then it does it all again for the next word.", {
    x: M + 0.35, y: 5.45, w: 11.2, h: 0.9, size: 16, color: C.text,
  });
  s.addNotes(
    "Use #3 of the one idea, and the moment the title of the series pays off.\n\n" +
    "Keep it honest and vague where you should be: you are NOT teaching " +
    "transformers. The claim is only that the expensive parts are matrix " +
    "multiplies, and matrix multiplies are what they just learned to think " +
    "about.\n\n" +
    "'Which words matter to each other' = attention, without the jargon. Use " +
    "the word if the room can take it."
  );
}

/* ══════════════════════════════════════════════════ 16. one word = N blurs */
{
  const s = slide(C.ink);
  title(s, "Put that on the scale of what you just wrote", { color: C.onDark });

  const stats = [
    ["361 million", "additions in the blur\nyou just wrote", C.gpu],
    ["350 billion", "operations for ONE word\nof a large model", C.onDark],
    ["≈ 1,000", "of your blurs,\nfor a single word", C.cue],
  ];
  stats.forEach((st, i) => {
    const x = M + i * 4.0;
    card(s, { x: x, y: 2.1, w: 3.7, h: 2.35, fill: C.panel, stroke: "2A333F" });
    s.addText(st[0], { x: x + 0.3, y: 2.4, w: 3.1, h: 0.75, fontFace: F.head,
      fontSize: 31, bold: true, color: st[2], isTextBox: true, margin: 0 });
    s.addText(st[1], { x: x + 0.3, y: 3.25, w: 3.1, h: 0.95, fontFace: F.body,
      fontSize: 15, color: C.onDarkDim, isTextBox: true, margin: 0,
      lineSpacingMultiple: 1.25 });
  });

  body(s, "The notebook works this out from YOUR machine's actual timing. " +
          "A real system answers in a few hundredths of a second per word — the gap " +
          "is engineering, not magic: faster memory, hardware built for exactly this " +
          "multiply, smaller numbers, and many GPUs at once.", {
    x: M, y: 5.25, w: 11.9, h: 1.3, size: 16, color: C.onDarkDim,
  });
  s.addNotes(
    "Run the last cell of the notebook while this is up - it prints these " +
    "numbers from their own run, which is far better than reading mine.\n\n" +
    "Be honest about the comparison: the blur adds whole numbers, a model " +
    "multiplies decimals. It's for scale, not a benchmark. The notebook says so " +
    "too. Say it out loud - a room that catches you overclaiming stops " +
    "believing the rest.\n\n" +
    "The useful takeaway is the ratio, not the seconds: one word is about a " +
    "thousand times the work you just watched happen instantly."
  );
}

/* ══════════════════════════════════════════════════ 17. the answer */
{
  const s = slide(C.ink);
  s.addText("So — why GPUs, and not CPUs?", {
    x: M, y: 1.6, w: 11, h: 0.7, fontFace: F.head, fontSize: 30, bold: true,
    color: C.onDark, isTextBox: true, margin: 0,
  });
  s.addText("Not because GPUs are mysteriously fast.\n" +
            "Because this job is millions of identical, independent sums —\n" +
            "and that is the one thing a stadium beats four geniuses at.", {
    x: M, y: 2.7, w: 11.6, h: 2.2, fontFace: F.head, fontSize: 27, bold: true,
    color: C.gpu, isTextBox: true, margin: 0, lineSpacingMultiple: 1.35,
  });
  s.addText("You proved it yourself, on a photo, about twenty minutes ago.", {
    x: M, y: 5.3, w: 11, h: 0.6, fontFace: F.body, fontSize: 18,
    color: C.onDarkDim, isTextBox: true, margin: 0,
  });
  s.addNotes(
    "The closing argument. Slow down and let it land.\n\n" +
    "Callback to the stadium is deliberate - it closes the loop opened in the " +
    "first five minutes.\n\n" +
    "Last line matters: they didn't take your word for it, they measured it."
  );
}

/* ══════════════════════════════════════════════════ 18. wrap */
{
  const s = slide();
  title(s, "What you did in the last hour");

  const did = [
    "Ran your own code on a genuinely different processor",
    "Handed data to a machine that couldn't otherwise see it — and got it back",
    "Pointed 2.4 million threads at 2.4 million pixels, exactly one each",
    "Made a real photo change, twice",
    "Measured it against a CPU, and found where the time actually goes",
  ];
  did.forEach((d, i) => {
    const y = 1.55 + i * 0.72;
    dot(s, { x: M, y: y + 0.03, d: 0.42, color: C.gpu, label: "✓", size: 13 });
    s.addText(d, { x: M + 0.65, y: y, w: 11, h: 0.5, fontFace: F.body,
      fontSize: 16, color: C.text, valign: "middle", isTextBox: true, margin: 0 });
  });

  card(s, { x: M, y: 5.35, w: 11.9, h: 1.35 });
  s.addText("If you want to keep going", { x: M + 0.35, y: 5.55, w: 6, h: 0.35,
    fontFace: F.head, fontSize: 15, bold: true, color: C.text, isTextBox: true, margin: 0 });
  body(s, "lab/extras/ in the repo — what happens when you forget the copy back, " +
          "what the bounds check is really protecting you from, and a matrix multiply " +
          "that gets several times faster purely by changing which memory each thread reads.", {
    x: M + 0.35, y: 5.92, w: 11.2, h: 0.8, size: 14,
  });
  s.addNotes(
    "Read the list out. People genuinely underestimate what they just did, and " +
    "hearing it back is the difference between 'I followed a tutorial' and 'I " +
    "wrote GPU code'.\n\n" +
    "Point at extras for the one or two who want more. Don't sell it hard.\n\n" +
    "Then: questions. Common ones - 'do I need an NVIDIA GPU?' (for CUDA yes; " +
    "there are other frameworks), 'is this what PyTorch does?' (yes, underneath " +
    "- it calls kernels like these, mostly written by NVIDIA)."
  );
}

const out = path.join(__dirname, "workshop-2-gpu-llms.pptx");
pres.writeFile({ fileName: out }).then(() => console.log("wrote " + out));
