# Facilitator Guide — Run Your Code on a GPU

For you, not the students. The session is **~30 minutes of slides, then ~30
minutes of you building the code live while they follow along in their own
Colab.**

Audience assumption throughout: **near-beginners with little or no C.** Nobody
is expected to invent anything. They type what you type, and they see a picture
change.

---

## The shape of the hour

| | Time | What |
|---|---|---|
| Slides | ~30 min | why GPUs exist, the five steps, threads, and what we're about to build |
| Live build 1 | ~16 min | all of `main()` + the greyscale kernel, in one file |
| Live build 2 | ~8 min | new file, `main()` given, copy the blur kernel from the slide |
| Run the race | ~5 min | CPU vs GPU, and where the time goes |
| The payoff | ~7 min | blur → matrix multiply → language models |

The notebook has five sections matching the last four rows. Nothing in it is a
puzzle — every code cell is either something you type together or something you
just run.

## The one idea to land

> **One thread per output element.**

Say it in section 1, say it again when the greyscale works, and say it a third
time when you connect to LLMs. Everything else is detail.

If they remember one sentence: **"A GPU is thousands of tiny workers each doing
one simple sum — and a language model is a mountain of those sums."**

---

## The live build

Two cells. **Build 1, `student/main.cu`: `main()` starts empty and every line
of it is typed** — the setup, the five CUDA steps, `return 0` — plus the kernel
body. **Build 2, `student/blur.cu`: `main()` is already written; only the
kernel is typed**, copied whole from its slide. The only things never written
by hand are four small helpers in `lab/gpulab.h` (`loadImage`, `makeImage`,
`saveImage`, `freeImage`) — students still type the calls to them.

Each typed piece has a STEP slide with the exact code on it. Students type from
the slide; you narrate. If someone runs the cell early they get *"Some parts are
still empty — the ones we type together"* with the steps listed, not compiler
output.

### Build 1 — greyscale (~14 min)

Have the five-steps slide in your head; the STEP slides carry the code. In order:

| STEP slide | You type | You say |
|---|---|---|
| device pointers | *(nothing — 30 s)* | "`in_d` is an ordinary variable. Its *value* is an address on the other machine." |
| 1 · cudaMalloc | `Image img = loadImage();` `Image out = makeImage(img.w, img.h);` `unsigned char *in_d, *out_d;` then `cudaMalloc(&in_d, img.bytes);` ×2 | "Photo in, empty picture out, two pointers. Then: the **address of** in_d, so CUDA can write the GPU address into it. Say the & out loud." |
| 2 · cudaMemcpy → | one line | "Where to, where from, how much, which way. Destination **first**." |
| 3 · the launch | `dim3 block`, `dim3 grid`, `<<< >>>`, `checkKernel(...)` | "16×16 is 256. 120 across, 80 down. 2,457,600. `+15 /16` rounds up. The last line waits and asks if it worked." |
| 3 · the kernel | the body | "Which pixel am I, am I on the picture, where does it live — then the grey line." |
| 4 · cudaMemcpy ← | one line, then `saveImage(out, "build/out.ppm");` | "Same call, reversed. Skip it and you get black — no error. Then write the file." |
| 5 · cudaFree | ×2, `freeImage` ×2, `return 0;` | "One free per malloc. Nothing does this for you." Then **run**. |

Expect `✅ Greyscale, and correct`. Then `lab.show()`. Let them look.

### Build 2 — blur (~8 min)

**A new cell, `student/blur.cu`.** Its `main()` is already written — the same
five steps they just typed, with the kernel's name changed to `blurKernel`.
Open it and scroll through `main()` first: *"you typed exactly this twenty
minutes ago."* That is the lesson — the host code is a shell; what the GPU does
lives in the kernel.

Then they **copy the whole `blurKernel` function from the slide** into the
marked spot above `main()`. One slide, one function, nothing else to type.

| You point at | You say |
|---|---|
| `col`, `row`, the `if` | "Same start as greyscale." |
| `int r = 0, g = 0, b = 0; int n = 0;` | "Add up the neighbours, and count how many we found." |
| the two `for` loops | "Walk the square around me. Radius 3 is 7 by 7." |
| `if (nrow >= 0 && nrow < h && ...)` | "A corner pixel has no neighbours above it. Skip those." |
| the three `/ n` lines | "Divide by what we counted, not by 49, or the edges come out dark." |

Run the cell, then `lab.run("blur")`. Expect `✅ Blur ... edges included`.
`lab.show()`, and point at the **bottom row** — the zoomed crop.

Then `BLUR_SIZE` to `15`, re-run. Twenty times the work, same instant.

### Nobody gets stranded

Under each build is a collapsed 🛟 **"Fell behind? The finished version"** cell —
the complete file. Say once, early: *"if you lose the thread, open that, copy the
whole thing over your cell, and you're back with us."* Don't slow down for
individual typos.

The check names the actual mistake, and since the host code is typed now it
distinguishes host from kernel:

