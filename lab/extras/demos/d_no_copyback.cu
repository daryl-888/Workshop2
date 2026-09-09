// DEMO — the GPU did the work. You just never went to collect it.
//
// This is Topic 2 with ONE line deleted: the copy back from device to
// host. Everything else is correct. The kernel really does run, and it
// really does double the numbers - in GPU memory, where the CPU cannot
// see them. The printout below is what a missing cudaMemcpy looks like.
#include "lab/gpulab.h"

__global__ void doubleIt(int* a, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) a[i] = a[i] * 2;
}

int main() {
    const int N = 8;
    int host[N] = {1, 2, 3, 4, 5, 6, 7, 8};
    size_t bytes = N * sizeof(int);

    int* dev;
    CUDA_CHECK(cudaMalloc(&dev, bytes));
    CUDA_CHECK(cudaMemcpy(dev, host, bytes, cudaMemcpyHostToDevice));

    doubleIt<<<1, N>>>(dev, N);
    checkKernel("doubleIt");

    // MISSING:
    // cudaMemcpy(host, dev, bytes, cudaMemcpyDeviceToHost);

    printf("what the CPU sees:  ");
    for (int i = 0; i < N; ++i) printf("%3d", host[i]);
    printf("\n");

    // Prove the GPU really did the work, by asking it properly this time.
    int truth[N];
    CUDA_CHECK(cudaMemcpy(truth, dev, bytes, cudaMemcpyDeviceToHost));
    printf("what the GPU has:   ");
    for (int i = 0; i < N; ++i) printf("%3d", truth[i]);
    printf("\n\nNo error. No warning. Just the old answer, quietly.\n");

    cudaFree(dev);
    return 0;
}
