#include <iostream>
#include <cuda_runtime.h>

#define CUDA_CHECK(err) \
    if(err != cudaSuccess){ \
        std::cerr << "CUDA Error: " << cudaGetErrorString(err) << std::endl; \
        exit(EXIT_FAILURE); \
    }

__global__ void add_kernel(int *a, int *b, int *c, int n) {
    int idx = threadIdx.x + blockIdx.x * blockDim.x;
    if (idx < n) c[idx] = a[idx] + b[idx];
}

int main() {
    int n = 10;
    int a[n], b[n], c[n];
    for(int i=0; i<n; i++){ a[i]=i; b[i]=i*2; }

    int *d_a, *d_b, *d_c;
    CUDA_CHECK(cudaMalloc(&d_a, n*sizeof(int)));
    CUDA_CHECK(cudaMalloc(&d_b, n*sizeof(int)));
    CUDA_CHECK(cudaMalloc(&d_c, n*sizeof(int)));

    CUDA_CHECK(cudaMemcpy(d_a, a, n*sizeof(int), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_b, b, n*sizeof(int), cudaMemcpyHostToDevice));

    int threadsPerBlock = 256;
    int blocksPerGrid = (n + threadsPerBlock - 1) / threadsPerBlock;
    add_kernel<<<blocksPerGrid, threadsPerBlock>>>(d_a, d_b, d_c, n);

    CUDA_CHECK(cudaDeviceSynchronize());

    CUDA_CHECK(cudaMemcpy(c, d_c, n*sizeof(int), cudaMemcpyDeviceToHost));

    for(int i=0; i<n; i++) std::cout << c[i] << " ";
    std::cout << std::endl;

    cudaFree(d_a); cudaFree(d_b); cudaFree(d_c);
    return 0;
}
