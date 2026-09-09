"""
lab/labkit.py — the notebook's helper. Students never open this file.

    lab.setup()             once, at the top
    lab.run("gray")         compile student/gray.cu, run it, check the result
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

# name -> (human title, finished-version filename, file it writes)
PROGRAMS = {
    "gray": ("Greyscale", "gray.cu", "gray.ppm"),
    "blur": ("Blur", "blur.cu", "blur.ppm"),
    "race": ("CPU vs GPU", "race.cu", "blur.ppm"),
}

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


CRASH_HINTS = [
    "A thread read or wrote outside the picture.",
    "Usual causes: the `if (col < w && row < h)` line is missing,",
    "or `row` and `col` are the wrong way round in (row * w + col) * 3.",
]


def run(name, show_output=True):
    """Compile student/<name>.cu, run it, then check what it produced."""
    if name not in PROGRAMS:
        raise ValueError("unknown program " + name)

    src = os.path.join(STUDENT, name + ".cu")
    exe = os.path.join(BUILD, name)

    if not os.path.exists(src):
        if name in GIVEN:
            import shutil
            shutil.copy(os.path.join(REPO, "lab", "solutions", PROGRAMS[name][1]), src)
        else:
            print(NO + " student/" + name + ".cu doesn't exist yet.")
            print("   Run the code cell just above this one first — that's what writes it.")
            return None

    # Never check against a previous run's leftovers.
    artifact = os.path.join(BUILD, PROGRAMS[name][2])
    if os.path.exists(artifact):
        os.remove(artifact)

    text = open(src, encoding="utf-8").read()

    # An empty kernel is perfectly legal C++ - it compiles and quietly writes a
    # black picture. Catch it here instead, where we can say something useful.
    holes = _unwritten(text)
    if holes:
        print(NO + " The kernel is still empty — that's the part we write together:")
        for h in holes:
            print("     " + DOT + " " + h.strip())
        print("\n   Type it in, run the cell above again (that's what saves the file),")
        print("   then re-run this one. Or open the 🛟 cell below to catch up.")
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
        if r.stderr.strip():
            print(textwrap.indent(r.stderr.strip(), "   "))
        for h in CRASH_HINTS:
            print("   " + DOT + " " + h)
        return out

    print()
    _CHECKS[name](out)
    return out


def solution(name):
    """Print the finished version — the catch-up net."""
    path = os.path.join(REPO, "lab", "solutions", PROGRAMS[name][1])
    print(open(path, encoding="utf-8").read())


# -------------------------------------------------------------- checks
def _pass(msg):
    print(OK + " " + msg)


def _fail(msg, *hints):
    print(NO + " " + msg)
    for h in hints:
        print("   " + DOT + " " + h)


def _check_gray(out):
    import numpy as np
    got = _read_ppm(os.path.join(BUILD, "gray.ppm"))
    if got is None:
        return _fail("build/gray.ppm wasn't written — did the program finish?")
    src = _read_ppm(IMAGE)
    ref = (0.21 * src[:, :, 0] + 0.72 * src[:, :, 1] + 0.07 * src[:, :, 2]).astype(np.uint8)
    ref3 = np.dstack([ref, ref, ref])

    if float(np.abs(got.astype(int) - ref3.astype(int)).mean()) <= 1.0:
        _pass("Grey, and correct — all " + f"{src.shape[0] * src.shape[1]:,}"
              + " pixels found themselves in the array.")
        return
    if got.max() == 0:
        return _fail("The picture is completely black.",
                     "Either the kernel wrote nothing, or the result never came back.")
    if np.array_equal(got, src):
        return _fail("The output is the same as the input — nothing happened.",
                     "Check you're writing to `out`, not to `in`.")
    _diagnose(got, ref3)


def _check_blur(out):
    import numpy as np
    got = _read_ppm(os.path.join(BUILD, "blur.ppm"))
    if got is None:
        return _fail("build/blur.ppm wasn't written — did the program finish?")
    src = _read_ppm(IMAGE)

    radius = 3
    m = re.search(r"radius (\d+)", out)
    if m:
        radius = int(m.group(1))
    ref = _cpu_blur(src, radius)

    if got.max() == 0:
        return _fail("The picture is completely black.",
                     "Either the kernel wrote nothing, or the result never came back.")
    if np.array_equal(got, src):
        return _fail("The output is the same as the input — no blurring happened.",
                     "Check you're writing to `out`, not to `in`.")

    # The edge pixels are ~1% of the image, so a whole-picture average would
    # happily hide a wrong edge case. Score the border separately.
    d = np.abs(got.astype(int) - ref.astype(int))
    inside = float(d[radius:-radius, radius:-radius].mean())
    edge_mask = np.ones(d.shape[:2], dtype=bool)
    edge_mask[radius:-radius, radius:-radius] = False
    edge = float(d[edge_mask].mean())

    if inside <= 1.0 and edge <= 1.0:
        _pass("Your blur matches a CPU version exactly, edges included.")
        print("   That ran on " + f"{src.shape[0] * src.shape[1]:,}" + " threads at once.")
        return

    if inside <= 1.0 < edge:
        return _fail(
            "The middle is right, but the outermost " + str(radius) + " pixels are dark.",
            "A corner pixel has no neighbours above or to its left, so its",
            "square is smaller than " + str((2 * radius + 1) ** 2) + " pixels.",
            "Divide by `n` — the number you actually counted — not by "
            + str((2 * radius + 1) ** 2) + ".")

    _diagnose(got, ref)


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


_CHECKS = {"gray": _check_gray, "blur": _check_blur, "race": _check_race}


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


def show(which="blur"):
    """Before and after, plus a zoomed crop where you can really see it."""
    import matplotlib.pyplot as plt
    after = _read_ppm(os.path.join(BUILD, which + ".ppm"))
    if after is None:
        print(NO + " Nothing to show yet — run the program above first.")
        return
    before = _read_ppm(IMAGE)

    size = 320
    y, x = _busiest_crop(before, size)
    label = {"blur": "blurred on the GPU", "gray": "greyscaled on the GPU"}.get(which, which)

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
