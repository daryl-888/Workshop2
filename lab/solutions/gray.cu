// Program 1 — Greyscale.  (the finished version)
//
// One GPU thread per pixel. 2,457,600 of them, all at once.
#include "lab/gpulab.h"

// ---------------------------------------------------------------
//  THE KERNEL — this is the part we write together.
//  It runs once per thread, and every thread runs it at the same
//  time on a different pixel.
// ---------------------------------------------------------------
__global__ void grayKernel(unsigned char* out, unsigned char* in, int w, int h) {
    // 1. Which pixel am I? My position in the grid of threads.
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;

    // 2. We asked for slightly more threads than pixels. Extras do nothing.
    if (col < w && row < h) {

        // 3. Where does my pixel live in the flat array? 3 bytes per pixel.
        int i = (row * w + col) * 3;

        // 4. The actual work. Eyes see green most, blue least.
        unsigned char grey = (unsigned char)(0.21f * in[i + 0] +
                                             0.72f * in[i + 1] +
                                             0.07f * in[i + 2]);
        out[i + 0] = grey;
        out[i + 1] = grey;
        out[i + 2] = grey;
    }
}

// ---------------------------------------------------------------
//  THE HOST CODE — the five steps every CUDA program takes.
//  Read along; we don't type this one.
// ---------------------------------------------------------------
int main() {
    Image img = loadImage();                  // reading a .ppm lives in lab/gpulab.h
    Image out = makeImage(img.w, img.h);

    unsigned char *in_d, *out_d;

    // 1. Ask the GPU for its own memory. It cannot see ours.
    cudaMalloc(&in_d,  img.bytes);
    cudaMalloc(&out_d, img.bytes);

    // 2. Ship the image across: CPU -> GPU.
    cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);

    // 3. Launch one thread per pixel, in 16x16 tiles.
    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);
    printf("launching %d threads for %d pixels\n",
           grid.x * grid.y * block.x * block.y, img.w * img.h);

    grayKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("grayKernel");                // did it actually work?

    // 4. Bring the answer home: GPU -> CPU. Skip this and nothing changes.
    cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost);
    saveImage(out, "build/gray.ppm");

    // 5. Give the memory back.
    cudaFree(in_d);
    cudaFree(out_d);
    freeImage(img);
    freeImage(out);
    return 0;
}
