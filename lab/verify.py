# -*- coding: utf-8 -*-
"""
Pre-flight check for facilitators. From the repo root:

    python lab/verify.py

Proves, on this machine's GPU, that:
  1. every fill-in-the-blank template in blur.ipynb still HAS its blanks
  2. a template with blanks does NOT compile (so the exercise is real)
  3. filling in the intended answers makes it compile, run and pass its check
  4. the read-and-run topics (6, 7) and the three demos still work

Run it after editing the notebook, or before class if you want to be sure the
Colab flow will behave. Takes about a minute.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "lab"))
import labkit as lab                                             # noqa: E402

# The blank's hint text -> what a correct student writes there.
ANSWERS = {
    "t0": [("the keyword that makes this a GPU kernel", "__global__"),
           ("blocks, threads per block", "1, 8")],
    "t1": [("a unique index built from blockIdx, blockDim, threadIdx",
            "blockIdx.x * blockDim.x + threadIdx.x")],
    "t2": [("which direction?", "cudaMemcpyHostToDevice"),
           ("which direction?", "cudaMemcpyDeviceToHost")],
    "t3": [("is this thread's index inside the array?", "i < n"),
           ("enough blocks to cover N, rounded up", "(N + THREADS - 1) / THREADS")],
    "t4": [("the same thing for y", "blockIdx.y * blockDim.y + threadIdx.y"),
           ("the flat index of pixel (row, col)", "(row * w + col) * 3")],
    "t5": [("is (cr, cc) inside the image?", "cr >= 0 && cr < h && cc >= 0 && cc < w"),
           ("flat index of pixel (cr, cc) - same as Topic 4", "(cr * w + cc) * 3"),
           ("r averaged over n, cast to unsigned char", "(unsigned char)((float)r / n)")],
}

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
        m = re.match(r"%%writefile student/(t\d)\.cu\n(.*)", "".join(c["source"]), re.S)
        if m:
            templates[m.group(1)] = m.group(2)

    if sorted(templates) != sorted(ANSWERS):
        problems.append("notebook has topics " + str(sorted(templates))
                        + " but answers are known for " + str(sorted(ANSWERS)))
        return report()

    os.makedirs(os.path.join(REPO, "student"), exist_ok=True)

    for topic in sorted(templates):
        tpl = templates[topic]
        markers = re.findall(r"/\*\s*YOUR CODE:([^*]*)\*/", tpl)
        expected = len(ANSWERS[topic])
        print("-" * 60)
        print(topic + "  (" + str(len(markers)) + " blanks)")

        if len(markers) != expected:
            problems.append(topic + ": expected " + str(expected)
                            + " blanks, notebook has " + str(len(markers)))
            continue

        path = os.path.join(REPO, "student", topic + ".cu")

        # 2. must NOT compile as shipped
        open(path, "w", encoding="utf-8").write(tpl)
        if lab._compile(path, os.path.join(REPO, "build", "_verify")).returncode == 0:
            problems.append(topic + ": template compiles with blanks unfilled"
                                    " - an answer has leaked into it")
            print("   !! compiles unfilled")
        else:
            print("   ok  blanks block compilation")

        # 3. must pass once filled in
        filled = tpl
        for hint, answer in ANSWERS[topic]:
            pat = re.compile(r"/\*\s*YOUR CODE:\s*" + re.escape(hint) + r"\s*\*/")
            if not pat.search(filled):
                problems.append(topic + ": no blank matching '" + hint + "'")
                break
            filled = pat.sub(lambda _: answer, filled, count=1)
        else:
            open(path, "w", encoding="utf-8").write(filled)
            if lab.run(topic, show_output=False) is None:
                problems.append(topic + ": filled-in version failed to run")

    print("-" * 60)
    print("read-and-run topics")
    for topic in sorted(lab.GIVEN):
        p = os.path.join(REPO, "student", topic + ".cu")
        if os.path.exists(p):
            os.remove(p)                     # force the copy-from-solutions path
        if lab.run(topic, show_output=False) is None:
            problems.append(topic + ": failed to run")

    print("-" * 60)
    print("demos")
    for name in lab.DEMOS:
        print("   " + name)
        lab.demo(name)

    return report()


def report():
    print("\n" + "=" * 60)
    if problems:
        print("PROBLEMS FOUND:")
        for p in problems:
            print("  - " + p)
        return 1
    print("All good. Every topic builds, runs and checks out on this GPU.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
