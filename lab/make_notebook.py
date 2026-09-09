# -*- coding: utf-8 -*-
"""Generates blur.ipynb. Edit this, not the JSON, then re-run:  python lab/make_notebook.py"""
import json, os

cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": text.strip("\n").splitlines(keepends=True)})


def code(text, metadata=None):
    cells.append({"cell_type": "code", "metadata": metadata or {},
                  "execution_count": None, "outputs": [],
                  "source": text.strip("\n").splitlines(keepends=True)})


def catchup(name, label):
    """Colab form cell — collapses to one title bar until clicked."""
    code('#@title 🛟 Fell behind? The finished ' + label + ' { display-mode: "form" }\n'
         'lab.solution("' + name + '")',
         {"cellView": "form"})


# ═══════════════════════════════════════════════════════════════ intro
md("""
# Run Your Code on a GPU

We're going to write a program that runs on a **GPU** — the same kind of chip
that runs ChatGPT — and watch it change a photo using **2.4 million threads at
once**.

### How this works

I'll build the code live and you follow along in your own copy. Two programs:

1. **Greyscale** — the whole shape of a CUDA program, on the simplest possible job.
2. **Blur** — the same program, with more interesting maths inside.

Then we'll race it against a CPU and see what that has to do with ChatGPT.

**If you fall behind, don't panic.** Under each program there's a
🛟 **finished version** cell — click it, copy the code, and you're caught up.
Nothing later depends on you having typed it yourself.

---

### Two things before we start

1. **Turn the GPU on:** Runtime → Change runtime type → **T4 GPU** → Save.
2. **Run the grey cell below** (hover over it and press ▶, or Shift+Enter).
""")

code('''#@title ▶ Run me first — sets everything up { display-mode: "form" }
import os, sys, subprocess

REPO = "/content/Workshop2"
if not os.path.isdir(REPO):
    if os.path.isdir("lab") and os.path.isdir("images"):
        REPO = os.getcwd()                       # already inside the repo (running locally)
    else:
        subprocess.run(["git", "clone", "--depth", "1", "--quiet",
                        "https://github.com/daryl-888/Workshop2.git", REPO])

if not os.path.isdir(REPO):
    raise SystemExit("Couldn't download the workshop. Ask the facilitator to make "
                     "the repo PUBLIC (Settings -> General -> Change visibility).")

os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "lab"))
import labkit as lab
lab.setup()''', {"cellView": "form"})

# ══════════════════════════════════════════════════════ part 1: the idea
md("""
---
# 1 · Two computers in one box

Your machine has two very different processors in it, and they're good at
opposite things.

|  | **CPU** | **GPU** |
|---|---|---|
| how many workers | a handful | thousands |
| how fast is one | very | not very |
| best at | anything, one job after another | the *same* small job, a million times |
| memory | your RAM | **its own, separate RAM** |

That last row is the one that catches people out. **The GPU can't see your
data.** You have to hand it over, and ask for the answer back.

So every CUDA program does the same five things:

1. ask the GPU for some memory
2. copy your data into it
3. run your code there — thousands of copies at once
4. copy the answer back
5. give the memory back

A function that runs on the GPU is called a **kernel**. And the one idea behind
all of this:

> ### One thread per output element.
> One pixel, one thread. Two and a half million of them, at the same moment.
""")

# ══════════════════════════════════════════════════ part 2: greyscale
md("""
---
# 2 · First program: greyscale

The simplest possible job, so we can concentrate on the shape rather than the
maths: turn a colour photo grey. Each pixel becomes a mix of its own red, green
and blue — it never needs to look at any other pixel.

**The bottom of the cell is already written** — that's the five steps, and it
won't change all session. **We write the kernel at the top together.**

Three things every kernel needs:

- **Which pixel am I?** `blockIdx.x * blockDim.x + threadIdx.x`. Threads arrive
  in blocks, so a thread works out its real position from which block it's in
  and where it sits inside that block. Once for across (`x`), once for down (`y`).
- **Am I even on the picture?** We ask for slightly more threads than pixels, so
  the leftovers have to sit still.
- **Where is my pixel?** The picture is one long line of bytes, three per pixel:
  `(row * width + col) * 3`.
""")

code('''%%writefile student/gray.cu
#include "lab/gpulab.h"

// ---------------------------------------------------------------
//  THE KERNEL — this is the bit we write together.
//  It runs once per thread. Every thread runs it at the same time,
//  on a different pixel.
// ---------------------------------------------------------------
__global__ void grayKernel(unsigned char* out, unsigned char* in, int w, int h) {

    /* YOUR CODE: the kernel — we type this in live, about 8 lines */

}

// ---------------------------------------------------------------
//  THE HOST CODE — the five steps. Read along, we don't type this.
// ---------------------------------------------------------------
int main() {
    Image img = loadImage();                  // reading a .ppm lives in lab/gpulab.h
    Image out = makeImage(img.w, img.h);

    unsigned char *in_d, *out_d;

    // 1. Ask the GPU for its own memory. It can't see ours.
    cudaMalloc(&in_d,  img.bytes);
    cudaMalloc(&out_d, img.bytes);

    // 2. Ship the photo across: CPU -> GPU.
    cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);

    // 3. Launch one thread per pixel, in 16x16 tiles.
    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);
    printf("launching %d threads for %d pixels\\n",
           grid.x * grid.y * block.x * block.y, img.w * img.h);

    grayKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("grayKernel");                // did it actually work?

    // 4. Bring the answer home: GPU -> CPU. Skip this and nothing changes.
    cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost);
    saveImage(out, "build/gray.ppm");

    // 5. Give the memory back.
    cudaFree(in_d);
    cudaFree(out_d);
    freeImage(img);
    freeImage(out);
    return 0;
}''')

