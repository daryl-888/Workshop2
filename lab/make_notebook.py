# -*- coding: utf-8 -*-
"""Generates blur.ipynb. Editing this file is easier than editing JSON by hand."""
import json, os

cells = []

def md(text):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": text.strip("\n").splitlines(keepends=True)})

def code(text, metadata=None):
    cells.append({"cell_type": "code", "metadata": metadata or {},
                  "execution_count": None, "outputs": [],
                  "source": text.strip("\n").splitlines(keepends=True)})

def reveal(topic, label):
    """A Colab form cell: collapses to a single title bar until clicked."""
    code('#@title 💡 Stuck? Reveal the answer for ' + label + ' { display-mode: "form" }\n'
         'lab.solution("' + topic + '")',
         {"cellView": "form"})

# ══════════════════════════════════════════════════════════ intro
md("""
# Workshop 2 · Run Your Code on a GPU

Last session you built a tool on a Linux machine. Today you write code that
runs on a **GPU** — the same kind of chip that runs ChatGPT — and you find out
*why* that chip, and not your CPU, is the one doing it.

### How this notebook works

Nine short topics. Each one is the same three steps:

1. **Read** a few paragraphs — one idea, no more.
2. **Fill in the blanks** in a small program. Every blank is marked
   `/* YOUR CODE: ... */` and is only a line or two.
3. **Run the check.** It tells you if you got it, and if not, it tells you
   *which* mistake you made — not just that something is wrong.

Nothing is longer than a screen. You never scroll through code you did not
write; all the file-reading and image-saving lives in `lab/gpulab.h`, which
you can ignore.

### The one idea, if you remember nothing else

> **One thread per output element.**

You will use it three times today, at three sizes: once per **pixel** (the
blur you are about to write), once per **matrix entry**, and — the punchline —
that is exactly how an LLM's arithmetic gets done.

---
""")

md("""
## Before you start — turn the GPU on

**Runtime → Change runtime type → T4 GPU → Save.**

Do this now. Nothing below works without it, and the first GPU allocation is
slow, so it is worth getting out of the way.
""")

code('''#@title ▶ Setup — run me first { display-mode: "form" }
# Downloads the workshop and checks your GPU. Takes about 20 seconds.
import os, sys, subprocess

REPO = "/content/Workshop2"
if not os.path.isdir(REPO):
    if os.path.isdir("lab") and os.path.isdir("images"):
        REPO = os.getcwd()                       # already inside the repo (running locally)
    else:
        subprocess.run(["git", "clone", "--depth", "1", "--quiet",
                        "https://github.com/daryl-888/Workshop2.git", REPO])

if not os.path.isdir(REPO):
    raise SystemExit("Could not download the workshop. Ask the facilitator to make "
                     "the repo PUBLIC (Settings -> General -> Change visibility).")

os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "lab"))
import labkit as lab
lab.setup()''', {"cellView": "form"})

# ══════════════════════════════════════════════════════════ topic 0
md("""
---
# Topic 0 · Two computers in one box

Your Colab machine is not one computer. It is two, bolted together and sharing
nothing:

|  | **CPU** — the *host* | **GPU** — the *device* |
|---|---|---|
| cores | a handful, each very fast | thousands, each fairly slow |
| good at | anything, mostly one thing at a time | the *same* small job, a million times |
| memory | your RAM | its own separate RAM |
| role | runs your program | waits to be given work |

That word **heterogeneous** just means this: one program, two machines that are
good at opposite things, and you deciding who does what. Nearly every CUDA rule
in this notebook is a consequence of the two facts in that table — *separate
memory*, and *many slow cores*.

A function that runs on the GPU is called a **kernel**. Two pieces of syntax:

- `__global__` in front of the function — "compile this for the GPU."
- `<<<blocks, threadsPerBlock>>>` when you call it — "run this many copies."

Notice what is *missing*: a loop. You do not tell the GPU to repeat something.
You tell it **how many copies of the function you want**, and it starts them all.

**Fill in the two blanks.**
""")