| what they see | what it means |
|---|---|
| *A CUDA call BEFORE the launch failed … look at STEP 1 and STEP 2* | wrong `cudaMemcpy` direction, arguments swapped, or a `cudaMalloc` missing |
| *The picture is completely black … check STEP 4* | the copy back is missing |
| *outside the picture … this one is in the kernel* | `row`/`col` swapped, or the `if` missing |
| *the outermost 3 pixels are dark* | divided by 49 instead of `n` |

---

## The slides

**The live deck is Google Slides** (link in the README) — that is the master
copy; edit it there. The repo holds two generated `.pptx` files that feed it:

- `slides/workshop-2-gpu-llms.pptx` — the original 18-slide deck, from which
  the Google Slides deck was imported. Historical now; your edits live in
  Google Slides, not here.
- **`slides/step-slides.pptx`** — 8 slides carrying the code students type,
  in the same grammar as the Workshop 3 deck (green `STEP` kicker, verbatim
  code panel, violet READ IT AS card). **Add these to the Google Slides deck
  with File → Import slides.** Each carries a faint `insert:` tag bottom-right
  saying where it goes; delete the tag after placing.

| # | slide | goes |
|---|---|---|
| 1 | What `in_d` actually is | right after your **Build 1** divider |
| 2 | STEP 1 · cudaMalloc | after 1 |
| 3 | STEP 2 · cudaMemcpy → | after 2 |
| 4 | STEP 3 · the launch | after 3 |
| 5 | STEP 3 · the kernel | after 4 |
| 6 | STEP 4 · cudaMemcpy ← | after 5 |
| 7 | STEP 5 · cudaFree *(checkpoint strip)* | after 6 |
| 8 | Build 2 · the kernel — the whole `blurKernel` function *(checkpoint strip)* | right after your **Build 2** divider |

The code on those slides is pulled verbatim from `lab/solutions/*.cu` when
the file is generated, so the slide and the notebook cannot drift.

**Two text edits to make in your existing divider slides**, since the build
changed shape:

- *Build 1 — greyscale*: replace "We write the kernel at the top together.
  About eight lines." with **"We type every CUDA call and the kernel — each
  has a STEP slide with the exact line. Reading and saving the photo is given."**
- *Build 2 — blur*: replace "Notebook section 3. Scroll to the bottom of the
  cell first: it is identical to last time." with **"New cell, student/blur.cu.
  main() is already written — scroll through it, it's yours from Build 1. Copy
  the kernel from the next slide into the marked spot."**

Running order with the additions: the lecture slides are unchanged and stop at
"What we're about to build"; then the Build 1 divider; then slides 1–7 as you
type; then the Build 2 divider and slide 8. Budget ~40 minutes of slides
including the typing — the STEP slides *are* the build, not extra lecture.

### Regenerating

```
node slides/generate-step-slides.js      # after editing lab/solutions/*.cu
```

The visual conventions, if you edit by hand: dark canvas, **green = STEP kicker
and CUDA tokens**, **violet = READ IT AS**, **amber = the one thing not to miss**,
green strip = checkpoint.

## Pre-flight (do this once, before class)

1. **Make the repo PUBLIC.** Essential — `git clone` inside Colab has no GitHub
   login, so a private repo breaks the one-click flow.
   (Repo → Settings → General → Change visibility → Public.)
2. Check the Colab badge in the README points at your repo.
3. Run the pre-flight script on any CUDA machine (or in Colab):

   ```
   python lab/verify.py
   ```

   It confirms both cells ship with an empty kernel, that running one empty
   gives the friendly message, and that the finished versions compile, run and
   pass their checks. Takes about a minute.
4. **Do the live build yourself once, from the empty cells, at speaking pace.**
   You'll find out whether 8 and 10 minutes are honest for you.
5. Have students open the notebook and switch to **T4 GPU before you start
   talking**, so the slow first GPU allocation is over with by build time.

## Common stumbles

- **"No GPU attached to this notebook"** → Runtime → Change runtime type → T4
  GPU. This is the number one issue; check it first.
- **"Some parts are still empty"** → they typed into the cell but didn't run it.
  `%%writefile` only saves when the cell is executed. Run the code cell, *then*
  the check.
- **"A CUDA call BEFORE the launch failed"** → STEP 1 or 2: a `cudaMemcpy` with
  the wrong direction or swapped arguments, or a missing `cudaMalloc`. The
  message lists all three.
- **Black picture** → STEP 4, the copy back, is missing. The check says so.
- **Crash: "an illegal memory access"** → almost always `row` and `col` swapped
  in `(row * w + col) * 3`, or the bounds check missing.
- **Dark edges on the blur** → divided by 49 instead of `n`. The check says so.
- **Free Colab GPU unavailable at peak times** → rare; have them pair up.

## What was cut, and where it went

`lab/extras/` holds material that didn't earn its place in a 30-minute build:
the silent missing copy-back, dereferencing a device pointer from the CPU, the
bounds-check crash, and a matrix multiply where changing *which* memory each
thread reads makes it several times faster.

They're all runnable and all good — they're just a second session, or homework
for the one student who asks. The notebook's last cell points at the folder.
