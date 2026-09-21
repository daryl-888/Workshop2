"""
lab/labkit.py — the notebook's helper. Students never open this file.

    lab.setup()             once, at the top
    lab.run()               compile student/main.cu, run it, check the result
    lab.run("blur")         same for student/blur.cu
    lab.show("gray")        before/after, with a zoomed crop
    lab.solution("gray")    print the finished version (the catch-up net)
    lab.llm_math()          turn the measured speed into an LLM-sized number

The checks exist so a student who has fallen behind hears WHAT went wrong
("your edges are dark", "row and col are swapped") instead of forty lines
of nvcc output.
"""

import os
import re
import subprocess
import textwrap

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(REPO, "build")
STUDENT = os.path.join(REPO, "student")
IMAGE = os.path.join(REPO, "images", "sample_1920x1280.ppm")

# Two student programs. Build 1 (student/main.cu) is typed from an empty
# main(); Build 2 (student/blur.cu) has main() filled in and only the kernel
# is typed. Both write build/out.ppm.
#
# name -> (finished-version filename, file the program writes)
PROGRAMS = {
    "main": ("gray.cu", "out.ppm"),
    "blur": ("blur.cu", "out.ppm"),
    "race": ("race.cu", "blur.ppm"),
}
EXPECT = {"main": "gray", "blur": "blur"}     # what each program should produce
SOLUTIONS = {"gray": "gray.cu", "blur": "blur.cu", "race": "race.cu"}

GIVEN = {"race"}          # we run this one, we don't write it

_last = {}                # remembers output between cells

OK = "✅"
NO = "❌"
DOT = "•"


# ----------------------------------------------------------------- setup
def setup(quiet=False):
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(STUDENT, exist_ok=True)
    os.chdir(REPO)

    smi = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                         capture_output=True, text=True)
    if smi.returncode != 0:
        print(NO + " No GPU attached to this notebook.")
        print("   Runtime -> Change runtime type -> T4 GPU -> Save, then run this again.")
        return False

    if not quiet:
        print(OK + " GPU:   " + smi.stdout.strip())
        print(OK + " image: " + ("found" if os.path.exists(IMAGE) else "MISSING"))
        print("\nYou're set. Follow along from here.")
    return True


# ------------------------------------------------------------ build/run
def _compile(src, exe):
    return subprocess.run(["nvcc", "-O2", "-I", REPO, src, "-o", exe],
                          capture_output=True, text=True, cwd=REPO)


def _compiler_output(c):
    """nvcc writes errors to stderr with gcc, to stdout with MSVC."""
    return ((c.stderr or "") + "\n" + (c.stdout or "")).strip()


def _unwritten(text):
    return re.findall(r"/\*\s*(YOUR CODE[^*]*)\*/", text)


def _explain_compile_error(err, text):
    print(NO + " It didn't compile.\n")

    left = _unwritten(text)
    if left:
        print("   The kernel is still empty — that's the part we write together:")
        for b in left:
            print("     " + DOT + " " + b.strip())
        print("\n   Type it in, run the cell above again (that's what saves the file),")
        print("   then re-run this one. Or open the 'finished version' cell to catch up.")
        return

    first = next((l.strip() for l in err.splitlines() if "error" in l.lower()), None)
    if first:
        print("   " + first + "\n")
    if err.strip():
        print("   Full compiler output:\n")
        print(textwrap.indent(err.strip(), "   "))


# What to say when the program compiled but stopped early. gpulab.h already
# printed WHAT failed; these say WHERE to look, keyed on its wording.
CRASH_HINTS = {
    "BEFORE the launch": [
        "A CUDA call before the launch failed — so look at STEP 1 and STEP 2, not the kernel.",
        "STEP 1: are BOTH cudaMalloc lines there, with `&in_d` and `&out_d`?",
        "STEP 2: cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice)",
        "        destination first, source second, and the direction is host TO device.",
    ],
    "CRASHED WHILE RUNNING": [
        "A thread read or wrote outside the picture — this one is in the kernel.",
        "Usual causes: the `if (col < w && row < h)` line is missing,",
        "or `row` and `col` are the wrong way round in (row * w + col) * 3.",
    ],
    "FAILED TO LAUNCH": [
        "The launch itself was rejected — look at STEP 3.",
        "dim3 block(16, 16) is 256 threads; more than 1024 per block is not allowed.",
    ],
}


