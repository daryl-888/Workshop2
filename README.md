# Workshop 2 — Run Your Code on a GPU (CUDA Image Blur)

Session 2 of the **From Zero to GPU** series. Last time you built a tool on a
Linux machine. Today you finish a **CUDA program that blurs an image on a real
GPU** — one thread per pixel, thousands running at once — and then we connect
that exact idea to how GPUs power LLMs like ChatGPT.

This session is **lecture-heavy**: most of the hour is the talk (why GPUs are
built for AI), with a short, satisfying fill-in-the-blank lab in the middle.

Google slides: https://docs.google.com/presentation/d/1yJQ0e8BnbxDxrRdlc75TmOKeTtUjmWHaUmNj1lCNkbg/edit?usp=sharing

---

## Start the lab — one click

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/daryl-888/Workshop2/blob/main/blur.ipynb)

1. **Click the badge above.** The notebook opens in Google Colab (free GPU in
   your browser — nothing to install).
2. Turn on the GPU: **Runtime → Change runtime type → T4 GPU → Save.**
3. **Run each cell top to bottom** (Shift+Enter). The first cell downloads this
   whole repo for you — the image and all the files. No uploads, no setup.
4. **Fill in the 9 blanks** in the CUDA code cell, then run to compile and see
   your blurred image appear.

That's the whole flow. The image is already there because the notebook clones
this repo automatically.

> **Facilitators:** this one-click clone flow needs the repo to be **public** so
> students can download it without a GitHub login. See `FACILITATOR.md`.

---

## The lab: fill in the blanks

You're completing **`blur_template.cu`** (embedded in the notebook so you edit it
right there). Each blank is marked `/* TODO n: ... */` and the comment above it
tells you what to compute. The program won't compile until all 9 are filled —
that's intentional.

### Hints (concepts, not answers)

<details>
<summary>Show hints</summary>

- **TODO 1 & 2 — which pixel is this thread?** A thread's global position is
  `blockIdx * blockDim + threadIdx`. Do it for `.x` (column) and `.y` (row).
- **TODO 3 — stay in bounds.** The grid is rounded up, so some threads are past
  the edge. Only run if the column is `< w` **and** the row is `< h`.
- **TODO 4 — find a pixel in memory.** The image is one flat array, row-major,
  3 bytes (R,G,B) per pixel. Pixel `(curRow, curCol)` starts at
  `(curRow * w + curCol) * 3`.
- **TODO 5a/b/c — average.** You summed `rVal/gVal/bVal` over `pixels`
  neighbours. Divide, and cast to `unsigned char` (use a `float` divide so you
  don't lose precision).
- **TODO 6 & 9 — copy direction.** CPU→GPU is `cudaMemcpyHostToDevice`;
  GPU→CPU is `cudaMemcpyDeviceToHost`.
- **TODO 7 — enough blocks.** Blocks are 16 wide. To cover `width` pixels and
  round up, use `(width + 15) / 16` (and the same idea for height).
- **TODO 8 — launch.** Between `<<< >>>` go your grid then your block:
  `dimGrid, dimBlock`.

Full answers live in **`blur_solution.cu`** — peek only if you're truly stuck.

</details>

---

## What's in this folder

- `blur.ipynb` — the Colab notebook you run (clones the repo, compiles, shows the result)
- `blur_template.cu` — the fill-in-the-blank CUDA program (9 blanks)
- `blur_solution.cu` — the completed, cleaned-up version (answer key)
- `images/sample_1920x1280.ppm` — the input image
- `slides/` — the lecture deck: **why GPUs power LLMs** (matrix mult → attention)
- `FACILITATOR.md` — the lecture plan, timing, and the blur→matmul→LLM through-line
- `matmul/Ch3exercises.cu` — the matrix-multiply kernel the lecture builds on

## A note on error checking

Real CUDA code checks the result of every `cudaMalloc`/`cudaMemcpy`. We left
those checks **out** here on purpose — they triple the line count and bury the
idea while you're learning. Once the blur works, `FACILITATOR.md` shows the tidy
one-macro way to add them back.

## Run it locally instead (optional)

Any machine with an NVIDIA GPU + CUDA Toolkit, from the repo root:

```
nvcc blur_solution.cu -o blur
./blur        # reads images/sample_1920x1280.ppm, writes output.ppm
```

## License

MIT.
