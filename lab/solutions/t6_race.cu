// Topic 6 — The race: same blur, one CPU thread vs the whole GPU.
//
// Nothing to fill in here. Read it, run it, and look at where the
// time actually goes. (Hint: the copies are not free.)
#include "lab/gpulab.h"

#define BLUR_SIZE 3

__global__ void blurKernel(unsigned char* out, const unsigned char* in, int w, int h) {
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    if (col < w && row < h) {
        int r = 0, g = 0, b = 0, n = 0;
        for (int dr = -BLUR_SIZE; dr <= BLUR_SIZE; ++dr) {
            for (int dc = -BLUR_SIZE; dc <= BLUR_SIZE; ++dc) {
                int cr = row + dr, cc = col + dc;
                if (cr >= 0 && cr < h && cc >= 0 && cc < w) {
                    int i = (cr * w + cc) * 3;
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
    Image img     = loadImage();
    Image cpuOut  = makeImage(img.w, img.h);
    Image gpuOut  = makeImage(img.w, img.h);

    long long pixels = (long long)img.w * img.h;
    printf("image: %d x %d  =  %lld pixels\n", img.w, img.h, pixels);
    printf("window: %dx%d, so ~%lld multiply-adds of work\n\n",
           2 * BLUR_SIZE + 1, 2 * BLUR_SIZE + 1,
           pixels * (2 * BLUR_SIZE + 1) * (2 * BLUR_SIZE + 1) * 3);

    // ---------- CPU: one core, one pixel at a time ----------
    CpuTimer cpu;
    cpu.start();
    blurOnCPU(img, cpuOut, BLUR_SIZE);
    double cpu_ms = cpu.stop_ms();
    printf("CPU  (1 core, nested loops)      %9.2f ms\n\n", cpu_ms);

    // ---------- GPU: every pixel at once ----------
    unsigned char *in_d, *out_d;
    CUDA_CHECK(cudaMalloc(&in_d,  img.bytes));
    CUDA_CHECK(cudaMalloc(&out_d, img.bytes));

    // Warm up: the very first CUDA call pays a one-time setup cost that
    // has nothing to do with your kernel. Timing it would be dishonest.
    blurKernel<<<1, 1>>>(out_d, in_d, 1, 1);
    cudaDeviceSynchronize();

    dim3 block(16, 16);
    dim3 grid((img.w + 15) / 16, (img.h + 15) / 16);

    GpuTimer t;
    t.start();
    CUDA_CHECK(cudaMemcpy(in_d, img.data, img.bytes, cudaMemcpyHostToDevice));
    float h2d_ms = t.stop_ms();

    t.start();
    blurKernel<<<grid, block>>>(out_d, in_d, img.w, img.h);
    checkKernel("blurKernel");
    float kernel_ms = t.stop_ms();

    t.start();
    CUDA_CHECK(cudaMemcpy(gpuOut.data, out_d, img.bytes, cudaMemcpyDeviceToHost));
    float d2h_ms = t.stop_ms();

    float gpu_total = h2d_ms + kernel_ms + d2h_ms;
    double mb = img.bytes / (1024.0 * 1024.0);

    printf("GPU  copy in   (%.1f MB CPU->GPU)  %9.2f ms\n", mb, h2d_ms);
    printf("GPU  kernel    (%d threads)   %9.2f ms   <-- the actual work\n",
           grid.x * grid.y * block.x * block.y, kernel_ms);
    printf("GPU  copy out  (%.1f MB GPU->CPU)  %9.2f ms\n", mb, d2h_ms);
    printf("GPU  TOTAL                        %9.2f ms\n\n", gpu_total);

    printf("kernel alone is %6.1fx faster than the CPU\n", cpu_ms / kernel_ms);
    printf("end to end it is %5.1fx faster than the CPU\n", cpu_ms / gpu_total);
    printf("...and %.0f%% of the GPU's time was just moving bytes, not computing.\n",
           100.0 * (h2d_ms + d2h_ms) / gpu_total);

    // ---------- did they agree? ----------
    long long diff = 0;
    for (size_t i = 0; i < img.bytes; ++i)
        diff += (cpuOut.data[i] > gpuOut.data[i]) ? (cpuOut.data[i] - gpuOut.data[i])
                                                  : (gpuOut.data[i] - cpuOut.data[i]);
    printf("\nCPU and GPU images differ by %.4f per byte on average (0 = identical)\n",
           (double)diff / img.bytes);

    saveImage(gpuOut, "build/blur.ppm");

    cudaFree(in_d); cudaFree(out_d);
    freeImage(img); freeImage(cpuOut); freeImage(gpuOut);
    return 0;
}
