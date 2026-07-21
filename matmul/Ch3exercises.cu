/*
  From "Programming Massively Parallel Processors" (PMPP), Ch.3.
  Two matrix-multiply kernels — one thread per output ROW, one per output COLUMN —
  plus notes on coalesced vs non-coalesced memory access. Used in the Workshop 2
  lecture to connect image blur -> matrix multiply -> the math inside LLMs.
*/
#include <cstdio>

// (a) each thread produces one output ROW
__global__ void MatrixMulRowKernel(float* M, float *N, float* P, int width) {
  int row = blockIdx.x*blockDim.x+threadIdx.x;
  if (row < width) {
    for (int j = 0; j < width; ++j) {
      float Pvalue = 0;
      for (int k = 0; k < width; ++k) {
        // result[row][j] = sum_k A[row][k] * B[k][j]
        Pvalue += M[row*width+k]*N[k*width+j];
      }
      P[row*width+j] = Pvalue;
    }
  }
}

// (b) each thread produces one output COLUMN
__global__ void MatrixMulColKernel(float* M, float *N, float* P, int width) {
  int col = blockIdx.x*blockDim.x+threadIdx.x;
  if (col < width) {
    for (int i = 0; i < width; ++i) {
      float Pvalue = 0;
      for (int k = 0; k < width; ++k) {
        // P[i][col] = sum_k M[i][k] * N[k][col]
        Pvalue += M[i*width+k]*N[k*width+col];
      }
      P[i*width + col] = Pvalue;
    }
  }
}

/*
  (c) GPUs love COALESCED memory access: neighbouring threads reading
  neighbouring addresses, instead of jumping around.
    Row kernel: M not coalesced, N not coalesced
    Col kernel: M not coalesced, N coalesced
  -> the column kernel is faster because its N access is coalesced.
*/

int main() {
  int width = 4;
  float M_h[] = {10,20,30,40, 10,20,30,40, 10,20,30,40, 10,20,30,40};
  float N_h[] = {10,20,30,40, 10,20,30,40, 10,20,30,40, 10,20,30,40};
  float P_h[16];

  float *M_d, *N_d, *P_d;
  cudaMalloc((void**)&M_d, 16*sizeof(float));
  cudaMalloc((void**)&N_d, 16*sizeof(float));
  cudaMalloc((void**)&P_d, 16*sizeof(float));

  cudaMemcpy(M_d, M_h, 16*sizeof(float), cudaMemcpyHostToDevice);
  cudaMemcpy(N_d, N_h, 16*sizeof(float), cudaMemcpyHostToDevice);

  dim3 dimGrid(ceil(width/256.0), 1, 1);
  dim3 dimBlock(256, 1, 1);
  MatrixMulRowKernel<<<dimGrid, dimBlock>>>(M_d, N_d, P_d, width);
  MatrixMulColKernel<<<dimGrid, dimBlock>>>(M_d, N_d, P_d, width);

  cudaMemcpy(P_h, P_d, 16*sizeof(float), cudaMemcpyDeviceToHost);
  for (int i = 0; i < width; ++i) { for (int j = 0; j < width; ++j) printf("%.1f ", P_h[i*width+j]); printf("\n"); }

  cudaFree(M_d); cudaFree(N_d); cudaFree(P_d);
  return 0;
}