def _crash_hints(out):
    for key, hints in CRASH_HINTS.items():
        if key in out:
            return hints
    return ["It stopped before writing the picture. Read the message above."]


def run(name="main", show_output=True):
    """Compile student/<name>.cu, run it, then check what it produced."""
    if name not in PROGRAMS:
        raise ValueError("unknown program " + name)

    src = os.path.join(STUDENT, name + ".cu")
    exe = os.path.join(BUILD, name)

    if not os.path.exists(src):
        if name in GIVEN:
            import shutil
            shutil.copy(os.path.join(REPO, "lab", "solutions", PROGRAMS[name][0]), src)
        else:
            print(NO + " student/" + name + ".cu doesn't exist yet.")
            print("   Run the code cell above first — that's what writes the file.")
            return None

    # Never check against a previous run's leftovers.
    artifact = os.path.join(BUILD, PROGRAMS[name][1])
    if os.path.exists(artifact):
        os.remove(artifact)

    text = open(src, encoding="utf-8").read()
    _last["source"] = text

    # A comment where code should be is perfectly legal C++ - the file compiles
    # and quietly does nothing. Catch it here, where we can say something useful.
    holes = _unwritten(text)
    if holes:
        print(NO + " Some parts are still empty — the ones we type together:")
        for h in holes:
            print("     " + DOT + " " + h.strip())
        print("\n   Type them in, run the cell above again (that's what saves the file),")
        print("   then re-run this one. Or open a 🛟 cell to catch up.")
        return None

    c = _compile(src, exe)
    if c.returncode != 0:
        _explain_compile_error(_compiler_output(c), text)
        return None

    r = subprocess.run([exe], capture_output=True, text=True, cwd=REPO)
    out = r.stdout
    if show_output:
        print(out.rstrip())
    _last[name] = out

    if r.returncode != 0:
        print("\n" + NO + " It stopped early (exit code " + str(r.returncode) + ").")
        if not show_output:
            # Make sure the program's own explanation is visible even when its
            # full output was suppressed.
            for line in out.strip().splitlines():
                if "BEFORE the launch" in line or "CRASHED" in line or "FAILED" in line:
                    print("   " + line.strip())
        if r.stderr.strip():
            print(textwrap.indent(r.stderr.strip(), "   "))
        for h in _crash_hints(out):
            print("   " + DOT + " " + h)
        return out

    print()
    _CHECKS[name](out)
    return out


def solution(name):
    """Print the finished version of a build — the catch-up net."""
    if name not in SOLUTIONS:
        raise ValueError("unknown solution " + name + "; try " + ", ".join(SOLUTIONS))
    path = os.path.join(REPO, "lab", "solutions", SOLUTIONS[name])
    print(open(path, encoding="utf-8").read())


# -------------------------------------------------------------- checks
def _pass(msg):
    print(OK + " " + msg)


def _fail(msg, *hints):
    print(NO + " " + msg)
    for h in hints:
        print("   " + DOT + " " + h)


def _looks_like_blur(text):
    """Is the student's file currently trying to be the blur?"""
    return bool(re.search(r"#\s*define\s+BLUR_SIZE", text)) or text.count("for (") >= 2


def _radius(text):
    m = re.search(r"#\s*define\s+BLUR_SIZE\s+(\d+)", text)
    return int(m.group(1)) if m else 3


