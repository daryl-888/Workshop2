# Workshop 2 — Run Your Code on a GPU

Session 2 of the **From Zero to GPU** series. Last time you built a tool on a
Linux machine. Today you write CUDA that runs on a real GPU — one thread per
pixel, millions at once — measure it against a CPU, and then see that the same
shape of code is what runs an LLM.

Slides: https://docs.google.com/presentation/d/1yJQ0e8BnbxDxrRdlc75TmOKeTtUjmWHaUmNj1lCNkbg/edit?usp=sharing

---

## Start — one click

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/daryl-888/Workshop2/blob/main/blur.ipynb)

1. **Click the badge.** The notebook opens in Google Colab — a free GPU in your
   browser, nothing to install.
2. **Turn the GPU on:** Runtime → Change runtime type → **T4 GPU** → Save.
3. **Run the setup cell**, then work down the notebook one topic at a time.

The setup cell clones this repo for you, so the image and every support file is
already there. No uploads.

> **Facilitators:** the one-click clone needs this repo to be **public** —
> Colab has no GitHub login. See [FACILITATOR.md](FACILITATOR.md).

---

## How the notebook is built

Nine short topics, each one idea. Every topic is the same three steps:

1. **Read** a few paragraphs.
2. **Fill in the blanks** — each marked `/* YOUR CODE: ... */`, one or two lines.
3. **Run the check** — it says whether you got it, and if not, *which* mistake
   you made.

| # | Topic | The idea |
|---|---|---|
| 0 | Two computers in one box | host vs device, `__global__`, `<<< >>>`, launches are async |
| 1 | Which thread am I? | `blockIdx * blockDim + threadIdx` |
| 2 | Two separate memories | `cudaMalloc` / `cudaMemcpy`, and two ways it fails silently |
| 3 | Enough threads, not one too far | ceil-division and the bounds guard |
| 4 | Finding a pixel | 2D grids, `(row * w + col) * 3` |
| 5 | **The blur** | the neighbourhood loop — everything else you already have |
| 6 | The race | your blur on CPU vs GPU, timed, transfers broken out |
| 7 | Where you read beats what you compute | coalesced vs scattered memory access |
| 8 | Why this chip runs ChatGPT | blur → matmul → transformer, using your own measured numbers |

Topics 0–5 are fill-in-the-blank (12 blanks total). Topics 6–8 are read-and-run:
they exist to make the lecture's claims *measured* rather than asserted.

Each topic has a collapsed **"Reveal the answer"** cell, so nobody is stuck for
ten minutes with their hand up.

### Why it is split this way

The program is not one big file edited in one big cell. All the plumbing — PPM
reading and writing, timing, error checking, the CPU reference blur — lives in
[`lab/gpulab.h`](lab/gpulab.h), which students never open. What is left in each
editable cell is only CUDA: short enough to read on a projector and to edit
without scrolling, and short enough that a topic can be *taught at its own cell*.

---

## What's in this folder

| Path | What it is |
|---|---|
| `blur.ipynb` | the notebook — the whole session |
| `lab/gpulab.h` | image I/O, timers, error checks, CPU reference (students ignore this) |
| `lab/labkit.py` | the notebook's helper: builds, runs, checks answers, draws images |
| `lab/solutions/` | answer key for every topic; also what the "Reveal" cells print |
| `lab/demos/` | three deliberately broken programs (used in Topics 2 and 3) |
| `images/sample_1920x1280.ppm` | the input image |
| `blur_solution.cu` | the whole blur in **one standalone file**, for running outside the notebook |
| `matmul/Ch3exercises.cu` | the original PMPP Ch.3 matmul, kept for the slides |
| `FACILITATOR.md` | lecture plan, timing, pre-flight, common stumbles |

`build/` and `student/` are created at runtime and are git-ignored.

---

## The through-line

> **One thread per output element.**

- **Blur** (Topic 5): each output pixel is an average over a neighbourhood.
- **Matrix multiply** (Topic 7): each output entry is a dot product. *Same kernel
  shape*, different arithmetic inside.
- **LLMs** (Topic 8): a transformer is mostly matrix multiplies — the Q/K/V
  projections, Q×Kᵀ, ×V, and the feed-forward layers. One token is billions of
  independent multiply-adds of exactly this form.

That is the answer to "why GPUs and not CPUs": the workload is millions of
identical independent sums, which is the one thing thousands of slow cores beat
a handful of fast ones at.

---

## Run it locally instead (optional)

Any machine with an NVIDIA GPU and the CUDA Toolkit:

```bash
nvcc blur_solution.cu -o blur && ./blur     # standalone, writes output.ppm
```

Or run a topic exactly the way the notebook does, from the repo root:

```bash
nvcc -O2 -I. lab/solutions/t6_race.cu -o build/t6 && ./build/t6
```

The notebook's setup cell also works locally — launch Jupyter from the repo root
and it uses the checkout you already have instead of cloning.

## A note on error checking

Real CUDA code checks the result of every call. Rather than strip that out for
readability, it is hidden behind two helpers in `lab/gpulab.h`: `CUDA_CHECK(...)`
around a call, and `checkKernel("name")` after a launch. One line each — and it
is why a mistake in this workshop produces a *located message* instead of a
silently black image. Topic 3's demo shows what the alternative looks like.

## License
MIT.