code('''%%writefile student/t0.cu
#include "lab/gpulab.h"

// This function should run on the GPU. Mark it with the keyword that says so.
/* YOUR CODE: the keyword that makes this a GPU kernel */
void helloFromGPU() {
    printf("    [GPU] hello from thread %d\\n", threadIdx.x);
}

int main() {
    printf("[CPU] I am the host. I run this program.\\n");

    // Launch it. Inside <<< >>>: how many blocks, and how many threads each.
    // Ask for 1 block of 8 threads.
    helloFromGPU<<</* YOUR CODE: blocks, threads per block */>>>();

    printf("[CPU] launch returned instantly - I did not wait for the GPU.\\n");

    checkKernel("helloFromGPU");     // <- the CPU waits HERE, not at the launch

    printf("[CPU] now the GPU is finished.\\n");
    return 0;
}''')

code('lab.run("t0")')
reveal("t0", "Topic 0")

md("""
### What just happened

- `__global__` means *"compile this for the GPU; the CPU is allowed to launch it."*
- `<<<1, 8>>>` asked for one block of eight threads. Eight copies of the function
  ran, and you never wrote a loop.
- Look at the order of the output. `[CPU] launch returned instantly` printed
  **before** any GPU line. Launching a kernel is **asynchronous** — the CPU
  hands the job over and immediately carries on. It only waits when something
  makes it wait, which here is `checkKernel()`.

That last point trips up more people than anything else in CUDA. **The GPU is
not a function you call. It is a co-processor you send jobs to.** A consequence
you will meet later: when a kernel crashes, the error does not appear at the
launch — it appears at whatever line finally waits.
""")

# ══════════════════════════════════════════════════════════ topic 1
md("""
---
# Topic 1 · Which thread am I?

You just started eight identical threads running identical code. Useless — unless
each one can work out **which piece of the job is mine**.

Threads do not arrive in a flat list. They come in **blocks**, and every thread
knows exactly three numbers:

| | means |
|---|---|
| `threadIdx.x` | my seat inside my own block (`0 .. blockDim.x-1`) |
| `blockDim.x` | how many seats a block has |
| `blockIdx.x` | which block I am in (`0, 1, 2, ...`) |

`threadIdx.x` alone is not enough — thread 0 of block 0 and thread 0 of block 1
would both claim it. You need a number unique across the *whole* launch.

Think of a cinema: to get your seat number in the room, count all the seats in
the rows before you, then add your seat in your own row.

**One blank. It is the single most-typed line in all of CUDA.**
""")

code('''%%writefile student/t1.cu
#include "lab/gpulab.h"

__global__ void whoAmI() {
    // Turn (which block, how big a block, which seat) into ONE unique number.
    int global = /* YOUR CODE: a unique index built from blockIdx, blockDim, threadIdx */;

    printf("blockIdx.x=%d  blockDim.x=%d  threadIdx.x=%d   ->  global index %2d\\n",
           blockIdx.x, blockDim.x, threadIdx.x, global);
}

int main() {
    whoAmI<<<3, 4>>>();       // 3 blocks x 4 threads = 12 threads, so 0..11
    checkKernel("whoAmI");
    return 0;
}''')

code('lab.run("t1")')
reveal("t1", "Topic 1")

md("""
### What just happened

`blockIdx.x * blockDim.x + threadIdx.x` — skip past the blocks in front of you,
then add your seat. Twelve threads, indices 0 to 11, **once each**.

"Once each" is the whole game. Give two threads the same index and they fight
over the same memory; miss an index and that element never gets computed. From
here on, every kernel starts with a version of this line.

*Why blocks at all, instead of a flat list?* Because the hardware schedules work
in blocks — a block is guaranteed to run on one processor, so threads in the same
block can cooperate cheaply. You are not using that today, but it is why the
numbering has this shape.
""")