md("""
Now compile and run it. `nvcc` is the CUDA compiler — it splits the file in two,
sending the kernel to the GPU and everything else to the CPU.
""")

code('lab.run("gray")')
catchup("gray", "greyscale program")

code('lab.show("gray")')

md("""
### What just happened

Two and a half million threads each did about five instructions and stopped.
Nobody wrote a loop over the pixels — we just said *how many* copies we wanted.

That's the whole trick, and it's why the chip is built the way it is. If every
thread runs the same instruction, you don't need thousands of separate control
units. Strip those out, spend the space on arithmetic instead, and you get a
processor with thousands of tiny workers.
""")

# ═════════════════════════════════════════════════════ part 3: the blur
md("""
---
# 3 · Second program: blur

Now something that actually looks like image processing. A blur replaces each
pixel with the **average of the pixels around it** — for radius 3, the 7×7
square centred on it.

**Watch what changes.** The five steps at the bottom: identical. The launch:
identical. The "which pixel am I" lines: identical. The *only* difference is
what one thread does once it knows where it is.

One wrinkle worth calling out: a pixel in the corner has no neighbours above or
to its left. So we check each neighbour before using it, count how many we
actually found, and divide by **that** — not by 49. Divide by 49 and the edges
of the picture come out dark.
""")

code('''%%writefile student/blur.cu
#include "lab/gpulab.h"

#define BLUR_SIZE 3     // radius -> a 7x7 box around each pixel

// ---------------------------------------------------------------
//  THE KERNEL — the only thing that changes from greyscale.
// ---------------------------------------------------------------
__global__ void blurKernel(unsigned char* out, unsigned char* in, int w, int h) {

    /* YOUR CODE: the blur — same start as greyscale, then the neighbourhood */

}

// ---------------------------------------------------------------
//  THE HOST CODE — identical to the last program. Copied, not rewritten.
// ---------------------------------------------------------------
int main() {
    Image img = loadImage();
    Image out = makeImage(img.w, img.h);

    unsigned char *in_d, *out_d;
    cudaMalloc(&in_d,  img.bytes);
    cudaMalloc(&out_d, img.bytes);
    cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);

    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);

    blurKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("blurKernel");

    cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost);
    saveImage(out, "build/blur.ppm");

    printf("radius %d -> each thread averaged up to %d pixels\\n",
           BLUR_SIZE, (2 * BLUR_SIZE + 1) * (2 * BLUR_SIZE + 1));

    cudaFree(in_d);
    cudaFree(out_d);
    freeImage(img);
    freeImage(out);
    return 0;
}''')

code('lab.run("blur")')
catchup("blur", "blur program")

code('lab.show("blur")')

md("""
### 🎉 You just wrote a GPU program

Look at the bottom row — that's the zoomed-in crop, where the softening is
obvious. (On the full photo it's real but easy to miss; a 7-pixel blur on a
1920-pixel-wide picture gets subtle once it's shrunk to fit a screen.)

**Try this:** go back to the code cell, change `#define BLUR_SIZE 3` to `15`,
then re-run that cell and the two under it. Each thread is now averaging 961
pixels instead of 49 — twenty times the work — and it will still finish
instantly. Try `31` if you like.
""")

# ═════════════════════════════════════════════════════ part 4: the race
md("""
---
# 4 · How fast was that, really?

The same blur, done both ways: once as an ordinary loop on the CPU, once on the
GPU. Nothing to write — just run it and look at where the time goes.
""")

code('lab.run("race")')

md("""
### Two numbers, and the gap between them

**The blur itself is hundreds of times faster than a CPU core.** Not because a
GPU core is fast — one GPU core is *slower* than a CPU core. Because there are
thousands of them, and this job splits into millions of identical independent
pieces.

**But counting the copying, it's much less impressive** — most of the GPU's time
went on moving bytes, not computing. That's the price of the GPU being a
separate machine with its own memory.

It's also the answer to something you may have wondered about: *why do people
care so much whether a model "fits" on a GPU?* Because the weights get loaded on
once and left there. Shipping them across for every single word would be
hopeless.
""")

# ══════════════════════════════════════════════════════ part 5: the payoff
md("""
---
# 5 · What this has to do with ChatGPT

Follow the shape.

**Your blur.** Each output pixel is a sum over its neighbours. One thread per
pixel.

**Multiplying two matrices.** Each output number is a sum of products of a row
and a column. One thread per number. *The same shape of program* — the "which
one am I", the bounds check, the loop that adds things up. Only the arithmetic
in the middle is different.

**A language model.** Almost everything expensive inside one is a matrix
multiply: turning words into numbers, the attention step that works out which
words matter to each other, and the big layers in between. Producing **one word**
means billions of these little sums — each one an independent "one thread per
output number" job. Then it does it all again for the next word.

That's the real answer to *why GPUs and not CPUs*. Not that GPUs are
mysteriously fast — but that this job is millions of identical independent sums,
and that's the one thing a stadium of slow workers beats a handful of brilliant
ones at.
""")

code('lab.llm_math()')

md("""
---
## What you did today

- Ran your own code on a genuinely different processor
- Handed data to a machine that couldn't otherwise see it, and got it back
- Pointed 2.4 million threads at 2.4 million pixels, exactly one each
- Made a real picture change, twice
- Measured it against a CPU, and found where the time actually goes

**If you want to keep going:** there are extra programs in `lab/extras/` — what
happens when you forget the copy back, what the bounds check is really
protecting you from, and a matrix multiply where changing *which* memory each
thread reads makes it several times faster for free.
""")

nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "T4", "toc_visible": True,
                  "name": "Run Your Code on a GPU"},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    },
    "cells": cells,
}

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blur.ipynb")
with open(out, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("wrote", out, "-", len(cells), "cells")
