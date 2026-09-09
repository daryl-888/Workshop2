"""
lab/labkit.py — the notebook's helper. Students never open this file.

It does four things:
  build + run a topic's .cu file          -> lab.run("t1")
  check the answer and give a real hint   -> (run() does this for you)
  show the answer key                     -> lab.solution("t1")
  draw images so the result is obvious    -> lab.show("gray") / lab.show("blur")

The point of the checks is that a student who gets ONE thing wrong hears
about that one thing, instead of staring at 40 lines of nvcc output.
"""

import os
import re
import subprocess
import sys
import textwrap

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(REPO, "build")
STUDENT = os.path.join(REPO, "student")
IMAGE = os.path.join(REPO, "images", "sample_1920x1280.ppm")

# topic id -> (title, answer-key filename)
TOPICS = {
    "t0": ("Two computers in one box", "t0_hello.cu"),
    "t1": ("Which thread am I?", "t1_whoami.cu"),
    "t2": ("Two separate memories", "t2_memory.cu"),
    "t3": ("Enough threads, not one too far", "t3_grid.cu"),
    "t4": ("Finding a pixel", "t4_gray.cu"),
    "t5": ("The blur", "t5_blur.cu"),
    "t6": ("The race", "t6_race.cu"),
    "t7": ("Coalesced memory", "t7_matmul.cu"),
}

# Topics you read and run rather than fill in.
GIVEN = {"t6", "t7"}

_last = {}          # remembers results between cells (topic 7 -> topic 8)

OK = "✅"
NO = "❌"
DOT = "•"


# ----------------------------------------------------------------- setup
def setup(quiet=False):
    """Run once at the top of the notebook."""
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(STUDENT, exist_ok=True)
    os.chdir(REPO)

    smi = subprocess.run(["nvidia-smi",
                          "--query-gpu=name,memory.total,driver_version",
                          "--format=csv,noheader"],
                         capture_output=True, text=True)
    if smi.returncode != 0:
        print(NO + " No GPU attached to this notebook.")
        print("   Fix it: Runtime -> Change runtime type -> T4 GPU -> Save,")
        print("   then run this cell again. Nothing below will work until you do.")
        return False

    nvcc = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
    ver = re.search(r"release ([\d.]+)", nvcc.stdout)
    if not quiet:
        print(OK + " GPU:  " + smi.stdout.strip())
        print(OK + " nvcc: " + (ver.group(1) if ver else "?"))
        print(OK + " image:", "found" if os.path.exists(IMAGE) else "MISSING")
        print("\nYou are ready. Work down the notebook one topic at a time.")
    return True


# ------------------------------------------------------------ build/run
def _compile(src, exe):
    return subprocess.run(
        ["nvcc", "-O2", "-I", REPO, src, "-o", exe],
        capture_output=True, text=True, cwd=REPO)


def _compiler_output(c):
    """nvcc puts diagnostics on stderr with gcc and on stdout with MSVC."""
    return ((c.stderr or "") + "\n" + (c.stdout or "")).strip()


def _blank_left(src_text):
    """Did they leave a fill-in marker in the file?"""
    return re.findall(r"/\*\s*(YOUR CODE[^*]*)\*/", src_text)


def _explain_compile_error(err, src_text):
    print(NO + " It did not compile.\n")

    left = _blank_left(src_text)
    if left:
        # Almost always the whole story. The compiler's own output here is
        # just noise about a stray `/*`, so don't bury the real message in it.
        print("   You still have " + str(len(left)) + " blank"
              + ("s" if len(left) > 1 else "") + " to fill in:\n")
        for b in left:
            print("     " + DOT + " " + b.strip())
        print("\n   Replace each /* YOUR CODE: ... */ with real code, then run")
        print("   the %%writefile cell again before re-running this one.")
        return

    # No blanks left, so this is a genuine mistake. Lead with the first error.
    first = next((l.strip() for l in err.splitlines() if "error" in l.lower()), None)
    if first:
        print("   " + first + "\n")
    if err.strip():
        print("   Full compiler output:\n")
        print(textwrap.indent(err.strip(), "   "))


# Files a topic is expected to produce. Deleted before every run, so a
# crashed program can never be "checked" against last run's leftovers.
ARTIFACTS = {"t4": ["gray.ppm"], "t5": ["blur.ppm"], "t6": ["blur.ppm"]}