# ══════════════════════════════════════════════════════════ topic 2
md("""
---
# Topic 2 · Two separate memories

Here is the fact that surprises everyone.

**The GPU cannot see your data.** Not "slowly" — *at all*. It has its own RAM,
physically separate from yours. A variable in your program is invisible to it
until you explicitly ship a copy across.

So every GPU program has the same five-step shape:

1. `cudaMalloc` — ask the GPU for memory. You get back a pointer that **the CPU
   must never dereference**. It is an address in another machine.
2. `cudaMemcpy( ... cudaMemcpyHostToDevice)` — ship the data over.
3. `kernel<<<...>>>` — do the work where the data now is.
4. `cudaMemcpy( ... cudaMemcpyDeviceToHost)` — bring the answer back.
5. `cudaFree` — hand the memory back. Nothing collects it for you.

Steps 2 and 4 are the ones people forget, and forgetting them is *silent*.

**Two blanks: the two copy directions.** They read exactly how they sound.
""")

code('''%%writefile student/t2.cu
#include "lab/gpulab.h"

__global__ void doubleIt(int* a, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;    // the line from Topic 1
    if (i < n) a[i] = a[i] * 2;
}

int main() {
    const int N = 8;
    int host[N] = {1, 2, 3, 4, 5, 6, 7, 8};           // lives in CPU RAM
    size_t bytes = N * sizeof(int);

    printf("before:  ");
    for (int i = 0; i < N; ++i) printf("%3d", host[i]);
    printf("\\n");

    int* dev;                                          // will point into GPU RAM
    CUDA_CHECK(cudaMalloc(&dev, bytes));

    // Send the data to the GPU.
    CUDA_CHECK(cudaMemcpy(dev, host, bytes, /* YOUR CODE: which direction? */));

    doubleIt<<<1, N>>>(dev, N);
    checkKernel("doubleIt");

    // Bring the answer back.
    CUDA_CHECK(cudaMemcpy(host, dev, bytes, /* YOUR CODE: which direction? */));

    printf("after:   ");
    for (int i = 0; i < N; ++i) printf("%3d", host[i]);
    printf("\\n");

    cudaFree(dev);
    return 0;
}''')

code('lab.run("t2")')
reveal("t2", "Topic 2")

md("""
### Two ways this goes wrong — worth seeing once

Run the two cells below. Neither is a puzzle; they take ten seconds each and
they are the failures you will actually hit.
""")

code('lab.demo("no_copyback")')
code('lab.demo("host_reads_device")')

md("""
### What just happened

The first demo is the dangerous one. **No crash, no warning, no error code** —
just the old answer, sitting there looking plausible. The GPU really did the
work; nobody went to collect it. If your GPU output ever looks suspiciously
like your input, this is why.

The second shows that `dev` is not a normal pointer. `cudaMalloc` hands you
something that *looks* exactly like an `int*`, and the CPU dies the moment it
follows it. Two machines, two address spaces, one innocent-looking variable.

Keep this in your head for Topic 6: **those copies are not free.** They are
about to cost you more time than the actual computing does.
""")

# ══════════════════════════════════════════════════════════ topic 3
md("""
---
# Topic 3 · Enough threads, and not one step too far

You want one thread per element. But you cannot ask for exactly 1000 threads —
you ask for **whole blocks**, and blocks come in fixed sizes (256 is typical;
1024 is the hard maximum).

1000 elements, 256 per block. How many blocks?

- `1000 / 256` is **3** in C. Integer division rounds *down* — that is 768
  threads, and the last 232 elements silently never get computed.
- You need to round **up**, which in integer arithmetic is written
  `(N + THREADS - 1) / THREADS`. That gives 4.

Four blocks is 1024 threads for 1000 elements. So **24 threads have no work**,
and they must be told to do nothing — otherwise they write past the end of your
array. That is the job of the bounds test:

```c
if (i < n) { ... }
```

Every real kernel has one. It is not defensive programming; it is the *price*
of only being able to order threads by the block.

**Two blanks: round up, and guard.**
""")

