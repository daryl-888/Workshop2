// ============================================================
//  blur_solution.cu  —  Box blur on the GPU (completed)
//  One CUDA thread blurs one pixel by averaging its neighbours.
//  Cleaned-up teaching version: no per-call error-check clutter,
//  so the shape of the program stays readable. (See README for a
//  note on where you'd add error checking in production.)
//
//  Build & run (on a machine/Colab with a GPU + CUDA):
//      nvcc blur_solution.cu -o blur
//      ./blur                       # reads images/sample_1920x1280.ppm, writes output.ppm
// ============================================================
#include <cstdio>
#include <cstdlib>

#define BLUR_SIZE 3          // radius; a (2*3+1) x (2*3+1) = 7x7 window

// ---- The kernel: this code runs on the GPU, once per thread ----
__global__
void blurKernel(unsigned char *out, unsigned char *in, int w, int h) {
    // Which pixel does THIS thread own? Its position in the grid.
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;

    // The grid is rounded up, so some threads fall outside the image. Skip them.
    if (col < w && row < h) {
        int rVal = 0, gVal = 0, bVal = 0;
        int pixels = 0;

        // Walk the square neighbourhood around (row, col).
        for (int blurRow = -BLUR_SIZE; blurRow <= BLUR_SIZE; ++blurRow) {
            for (int blurCol = -BLUR_SIZE; blurCol <= BLUR_SIZE; ++blurCol) {
                int curRow = row + blurRow;
                int curCol = col + blurCol;

                // Only count neighbours that are actually inside the image.
                if (curRow >= 0 && curRow < h && curCol >= 0 && curCol < w) {
                    // Row-major index into a flat RGB array: 3 bytes per pixel.
                    int idx = (curRow * w + curCol) * 3;
                    rVal += in[idx + 0];
                    gVal += in[idx + 1];
                    bVal += in[idx + 2];
                    ++pixels;
                }
            }
        }

        // Write this pixel's average colour to the output image.
        int outIdx = (row * w + col) * 3;
        out[outIdx + 0] = (unsigned char)((float)rVal / pixels);
        out[outIdx + 1] = (unsigned char)((float)gVal / pixels);
        out[outIdx + 2] = (unsigned char)((float)bVal / pixels);
    }
}

// ---- Host helper: move data to the GPU, launch, bring it back ----
void blurOnGPU(unsigned char *in_h, unsigned char *out_h, int width, int height, int size) {
    unsigned char *in_d, *out_d;

    // 1. Allocate memory ON the GPU (device).
    cudaMalloc((void **)&in_d,  size);
    cudaMalloc((void **)&out_d, size);

    // 2. Copy the input image from CPU (host) -> GPU (device).
    cudaMemcpy(in_d, in_h, size, cudaMemcpyHostToDevice);

    // 3. Choose the grid: 16x16 threads per block, enough blocks to cover the image.
    dim3 dimBlock(16, 16, 1);
    dim3 dimGrid((width + 15) / 16, (height + 15) / 16, 1);

    // 4. Launch: thousands of threads run blurKernel at once.
    blurKernel<<<dimGrid, dimBlock>>>(out_d, in_d, width, height);

    // 5. Copy the finished image back GPU (device) -> CPU (host).
    cudaMemcpy(out_h, out_d, size, cudaMemcpyDeviceToHost);

    // 6. Free the GPU memory.
    cudaFree(in_d);
    cudaFree(out_d);
}

// ---- Read a binary (P6) PPM image from disk ----
void ReadImage(unsigned char **imgData, int *width, int *height) {
    FILE *f = fopen("images/sample_1920x1280.ppm", "rb");
    if (!f) { printf("Could not open images/sample_1920x1280.ppm\n"); exit(EXIT_FAILURE); }
    // PPM header: magic (P6), width, height, maxval — any whitespace between.
    char magic[3] = {0};
    int maxval = 0;
    if (fscanf(f, "%2s %d %d %d", magic, width, height, &maxval) != 4) {
        printf("Bad PPM header\n"); exit(EXIT_FAILURE);
    }
    fgetc(f);  // consume exactly one whitespace byte before the pixel data
    int n = (*width) * (*height) * 3;
    *imgData = (unsigned char *)malloc(n);
    fread(*imgData, 1, n, f);
    fclose(f);
}

// ---- Write a binary (P6) PPM image to disk ----
void WriteImage(unsigned char *pixOut, int width, int height) {
    FILE *fptr = fopen("output.ppm", "wb");
    if (!fptr) { printf("Could not open output.ppm for writing\n"); return; }
    fprintf(fptr, "P6\n%d %d\n255\n", width, height);
    fwrite(pixOut, 1, width * height * 3, fptr);
    fclose(fptr);
    printf("Wrote output.ppm (%dx%d)\n", width, height);
}

int main() {
    unsigned char *imgData, *pixOut;
    int width, height;

    ReadImage(&imgData, &width, &height);

    int size = width * height * 3;
    pixOut = (unsigned char *)malloc(size);

    blurOnGPU(imgData, pixOut, width, height, size);

    WriteImage(pixOut, width, height);

    free(imgData);
    free(pixOut);
    return 0;
}
