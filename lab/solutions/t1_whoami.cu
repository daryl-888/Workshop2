// Topic 1 — Which thread am I?  (SOLUTION)
#include "lab/gpulab.h"

__global__ void whoAmI() {
    // Threads are delivered in BLOCKS. Inside its block a thread only knows
    // threadIdx.x (0,1,2,...). To get a unique number across the whole launch,
    // skip past all the blocks that came before you, then add your offset:
    int global = blockIdx.x * blockDim.x + threadIdx.x;

    printf("blockIdx.x=%d  blockDim.x=%d  threadIdx.x=%d   ->  global index %2d\n",
           blockIdx.x, blockDim.x, threadIdx.x, global);
}

int main() {
    // 3 blocks of 4 threads = 12 threads. Their global indices should be 0..11
    // with no gaps and no repeats.
    whoAmI<<<3, 4>>>();
    checkKernel("whoAmI");
    return 0;
}