code('''%%writefile student/t3.cu
#include "lab/gpulab.h"

__global__ void square(int* a, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    // Some threads are past the end of the array. They must not write.
    if (/* YOUR CODE: is this thread's index inside the array? */) {
        a[i] = i * i;
    }
}

int main() {
    const int N = 1000;                 // deliberately NOT a multiple of 256
    const int THREADS = 256;
    size_t bytes = N * sizeof(int);

    // Round UP, or the last partial block never launches.
    int blocks = /* YOUR CODE: enough blocks to cover N, rounded up */;

    printf("%d elements, %d threads per block\\n", N, THREADS);
    printf("that launches %d threads -> %d threads do nothing\\n\\n",
           blocks * THREADS, blocks * THREADS - N);

    int* dev;
    CUDA_CHECK(cudaMalloc(&dev, bytes));
    square<<<blocks, THREADS>>>(dev, N);
    checkKernel("square");

    int* host = (int*)malloc(bytes);
    CUDA_CHECK(cudaMemcpy(host, dev, bytes, cudaMemcpyDeviceToHost));

    printf("first three:  %d %d %d\\n", host[0], host[1], host[2]);
    printf("last three:   %d %d %d   (should be 997^2 998^2 999^2)\\n",
           host[N - 3], host[N - 2], host[N - 1]);

    int wrong = 0;
    for (int i = 0; i < N; ++i) if (host[i] != i * i) ++wrong;
    printf("\\n%s\\n", wrong == 0 ? "all 1000 elements correct" : "some elements are wrong");

    free(host);
    cudaFree(dev);
    return 0;
}''')

code('lab.run("t3")')
reveal("t3", "Topic 3")

md("""
### And here is what the guard prevents

Same kernel with the `if` deleted, and far more threads than work:
""")

code('lab.demo("no_guard")')

md("""
### What just happened

Notice **where** that error was reported: not at the launch line, but inside
`checkKernel()`. That is Topic 0's asynchrony biting. The launch returned
"fine" because the GPU had not started yet. Without a call that waits and asks,
the program would have exited with status 0 and told you nothing at all.

This is why `lab/gpulab.h` calls `checkKernel()` after every launch, and why
real CUDA code is littered with error checks. A GPU that silently computes
garbage is much worse than one that stops.
""")

# ══════════════════════════════════════════════════════════ topic 4
md("""
---
# Topic 4 · Finding a pixel in a flat array

Time for a real image. Two new things, both small.

**First: the grid gets a second dimension.** An image has rows and columns, so
ask for threads in 2D — `dim3 block(16, 16)` is a 16×16 tile of 256 threads.
Now each thread reads `.x` for its column and `.y` for its row. Same formula
as Topic 1, twice.

**Second: the image is not a 2D array.** It is one long flat run of bytes:

```
row 0                          row 1                          row 2
[R G B][R G B][R G B]...       [R G B][R G B]...              [R G B]...
 pixel0 pixel1 pixel2           pixel0 pixel1
```

To find pixel `(row, col)`: skip `row` whole rows (each `w` pixels wide), walk
`col` pixels along, and multiply by 3 because each pixel is three bytes.

```
index = (row * w + col) * 3
```

Then `+0` is red, `+1` green, `+2` blue. **Every image kernel you ever write
starts with this line.** Get it wrong and threads read each other's pixels — or
run off the end of the image entirely.

The grid is 120×80 blocks of 16×16 threads. That is **2,457,600 threads**, one
per pixel, and you are about to launch all of them.

**Two blanks: the row index, and the flat index.**
""")

