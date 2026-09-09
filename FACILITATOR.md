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
| Live build 1 | ~8 min | the greyscale kernel |
| Live build 2 | ~10 min | the blur kernel |
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

Both programs ship with the host code already written and the **kernel body
empty**. You type the kernel; the five steps below it never change. That's
deliberate — the second build should feel like "only the middle changed."

If someone runs a cell before you've typed the kernel, they get
*"The kernel is still empty — that's the part we write together"*, not a wall of
compiler output.

### Build 1 — greyscale (~8 min)

Type it in this order, saying the thing in the right-hand column:

| You type | You say |
|---|---|
| `int col = blockIdx.x * blockDim.x + threadIdx.x;` | "Threads arrive in blocks. This is how one thread works out which column it owns." |
| `int row = blockIdx.y * blockDim.y + threadIdx.y;` | "Same again, downwards. Now this thread knows its pixel." |
| `if (col < w && row < h) {` | "We asked for slightly more threads than pixels. The leftovers have to sit still." |
| `int i = (row * w + col) * 3;` | "The picture is one long line of bytes. Skip whole rows, then along, times three." |
| the three-channel weighted sum | "And that's the only line that's actually about greyscale." |

Then run it. **Point at the launch line printing 2,457,600 threads** — that number
is the moment the room gets it. Show the picture.

### Build 2 — blur (~10 min)

Open the blur cell and point out that the bottom half is *identical*. Then:

| You type | You say |
|---|---|
| the same `col` / `row` / `if` lines | "Copied. Every kernel starts this way." |
| `int r = 0, g = 0, b = 0; int n = 0;` | "We're going to add up the neighbours, and count how many we found." |
| the two `for` loops | "Walk the square around me. Radius 3 means 7 by 7." |
| `if (nrow >= 0 && nrow < h && ...)` | "A corner pixel has no neighbours above it. Skip those." |
| `int i = (nrow * w + ncol) * 3;` | "Same address maths as before — just for the neighbour instead of me." |
| the three `/ n` lines | "Divide by what we counted, not by 49. Otherwise the edges come out dark." |

Run it, show the picture, and point at the **bottom row of the figure** — the
zoomed crop. At full size a 7-pixel blur on a 1920-pixel photo is easy to miss;
zoomed in it's obvious.

Then have them change `BLUR_SIZE` to `15` and re-run. Twenty times the work,
same instant result. That lands harder than anything you can say.

### Nobody gets stranded

Under each program is a collapsed 🛟 **"Fell behind? The finished version"**
cell. Say out loud, once, near the start: *"if you lose the thread, open that,
copy it, and you're back with us."* Then don't slow down for individual typos —
point at the 🛟 cell and keep moving.

If someone's picture comes out wrong, the check under the cell names the actual
mistake (dark edges, swapped colour channels, row and col the wrong way round)
rather than saying "incorrect".

---

## What the slides need to cover

The notebook deliberately explains very little — you're doing that. The 30
minutes before the build should land, in this order:

1. **The hook** — this chip is the reason ChatGPT can answer you.
2. **CPU vs GPU** — a few brilliant mathematicians versus a stadium of students
   each doing one sum. Same total work, wildly different shape.
3. **Two computers, two memories** — the GPU cannot see your data. This is the
   idea that makes `cudaMemcpy` obvious later instead of arbitrary.
4. **The five steps** — allocate, copy over, run, copy back, free. Put them on
   one slide and leave it up during the build.
5. **Threads, blocks, and "which one am I"** — a diagram of a grid of blocks,
   and the `blockIdx * blockDim + threadIdx` line. This is the single line they
   will most need to have seen before typing it.
6. **A picture is a flat array** — `(row * width + col) * 3`, drawn.
7. **What we're building** — the before/after photo, so they know where this ends.

Keep the LLM material for *after* the build, when they have something to connect
it to.

---

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
- **"The kernel is still empty"** → they typed into the cell but didn't run it.
  `%%writefile` only saves when the cell is executed. Run the code cell, *then*
  the one under it.
- **Black picture** → the kernel wrote nothing, or the copy back is missing.
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