def _check_image(out, expect):
    """Compare build/out.ppm against the greyscale and blur references."""
    import numpy as np
    got = _read_ppm(os.path.join(BUILD, "out.ppm"))
    if got is None:
        return _fail("build/out.ppm wasn't written — did the program get to saveImage?")
    src = _read_ppm(IMAGE)
    text = _last.get("source", "")
    pixels = f"{src.shape[0] * src.shape[1]:,}"

    grey = (0.21 * src[:, :, 0] + 0.72 * src[:, :, 1] + 0.07 * src[:, :, 2]).astype(np.uint8)
    grey3 = np.dstack([grey, grey, grey])
    radius = _radius(text)
    blurred = _cpu_blur(src, radius)

    d_grey = float(np.abs(got.astype(int) - grey3.astype(int)).mean())
    d_blur = np.abs(got.astype(int) - blurred.astype(int))
    inside = float(d_blur[radius:-radius, radius:-radius].mean())
    edge_mask = np.ones(d_blur.shape[:2], dtype=bool)
    edge_mask[radius:-radius, radius:-radius] = False
    edge = float(d_blur[edge_mask].mean())

    # ---- the right answers ----
    if d_grey <= 1.0:
        _last["stage"] = "gray"
        if expect == "blur":
            return _fail("This picture is greyscale, not blurred.",
                         "The blur kernel isn't doing its job yet - is the whole function",
                         "from the slide in the file, with BLUR_SIZE defined above it?")
        _pass("Greyscale, and correct — all " + pixels + " pixels found themselves in the array.")
        print("   Five CUDA calls and one kernel. That was the whole program.")
        return
    if inside <= 1.0 and edge <= 1.0:
        _last["stage"] = "blur"
        _pass("Blur, and it matches a CPU version exactly — edges included.")
        print("   Same five calls as before. Only the kernel is different.")
        print("   That ran on " + pixels + " threads at once.")
        return

    # ---- the wrong answers, most specific first ----
    if got.max() == 0:
        return _fail(
            "The picture is completely black.",
            "The GPU probably did the work — the CPU just never went to collect it.",
            "Check STEP 4: cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost).",
            "Destination first (the CPU's `out.data`), then the source on the GPU.")
    if np.array_equal(got, src):
        return _fail("The output is the same as the input — nothing happened.",
                     "Check the kernel writes to `out`, not to `in`.")

    blur_attempt = expect == "blur" or _looks_like_blur(text)
    if blur_attempt and inside <= 1.0 < edge:
        return _fail(
            "The middle is right, but the outermost " + str(radius) + " pixels are dark.",
            "A corner pixel has no neighbours above or to its left, so its",
            "square is smaller than " + str((2 * radius + 1) ** 2) + " pixels.",
            "Divide by `n` — the number you actually counted — not by "
            + str((2 * radius + 1) ** 2) + ".")

    _last["stage"] = "blur" if blur_attempt else "gray"
    _diagnose(got, blurred if blur_attempt else grey3)


def _check_race(out):
    k = re.search(r"blur itself was (\d+)x", out)
    g = re.search(r"BLUR_OPS (\d+)\s+KERNEL_MS ([\d.]+)", out)
    if g:
        _last["blur_ops"] = float(g.group(1))
        _last["kernel_ms"] = float(g.group(2))
    if not k:
        return _fail("The race didn't finish.")

    _pass("Race complete.")
    print("   Two numbers worth pausing on:")
    print("   " + DOT + " the blur itself was ~" + k.group(1) + "x faster than one CPU core")
    e = re.search(r"Counting the copying, (\d+)x", out)
    if e:
        print("   " + DOT + " counting the copying, only ~" + e.group(1) + "x")
    print("   The gap between them is the price of the GPU being a separate")
    print("   machine: nothing happens until the data is shipped over and back.")
    print("   It's also why a model's weights get loaded onto the GPU once and")
    print("   left there, instead of being sent across for every word.")


_CHECKS = {"main": lambda out: _check_image(out, "gray"),
           "blur": lambda out: _check_image(out, "blur"),
           "race": _check_race}


def _diagnose(got, ref):
    """Say something more useful than 'wrong'."""
    import numpy as np
    for perm, label in [((1, 0, 2), "red and green"), ((0, 2, 1), "green and blue"),
                        ((2, 1, 0), "red and blue")]:
        if float(np.abs(got[:, :, perm].astype(int) - ref.astype(int)).mean()) <= 1.0:
            return _fail("Your colour channels are swapped (" + label + ").",
                         "The bytes go red, green, blue: i + 0, i + 1, i + 2.")

    err = float(np.abs(got.astype(int) - ref.astype(int)).mean())
    if err > 40:
        _fail("The picture is badly wrong (average error " + str(round(err, 1)) + "/255).",
              "Most likely the address maths. The picture is one long flat array:",
              "row `row` starts row*w pixels in, then col along, 3 bytes each.",
              "Swapping row and col is the classic one.")
    else:
        _fail("Close, but not right (average error " + str(round(err, 1)) + "/255).",
              "Check the divide at the end.")


