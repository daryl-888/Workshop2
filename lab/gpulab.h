// ============================================================
//  lab/gpulab.h — the plumbing, so your cell stays about CUDA.
//
//  You never edit this file. It holds the boring parts: reading and
//  writing PPM images, a stopwatch, a CPU reference blur, and error
//  checking. Every lab file starts with:
//
//      #include "lab/gpulab.h"
//
//  so the code YOU write is only ever the GPU part.
// ============================================================
#ifndef GPULAB_H
#define GPULAB_H

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>

// ------------------------------------------------------------
//  0. Make printf honest
//
//  A notebook captures your program's output through a pipe, and C
//  buffers pipes: the CPU's printf lines would pile up and flush at
//  the very end, AFTER the GPU's. Topic 0 is entirely about the order
//  those lines appear in, so we turn buffering off. This runs before
//  main() does; you never call it.
// ------------------------------------------------------------
struct GpuLabUnbuffered {
    GpuLabUnbuffered() { setvbuf(stdout, nullptr, _IONBF, 0); }
};
static GpuLabUnbuffered _gpulab_unbuffered;

// ------------------------------------------------------------
//  1. Error checking
//
//  CUDA calls do not throw. They return a status code that is very
//  easy to ignore — and then your image is silently black and you
//  have no idea why. These two helpers turn a silent wrong answer
//  into a loud, located message.
// ------------------------------------------------------------