code('''%%writefile student/t4.cu
#include "lab/gpulab.h"

__global__ void grayKernel(unsigned char* out, const unsigned char* in, int w, int h) {
    int col = blockIdx.x * blockDim.x + threadIdx.x;      // given: the x direction
    int row = /* YOUR CODE: the same thing for y */;

    if (col < w && row < h) {                             // the Topic 3 guard, in 2D
        // Where does this pixel start in the flat byte array?
        int i = /* YOUR CODE: the flat index of pixel (row, col) */;

        // Eyes weight green most, blue least.
        unsigned char g = (unsigned char)(0.21f * in[i + 0] +
                                          0.72f * in[i + 1] +
                                          0.07f * in[i + 2]);
        out[i + 0] = g;
        out[i + 1] = g;
        out[i + 2] = g;
    }
}

int main() {
    Image img = loadImage();                 // from lab/gpulab.h - not your problem
    Image out = makeImage(img.w, img.h);

    unsigned char *in_d, *out_d;
    CUDA_CHECK(cudaMalloc(&in_d,  img.bytes));
    CUDA_CHECK(cudaMalloc(&out_d, img.bytes));
    CUDA_CHECK(cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice));

    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);      // Topic 3's round-up, twice
    printf("%dx%d image -> %dx%d blocks of %dx%d threads = %d threads\\n",
           img.w, img.h, grid.x, grid.y, block.x, block.y,
           grid.x * grid.y * block.x * block.y);

    grayKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("grayKernel");

    CUDA_CHECK(cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost));
    saveImage(out, "build/gray.ppm");

    cudaFree(in_d); cudaFree(out_d);
    freeImage(img); freeImage(out);
    return 0;
}''')

code('lab.run("t4")')
reveal("t4", "Topic 4")

code('lab.show("gray")')

md("""
### What just happened

Two and a half million threads each did about five instructions and stopped.
On a CPU that is a loop with 2,457,600 iterations. Here it is one launch.

Every thread ran the *same* code and touched a *different* pixel — that is
**data parallelism**, and it is the only thing GPUs are good at. It also
explains the shape of the whole machine: if every thread runs the same
instruction, you do not need thousands of independent instruction decoders.
Strip them out, spend the silicon on arithmetic units instead, and you get a
chip with thousands of cores.
""")

# ══════════════════════════════════════════════════════════ topic 5
md("""
---
# Topic 5 · The blur

Everything you need, you already have. A blur replaces each pixel with the
**average of its neighbourhood** — for radius 3, the 7×7 square around it.

Two wrinkles:

**Pixels near the edge have fewer neighbours.** A corner pixel's window hangs
off the image. So you test each neighbour before using it, and count how many
you actually used — then divide by *that count*, not by 49. Divide by 49 and
your borders come out dark.

**The window is the only new code.** The thread index, the guard, the flat
index — all Topics 1, 3 and 4. This is the pattern: kernels are mostly the
same four lines, plus the bit that is actually your problem.

**Three blanks.**
""")

