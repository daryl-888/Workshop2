// Build 2 — blur.  (the finished version of student/main.cu)
//
// The SAME file as greyscale. Only the kernel body changed, plus one
// #define. Every CUDA call in main() is untouched.
#include "lab/gpulab.h"

#define BLUR_SIZE 3     // radius -> a 7x7 box around each pixel

// ---------------------------------------------------------------
//  STEP 3, the kernel — now "average my neighbours" instead of
//  "mix my own three colours".
// ---------------------------------------------------------------
__global__ void imageKernel(unsigned char* out, unsigned char* in, int w, int h) {
    int col = blockIdx.x * blockDim.x + threadIdx.x;    // same as before
    int row = blockIdx.y * blockDim.y + threadIdx.y;

    if (col < w && row < h) {
        int r = 0, g = 0, b = 0;
        int n = 0;                          // how many neighbours I actually found

        for (int dr = -BLUR_SIZE; dr <= BLUR_SIZE; ++dr) {          // walk the square
            for (int dc = -BLUR_SIZE; dc <= BLUR_SIZE; ++dc) {
                int nrow = row + dr;
                int ncol = col + dc;
                if (nrow >= 0 && nrow < h && ncol >= 0 && ncol < w) {   // edge pixels have fewer
                    int i = (nrow * w + ncol) * 3;                      // same address maths
                    r += in[i + 0];
                    g += in[i + 1];
                    b += in[i + 2];
                    ++n;
                }
            }
        }

        int o = (row * w + col) * 3;
        out[o + 0] = (unsigned char)((float)r / n);     // divide by n, not by 49
        out[o + 1] = (unsigned char)((float)g / n);
        out[o + 2] = (unsigned char)((float)b / n);
    }
}

// ---------------------------------------------------------------
//  The host code — IDENTICAL to greyscale. Not one character changed.
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
