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
//  The host code. Loading and saving the photo is plain file I/O
//  (given, from lab/gpulab.h). The CUDA calls are the five steps.
// ---------------------------------------------------------------
int main() {
    Image img = loadImage();                  // given
    Image out = makeImage(img.w, img.h);      // given

    unsigned char *in_d, *out_d;              // will hold addresses in GPU memory

    // STEP 1 — ask the GPU for its own memory: one block for the photo, one for the result
    cudaMalloc(&in_d,  img.bytes);
    cudaMalloc(&out_d, img.bytes);

    // STEP 2 — ship the photo across: CPU -> GPU
    cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);

    // STEP 3 — decide how many threads, then launch one per pixel
    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);
    imageKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("imageKernel");               // given: waits for the GPU, asks if it worked

    // STEP 4 — bring the answer home: GPU -> CPU
    cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost);
    saveImage(out, "build/out.ppm");          // given

    // STEP 5 — give the GPU memory back. Nothing does this for you.
    cudaFree(in_d);
    cudaFree(out_d);
    freeImage(img);                           // given
    freeImage(out);
    return 0;
}
