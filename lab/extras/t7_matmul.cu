// Topic 7 — Same math, same thread count, 10x the speed.
//
// Two matrix-multiply kernels. Both compute the identical answer with
// the identical number of threads. The ONLY difference is which memory
// address each thread touches on each step -- and that difference is
// worth an order of magnitude.
//
// Nothing to fill in. Run it and look at the two numbers.
#include "lab/gpulab.h"

// (a) One thread per output ROW.
//     Step k: thread `row` reads N[k*width + col] as col marches along.
//     Neighbouring THREADS are on different rows, so they read addresses
//     `width` floats apart. Scattered.
__global__ void matMulRow(const float* M, const float* N, float* P, int width) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < width) {
        for (int j = 0; j < width; ++j) {
            float sum = 0.f;
            for (int k = 0; k < width; ++k)
                sum += M[row * width + k] * N[k * width + j];
            P[row * width + j] = sum;
        }
    }
}

// (b) One thread per output COLUMN.
//     Step k: thread `col` reads N[k*width + col]. Thread 0 reads
//     N[k*width+0], thread 1 reads N[k*width+1], ... consecutive
//     addresses, at the same moment. The hardware fetches that whole
//     run in ONE transaction. This is called a COALESCED access.
__global__ void matMulCol(const float* M, const float* N, float* P, int width) {
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (col < width) {
        for (int i = 0; i < width; ++i) {
            float sum = 0.f;
            for (int k = 0; k < width; ++k)
                sum += M[i * width + k] * N[k * width + col];
            P[i * width + col] = sum;
        }
    }
}

static bool verify(const float* P, int width) {
    // Every entry of M and N is 1.0, so every entry of P must equal `width`.
    for (int i = 0; i < width * width; ++i)
        if (P[i] != (float)width) return false;
    return true;
}

int main() {
    const int width = 1024;
    const size_t n = (size_t)width * width;
    const size_t bytes = n * sizeof(float);

    float* M_h = (float*)malloc(bytes);
    float* N_h = (float*)malloc(bytes);
    float* P_h = (float*)malloc(bytes);
    for (size_t i = 0; i < n; ++i) { M_h[i] = 1.f; N_h[i] = 1.f; }

    float *M_d, *N_d, *P_d;
    CUDA_CHECK(cudaMalloc(&M_d, bytes));
    CUDA_CHECK(cudaMalloc(&N_d, bytes));
    CUDA_CHECK(cudaMalloc(&P_d, bytes));
    CUDA_CHECK(cudaMemcpy(M_d, M_h, bytes, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(N_d, N_h, bytes, cudaMemcpyHostToDevice));

    const int THREADS = 256;
    int blocks = (width + THREADS - 1) / THREADS;   // same ceil-div as Topic 3

    double gflop = 2.0 * width * width * width / 1e9;
    printf("%d x %d matrices, %d threads either way\n", width, width, width);
    printf("%.1f billion multiply-adds per run\n\n", gflop / 2.0);

    GpuTimer t;

    matMulRow<<<blocks, THREADS>>>(M_d, N_d, P_d, width);   // warm up
    cudaDeviceSynchronize();

    t.start();
    matMulRow<<<blocks, THREADS>>>(M_d, N_d, P_d, width);
    checkKernel("matMulRow");
    float row_ms = t.stop_ms();
    CUDA_CHECK(cudaMemcpy(P_h, P_d, bytes, cudaMemcpyDeviceToHost));
    bool row_ok = verify(P_h, width);

    t.start();
    matMulCol<<<blocks, THREADS>>>(M_d, N_d, P_d, width);
    checkKernel("matMulCol");
    float col_ms = t.stop_ms();
    CUDA_CHECK(cudaMemcpy(P_h, P_d, bytes, cudaMemcpyDeviceToHost));
    bool col_ok = verify(P_h, width);

    printf("one thread per ROW     %8.2f ms   %6.1f GFLOP/s   %s\n",
           row_ms, gflop / (row_ms / 1000.0), row_ok ? "correct" : "WRONG");
    printf("one thread per COLUMN  %8.2f ms   %6.1f GFLOP/s   %s\n",
           col_ms, gflop / (col_ms / 1000.0), col_ok ? "correct" : "WRONG");
    printf("\ncolumn version is %.1fx faster - same math, same threads,\n", row_ms / col_ms);
    printf("only the memory addresses differ.\n");

    free(M_h); free(N_h); free(P_h);
    cudaFree(M_d); cudaFree(N_d); cudaFree(P_d);
    return 0;
}
