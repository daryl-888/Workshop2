# Facilitator Guide — Workshop 2: Run Your Code on a GPU

For you, the person running the session. Students don't need this file.

## Format: the notebook *is* the lecture

This session is not "a talk with a lab in the middle". The notebook is the spine:
you teach each topic **at its cell**, students fill in two or three lines, the
check confirms it, and you move on. Every claim you make in the talk has a cell
below it that demonstrates the claim.

Nine topics, ~45 minutes hands-on with talk interleaved. Each is one idea and
one screen — you can project the cell you are teaching without scrolling.

## The one idea to land: "one thread per output element"

The same idea at three scales. Teach it as a single through-line and the LLM
payoff lands on its own:

1. **Blur (Topic 5).** Each output pixel is the average of its neighbourhood.
   Every pixel is independent, so you assign **one GPU thread per pixel** and do
   millions at once. That's the whole kernel.

2. **Matrix multiply (Topic 7).** Zoom out one step: instead of "average a
   neighbourhood", each output element is a **dot product**. Still independent
   per element, so again: one thread per output element. Same launch pattern,
   same index math they just used. Show the blur and the matmul side by side —
   the shape is identical.

3. **LLMs (Topic 8).** A transformer is *mostly* matrix multiplies: token
   embedding and the Q/K/V projections; attention scores Q×Kᵀ; softmax then ×V;
   and the feed-forward layers, the biggest of all. One token is billions of
   multiply-adds, all of the "one thread per output element" form.

If they remember one sentence: **"A GPU is thousands of tiny workers each doing
one simple sum — and an LLM is a mountain of those sums."**

## What is new in this version, and why

The lab used to be one 130-line file with nine blanks scattered through it. Three
things were wrong with that, and each fix has a topic behind it:

- **You could not teach a topic at a cell.** Host/device, indexing, memory, and
  grid sizing were interleaved with PPM parsing and `main`. Now the plumbing is
  in `lab/gpulab.h` and each editable cell is only the CUDA for one idea.
- **Feedback was all-or-nothing.** Nothing compiled until all nine blanks were
  right. Now every topic compiles, runs and checks on its own, so a student gets
  five wins before the blur instead of zero.
- **Heterogeneity was asserted, never shown.** There was no CPU baseline, no
  timing, and no demonstration of what separate memory actually costs. Topics 2,
  3 and 6 now *show* it: the silent missing copy-back, the CPU dying on a device
  pointer, the out-of-bounds write, and a measured race.

## The three moments worth slowing down for

1. **Topic 0, the output order.** `[CPU] launch returned instantly` prints
   *before* the GPU's lines. Launching is asynchronous. Almost every confusing
   CUDA error later comes from this. Ask the room why the CPU line came first.

2. **Topic 2's `no_copyback` demo.** No crash, no warning — just the old answer
   sitting there looking plausible. This is the failure mode they will actually
   hit. Let it land before you move on.

3. **Topic 6, the two speedup numbers.** The kernel is ~1000× faster than one
   CPU core; end-to-end it is far less, and most of the GPU's time was spent
   *moving bytes*. That gap is the entire cost of being a guest processor. It is
   also the setup for "this is why model weights live on the GPU permanently" —
   the best bridge you have into Topic 8.

Exact numbers vary by machine. On a T4 expect the CPU blur around 1–3 s and the
kernel in single-digit milliseconds. **Run it yourself the morning of, and put
your own numbers on a slide** — a measured number beats a claimed one.

## Rough timing (60 minutes)

| Segment | Time |
|---|---|
| Hook: "this chip runs ChatGPT" + recap of Workshop 1 | 4 min |
| Topic 0–1: two computers, and which thread am I | 8 min |
| Topic 2–3: separate memory, grid sizing (incl. the three demos) | 10 min |
| Topic 4: 2D indexing, greyscale — first image on screen | 6 min |
| **Topic 5: the blur** | 12 min |
| Topic 6: the race, CPU vs GPU | 6 min |
| Topic 7: coalescing | 6 min |
| Topic 8: blur → matmul → LLM, wrap, Q&A | 8 min |

**If you are running short,** cut Topic 7 (coalescing) — it is the most
self-contained. Do not cut Topic 6; the measured speedup is what makes Topic 8
land. Topics 0–5 are the spine and should not be skipped.

**If you have 90 minutes,** have them raise `BLUR_SIZE` to 15 and 31 after
Topic 5 (20× the work, same wall clock), and talk through `lab/gpulab.h`.

## Colab pre-flight (do once before class)

1. **Make the repo PUBLIC.** Essential — `git clone` inside Colab has no GitHub
   login, so a private repo breaks the one-click flow.
   (Repo → Settings → General → Change visibility → Public.)
2. Check the badge URL matches your repo:
   `colab.research.google.com/github/<user>/<repo>/blob/main/blur.ipynb`.
3. Open the notebook yourself, set **Runtime → T4 GPU**, and run it end to end.
   To check everything still builds without doing that by hand, run the
   pre-flight script from the repo root (in Colab, or on any CUDA machine):

   ```
   python lab/verify.py
   ```

   It confirms every template still has its blanks, that the blanks really do
   block compilation, that the intended answers compile and pass their checks,
   and that the read-and-run topics and demos work. Takes about a minute.
   If you edit the notebook's code cells, edit `lab/make_notebook.py` and
   regenerate — then re-run `verify.py`.
4. Have students click the badge and switch to GPU **before** you start talking,
   so the slow first GPU allocation is already done.
5. Colab's left sidebar shows the topic outline (the notebook sets
   `toc_visible`). Use it to jump between topics while presenting.

## Common stumbles & quick fixes

- **"No GPU attached to this notebook"** from the setup cell → Runtime → Change
  runtime type → T4 GPU, then re-run it. This is the #1 issue; check it first.
- **"You still have N blanks to fill in"** → they edited the cell but did not
  re-run it. `%%writefile` only saves when the cell is executed. Re-run the
  code cell, *then* the check cell.
- **A check fails with a specific hint** → read the hint aloud; it names the
  actual mistake (wrong copy direction, divided by 49 instead of the count,
  row/col swapped, channels swapped). That is the whole point of it.
- **"CRASHED WHILE RUNNING: an illegal memory access"** in Topic 4 or 5 → almost
  always `row` and `col` swapped in the flat index, or a broken bounds test.
- **Free Colab GPU unavailable at peak times** → rare; have students pair up on
  one notebook.
- **A student is stuck and the room is moving** → point them at the collapsed
  "Reveal the answer" cell under the topic. Better they read the answer and stay
  with the class than fall two topics behind.

## Slides

The deck lives in Google Slides (link at the top of the README). There is no
`slides/` folder in this repo — earlier versions of these docs referred to one
that never existed.

Worth putting on slides, since the notebook cannot: the **CPU vs GPU** analogy
(a few brilliant mathematicians vs a stadium of students each doing one sum),
and **your own measured numbers** from Topic 6 and Topic 7.

## If you want to extend it

The natural Topic 9 is **tiling / shared memory**: cooperatively loading a patch
into a block's fast shared memory so neighbouring threads stop re-reading the
same values from slow memory. It is the biggest remaining win in both the blur
and the matmul, and it explains why CUDA groups threads into blocks at all —
which Topic 1 raises and deliberately leaves hanging.