# What to say when the program compiled but died while running.
CRASH_HINTS = {
    "t3": ["A thread wrote outside the array.",
           "That is what the `if (i < n)` guard is for - check it is still there."],
    "t4": ["A thread read or wrote outside the image.",
           "Two usual causes: the bounds test is missing/wrong, or `row` and `col`",
           "are swapped in the flat index - which sends threads far past the end."],
    "t5": ["A thread read or wrote outside the image.",
           "Check the bounds test, and check `row` and `col` are not swapped",
           "in `(row * w + col) * 3`."],
}


def run(topic, show_output=True):
    """Compile student/<topic>.cu, run it, then check the answer."""
    if topic not in TOPICS:
        raise ValueError("unknown topic " + topic)

    src = os.path.join(STUDENT, topic + ".cu")
    exe = os.path.join(BUILD, topic)
    if not os.path.exists(src):
        if topic in GIVEN:      # topics 6 and 7 are read-and-run, not fill-in
            import shutil
            shutil.copy(os.path.join(REPO, "lab", "solutions", TOPICS[topic][1]), src)
        else:
            print(NO + " student/" + topic + ".cu does not exist"
                  + " - run the code cell just above this one first.")
            return None

    # Clear anything a previous attempt left behind.
    for f in ARTIFACTS.get(topic, []):
        p = os.path.join(BUILD, f)
        if os.path.exists(p):
            os.remove(p)

    text = open(src, encoding="utf-8").read()
    c = _compile(src, exe)
    if c.returncode != 0:
        _explain_compile_error(_compiler_output(c), text)
        return None

    r = subprocess.run([exe], capture_output=True, text=True, cwd=REPO)
    out = r.stdout
    if show_output:
        print(out.rstrip())
    _last[topic] = out

    if r.returncode != 0:
        print("\n" + NO + " The program stopped early (exit code "
              + str(r.returncode) + ") - so there is no answer to check.")
        if r.stderr.strip():
            print(textwrap.indent(r.stderr.strip(), "   "))
        for h in CRASH_HINTS.get(topic, []):
            print("   " + DOT + " " + h)
        return out

    print()
    _CHECKS[topic](out)
    return out


def solution(topic):
    """Print the answer key for a topic."""
    path = os.path.join(REPO, "lab", "solutions", TOPICS[topic][1])
    print(open(path, encoding="utf-8").read())


DEMOS = {
    "no_copyback": ("d_no_copyback.cu",
                    "The GPU did the work. Nobody went to collect it."),
    "host_reads_device": ("d_host_reads_device.cu",
                          "The CPU follows a GPU pointer. It does not end well."),
    "no_guard": ("d_no_guard.cu",
                 "The bounds test, deleted."),
}


def demo(name):
    """Run one of the deliberately-broken programs in lab/demos/."""
    if name not in DEMOS:
        raise ValueError("unknown demo " + name + "; try " + ", ".join(DEMOS))
    fname, blurb = DEMOS[name]
    src = os.path.join(REPO, "lab", "demos", fname)
    exe = os.path.join(BUILD, "demo_" + name)

    print("DEMO: " + blurb)
    print("source: lab/demos/" + fname)
    print("-" * 64)
    c = _compile(src, exe)
    if c.returncode != 0:
        print(textwrap.indent(_compiler_output(c), "   "))
        return
    r = subprocess.run([exe], capture_output=True, text=True, cwd=REPO)
    print(r.stdout.rstrip())
    if r.stderr.strip():
        print(textwrap.indent(r.stderr.strip(), "   "))
    print("-" * 64)

    if name == "host_reads_device":
        if r.returncode == 0 and "somehow read" not in r.stdout:
            print("The program died right there - it never reached the next printf.")
        print("exit code " + str(r.returncode) + ": the process was killed for touching")
        print("memory that does not belong to it. `dev` is a valid address ON THE GPU,")
        print("and meaningless to the CPU. Two machines, two address spaces.")
    elif name == "no_copyback":
        print("This is the failure mode to fear: no crash, no message, just a")
        print("stale answer. cudaMemcpy is not bookkeeping - it IS the result.")
    elif name == "no_guard":
        print("Note that the error came from checkKernel(), not from the launch.")
        print("Without that call the program would have exited 0 and told you nothing.")


# -------------------------------------------------------------- checks
def _pass(msg):
    print(OK + " " + msg)


def _fail(msg, *hints):
    print(NO + " " + msg)
    for h in hints:
        print("   " + DOT + " " + h)