code('''%%writefile student/t5.cu
#include "lab/gpulab.h"

#define BLUR_SIZE 3     // radius -> a (2*3+1) x (2*3+1) = 7x7 window

__global__ void blurKernel(unsigned char* out, const unsigned char* in, int w, int h) {
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;

    if (col < w && row < h) {
        int r = 0, g = 0, b = 0;
        int n = 0;                          // how many neighbours we ACTUALLY used

        for (int dr = -BLUR_SIZE; dr <= BLUR_SIZE; ++dr) {
            for (int dc = -BLUR_SIZE; dc <= BLUR_SIZE; ++dc) {
                int cr = row + dr;          // the neighbour's row
                int cc = col + dc;          // the neighbour's column

                // Skip neighbours that fall outside the image.
                if (/* YOUR CODE: is (cr, cc) inside the image? */) {
                    int i = /* YOUR CODE: flat index of pixel (cr, cc) - same as Topic 4 */;
                    r += in[i + 0];
                    g += in[i + 1];
                    b += in[i + 2];
                    ++n;
                }
            }
        }

        int o = (row * w + col) * 3;
        // Divide by n, not by 49. Use a float divide so you keep the precision.
        out[o + 0] = /* YOUR CODE: r averaged over n, cast to unsigned char */;
        out[o + 1] = (unsigned char)((float)g / n);     // same idea, green
        out[o + 2] = (unsigned char)((float)b / n);     // and blue
    }
}

int main() {
    Image img = loadImage();
    Image out = makeImage(img.w, img.h);

    unsigned char *in_d, *out_d;
    CUDA_CHECK(cudaMalloc(&in_d,  img.bytes));
    CUDA_CHECK(cudaMalloc(&out_d, img.bytes));
    CUDA_CHECK(cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice));

    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);

    blurKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("blurKernel");

    CUDA_CHECK(cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost));
    saveImage(out, "build/blur.ppm");
    printf("radius %d -> each of %d threads averaged up to %d pixels\\n",
           BLUR_SIZE, img.w * img.h, (2*BLUR_SIZE+1) * (2*BLUR_SIZE+1));

    cudaFree(in_d); cudaFree(out_d);
    freeImage(img); freeImage(out);
    return 0;
}''')

code('lab.run("t5")')
reveal("t5", "Topic 5")

code('lab.show("blur")')

md("""
### 🎉 You wrote a GPU kernel

Look at the bottom row — that is the zoomed crop, where the softening is
obvious. (At full size the effect is real but easy to miss; a 7-pixel blur on a
1920-pixel-wide photo is subtle once the whole thing is squeezed onto a screen.)

**Try this now — it takes 20 seconds.** Go back up to the code cell, change
`#define BLUR_SIZE 3` to `15`, and re-run that cell, then the run cell, then the
picture cell. Each thread is now averaging 961 pixels instead of 49 — twenty
times the work — and it will still finish instantly. Then try `31`.

That is the thing worth feeling: you scaled the work up twentyfold and the
wall-clock barely moved. Topic 6 measures exactly how much room you have.
""")

# ══════════════════════════════════════════════════════════ topic 6
md("""
---
# Topic 6 · The race

Nothing to fill in here. This runs **your blur, twice**: once as an ordinary
CPU loop over every pixel, once on the GPU — and times the GPU in three
separate pieces, because where the time goes is the actual lesson.

Read the numbers before you read the explanation underneath.
""")

code('lab.run("t6")')

md("""
### What just happened

Two numbers, and the gap between them is the whole point of this workshop.

**The kernel is hundreds to thousands of times faster than one CPU core.** Not
because a GPU core is fast — individually they are *slower* than a CPU core.
Because there are thousands of them and this problem splits into millions of
identical independent pieces. That is the trade the hardware makes: give up
being good at one thing quickly, to be extraordinary at the same thing a
million times.

**But end-to-end it is much less impressive** — and most of the GPU's time was
spent *moving bytes, not computing*. That is the cost of the separate memory
from Topic 2, showing up as a bill. It is why:

- work is only worth offloading if there is enough of it to pay for the trip;
- real GPU code keeps data **resident on the device** across many kernels
  instead of copying back and forth each time;
- and when people say a model "fits in 80GB of VRAM", *this* is why that
  matters so much. The weights live on the GPU permanently. Shipping them
  across for every token would be unthinkable.

*(Fair-fight note: the CPU version is compiled with `-O2`, the same optimiser
the GPU code gets. It is one thread, though — a multi-threaded CPU blur would
close some of that gap, but nowhere near all of it.)*
""")

