// Topic 3 — Enough threads, and not one step too far.  (SOLUTION)
#include "lab/gpulab.h"

__global__ void square(int* a, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    // You asked for MORE threads than there is work. The extra ones must
    // do nothing. Without this line they write past the end of the array.
    if (i < n) {
        a[i] = i * i;
    }
}

int main() {
    const int N = 1000;                 // 1000 is NOT a multiple of 256
    const int THREADS = 256;
    size_t bytes = N * sizeof(int);

    // Round UP, so the last partial block still gets launched.
    // 1000/256 = 3 (too few!).  (1000 + 255)/256 = 4. Correct.
    int blocks = (N + THREADS - 1) / THREADS;

    printf("%d elements, %d threads per block\n", N, THREADS);
    printf("blocks = (%d + %d) / %d = %d\n", N, THREADS - 1, THREADS, blocks);
    printf("that launches %d threads for %d elements -> %d threads do nothing\n\n",
           blocks * THREADS, N, blocks * THREADS - N);

    int* dev;
    CUDA_CHECK(cudaMalloc(&dev, bytes));

    square<<<blocks, THREADS>>>(dev, N);
    checkKernel("square");

    int* host = (int*)malloc(bytes);
    CUDA_CHECK(cudaMemcpy(host, dev, bytes, cudaMemcpyDeviceToHost));

    printf("first three:  %d %d %d\n", host[0], host[1], host[2]);
    printf("last three:   %d %d %d   (should be 997^2 998^2 999^2)\n",
           host[N - 3], host[N - 2], host[N - 1]);

    int wrong = 0;
    for (int i = 0; i < N; ++i) if (host[i] != i * i) ++wrong;
    printf("\n%s\n", wrong == 0 ? "all 1000 elements correct" : "some elements are wrong");

    free(host);
    cudaFree(dev);
    return 0;
}
