// DEMO — "it's just a pointer, right?"
//
// cudaMalloc hands back a perfectly ordinary-looking `int*`. It is not
// ordinary. It is an address in a DIFFERENT machine's memory. The CPU
// has no way to follow it. This program proves that, loudly.
#include "lab/gpulab.h"

int main() {
    int* dev;
    CUDA_CHECK(cudaMalloc(&dev, 4 * sizeof(int)));

    printf("cudaMalloc gave us the pointer %p\n", (void*)dev);
    printf("It looks like any other pointer. The CPU will now try to read it.\n\n");
    fflush(stdout);

    int stolen = dev[0];        // <-- the CPU dereferencing GPU memory

    printf("we somehow read %d (you should never get this far)\n", stolen);
    cudaFree(dev);
    return 0;
}