# --------------------------------------------------------------- images
def _read_ppm(path):
    import numpy as np
    from PIL import Image
    if not os.path.exists(path):
        return None
    return np.asarray(Image.open(path).convert("RGB"))


def _cpu_blur(src, radius):
    """Reference blur: the average of the in-bounds neighbours only."""
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

    return (boxsum(pad) / boxsum(cnt)[:, :, None]).astype(np.uint8)


def _busiest_crop(img, size=320):
    """Pick the most detailed square, so the effect is actually visible."""
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


def show(which=None):
    """Before and after, plus a zoomed crop where you can really see it."""
    import matplotlib.pyplot as plt
    # The student's program always writes build/out.ppm; the race writes blur.ppm.
    fname = "blur.ppm" if which == "race" else "out.ppm"
    after = _read_ppm(os.path.join(BUILD, fname))
    if after is None:
        print(NO + " Nothing to show yet — run the program above first.")
        return
    before = _read_ppm(IMAGE)

    size = 320
    y, x = _busiest_crop(before, size)
    stage = which if which in ("gray", "blur") else _last.get("stage", "")
    label = {"blur": "blurred on the GPU", "gray": "greyscaled on the GPU"}.get(stage, "your output")

    fig, ax = plt.subplots(2, 2, figsize=(13, 9))
    ax[0][0].imshow(before)
    ax[0][0].set_title("before")
    ax[0][1].imshow(after)
    ax[0][1].set_title("after — " + label)
    ax[1][0].imshow(before[y:y + size, x:x + size])
    ax[1][0].set_title("before, zoomed in")
    ax[1][1].imshow(after[y:y + size, x:x + size])
    ax[1][1].set_title("after, zoomed in")
    for row in ax:
        for a in row:
            a.axis("off")
    fig.suptitle("Top row: the whole picture. Bottom row: a "
                 + str(size) + "x" + str(size) + " crop, where it's obvious.",
                 fontsize=11)
    plt.tight_layout()
    plt.show()


# ------------------------------------------------------- the last cell
def llm_math(params_billions=175.0):
    """Put one word of a large model on the same scale as the blur they wrote."""
    ops = _last.get("blur_ops")
    ms = _last.get("kernel_ms")
    if ops is None or ms is None:
        print("Run the CPU-vs-GPU cell above first — this uses your own numbers.")
        return

    per_word = 2.0 * params_billions * 1e9      # ~2 operations per parameter, per word
    blurs = per_word / ops
    seconds = blurs * ms / 1000.0

    print("Your blur, just now:")
    print("   " + format(ops / 1e6, ",.0f") + " million additions, in "
          + format(ms, ".2f") + " milliseconds\n")
    print("One word out of a " + format(params_billions, ".0f")
          + "-billion-parameter model:")
    print("   roughly 2 x parameters = " + format(per_word / 1e9, ",.0f")
          + " billion arithmetic operations\n")
    print("   That is about " + format(blurs, ",.0f") + " of your blurs. For ONE word.")
    print("   At your blur's speed, that's roughly " + format(seconds, ".1f")
          + " seconds per word —")
    print("   and a real system answers in a few hundredths of a second.\n")
    print("The gap is engineering, not magic: keeping the numbers in the GPU's")
    print("fastest memory, hardware built specifically for matrix multiplication,")
    print("smaller number formats, and many GPUs at once. What never changes is")
    print("the SHAPE of the work — one thread per output number, millions at a")
    print("time, exactly like the blur you wrote.\n")
    print("(Rough comparison: the blur adds bytes, a model multiplies decimals.")
    print(" It's for scale, not a benchmark.)")
