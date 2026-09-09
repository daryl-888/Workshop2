// Program 2 — Blur.  (the finished version)
//
// Notice what changed from greyscale: NOTHING below the kernel.
// Same five steps, same launch, same everything. Only the maths
// each thread does is different.
#include "lab/gpulab.h"

#define BLUR_SIZE 3     // radius -> a 7x7 box around each pixel

// ---------------------------------------------------------------
//  THE KERNEL — the only part that changes.
//  Instead of "mix my own 3 colours", it is now
//  "average everybody in my neighbourhood".
// ---------------------------------------------------------------
__global__ void blurKernel(unsigned char* out, unsigned char* in, int w, int h) {
    // 1 and 2: exactly the same as greyscale.
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;

    if (col < w && row < h) {
        int r = 0, g = 0, b = 0;
        int n = 0;                      // how many neighbours I actually found

        // 3. Walk the square of pixels around me.
        for (int dr = -BLUR_SIZE; dr <= BLUR_SIZE; ++dr) {
            for (int dc = -BLUR_SIZE; dc <= BLUR_SIZE; ++dc) {
                int nrow = row + dr;
                int ncol = col + dc;

                // Pixels at the edge of the picture have fewer neighbours.
                if (nrow >= 0 && nrow < h && ncol >= 0 && ncol < w) {
                    int i = (nrow * w + ncol) * 3;    // same address maths as before
                    r += in[i + 0];
                    g += in[i + 1];
                    b += in[i + 2];
                    ++n;
                }
            }
        }

        // 4. Average = total / how many I counted. Not / 49 - the edges
        //    would come out dark.
        int o = (row * w + col) * 3;
        out[o + 0] = (unsigned char)((float)r / n);
        out[o + 1] = (unsigned char)((float)g / n);
        out[o + 2] = (unsigned char)((float)b / n);
    }
}

// ---------------------------------------------------------------
//  THE HOST CODE — identical to Program 1. Copied, not rewritten.
// ---------------------------------------------------------------
int main() {
    Image img = loadImage();
    Image out = makeImage(img.w, img.h);

    unsigned char *in_d, *out_d;
    cudaMalloc(&in_d,  img.bytes);
    cudaMalloc(&out_d, img.bytes);
    cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);

    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);

    blurKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("blurKernel");

    cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost);
    saveImage(out, "build/blur.ppm");

    printf("radius %d -> each thread averaged up to %d pixels\n",
           BLUR_SIZE, (2 * BLUR_SIZE + 1) * (2 * BLUR_SIZE + 1));

    cudaFree(in_d);
    cudaFree(out_d);
    freeImage(img);
    freeImage(out);
    return 0;
}