def _check_t0(out):
    gpu = re.findall(r"\[GPU\] hello from thread (\d+)", out)
    if len(gpu) != 8:
        return _fail(
            "Expected 8 GPU lines, got " + str(len(gpu)) + ".",
            "The launch config <<<blocks, threads>>> decides how many run.",
            "You want 1 block of 8 threads.")
    lines = out.splitlines()
    try:
        launched = next(i for i, l in enumerate(lines) if "launch returned" in l)
        first_gpu = next(i for i, l in enumerate(lines) if "[GPU]" in l)
    except StopIteration:
        return _fail("Could not find the expected CPU/GPU lines.")
    if launched > first_gpu:
        return _fail("The CPU line printed after the GPU lines - that is not the point here.")
    _pass("8 GPU threads ran, and the CPU carried on without waiting.")
    print("   Notice the thread numbers are not always in order. Nobody is")
    print("   taking turns - they genuinely run at the same time.")


def _check_t1(out):
    got = [int(m) for m in re.findall(r"global index\s+(\d+)", out)]
    if not got:
        return _fail("No output - did the kernel print anything?")
    if sorted(got) != list(range(12)):
        dupes = len(got) - len(set(got))
        return _fail(
            "The 12 threads produced " + str(sorted(got)) + ".",
            "You want exactly 0..11, once each." if not dupes else
            "Some threads got the SAME index - so they would fight over the same pixel.",
            "blockIdx.x tells you which block; blockDim.x is how big a block is;",
            "threadIdx.x is your seat inside it. Skip the earlier blocks, then add your seat.")
    _pass("0 through 11, once each - every element gets exactly one owner.")


def _check_t2(out):
    m = re.search(r"after:\s*(.*)", out)
    if not m:
        return _fail("No 'after:' line printed.")
    after = [int(x) for x in m.group(1).split()]
    before = [1, 2, 3, 4, 5, 6, 7, 8]
    if after == before:
        return _fail(
            "The numbers came back unchanged.",
            "The GPU probably did double them - in ITS memory.",
            "If you never copy the result back, the CPU is still looking at its own old array.",
            "Check the direction on the SECOND cudaMemcpy: cudaMemcpyDeviceToHost.")
    if after == [0] * 8:
        return _fail(
            "Everything came back as zero.",
            "The kernel doubled memory that was never filled in.",
            "Check the FIRST cudaMemcpy: cudaMemcpyHostToDevice.")
    if after != [2 * x for x in before]:
        return _fail("Got " + str(after) + ", expected " + str([2 * x for x in before]) + ".")
    _pass("There and back again. The data crossed to GPU memory and returned changed.")


def _check_t3(out):
    if "all 1000 elements correct" not in out:
        return _fail(
            "Some elements are wrong.",
            "If the LAST ones are wrong, you launched too few blocks.",
            "Integer division rounds DOWN: 1000 / 256 = 3, which is only 768",
            "threads, so the final 232 elements never get an owner.",
            "Round up instead: (N + THREADS - 1) / THREADS.")
    m = re.search(r"-> (\d+) threads do nothing", out)
    _pass("All 1000 correct" + (", with " + m.group(1) + " threads idling harmlessly."
                                if m else "."))
    print("   That waste is the deal you accept: you can only ask for whole")
    print("   blocks, so you over-ask and switch the extras off with an `if`.")


def _check_t4(out):
    import numpy as np
    got = _read_ppm(os.path.join(BUILD, "gray.ppm"))
    if got is None:
        return _fail("build/gray.ppm was not written - did the program finish?")
    src = _read_ppm(IMAGE)
    ref = (0.21 * src[:, :, 0] + 0.72 * src[:, :, 1] + 0.07 * src[:, :, 2]).astype(np.uint8)
    ref3 = np.dstack([ref, ref, ref])
    diff = float(np.abs(got.astype(int) - ref3.astype(int)).mean())
    if diff <= 1.0:
        _pass("Grey and correct. Every one of 2,457,600 pixels found itself in the array.")
        return
    if got.max() == 0:
        return _fail("The image is entirely black.",
                     "Either the kernel wrote nothing, or the result was never copied back.")
    _diagnose_image(got, ref3, "gray")


