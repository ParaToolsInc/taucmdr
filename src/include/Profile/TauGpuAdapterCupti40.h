#include <Profile/TauGpu.h>
#include <cupti_events.h>
#include <cupti_callbacks.h>
#include <cupti_runtime_cbid.h>
#include <generated_cuda_runtime_api_meta.h>
#include <cupti_driver_cbid.h>
//Hack need to get this to compile on older version of g++.
#define CUdeviceptr_v1 CUdeviceptr
#define CUDA_MEMCPY2D_v1 CUDA_MEMCPY2D
#define CUDA_MEMCPY3D_v1 CUDA_MEMCPY3D
#define CUDA_ARRAY_DESCRIPTOR_v1 CUDA_ARRAY_DESCRIPTOR
#define CUDA_ARRAY3D_DESCRIPTOR_v1 CUDA_ARRAY3D_DESCRIPTOR
//end Hack
#include <generated_cuda_meta.h>
#include <cuda.h>

#define CUPTI_METRIC_INSTRUCTIONS "CUDA_INS"

double metric_read_cupti(int type);
void metric_read_cupti_ins(int tid, int idx, double values[]);

#define CUDA_CHECK_ERROR(err, str) \
	if (err != CUDA_SUCCESS) \
  { \
		fprintf(stderr, str); \
		exit(1); \
	} \

#define CUPTI_CHECK_ERROR(err, str) \
	if (err != CUPTI_SUCCESS) \
  { \
		fprintf(stderr, str); \
		exit(1); \
	} \

// Structure to hold API parameters
//#define cudaMemcpy cudaMemcpy
/*typedef struct cudaMemcpy_params_st {
    void *dst;
    const void *src;
    size_t count;
    unsigned int kind;
}cudaMemcpy_params;*/

//#define cudaMemcpyToArray cudaMemcpyToArray
/*typedef struct cudaMemcpyToArray_params_st {
    void *dst;
		size_t wOffset;
		size_t hOffset;
    const void *src;
    size_t count;
    unsigned int kind;
}cudaMemcpyToArray_params;*/

//#define cudaMemcpyToSymbol cudaMemcpyToSymbol
/*typedef struct cudaMemcpyToSymbol_params_st {
    void *symbol;
    const void *src;
    size_t count;
		size_t offset;
    unsigned int kind;
}cudaMemcpyToSymbol_params;*/

#define CAST_TO_RUNTIME_MEMCPY_TYPE_AND_CALL(name, id, info, kind, count) \
	if ((id) == CUPTI_RUNTIME_TRACE_CBID_##name##_v3020) \
	{ \
		kind = ((name##_v3020_params *) info->functionParams)->kind; \
		count = ((name##_v3020_params *) info->functionParams)->count; \
	}
			
#define CAST_TO_DRIVER_MEMCPY_TYPE_AND_CALL(name, id, info, kind, count) \
	if ((id) == CUPTI_DRIVER_TRACE_CBID_##name) \
	{ \
		count = ((name##_params *) info->functionParams)->ByteCount; \
	}

#define CAST_TO_DRIVER_CONTEXT_TYPE_AND_CALL(name, id, info, ctx) \
	if ((id) == CUPTI_DRIVER_TRACE_CBID_##name) \
	{ \
		ctx = ((name##_params *) info->functionParams)->pctx; \
	}

#define CAST_TO_RUNTIME_LAUNCH_TYPE_AND_CALL(name, id, info, kind, count) \
	if ((id) == CUPTI_RUNTIME_TRACE_CBID_##name) \
	{ \
		stream = ((name##_params *) info->functionParams)->ByteCount; \
	}

#define CAST_TO_DRIVER_LAUNCH_TYPE_AND_CALL(name, id, info, stream) \
	if ((id) == CUPTI_DRIVER_TRACE_CBID_##name) \
	{ \
		stream = ((name##_params *) info->functionParams)->hStream; \
	}


// Structure to hold data collected by callback
typedef struct RuntimeApiTrace_st {
    CUpti_CallbackData traceInfo;
    uint64_t startTimestamp;
    uint64_t endTimestamp;
    cudaMemcpy_v3020_params memcpy_params;
} RuntimeApiTrace_t;


enum launchOrder{ MEMCPY_H2D1, MEMCPY_H2D2, MEMCPY_D2H, KERNEL, THREAD_SYNC, LAUNCH_LAST};

