# -*- coding: utf-8 -*-
"""
Pre-flight check. From the repo root:

    python lab/verify.py

On this machine's GPU, proves that:
  1. main.cu ships with the kernel body and all of main() empty; blur.cu ships
     with only the kernel missing and a main() identical to the finished one
  2. run() refuses both while empty, naming what's missing
  3. the finished greyscale passes; the finished blur passes; a greyscale
     kernel pasted into the blur file is called out
  4. the host-side mistakes students actually make get named, not just "wrong"
  5. the CPU-vs-GPU race runs and feeds the last cell

Run it before class, or after editing lab/make_notebook.py. About a minute.
"""
import contextlib
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
SOL = os.path.join(REPO, "lab", "solutions")
STUDENT = {"main": os.path.join(REPO, "student", "main.cu"),
           "blur": os.path.join(REPO, "student", "blur.cu")}


def section(t):
    print("-" * 60)
    print(t)


def quiet_run(program):
    """Run a program with all output captured; return (result, what was printed)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = lab.run(program, show_output=False)
    return out, buf.getvalue()


def expect_pass(label, program, stage):
    out, said = quiet_run(program)
    if out is None or lab._last.get("stage") != stage:
        problems.append(label + ": expected a pass detected as '" + stage
                        + "', got stage=" + str(lab._last.get("stage")))
    print("   " + (said.strip().splitlines()[0] if said.strip() else "(no output)"))


def expect_hint(label, base, old, new, must_mention):
    """Mutate a finished version, run it, and require the hint to name the cause."""
    program = "blur" if base == "blur.cu" else "main"
    text = open(os.path.join(SOL, base), encoding="utf-8").read()
    if old not in text:
        problems.append(label + ": mutation target not found: " + old)
        return
    open(STUDENT[program], "w", encoding="utf-8").write(text.replace(old, new, 1))
    _, said = quiet_run(program)
    print("   " + label)
    if not all(m.lower() in said.lower() for m in must_mention):
        problems.append(label + ": hint did not mention " + str(must_mention)
                        + "\n      got: " + said.strip().replace("\n", "\n           "))
    for line in said.strip().splitlines()[:3]:
        print("      " + line)


def main_of(text):
    """main() with comments removed, for comparing the shipped cell to the solution."""
    m = re.search(r"int main\(\) \{.*?\n\}", text, re.S)
    if not m:
        return None
    lines = [re.sub(r"[ \t]*//.*", "", l).rstrip() for l in m.group(0).split("\n")]
    return "\n".join(l for l in lines if l.strip())


def main():
    if not lab.setup(quiet=True):
        print("No GPU here - nothing to verify.")
        return 1
    print("GPU found. Verifying blur.ipynb ...\n")
    os.makedirs(os.path.join(REPO, "student"), exist_ok=True)

    # ---- 1 + 2: the two shipped cells ----
    nb = json.load(io.open(os.path.join(REPO, "blur.ipynb"), encoding="utf-8"))
    cells = {}
    for c in nb["cells"]:
        src = "".join(c["source"])
        m = re.match(r"%%writefile student/(\w+)\.cu\n(.*)", src, re.S)
        if c["cell_type"] == "code" and m:
            cells[m.group(1)] = m.group(2)

    section("the shipped cells")
    if set(cells) != {"main", "blur"}:
        problems.append("expected %%writefile cells for main.cu and blur.cu; found "
                        + str(sorted(cells)))
        return report()

    # Build 1: kernel body + all of main() empty
    tpl = cells["main"]
    holes = lab._unwritten(tpl)
    print("   main.cu: " + str(len(holes)) + " markers: " + " | ".join(h.strip() for h in holes))
    if len(holes) != 2 or not any("kernel" in h for h in holes) \
            or not any("STEP 1 to STEP 5" in h for h in holes):
        problems.append("main.cu should have exactly two markers: the kernel body and all of main()")
    m = re.search(r"int main\(\) \{(.*?)\n\}", tpl, re.S)
    body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S).strip() if m else "?"
    if body:
        problems.append("main.cu: main() is not blank - found: " + body[:60])
    else:
        print("   ok  main.cu: main() is blank")
    open(STUDENT["main"], "w", encoding="utf-8").write(tpl)
    if quiet_run("main")[0] is not None:
        problems.append("run() accepted main.cu with everything empty")
    else:
        print("   ok  refused while empty")

    # Build 2: kernel marker only; main() already filled, identical to the solution's
    btpl = cells["blur"]
    bholes = lab._unwritten(btpl)
    print("   blur.cu: " + str(len(bholes)) + " marker: " + " | ".join(h.strip() for h in bholes))
    if len(bholes) != 1 or "blurKernel" not in bholes[0]:
        problems.append("blur.cu should have exactly one marker, for the whole kernel function")
    sol_blur = open(os.path.join(SOL, "blur.cu"), encoding="utf-8").read()
    if main_of(btpl) != main_of(sol_blur):
        problems.append("blur.cu: the pre-filled main() differs from lab/solutions/blur.cu")
    else:
        print("   ok  blur.cu: main() matches the finished version")
    open(STUDENT["blur"], "w", encoding="utf-8").write(btpl)
    if quiet_run("blur")[0] is not None:
        problems.append("run('blur') accepted blur.cu with the kernel missing")
    else:
        print("   ok  refused while the kernel is missing")

    # ---- 3: finished versions, and the wrong-kernel case ----
    section("finished greyscale, in student/main.cu")
    shutil.copy(os.path.join(SOL, "gray.cu"), STUDENT["main"])
    expect_pass("greyscale", "main", "gray")

    section("finished blur, in student/blur.cu")
    shutil.copy(os.path.join(SOL, "blur.cu"), STUDENT["blur"])
    expect_pass("blur", "blur", "blur")

    section("greyscale kernel pasted into the blur file")
    gray_src = open(os.path.join(SOL, "gray.cu"), encoding="utf-8").read()
    gray_kernel = re.search(r"__global__.*?\n\}\n", gray_src, re.S).group(0)
    wrong = re.sub(r"__global__.*?\n\}\n",
                   lambda _: gray_kernel.replace("imageKernel", "blurKernel"),
                   sol_blur, count=1, flags=re.S)
    open(STUDENT["blur"], "w", encoding="utf-8").write(wrong)
    _, said = quiet_run("blur")
    if "greyscale, not blurred" not in said:
        problems.append("blur.cu with a greyscale kernel should be called out as still greyscale")
    else:
        print("   ok  called out as still greyscale")

    # ---- 4: the mistakes that actually happen ----
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

    # ---- 5: the race + last cell ----
    section("race")
    p = os.path.join(REPO, "student", "race.cu")
    if os.path.exists(p):
        os.remove(p)
    if quiet_run("race")[0] is None:
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
    print("All good. Both builds, every hint, on this GPU.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
