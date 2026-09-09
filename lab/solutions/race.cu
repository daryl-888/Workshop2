// The race — the same blur, done both ways.
//
// Nothing to write here. We just run it and look at the numbers.
// The CPU version is the identical maths in two ordinary loops.
#include "lab/gpulab.h"

#define BLUR_SIZE 3

__global__ void blurKernel(unsigned char* out, unsigned char* in, int w, int h) {
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    if (col < w && row < h) {
        int r = 0, g = 0, b = 0, n = 0;
        for (int dr = -BLUR_SIZE; dr <= BLUR_SIZE; ++dr) {
            for (int dc = -BLUR_SIZE; dc <= BLUR_SIZE; ++dc) {
                int nrow = row + dr, ncol = col + dc;
                if (nrow >= 0 && nrow < h && ncol >= 0 && ncol < w) {
                    int i = (nrow * w + ncol) * 3;
                    r += in[i + 0]; g += in[i + 1]; b += in[i + 2]; ++n;
                }
            }
        }
        int o = (row * w + col) * 3;
        out[o + 0] = (unsigned char)((float)r / n);
        out[o + 1] = (unsigned char)((float)g / n);
        out[o + 2] = (unsigned char)((float)b / n);
    }
}

int main() {
    Image img    = loadImage();
    Image cpuOut = makeImage(img.w, img.h);
    Image gpuOut = makeImage(img.w, img.h);

    long long pixels = (long long)img.w * img.h;
    long long ops    = pixels * (2 * BLUR_SIZE + 1) * (2 * BLUR_SIZE + 1) * 3;
    printf("%d x %d = %lld pixels, about %lld additions in total\n\n",
           img.w, img.h, pixels, ops);

    // ---------- the CPU: one worker, one pixel at a time ----------
    CpuTimer cpu;
    cpu.start();
    blurOnCPU(img, cpuOut, BLUR_SIZE);
    double cpu_ms = cpu.stop_ms();
    printf("CPU   one core, nested loops      %9.2f ms\n\n", cpu_ms);

    // ---------- the GPU: every pixel at once ----------
    unsigned char *in_d, *out_d;
    cudaMalloc(&in_d,  img.bytes);
    cudaMalloc(&out_d, img.bytes);

    // The first CUDA call of a program pays a one-off startup cost.
    // Timing that would be unfair, so we get it out of the way first.
    blurKernel<<<1, 1>>>(out_d, in_d, 1, 1);
    cudaDeviceSynchronize();

    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);
    GpuTimer t;

    t.start();
    cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice);
    float send_ms = t.stop_ms();

    t.start();
    blurKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("blurKernel");
    float kernel_ms = t.stop_ms();

    t.start();
    cudaMemcpy(gpuOut.data, out_d, img.bytes, cudaMemcpyDeviceToHost);
    float back_ms = t.stop_ms();

    float total = send_ms + kernel_ms + back_ms;
    double mb = img.bytes / (1024.0 * 1024.0);

    printf("GPU   send the image over (%.0f MB)  %9.2f ms\n", mb, send_ms);
    printf("GPU   do the work                   %9.2f ms   <-- the blur itself\n", kernel_ms);
    printf("GPU   bring the answer back         %9.2f ms\n", back_ms);
    printf("GPU   TOTAL                         %9.2f ms\n\n", total);

    printf("The blur itself was %.0fx faster than the CPU.\n", cpu_ms / kernel_ms);
    printf("Counting the copying, %.0fx faster.\n", cpu_ms / total);
    printf("%.0f%% of the GPU's time was spent moving data, not computing.\n",
           100.0 * (send_ms + back_ms) / total);

    // Used by the last cell of the notebook.
    printf("\nBLUR_OPS %lld  KERNEL_MS %.4f\n", ops, kernel_ms);

    // Did they agree?
    long long diff = 0;
    for (size_t i = 0; i < img.bytes; ++i)
        diff += (cpuOut.data[i] > gpuOut.data[i]) ? (cpuOut.data[i] - gpuOut.data[i])
                                                  : (gpuOut.data[i] - cpuOut.data[i]);
    printf("CPU and GPU pictures differ by %.4f per byte (0 = identical)\n",
           (double)diff / img.bytes);

    saveImage(gpuOut, "build/blur.ppm");

    cudaFree(in_d); cudaFree(out_d);
    freeImage(img); freeImage(cpuOut); freeImage(gpuOut);
    return 0;
}
