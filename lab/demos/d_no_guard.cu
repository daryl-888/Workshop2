// DEMO — what the `if (i < n)` guard is actually protecting you from.
//
// Same kernel as Topic 3, with the bounds test deleted. We ask for far
// more threads than there is work, and every extra thread writes past
// the end of the array. On a CPU this is a segfault. On a GPU it is an
// "illegal memory access" - and you only ever hear about it if someone
// bothers to ask, which is what checkKernel() does.
#include "lab/gpulab.h"

__global__ void squareNoGuard(int* a) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    a[i] = i * i;               // no `if (i < n)` - every thread writes
}

int main() {
    const int N = 1000;
    int* dev;
    CUDA_CHECK(cudaMalloc(&dev, N * sizeof(int)));

    int blocks = 4096, threads = 256;
    printf("array holds %d ints (%zu bytes)\n", N, N * sizeof(int));
    printf("launching %d threads, each writing a[i] with no bounds test\n",
           blocks * threads);
    printf("-> %d of them write past the end of the array\n\n",
           blocks * threads - N);

    squareNoGuard<<<blocks, threads>>>(dev);
    checkKernel("squareNoGuard");        // this is where it surfaces

    printf("no error reported (you should not see this line)\n");
    cudaFree(dev);
    return 0;
}
