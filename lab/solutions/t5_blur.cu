// Topic 5 — The blur.  (SOLUTION)
#include "lab/gpulab.h"

#define BLUR_SIZE 3     // radius: a (2*3+1) x (2*3+1) = 7x7 window

__global__ void blurKernel(unsigned char* out, const unsigned char* in, int w, int h) {
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;

    if (col < w && row < h) {
        int r = 0, g = 0, b = 0;
        int n = 0;                       // how many neighbours we actually counted

        // Walk the square window centred on MY pixel.
        for (int dr = -BLUR_SIZE; dr <= BLUR_SIZE; ++dr) {
            for (int dc = -BLUR_SIZE; dc <= BLUR_SIZE; ++dc) {
                int cr = row + dr;
                int cc = col + dc;

                // Pixels at the edge of the image have a smaller window.
                if (cr >= 0 && cr < h && cc >= 0 && cc < w) {
                    int i = (cr * w + cc) * 3;     // same index math as Topic 4
                    r += in[i + 0];
                    g += in[i + 1];
                    b += in[i + 2];
                    ++n;
                }
            }
        }

        // Average. Divide as float so we don't throw away precision,
        // then squeeze back into one byte.
        int o = (row * w + col) * 3;
        out[o + 0] = (unsigned char)((float)r / n);
        out[o + 1] = (unsigned char)((float)g / n);
        out[o + 2] = (unsigned char)((float)b / n);
    }
}

int main() {
    Image img = loadImage();
    Image out = makeImage(img.w, img.h);

    unsigned char *in_d, *out_d;
    CUDA_CHECK(cudaMalloc(&in_d,  img.bytes));
    CUDA_CHECK(cudaMalloc(&out_d, img.bytes));
    CUDA_CHECK(cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice));

    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);

    blurKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("blurKernel");

    CUDA_CHECK(cudaMemcpy(out.data, out_d, img.bytes, cudaMemcpyDeviceToHost));
    saveImage(out, "build/blur.ppm");

    printf("radius %d -> each of %d threads averaged up to %d pixels\n",
           BLUR_SIZE, img.w * img.h, (2 * BLUR_SIZE + 1) * (2 * BLUR_SIZE + 1));

    cudaFree(in_d); cudaFree(out_d);
    freeImage(img); freeImage(out);
    return 0;
}
