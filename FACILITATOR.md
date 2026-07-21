# Facilitator Guide — Workshop 2: Run Your Code on a GPU

For you, the person running the session. Covers the lecture plan, the core
through-line to teach, timing, Colab logistics, and common stumbles. Students
don't need this file.

## Format: lecture-heavy, short lab

Workshop 1 was hands-on the whole hour. This one flips: it's mostly **lecture**
(why GPUs are the engine of modern AI), wrapped around a short, high-payoff
**fill-in-the-blank lab** (blur an image on a real GPU in Colab). The lab exists
to make the lecture concrete — students *feel* "one thread per output element"
in their fingers before you scale that idea up to LLMs.

## The one idea to land: "one thread per output element"

Everything in this workshop is the same idea at three scales. Teach it as a
single through-line and the LLM payoff lands naturally:

1. **Blur (what they code today).** Each output pixel = the average of its
   neighbourhood. Every pixel is independent, so you assign **one GPU thread per
   pixel** and compute millions at once. That's the whole kernel.

2. **Matrix multiply (`matmul/Ch3exercises.cu`).** Zoom out one step: instead of
   "average a neighbourhood," each output element is a **dot product** — a sum of
   products of a row and a column. Still independent per element, so again: **one
   thread per output element.** Same launch pattern, same indexing math
   (`row*width + col`) they just used in the blur. Show both kernels side by
   side; the shape is identical.

3. **LLMs (the punchline).** A transformer is *mostly* matrix multiplies:
   - Turning tokens into vectors, and the Q/K/V projections — matmuls.
   - Attention scores = Q times K-transpose — a matmul. Softmax, then times V —
     another matmul.
   - The feed-forward layers — the biggest matmuls of all.
   A single response from an LLM is **billions of these multiply-adds**, all of
   the "one thread per output element" form. The GPU does them by the thousand
   simultaneously. That is *why* GPUs, not CPUs, run AI.

If students remember one sentence, make it: **"A GPU is thousands of tiny
workers each doing one simple sum — and an LLM is just a mountain of those
sums."**

## Two supporting points (in the slides)

- **CPU vs GPU.** A CPU has a few very fast cores (a few brilliant
  mathematicians); a GPU has thousands of simple cores (a stadium of students
  each doing one arithmetic problem). For "the same small math a million times,"
  the stadium wins overwhelmingly.
- **Coalesced memory** (from the Ch3 notes). Threads should read *neighbouring*
  memory addresses so the hardware can fetch them in one go. It's why the column
  matmul beats the row matmul, and it's a big part of why GPU code is fast. Keep
  this light — one slide, one analogy (grabbing a whole row of items in one
  reach vs walking back and forth).

## Rough timing (60 minutes)

| Segment | Time |
|---|---|
| Hook: "this chip runs ChatGPT" + recap of Workshop 1 | 5 min |
| Lecture: CPU vs GPU, data parallelism | 8 min |
| Lecture: blur = one thread per pixel (show the kernel) | 7 min |
| **Lab: fill in the blanks in Colab, see the blur** | 18 min |
| Lecture: blur -> matrix multiply (show both kernels) | 8 min |
| Lecture: matmul -> attention/FFN -> LLMs | 10 min |
| By the numbers + wrap / Q&A | 4 min |

If the lab runs long, cut the coalesced-memory slide, not the LLM payoff.

## Colab pre-flight (do once before class)

The student flow is one click: they open `blur.ipynb` in Colab from the "Open in
Colab" badge in the README, and the notebook's first cell **clones this repo**
(image + files) automatically. No uploads.

1. **Make the repo PUBLIC.** This is essential — `git clone` inside Colab has no
   GitHub login, so a private repo can't be downloaded and the one-click flow
   breaks. (Repo → Settings → General → Change visibility → Public.)
2. Confirm the badge URL matches your repo. It points to
   `colab.research.google.com/github/<user>/<repo>/blob/main/blur.ipynb`.
3. Open the notebook yourself, set **Runtime → T4 GPU**, and run it end to end.
   To sanity-check the *solution* compiles, temporarily paste `blur_solution.cu`
   into the `%%writefile` cell (or run `!nvcc blur_solution.cu -o blur && ./blur`
   after the clone cell) and confirm the before/after shows.
4. Put the "Open in Colab" badge + "switch to T4 GPU first" on a slide.
5. Have students click the badge and switch to GPU **before** the lecture starts,
   so the slow first GPU allocation is done by lab time.

## Common stumbles & quick fixes

- **"nvcc: command not found" or CUDA errors on launch** → GPU runtime isn't on.
  Runtime → Change runtime type → T4 GPU. This is the #1 issue; check it first.
- **Compile error pointing at a `/* TODO */` line** → that blank is empty or
  wrong. The message names the line. Good — it means the "must fill all blanks"
  design is working.
- **Output image looks identical / wrong colours** → usually TODO 4 (pixel
  index) or TODO 5 (the average). Re-derive `(row * w + col) * 3`.
- **Forgot to upload the image** → the run prints "Could not open
  sample_1920x1280.ppm". Re-run the upload cell.
- **Free Colab GPU unavailable at peak times** → rare, but have students pair up
  on one notebook as a fallback, or use CPU to at least compile (it won't run the
  kernel without a GPU).

## Adding error checks back (optional, post-lab)

We stripped the per-call error handling so the program stays readable. The tidy
way to bring it back is one macro:

```c
#define CUDA_CHECK(call)                                                     \
  do { cudaError_t _e = (call);                                              \
       if (_e != cudaSuccess) {                                             \
         printf("CUDA error %s at %s:%d\n", cudaGetErrorString(_e),          \
                __FILE__, __LINE__); exit(EXIT_FAILURE); } } while (0)

// then wrap calls:  CUDA_CHECK(cudaMalloc((void**)&in_d, size));
```

One line per call instead of a five-line `if` block — same safety, none of the
clutter that made the original hard to read. Good "here's how the pros do it"
footnote once the blur works.

## Slides

`slides/workshop-2-gpu-llms.pptx` — the lecture deck, built around the
through-line above. Facilitator notes are in each slide's speaker notes.
Regenerate from `slides/generate-slides.js` after edits.
