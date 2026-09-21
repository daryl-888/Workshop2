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

I'll build the code live and you follow along in your own copy. **One file,
two stages** — you keep editing the same cell:

1. **Greyscale** — every CUDA call a program needs, on the simplest possible job.
2. **Blur** — go back to that file and change only the kernel.

Then we'll race it against a CPU and see what that has to do with ChatGPT.

**If you fall behind, don't panic.** Under each build there's a
🛟 **finished version** cell — click it, copy the whole thing over your cell, and
you're caught up. Nothing later depends on you having typed it yourself.

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

# ══════════════════════════════════════════════════ part 2: build 1
md("""
---
# 2 · Build 1: greyscale

**One file, all session.** The cell below is `student/main.cu`. We build the
greyscale program in it now, and later we come back and turn the same file into
a blur. Every time you change it: run the cell (that saves the file), then run
the check cell under it.

**`main()` starts empty and we type all of it.** Each piece has a STEP slide
with the exact lines on it. Four of those lines call small helpers from
`lab/gpulab.h` — `loadImage`, `makeImage`, `saveImage`, `freeImage` — because
reading a `.ppm` isn't CUDA. Everything else is.

| STEP | what you type | what it does |
|---|---|---|
| 1 | `loadImage()`, `makeImage(...)`, the two pointers, then `cudaMalloc(&in_d, img.bytes);` ×2 | the photo into CPU memory; ask the GPU for memory and write its address into `in_d` |
| 2 | `cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);` | destination, source, how many, which way |
| 3 | `dim3 block(16, 16); dim3 grid(...); imageKernel<<<grid, block>>>(...); checkKernel(...)` | how many threads, run it, then wait and ask if it worked |
| 3 | the kernel body | what one thread does with its one pixel |
| 4 | `cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost); saveImage(...)` | the same call, reversed; then write the file |
| 5 | `cudaFree` ×2, `freeImage` ×2, `return 0;` | give it all back — nothing does this for you |

Type them in order. Nothing runs until you run the cell, so a half-typed
`main()` is fine while we go.
""")

code('''%%writefile student/main.cu
#include "lab/gpulab.h"

// ---------------------------------------------------------------
//  STEP 3, the kernel — runs once per thread, each on its own pixel.
//  Greyscale first. Later we come back and turn this into a blur.
// ---------------------------------------------------------------
__global__ void imageKernel(unsigned char* out, unsigned char* in, int w, int h) {

    /* YOUR CODE: STEP 3 — the kernel body, about 8 lines */

}

// ---------------------------------------------------------------
//  The host code — the five steps. All of it is typed, from the
//  STEP slides. (loadImage, makeImage, saveImage and freeImage are
//  small helpers that live in lab/gpulab.h.)
// ---------------------------------------------------------------
int main() {

    /* YOUR CODE: STEP 1 to STEP 5 — setup, malloc, copy over, launch, copy back, free */

}''')

md("""
Compile, run, check. `nvcc` splits the file in two: the kernel goes to the GPU,
everything else to the CPU. If something's wrong, the message below says *which
step* to look at.
""")

code('lab.run()')
catchup("gray", "greyscale program")

code('lab.show()')

md("""
### What just happened

Five CUDA calls and one kernel — that was the entire program. Two and a half
million threads each did about five instructions and stopped, and nobody wrote a
loop over the pixels.

That's the whole trick, and it's why the chip is built the way it is. If every
thread runs the same instruction, you don't need thousands of separate control
units. Strip those out, spend the space on arithmetic instead, and you get a
processor with thousands of tiny workers.
""")

# ═════════════════════════════════════════════════════ part 3: build 2
md("""
---
# 3 · Build 2: blur — same file, new kernel

**Don't make a new cell. Scroll back up to `student/main.cu`.**

A blur replaces each pixel with the **average of the pixels around it** — for
radius 3, the 7×7 square centred on it. Two changes to the file, and *only* two:

1. Add `#define BLUR_SIZE 3` near the top, under the `#include`.
2. Replace the **body** of `imageKernel` with the blur (STEP 3 slide, blur
   version). The first three lines — `col`, `row`, the `if` — stay exactly as
   they are.

**Watch what you are *not* changing.** Every CUDA call in `main()` — the mallocs,
both memcpys, the launch, the frees — is untouched. The host code doesn't care
what the kernel does.

The one wrinkle: a pixel in the corner has no neighbours above or to its left.
So check each neighbour before using it, count how many you actually found, and
divide by **that** — not by 49. Divide by 49 and the edges come out dark.

When you've changed it, run that cell again, then come back and run this:
""")

code('lab.run()')
catchup("blur", "blur program")

code('lab.show()')

md("""
### 🎉 Same program, different picture

Look at the bottom row — the zoomed-in crop, where the softening is obvious. (On
the full photo it's real but easy to miss; a 7-pixel blur on a 1920-pixel-wide
picture gets subtle once it's shrunk to fit a screen.)

**Try this:** change `#define BLUR_SIZE 3` to `15`, re-run the cell and the
check. Each thread is now averaging 961 pixels instead of 49 — twenty times the
work — and it still finishes instantly. Try `31` if you like.
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