def _check_t5(out):
    got = _read_ppm(os.path.join(BUILD, "blur.ppm"))
    if got is None:
        return _fail("build/blur.ppm was not written - did the program finish?")
    src = _read_ppm(IMAGE)
    radius = 3
    m = re.search(r"radius (\d+)", out)
    if m:
        radius = int(m.group(1))
    ref = _cpu_blur(src, radius)
    import numpy as np

    if got.max() == 0:
        return _fail("The image is entirely black.",
                     "The kernel wrote nothing, or the result was never copied back.")
    if np.array_equal(got, src):
        return _fail("The output is identical to the input - no blurring happened.",
                     "Check that you are writing to `out`, not reading and rewriting `in`.")

    # The edge pixels are only ~1% of the image, so a whole-image average
    # would happily hide a wrong edge case. Score the border on its own.
    d = np.abs(got.astype(int) - ref.astype(int))
    interior = float(d[radius:-radius, radius:-radius].mean())
    border_mask = np.ones(d.shape[:2], dtype=bool)
    border_mask[radius:-radius, radius:-radius] = False
    border = float(d[border_mask].mean())

    if interior <= 1.0 and border <= 1.0:
        _pass("Your blur matches a CPU reference to within rounding, edges included.")
        print("   You just ran your own code on " + f"{src.shape[0]*src.shape[1]:,}"
              + " GPU threads at once.")
        return

    if interior <= 1.0 < border:
        return _fail(
            "The middle of the image is right, but the outermost "
            + str(radius) + " pixels are wrong (error "
            + str(round(border, 1)) + "/255 there vs "
            + str(round(interior, 2)) + " inside).",
            "A pixel in the corner has no neighbours above or to its left,",
            "so its window is smaller than " + str((2 * radius + 1) ** 2) + " pixels.",
            "Divide by the number of neighbours you actually COUNTED, not by",
            "the full window size - that is what the `n` counter is for.")

    _diagnose_image(got, ref, "blur")


def _check_t6(out):
    m = re.search(r"kernel alone is\s+([\d.]+)x", out)
    e = re.search(r"end to end it is\s+([\d.]+)x", out)
    if not m:
        return _fail("The race did not finish.")
    _last["t6_kernel_speedup"] = float(m.group(1))
    _last["t6_e2e_speedup"] = float(e.group(1)) if e else None
    _pass("Race complete.")
    print("   Two numbers worth arguing about:")
    print("   " + DOT + " the kernel is ~" + m.group(1) + "x faster than one CPU core")
    if e:
        print("   " + DOT + " but end to end it is only ~" + e.group(1) + "x")
    print("   The gap between those is the cost of being a GUEST processor:")
    print("   the GPU cannot touch your data until you ship it over and back.")
    print("   That is the whole reason real GPU code tries to keep data resident")
    print("   on the device across many kernels instead of round-tripping each time.")


def _check_t7(out):
    row = re.search(r"per ROW\s+([\d.]+) ms\s+([\d.]+) GFLOP/s", out)
    col = re.search(r"per COLUMN\s+([\d.]+) ms\s+([\d.]+) GFLOP/s", out)
    if not (row and col):
        return _fail("The benchmark did not finish.")
    _last["gflops_row"] = float(row.group(2))
    _last["gflops_col"] = float(col.group(2))
    _pass("Both kernels computed the same correct answer.")
    print("   Same math. Same number of threads. Different speed.")
    print("   The column kernel's neighbouring threads read neighbouring")
    print("   addresses, so the memory system serves them in one trip.")
    print("   On a GPU, WHERE you read is often worth more than HOW MUCH you compute.")


_CHECKS = {"t0": _check_t0, "t1": _check_t1, "t2": _check_t2, "t3": _check_t3,
           "t4": _check_t4, "t5": _check_t5, "t6": _check_t6, "t7": _check_t7}


def _diagnose_image(got, ref, kind):
    """Try to say something more useful than 'wrong'."""
    import numpy as np
    r = 8
    inner_got, inner_ref = got[r:-r, r:-r], ref[r:-r, r:-r]
    inner = float(np.abs(inner_got.astype(int) - inner_ref.astype(int)).mean())
    overall = float(np.abs(got.astype(int) - ref.astype(int)).mean())

    if inner <= 1.0 < overall:
        return _fail(
            "The middle of the image is right, but the edges are wrong.",
            "Pixels at the border have a smaller neighbourhood.",
            "Only add up neighbours that are actually inside the image,",
            "and divide by how many you COUNTED - not by the full window size.")

    # channel mix-up?
    for perm, name in [((1, 0, 2), "red and green"), ((0, 2, 1), "green and blue"),
                       ((2, 1, 0), "red and blue")]:
        if float(np.abs(got[:, :, perm].astype(int) - ref.astype(int)).mean()) <= 1.0:
            return _fail("Your colour channels are swapped (" + name + ").",
                         "Bytes go R, G, B in that order: idx+0, idx+1, idx+2.")

    if overall > 40:
        _fail("The output is badly wrong (average error " + str(round(overall, 1)) + "/255).",
              "Most likely the pixel index. The array is flat and row-major:",
              "row `row` starts row*w pixels in, then col along, 3 bytes each.",
              "Swapping row and col here is the classic mistake.")
    else:
        _fail("Close but not right (average error " + str(round(overall, 1)) + "/255).",
              "Check the divide: use a float divide by the number of neighbours counted.")


