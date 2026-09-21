// Build 1 — greyscale.  (the finished version of student/main.cu)
//
// One GPU thread per pixel. 2,457,600 of them, all at once.
#include "lab/gpulab.h"

// ---------------------------------------------------------------
//  STEP 3, the kernel — runs once per thread, each on its own pixel.
// ---------------------------------------------------------------
__global__ void imageKernel(unsigned char* out, unsigned char* in, int w, int h) {
    int col = blockIdx.x * blockDim.x + threadIdx.x;    // which column is mine
    int row = blockIdx.y * blockDim.y + threadIdx.y;    // which row is mine

    if (col < w && row < h) {                           // am I on the picture?
        int i = (row * w + col) * 3;                    // where my pixel lives

        unsigned char grey = (unsigned char)(0.21f * in[i + 0] +
                                             0.72f * in[i + 1] +
                                             0.07f * in[i + 2]);
        out[i + 0] = grey;
        out[i + 1] = grey;
        out[i + 2] = grey;
    }
}

// ---------------------------------------------------------------
//  The host code — all typed. loadImage / makeImage / saveImage /
//  freeImage are plain file I/O helpers from lab/gpulab.h; everything
//  else is CUDA, in five steps.
// ---------------------------------------------------------------
int main() {
    // setup — the photo into CPU memory, an empty picture the same size, two GPU pointers
    Image img = loadImage();
    Image out = makeImage(img.w, img.h);
    unsigned char *in_d, *out_d;

    // STEP 1 — ask the GPU for its own memory: one block for the photo, one for the result
    cudaMalloc(&in_d,  img.bytes);
    cudaMalloc(&out_d, img.bytes);

    // STEP 2 — ship the photo across: CPU -> GPU
    cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);

    // STEP 3 — decide how many threads, launch one per pixel, then wait and ask if it worked
    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);
    imageKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("imageKernel");

    // STEP 4 — bring the answer home: GPU -> CPU, then save it
    cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost);
    saveImage(out, "build/out.ppm");

    // STEP 5 — give the memory back. Nothing does this for you.
    cudaFree(in_d);
    cudaFree(out_d);
    freeImage(img);
    freeImage(out);
    return 0;
}
