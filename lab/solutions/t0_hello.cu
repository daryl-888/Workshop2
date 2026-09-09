// Topic 0 — Two computers in one box.  (SOLUTION)
#include "lab/gpulab.h"

// __global__ means: "compile this for the GPU, and let the CPU launch it."
// A function marked __global__ is called a KERNEL.
__global__ void helloFromGPU() {
    printf("    [GPU] hello from thread %d\n", threadIdx.x);
}

int main() {
    printf("[CPU] I am the host. I run this program.\n");

    // <<<blocks, threadsPerBlock>>> says HOW MANY copies of the kernel to run.
    // 1 block of 8 threads = 8 copies, all at the same time.
    helloFromGPU<<<1, 8>>>();

    // This line runs IMMEDIATELY. The CPU does not wait for the GPU.
    printf("[CPU] launch returned instantly - I did not wait for the GPU.\n");

    checkKernel("helloFromGPU");   // <- THIS is where the CPU waits.

    printf("[CPU] now the GPU is finished.\n");
    return 0;
}