// Wrap any cudaSomething(...) call:  CUDA_CHECK(cudaMalloc(&p, n));
#define CUDA_CHECK(call)                                                     \
    do {                                                                     \
        cudaError_t _err = (call);                                           \
        if (_err != cudaSuccess) {                                           \
            printf("\nCUDA ERROR at %s:%d\n  %s\n  -> %s\n",                 \
                   __FILE__, __LINE__, #call, cudaGetErrorString(_err));     \
            exit(EXIT_FAILURE);                                              \
        }                                                                    \
    } while (0)

// Call this on the line AFTER a <<< >>> launch.
//
// Launching a kernel is asynchronous: the CPU fires it off and keeps
// going without waiting. So a crash inside your kernel shows up later,
// or not at all. This asks two questions: "did the launch itself fail?"
// and then "wait for it to finish — did it crash while running?"
static void checkKernel(const char* name) {
    cudaError_t err = cudaGetLastError();          // did the launch fail?
    if (err != cudaSuccess) {
        // cudaGetLastError also returns errors from calls made BEFORE the
        // launch (a bad cudaMemcpy, say) that nobody checked. Those have a
        // recognisable shape - say so, rather than blaming the kernel.
        if (err == cudaErrorInvalidValue || err == cudaErrorInvalidMemcpyDirection ||
            err == cudaErrorInvalidDevicePointer) {
            printf("\nA CUDA call BEFORE the launch of '%s' failed: %s\n", name,
                   cudaGetErrorString(err));
            printf("  Usually one of:\n");
            printf("   - cudaMemcpy with the wrong direction (over = cudaMemcpyHostToDevice)\n");
            printf("   - cudaMemcpy arguments swapped (destination comes FIRST, then source)\n");
            printf("   - cudaMalloc never ran, so the device pointer holds junk\n");
            exit(EXIT_FAILURE);
        }
        printf("\nKernel '%s' FAILED TO LAUNCH: %s\n", name, cudaGetErrorString(err));
        printf("  (usually a bad grid/block size - e.g. over 1024 threads per block)\n");
        exit(EXIT_FAILURE);
    }
    err = cudaDeviceSynchronize();                 // wait, then: did it crash?
    if (err != cudaSuccess) {
        printf("\nKernel '%s' CRASHED WHILE RUNNING: %s\n", name, cudaGetErrorString(err));
        printf("  (usually an out-of-bounds read/write - check your bounds test)\n");
        exit(EXIT_FAILURE);
    }
}

// ------------------------------------------------------------
//  2. Images
//
//  An Image is just a flat array of bytes, 3 per pixel (R,G,B),
//  stored row by row. That flatness is the whole reason the index
//  math in the lab looks the way it does.
// ------------------------------------------------------------
struct Image {
    int    w = 0;
    int    h = 0;
    size_t bytes = 0;          // w * h * 3
    unsigned char* data = nullptr;
};

// Skip whitespace and #comments in a PPM header.
static void ppmSkipJunk(FILE* f) {
    int c;
    for (;;) {
        c = fgetc(f);
        if (c == '#') { while (c != '\n' && c != EOF) c = fgetc(f); }
        else if (c == ' ' || c == '\t' || c == '\n' || c == '\r') { continue; }
        else { ungetc(c, f); return; }
    }
}

static Image loadImage(const char* path = "images/sample_1920x1280.ppm") {
    Image img;
    FILE* f = fopen(path, "rb");
    if (!f) {
        printf("Could not open '%s'.\n", path);
        printf("  Are you running from the repo root? Try the setup cell again.\n");
        exit(EXIT_FAILURE);
    }
    char magic[3] = {0};
    int maxval = 0;
    ppmSkipJunk(f);
    if (fscanf(f, "%2s", magic) != 1 || strcmp(magic, "P6") != 0) {
        printf("'%s' is not a binary P6 PPM.\n", path); exit(EXIT_FAILURE);
    }
    ppmSkipJunk(f); if (fscanf(f, "%d", &img.w)  != 1) { printf("Bad PPM width\n");  exit(EXIT_FAILURE); }
    ppmSkipJunk(f); if (fscanf(f, "%d", &img.h)  != 1) { printf("Bad PPM height\n"); exit(EXIT_FAILURE); }
    ppmSkipJunk(f); if (fscanf(f, "%d", &maxval) != 1) { printf("Bad PPM maxval\n"); exit(EXIT_FAILURE); }
    fgetc(f);                                  // exactly one whitespace byte before the pixels
    img.bytes = (size_t)img.w * img.h * 3;
    img.data  = (unsigned char*)malloc(img.bytes);
    if (fread(img.data, 1, img.bytes, f) != img.bytes) {
        printf("'%s' ended early - file may be truncated.\n", path); exit(EXIT_FAILURE);
    }
    fclose(f);
    return img;
}

static Image makeImage(int w, int h) {
    Image img;
    img.w = w; img.h = h;
    img.bytes = (size_t)w * h * 3;
    img.data  = (unsigned char*)calloc(img.bytes, 1);
    return img;
}

static void saveImage(const Image& img, const char* path) {
    FILE* f = fopen(path, "wb");
    if (!f) { printf("Could not write '%s'\n", path); return; }
    fprintf(f, "P6\n%d %d\n255\n", img.w, img.h);
    fwrite(img.data, 1, img.bytes, f);
    fclose(f);
    printf("wrote %s (%dx%d)\n", path, img.w, img.h);
}

static void freeImage(Image& img) { free(img.data); img.data = nullptr; }

// ------------------------------------------------------------
//  3. Stopwatches
//
//  Two of them, because there are two computers in the box and each
//  keeps its own time.
// ------------------------------------------------------------

// CPU stopwatch (ordinary wall-clock).
struct CpuTimer {
    std::chrono::high_resolution_clock::time_point t0;
    void start() { t0 = std::chrono::high_resolution_clock::now(); }
    double stop_ms() {
        auto t1 = std::chrono::high_resolution_clock::now();
        return std::chrono::duration<double, std::milli>(t1 - t0).count();
    }
};

// GPU stopwatch. Uses CUDA events, which are timestamps the GPU itself
// records in its own work queue — the only honest way to time a device
// that runs asynchronously from the CPU.
struct GpuTimer {
    cudaEvent_t a, b;
    GpuTimer()  { cudaEventCreate(&a); cudaEventCreate(&b); }
    ~GpuTimer() { cudaEventDestroy(a); cudaEventDestroy(b); }
    void start() { cudaEventRecord(a); }
    float stop_ms() {
        cudaEventRecord(b);
        cudaEventSynchronize(b);
        float ms = 0.f;
        cudaEventElapsedTime(&ms, a, b);
        return ms;
    }
};

// ------------------------------------------------------------
//  4. The same blur, written for the CPU
//
//  Identical math to the kernel you write — but one pixel at a time,
//  in two ordinary nested loops. This is what you race against.
// ------------------------------------------------------------
static void blurOnCPU(const Image& in, Image& out, int radius) {
    for (int row = 0; row < in.h; ++row) {
        for (int col = 0; col < in.w; ++col) {
            int r = 0, g = 0, b = 0, n = 0;
            for (int dr = -radius; dr <= radius; ++dr) {
                for (int dc = -radius; dc <= radius; ++dc) {
                    int cr = row + dr, cc = col + dc;
                    if (cr >= 0 && cr < in.h && cc >= 0 && cc < in.w) {
                        int i = (cr * in.w + cc) * 3;
                        r += in.data[i + 0];
                        g += in.data[i + 1];
                        b += in.data[i + 2];
                        ++n;
                    }
                }
            }
            int o = (row * in.w + col) * 3;
            out.data[o + 0] = (unsigned char)((float)r / n);
            out.data[o + 1] = (unsigned char)((float)g / n);
            out.data[o + 2] = (unsigned char)((float)b / n);
        }
    }
}

#endif  // GPULAB_H
