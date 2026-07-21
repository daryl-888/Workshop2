// ============================================================
//  blur_template.cu  —  Box blur on the GPU (FILL IN THE BLANKS)
//
//  One CUDA thread blurs one pixel by averaging its neighbours.
//  Your job: fill in each  /* TODO n: ... */  blank. There are 9.
//  The file will NOT compile until every blank is filled — that's
//  intentional. Work top to bottom; the comments tell you what
//  each line should compute. Stuck? See HINTS in the README, and
//  blur_solution.cu has the full answer if you're truly stuck.
//
//  Build & run (Colab or any GPU + CUDA machine):
//      nvcc blur_template.cu -o blur
//      ./blur                    # reads images/sample_1920x1280.ppm, writes output.ppm
// ============================================================
#include <cstdio>
#include <cstdlib>

#define BLUR_SIZE 3          // radius; a (2*3+1) x (2*3+1) = 7x7 window

// ---- The kernel: this code runs on the GPU, once per thread ----
__global__
void blurKernel(unsigned char *out, unsigned char *in, int w, int h) {
    // Which pixel does THIS thread own? Combine the block index, the
    // block dimension, and the thread index for BOTH x (col) and y (row).
    int col = /* TODO 1: block index x * block dim x + thread index x */;
    int row = /* TODO 2: block index y * block dim y + thread index y */;

    // The grid is rounded up, so some threads land outside the image.
    // Only work if this pixel is actually inside the width and height.
    if (/* TODO 3: col in range AND row in range */) {
        int rVal = 0, gVal = 0, bVal = 0;
        int pixels = 0;

        // Walk the square neighbourhood around (row, col).
        for (int blurRow = -BLUR_SIZE; blurRow <= BLUR_SIZE; ++blurRow) {
            for (int blurCol = -BLUR_SIZE; blurCol <= BLUR_SIZE; ++blurCol) {
                int curRow = row + blurRow;
                int curCol = col + blurCol;

                if (curRow >= 0 && curRow < h && curCol >= 0 && curCol < w) {
                    // Flat row-major index into the RGB array (3 bytes per pixel).
                    int idx = /* TODO 4: (curRow * w + curCol) * 3 */;
                    rVal += in[idx + 0];
                    gVal += in[idx + 1];
                    bVal += in[idx + 2];
                    ++pixels;
                }
            }
        }

        // Average = sum / number of neighbours counted. Write all 3 channels.
        int outIdx = (row * w + col) * 3;
        out[outIdx + 0] = /* TODO 5a: average of rVal over pixels, as unsigned char */;
        out[outIdx + 1] = /* TODO 5b: average of gVal over pixels, as unsigned char */;
        out[outIdx + 2] = /* TODO 5c: average of bVal over pixels, as unsigned char */;
    }
}

// ---- Host helper: move data to the GPU, launch, bring it back ----
void blurOnGPU(unsigned char *in_h, unsigned char *out_h, int width, int height, int size) {
    unsigned char *in_d, *out_d;

    // 1. Allocate memory ON the GPU (device).
    cudaMalloc((void **)&in_d,  size);
    cudaMalloc((void **)&out_d, size);

    // 2. Copy the input image from CPU (host) -> GPU (device).
    cudaMemcpy(in_d, in_h, size, /* TODO 6: copy direction, host -> device */);

    // 3. Choose the grid. Block = 16x16 threads. The grid must have ENOUGH
    //    blocks to cover every pixel, rounding UP so nothing is missed.
    dim3 dimBlock(16, 16, 1);
    dim3 dimGrid(/* TODO 7a: blocks across width */, /* TODO 7b: blocks down height */, 1);

    // 4. Launch the kernel with your grid and block.
    blurKernel<<</* TODO 8: dimGrid, dimBlock */>>>(out_d, in_d, width, height);

    // 5. Copy the finished image back GPU (device) -> CPU (host).
    cudaMemcpy(out_h, out_d, size, /* TODO 9: copy direction, device -> host */);

    // 6. Free the GPU memory.
    cudaFree(in_d);
    cudaFree(out_d);
}

// ---- Read a binary (P6) PPM image from disk (given) ----
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

// ---- Write a binary (P6) PPM image to disk (given) ----
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
