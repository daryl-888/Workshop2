// Topic 2 — Two separate memories.  (SOLUTION)
#include "lab/gpulab.h"

__global__ void doubleIt(int* a, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) a[i] = a[i] * 2;
}

int main() {
    const int N = 8;
    int host[N] = {1, 2, 3, 4, 5, 6, 7, 8};      // lives in CPU RAM
    size_t bytes = N * sizeof(int);

    printf("before:  ");
    for (int i = 0; i < N; ++i) printf("%3d", host[i]);
    printf("\n");

    // 1. Ask the GPU for its own memory. `dev` is an address in GPU RAM.
    //    The CPU may NOT read through it. It is not your memory.
    int* dev;
    CUDA_CHECK(cudaMalloc(&dev, bytes));

    // 2. Ship the data across: CPU -> GPU.
    CUDA_CHECK(cudaMemcpy(dev, host, bytes, cudaMemcpyHostToDevice));

    // 3. Do the work where the data now is.
    doubleIt<<<1, N>>>(dev, N);
    checkKernel("doubleIt");

    // 4. Bring the answer home: GPU -> CPU. Without this line the CPU
    //    never sees any change at all.
    CUDA_CHECK(cudaMemcpy(host, dev, bytes, cudaMemcpyDeviceToHost));

    printf("after:   ");
    for (int i = 0; i < N; ++i) printf("%3d", host[i]);
    printf("\n");

    cudaFree(dev);                                // GPU memory is not garbage collected
    return 0;
}