# ══════════════════════════════════════════════════════════ topic 7
md("""
---
# Topic 7 · Where you read beats how much you compute

One more idea, and it is the one that separates working GPU code from *fast*
GPU code.

Below are two matrix-multiply kernels. Same answer, same number of threads,
same arithmetic. The only difference is **which addresses each thread touches**:

- **one thread per row** — at each step, neighbouring threads read memory
  locations that are a whole row apart. Scattered.
- **one thread per column** — at each step, thread 0 reads address *k*,
  thread 1 reads *k+1*, thread 2 reads *k+2*. Consecutive.

GPU memory is delivered in wide chunks. When neighbouring threads want
neighbouring addresses, the hardware fetches them **in one transaction** — this
is called a **coalesced** access. When they are scattered, it needs a separate
trip for each, and the arithmetic units sit idle waiting.

Also notice the *shape* of these kernels: one thread per output element, index
math, bounds guard. **It is the blur again**, with a dot product where the
average used to be.
""")

code('lab.run("t7")')

md("""
### What just happened

Several times faster, from nothing but the memory access pattern. Same math,
same thread count.

This is the counterintuitive truth about GPUs: they have so much arithmetic
capability that **feeding them is the hard part**. Most GPU optimisation is
about memory — coalescing, reusing data in fast on-chip memory, using smaller
number formats so more values fit per fetch. The multiply-adds were never the
bottleneck.
""")

# ══════════════════════════════════════════════════════════ topic 8
md("""
---
# Topic 8 · Why this is the chip that runs ChatGPT

Follow the shape you have used all day.

**Blur.** Each output pixel = a weighted sum over a neighbourhood.
One thread per pixel.

**Matrix multiply.** Each output entry = a sum of products of a row and a
column. One thread per entry. *Same kernel shape*, different arithmetic inside
— you saw both in Topic 7.

**A transformer.** Almost every expensive thing in an LLM is a matrix multiply:

| Step | What it is |
|---|---|
| Token → vector, and the Q/K/V projections | matrix multiplies |
| Attention scores, Q × Kᵀ | a matrix multiply |
| Weighted sum of values, × V | a matrix multiply |
| The feed-forward layers | the biggest matrix multiplies of all |

Producing **one token** of a large model means billions of multiply-adds, every
one of them an independent "one thread per output element" job. Then it does it
again for the next token.

That is the answer to *why GPUs and not CPUs*. Not because GPUs are
mysteriously fast — because this workload is millions of identical independent
sums, and that is the one thing a stadium of slow cores beats a handful of
brilliant ones at.

Run the cell: it takes the speed **your own kernel** hit in Topic 7 and turns
it into tokens.
""")

code('lab.llm_math()')

md("""
### The gap is the interesting part

Your kernel is nowhere near a production system. Every bit of that difference
is real engineering, and it is all made of ideas you met today:

- **keep data close** — on-chip memory instead of a round trip to VRAM
  (Topic 7's lesson, taken seriously)
- **tensor cores** — hardware that does a whole small matrix multiply as one
  instruction
- **smaller number formats** — 8 or 16 bits instead of 32, so more numbers
  arrive per fetch (Topic 7 again: feeding the machine is the bottleneck)
- **many GPUs at once** — with the model split across them, which turns
  Topic 2's copy problem into a full-time engineering discipline

None of it changes the shape of the work. It is still one thread per output
element, millions at a time — which is what you wrote today.

---

## What you actually did

- Ran code on a genuinely different processor, and saw it start work without
  waiting for you
- Managed two separate memories by hand, and saw both ways that goes wrong
- Indexed millions of threads onto millions of data elements, once each
- Wrote a real image kernel and measured it against a CPU
- Found out that on a GPU, memory access patterns beat arithmetic
- Connected all of it to the arithmetic inside an LLM

**If you keep going:** the natural next step is *tiling* — cooperatively loading
a patch of data into a block's fast shared memory so that neighbouring threads
stop re-reading the same values from slow memory. It is the single biggest win
left in both the blur and the matmul, and it is the reason CUDA groups threads
into blocks at all.

`lab/gpulab.h` has the plumbing you have been ignoring, and it is worth ten
minutes — it is where the error checking and timing live.
""")

nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "T4", "toc_visible": True,
                  "name": "Workshop 2 - Run Your Code on a GPU"},
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
