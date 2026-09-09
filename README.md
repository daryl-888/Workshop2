# Workshop 2 — Run Your Code on a GPU

Session 2 of the **From Zero to GPU** series. You write a program that runs on a
real GPU, changes a photo using 2.4 million threads at once, and then see why
that same shape of code is what runs a language model.

Slides: [`slides/workshop-2-gpu-llms.pptx`](slides/workshop-2-gpu-llms.pptx) —
18 slides with speaker notes, importable into Google Slides via
**File → Import slides**.
([the older deck](https://docs.google.com/presentation/d/1yJQ0e8BnbxDxrRdlc75TmOKeTtUjmWHaUmNj1lCNkbg/edit?usp=sharing))

---

## Start — one click

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/daryl-888/Workshop2/blob/main/blur.ipynb)

1. **Click the badge.** The notebook opens in Google Colab — a free GPU in your
   browser, nothing to install.
2. **Turn the GPU on:** Runtime → Change runtime type → **T4 GPU** → Save.
3. **Run the setup cell**, then follow along.

The setup cell downloads this repo for you, so the photo and the support files
are already there. No uploads.

> **Facilitators:** the one-click flow needs this repo to be **public** — Colab
> has no GitHub login. See [FACILITATOR.md](FACILITATOR.md).

---

## The session

Roughly **30 minutes of slides, then 30 minutes of live coding** — the
facilitator builds each program while everyone follows along in their own copy.
Nothing is a puzzle; every cell is either typed together or just run.

| § | What | You do |
|---|---|---|
| 1 | Two computers in one box | read — CPU vs GPU, separate memory, the five steps |
| 2 | **Greyscale** | write the kernel together; see the picture change |
| 3 | **Blur** | same program, new maths in the middle |
| 4 | CPU vs GPU, timed | run it; see where the time actually goes |
| 5 | What this has to do with ChatGPT | blur → matrix multiply → language models |

Both programs ship with the **host code already written and the kernel body
empty**. That's the point: the five steps never change, so the second build
feels like "only the middle is different." Under each is a collapsed
🛟 **finished version** cell, so anyone who falls behind can catch up in one
click.

If a picture comes out wrong, the check underneath names the actual mistake —
dark edges, swapped colour channels, row and column the wrong way round — rather
than printing forty lines of compiler output.

---

## What's in this folder

| Path | What it is |
|---|---|
| `blur.ipynb` | the notebook — the live-coded half of the session |
| `slides/workshop-2-gpu-llms.pptx` | the deck — the first 30 minutes, with speaker notes |
| `slides/generate-slides.js` | generates the deck. Edit this, not the `.pptx` |
| `slides/make_assets.py` | renders the deck's photos from the workshop's own image |
| `lab/gpulab.h` | image loading/saving, timers, error checks (nobody edits this) |
| `lab/labkit.py` | builds and runs each program, checks the result, draws the pictures |
| `lab/solutions/` | the finished versions; also what the 🛟 cells print |
| `lab/extras/` | material cut from the session — see below |
| `lab/make_notebook.py` | generates `blur.ipynb`. Edit this, not the JSON |
| `lab/verify.py` | facilitator pre-flight: proves everything still builds and runs |
| `images/sample_1920x1280.ppm` | the photo |
| `blur_solution.cu` | the blur as one standalone file, for running outside the notebook |
| `matmul/Ch3exercises.cu` | the original PMPP Ch.3 matrix multiply, kept for the slides |

`build/` and `student/` are created at runtime and git-ignored.

### `lab/extras/`

Runnable, tested, and deliberately not in the session — they made a 30-minute
build feel like a course:

- **`demos/d_no_copyback.cu`** — forget the copy back and you get the old answer
  with no error at all
- **`demos/d_host_reads_device.cu`** — the CPU follows a GPU pointer and dies
- **`demos/d_no_guard.cu`** — what the bounds check is really protecting you from
- **`t7_matmul.cu`** — the same matrix multiply twice, where changing *which*
  memory each thread reads makes it several times faster
- **`t0`–`t3`** — standalone exercises on host/device, thread indexing, memory
  transfer and grid sizing

Good for a follow-up session, or for the student who finishes early. Build any
of them from the repo root with `nvcc -O2 -I. lab/extras/<file>.cu -o build/x`.

---

## The through-line

> **One thread per output element.**

- **Blur**: each output pixel is a sum over its neighbours.
- **Matrix multiply**: each output number is a sum of products. Same shape of
  program, different arithmetic in the middle.
- **Language models**: almost everything expensive inside one is a matrix
  multiply. One word means billions of these independent little sums.

That's the answer to "why GPUs and not CPUs" — the work is millions of identical
independent sums, which is the one thing thousands of slow cores beat a handful
of fast ones at.

---

## Run it locally instead (optional)

Any machine with an NVIDIA GPU and the CUDA Toolkit:

```bash
nvcc blur_solution.cu -o blur && ./blur     # standalone, writes output.ppm
```

Or run a program the way the notebook does, from the repo root:

```bash
nvcc -O2 -I. lab/solutions/race.cu -o build/race && ./build/race
```

The notebook's setup cell works locally too — launch Jupyter from the repo root
and it uses the checkout you already have instead of downloading one.

## A note on error checking

The student-facing programs call `cudaMalloc` and `cudaMemcpy` bare, because
wrapping every one in a check triples the line count and buries the shape while
you're still learning it. The one check that *is* there is `checkKernel()` after
each launch — that's the failure students actually hit, and without it a broken
kernel writes a silently black picture and tells you nothing.

## License
MIT.
