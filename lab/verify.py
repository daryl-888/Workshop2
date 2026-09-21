# -*- coding: utf-8 -*-
"""
Pre-flight check. From the repo root:

    python lab/verify.py

On this machine's GPU, proves that:
  1. the one editable cell in blur.ipynb still ships with every STEP empty
  2. run() refuses it with a message naming the steps, instead of compiling it
  3. the greyscale finished version passes, and is detected as greyscale
  4. the blur finished version passes in the SAME file, detected as blur
  5. the host-side mistakes students actually make get named, not just "wrong"
  6. the CPU-vs-GPU race runs and feeds the last cell

Run it before class, or after editing lab/make_notebook.py. About a minute.
"""
import io
import json
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "lab"))
import labkit as lab                                             # noqa: E402

problems = []
STUDENT_MAIN = os.path.join(REPO, "student", "main.cu")
SOL = os.path.join(REPO, "lab", "solutions")


def section(t):
    print("-" * 60)
    print(t)


def expect_pass(label, stage):
    out = lab.run(show_output=False)
    if out is None or lab._last.get("stage") != stage:
        problems.append(label + ": expected a pass detected as '" + stage
                        + "', got stage=" + str(lab._last.get("stage")))


def expect_hint(label, base, old, new, must_mention):
    """Mutate a finished version, run it, and require the hint to name the cause."""
    text = open(os.path.join(SOL, base), encoding="utf-8").read()
    if old not in text:
        problems.append(label + ": mutation target not found: " + old)
        return
    open(STUDENT_MAIN, "w", encoding="utf-8").write(text.replace(old, new, 1))

    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lab.run(show_output=False)
    said = buf.getvalue()
    print("   " + label)
    ok = all(m.lower() in said.lower() for m in must_mention)
    if not ok:
        problems.append(label + ": hint did not mention " + str(must_mention)
                        + "\n      got: " + said.strip().replace("\n", "\n           "))
    for line in said.strip().splitlines()[:3]:
        print("      " + line)


def main():
    if not lab.setup(quiet=True):
        print("No GPU here - nothing to verify.")
        return 1
    print("GPU found. Verifying blur.ipynb ...\n")
    os.makedirs(os.path.join(REPO, "student"), exist_ok=True)

    # ---- 1 + 2: the shipped cell ----
    nb = json.load(io.open(os.path.join(REPO, "blur.ipynb"), encoding="utf-8"))
    cells = [
        "".join(c["source"]) for c in nb["cells"]
        if c["cell_type"] == "code" and "".join(c["source"]).startswith("%%writefile student/")
    ]
    section("the editable cell")
    if len(cells) != 1 or not cells[0].startswith("%%writefile student/main.cu\n"):
        problems.append("expected exactly one %%writefile cell, for student/main.cu; found "
                        + str(len(cells)))
        return report()
    tpl = cells[0].split("\n", 1)[1]
    holes = lab._unwritten(tpl)
    print("   " + str(len(holes)) + " empty markers: " + " | ".join(h.strip() for h in holes))
    if len(holes) != 2 or not any("kernel" in h for h in holes) \
            or not any("STEP 1 to STEP 5" in h for h in holes):
        problems.append("cell should have exactly two markers: the kernel body and all of main()")
    # main() must be genuinely empty apart from its marker
    m = re.search(r"int main\(\) \{(.*?)\n\}", tpl, re.S)
    body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S).strip() if m else "?"
    if body:
        problems.append("main() is not blank - found: " + body[:60])
    else:
        print("   ok  main() is blank")
    open(STUDENT_MAIN, "w", encoding="utf-8").write(tpl)
    if lab.run(show_output=False) is not None:
        problems.append("run() accepted the cell with all steps empty")
    else:
        print("   ok  refused while empty")

    # ---- 3 + 4: both finished versions, same file ----
    section("finished greyscale, in student/main.cu")
    shutil.copy(os.path.join(SOL, "gray.cu"), STUDENT_MAIN)
    expect_pass("greyscale", "gray")

    section("finished blur, in the SAME student/main.cu")
    shutil.copy(os.path.join(SOL, "blur.cu"), STUDENT_MAIN)
    expect_pass("blur", "blur")

    # ---- 5: the mistakes that actually happen ----
    section("host-side mistakes get named")
    expect_hint("STEP 4 missing (no copy back)", "gray.cu",
                "cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost);", "",
                ["black", "STEP 4"])
    expect_hint("STEP 2 wrong direction", "gray.cu",
                "cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);",
                "cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyDeviceToHost);",
                ["before the launch", "direction"])
    expect_hint("STEP 2 arguments swapped", "gray.cu",
                "cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);",
                "cudaMemcpy(img.data, in_d, img.bytes, cudaMemcpyHostToDevice);",
                ["before the launch"])
    expect_hint("STEP 1 missing (no cudaMalloc)", "gray.cu",
                "cudaMalloc(&in_d,  img.bytes);\n    cudaMalloc(&out_d, img.bytes);", "",
                ["before the launch", "cudaMalloc"])
    expect_hint("kernel: row and col swapped", "gray.cu",
                "int i = (row * w + col) * 3;", "int i = (col * w + row) * 3;",
                ["outside the picture"])
    expect_hint("blur: divided by 49 not n", "blur.cu",
                "out[o + 0] = (unsigned char)((float)r / n);",
                "out[o + 0] = (unsigned char)((float)r / 49);",
                ["outermost", "divide by `n`"])

    # ---- 6: the race + last cell ----
    section("race")
    p = os.path.join(REPO, "student", "race.cu")
    if os.path.exists(p):
        os.remove(p)
    if lab.run("race", show_output=False) is None:
        problems.append("race: failed to run")
    elif "blur_ops" not in lab._last:
        problems.append("race: didn't report BLUR_OPS/KERNEL_MS")
    else:
        section("final cell")
        lab.llm_math()

    return report()


def report():
    print("\n" + "=" * 60)
    if problems:
        print("PROBLEMS FOUND:")
        for p in problems:
            print("  - " + p)
        return 1
    print("All good. One file, both builds, every hint, on this GPU.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
