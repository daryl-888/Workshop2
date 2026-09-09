// Topic 4 — Finding a pixel in a flat array.  (SOLUTION)
#include "lab/gpulab.h"

__global__ void grayKernel(unsigned char* out, const unsigned char* in, int w, int h) {
    // Now the grid is 2D, so ask for your position in BOTH directions.
    int col = blockIdx.x * blockDim.x + threadIdx.x;   // which column (x)
    int row = blockIdx.y * blockDim.y + threadIdx.y;   // which row    (y)

    if (col < w && row < h) {
        // The image is ONE flat array. Row `row` starts at row*w pixels in,
        // then col more pixels along, and each pixel is 3 bytes (R,G,B).
        int i = (row * w + col) * 3;

        // Human eyes weight green most, blue least.
        unsigned char g = (unsigned char)(0.21f * in[i + 0] +
                                          0.72f * in[i + 1] +
                                          0.07f * in[i + 2]);
        out[i + 0] = g;
        out[i + 1] = g;
        out[i + 2] = g;
    }
}

int main() {
    Image img = loadImage();
    Image out = makeImage(img.w, img.h);

    unsigned char *in_d, *out_d;
    CUDA_CHECK(cudaMalloc(&in_d,  img.bytes));
    CUDA_CHECK(cudaMalloc(&out_d, img.bytes));
    CUDA_CHECK(cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice));

    // A 2D grid of 16x16 blocks, rounded up in both directions.
    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);
    printf("%dx%d image -> grid of %dx%d blocks of %dx%d threads = %d threads\n",
           img.w, img.h, grid.x, grid.y, block.x, block.y,
           grid.x * grid.y * block.x * block.y);

    grayKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("grayKernel");

    CUDA_CHECK(cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost));
    saveImage(out, "build/gray.ppm");

    cudaFree(in_d); cudaFree(out_d);
    freeImage(img); freeImage(out);
    return 0;
}