# --------------------------------------------------------------- images
def _read_ppm(path):
    import numpy as np
    if not os.path.exists(path):
        return None
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"))


def _cpu_blur(src, radius):
    """Reference blur: average of the in-bounds neighbours only."""
    import numpy as np
    a = src.astype(np.float64)
    h, w, _ = a.shape
    pad = np.zeros((h + 2 * radius, w + 2 * radius, 3))
    pad[radius:radius + h, radius:radius + w] = a
    cnt = np.zeros((h + 2 * radius, w + 2 * radius))
    cnt[radius:radius + h, radius:radius + w] = 1.0

    def boxsum(x):
        c = np.cumsum(np.cumsum(x, 0), 1)
        c = np.pad(c, [(1, 0), (1, 0)] + ([(0, 0)] if x.ndim == 3 else []))
        k = 2 * radius + 1
        return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]

    s = boxsum(pad)
    n = boxsum(cnt)[:, :, None]
    return (s / n).astype(np.uint8)          # truncates, same as (unsigned char) cast


def _busiest_crop(img, size=320):
    """Pick the most detailed square region, so a blur is actually visible."""
    import numpy as np
    g = img.astype(np.float32).mean(axis=2)
    h, w = g.shape
    best, best_v = (0, 0), -1.0
    for y in range(0, h - size, max(1, (h - size) // 8)):
        for x in range(0, w - size, max(1, (w - size) // 8)):
            v = float(g[y:y + size, x:x + size].std())
            if v > best_v:
                best_v, best = v, (y, x)
    return best


def show(which="blur"):
    """Draw before/after, plus a zoomed crop where the effect is actually visible."""
    import matplotlib.pyplot as plt
    path = os.path.join(BUILD, which + ".ppm")
    before = _read_ppm(IMAGE)
    after = _read_ppm(path)
    if after is None:
        print(NO + " " + path + " not found - run the topic above first.")
        return

    size = 320
    y, x = _busiest_crop(before, size)
    label = {"blur": "blurred on the GPU", "gray": "greyscaled on the GPU"}.get(which, which)

    fig, ax = plt.subplots(2, 2, figsize=(13, 9))
    ax[0][0].imshow(before);                      ax[0][0].set_title("before (full)")
    ax[0][1].imshow(after);                       ax[0][1].set_title("after - " + label)
    ax[1][0].imshow(before[y:y + size, x:x + size]); ax[1][0].set_title("before (zoomed in)")
    ax[1][1].imshow(after[y:y + size, x:x + size]);  ax[1][1].set_title("after (zoomed in)")
    for r in ax:
        for a in r:
            a.axis("off")
    fig.suptitle("Full image on top; the bottom row is a " + str(size) +
                 "x" + str(size) + " crop - that is where you can really see it.",
                 fontsize=11)
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------- topic 8: the payoff
def llm_math(params_billions=175.0):
    """Turn the number the student just measured into an LLM-sized statement."""
    g_row = _last.get("gflops_row")
    g_col = _last.get("gflops_col")
    if g_col is None:
        print("Run topic 7 first - this uses the speed YOUR kernel actually hit.")
        return

    # A forward pass costs roughly 2 FLOPs per parameter per token.
    flops_per_token = 2.0 * params_billions * 1e9
    gflop_per_token = flops_per_token / 1e9

    print("Your numbers, from the kernel you just ran:")
    print("   one thread per ROW      " + format(g_row, ".1f") + " GFLOP/s")
    print("   one thread per COLUMN   " + format(g_col, ".1f") + " GFLOP/s")
    print()
    print("A " + format(params_billions, ".0f") + "B-parameter model costs about "
          + "2 x params = " + format(gflop_per_token, ",.0f")
          + " GFLOP for ONE token.")
    print()
    slow = gflop_per_token / g_row
    fast = gflop_per_token / g_col
    print("   at your ROW kernel's speed:     " + format(slow, ".1f") + " s per token")
    print("   at your COLUMN kernel's speed:  " + format(fast, ".1f") + " s per token")
    print()
    print("A real deployment answers in tens of milliseconds per token. The gap")
    print("is not magic - it is the same tricks, taken further: keeping data in")
    print("fast on-chip memory, tensor cores, smaller number formats, and many")
    print("GPUs at once. But the shape of the work is exactly what you wrote:")
    print("one thread per output element, millions at a time.")
