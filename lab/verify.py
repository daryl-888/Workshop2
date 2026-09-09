# -*- coding: utf-8 -*-
"""
Pre-flight check. From the repo root:

    python lab/verify.py

On this machine's GPU, proves that:
  1. both live-coded cells in blur.ipynb still ship with an EMPTY kernel
  2. an empty kernel doesn't compile (so the live build is real)
  3. the finished versions in lab/solutions/ compile, run and pass their checks
  4. the CPU-vs-GPU race runs and feeds the last cell

Run it before class, or after editing lab/make_notebook.py. Takes about a minute.
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


def main():
    if not lab.setup(quiet=True):
        print("No GPU here - nothing to verify.")
        return 1
    print("GPU found. Verifying blur.ipynb ...\n")

    nb = json.load(io.open(os.path.join(REPO, "blur.ipynb"), encoding="utf-8"))
    templates = {}
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        m = re.match(r"%%writefile student/(\w+)\.cu\n(.*)", "".join(c["source"]), re.S)
        if m:
            templates[m.group(1)] = m.group(2)

    expected = {"gray", "blur"}
    if set(templates) != expected:
        problems.append("notebook writes " + str(sorted(templates))
                        + ", expected " + str(sorted(expected)))
        return report()

    os.makedirs(os.path.join(REPO, "student"), exist_ok=True)

    for name in sorted(templates):
        print("-" * 60)
        print(name)
        tpl = templates[name]
        path = os.path.join(REPO, "student", name + ".cu")

        # 1 + 2. Ships empty, and empty doesn't build.
        holes = lab._unwritten(tpl)
        if len(holes) != 1:
            problems.append(name + ": expected exactly 1 empty kernel marker, found "
                            + str(len(holes)))
        # An empty kernel body is legal C++, so run() has to refuse it up front
        # rather than relying on a compile error.
        open(path, "w", encoding="utf-8").write(tpl)
        if lab.run(name, show_output=False) is not None:
            problems.append(name + ": run() accepted an empty kernel"
                                   " - a student would just get a black picture")
            print("   !! accepted while still empty")
        else:
            print("   ok  ships empty, and run() says so instead of compiling it")

        # 3. The finished version works.
        shutil.copy(os.path.join(REPO, "lab", "solutions", lab.PROGRAMS[name][1]), path)
        if lab.run(name, show_output=False) is None:
            problems.append(name + ": the finished version failed to run")

    # 4. The race, and the cell that depends on it.
    print("-" * 60)
    print("race")
    p = os.path.join(REPO, "student", "race.cu")
    if os.path.exists(p):
        os.remove(p)                             # force the copy-from-solutions path
    if lab.run("race", show_output=False) is None:
        problems.append("race: failed to run")
    elif "blur_ops" not in lab._last:
        problems.append("race: didn't report BLUR_OPS/KERNEL_MS, so the last cell is blank")
    else:
        print("-" * 60)
        print("final cell")
        lab.llm_math()

    return report()


def report():
    print("\n" + "=" * 60)
    if problems:
        print("PROBLEMS FOUND:")
        for p in problems:
            print("  - " + p)
        return 1
    print("All good. Both programs build, run and check out on this GPU.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
